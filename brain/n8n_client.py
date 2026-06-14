"""Brain module — intent classification + action library lookup.

The LLM's ONLY job is:
  1. Understand what the user wants (natural language → intent)
  2. Pick the matching action_id from the Excel Action Library
  3. Extract any parameters (font size, font name, cell ref, etc.)

The actual key sequences come from excel_actions.py — never from the LLM.
This makes execution 100% reliable regardless of which LLM is used.

Provider cascade: groq → gemini → openai → custom
"""

import json
import logging
import re
import sys
import os
import threading
from datetime import datetime, date
from typing import Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GEMINI_API_KEY, GROQ_API_KEY, OPENAI_API_KEY, LLM_PROVIDER, N8N_WEBHOOK_URL, N8N_TIMEOUT
from excel_actions import REGISTRY, get_steps, get_description, requires_confirmation as action_requires_confirm, build_action_menu_for_llm

logger = logging.getLogger(__name__)

# ─── Provider endpoints ──────────────────────────────────────────────────────
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
GROQ_URL   = "https://api.groq.com/openai/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

PROVIDER_LIMITS = {
    "groq":   {"daily_requests": 14400, "daily_tokens": 500000,  "rpm": 30},
    "gemini": {"daily_requests": 1500,  "daily_tokens": 1000000, "rpm": 15},
    "openai": {"daily_requests": 999999,"daily_tokens": 999999,  "rpm": 500},
    "custom": {"daily_requests": 999999,"daily_tokens": 999999,  "rpm": 999},
}

# ─── Usage tracker ────────────────────────────────────────────────────────────
class UsageTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._data: dict = {}

    def _today(self) -> str:
        return date.today().isoformat()

    def record(self, provider: str, tokens_in: int, tokens_out: int):
        with self._lock:
            today = self._today()
            self._data.setdefault(provider, {}).setdefault(today, {"requests": 0, "tokens_in": 0, "tokens_out": 0})
            self._data[provider][today]["requests"] += 1
            self._data[provider][today]["tokens_in"] += tokens_in
            self._data[provider][today]["tokens_out"] += tokens_out

    def get_today(self, provider: str) -> dict:
        with self._lock:
            today = self._today()
            return self._data.get(provider, {}).get(today, {"requests": 0, "tokens_in": 0, "tokens_out": 0}).copy()

    def get_usage_pct(self, provider: str) -> float:
        today = self.get_today(provider)
        limit = PROVIDER_LIMITS.get(provider, {}).get("daily_requests", 1)
        return min(100.0, round(today["requests"] / limit * 100, 1))

    def get_all_stats(self) -> dict:
        result = {}
        for p in ["groq", "gemini", "openai", "custom"]:
            today = self.get_today(p)
            limits = PROVIDER_LIMITS.get(p, {})
            result[p] = {
                **today,
                "daily_request_limit": limits.get("daily_requests", 0),
                "usage_pct": self.get_usage_pct(p),
            }
        return result

usage = UsageTracker()

# ─── Runtime provider config ──────────────────────────────────────────────────
class ProviderConfig:
    def __init__(self):
        self._lock = threading.Lock()
        self.provider: str = LLM_PROVIDER
        self.keys: dict = {
            "groq":   GROQ_API_KEY,
            "gemini": GEMINI_API_KEY,
            "openai": OPENAI_API_KEY,
            "custom": "",
        }
        self.custom_url:   str = ""
        self.custom_model: str = ""

    def set_provider(self, p: str):
        with self._lock:
            self.provider = p.lower()
        logger.info("Provider → %s", self.provider)

    def set_key(self, provider: str, key: str):
        with self._lock:
            self.keys[provider.lower()] = key

    def set_custom(self, url: str, model: str, key: str = ""):
        with self._lock:
            self.custom_url = url
            self.custom_model = model
            self.keys["custom"] = key

    def get(self) -> dict:
        with self._lock:
            return {
                "provider": self.provider,
                "custom_url": self.custom_url,
                "custom_model": self.custom_model,
                "keys_set": {k: bool(v) for k, v in self.keys.items()},
            }

provider_config = ProviderConfig()

# ─── System prompt ────────────────────────────────────────────────────────────
# Build once at import time — includes the full action menu
_ACTION_MENU = build_action_menu_for_llm()

SYSTEM_PROMPT = f"""You are the brain of Sutra, a voice-controlled Excel assistant.
The user speaks in Hindi or Marathi. Their speech is translated to English for you.

YOUR ONLY JOB: understand the user's intent and return a JSON object selecting
the correct action_id from the Action Library below, plus any required parameters.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT — return ONLY this JSON, nothing else:
{{
  "action_id": "bold",
  "params": {{}},
  "plan": "Make selected text bold",
  "confidence": "high"
}}

If the user wants multiple things done sequentially, return an array:
{{
  "actions": [
    {{"action_id": "bold", "params": {{}}}},
    {{"action_id": "align_center", "params": {{}}}}
  ],
  "plan": "Make text bold and center-align it",
  "confidence": "high"
}}

confidence must be "high", "medium", or "low".
If confidence is "low", still pick the best match but explain in plan.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARAMETER TYPES:
- size: integer (e.g. 8, 10, 11, 12, 14, 16, 18, 20, 24, 28, 36)
- font_name: string (e.g. "Arial", "Calibri", "Times New Roman", "Verdana")
- width: number (e.g. 15, 20, 25, 30)
- height: number (e.g. 15, 20, 25, 30)
- cell_ref: string (e.g. "A1", "B5", "C10", "D:D")
- text: string (what to type)
- formula: string starting with = (e.g. "=SUM(A1:A10)")

INTENT EXAMPLES:
- "make it bold" → bold
- "font size 16 karo" → set_font_size, size=16
- "column width badao autofit" → autofit_column_width
- "column width 25 set karo" → set_column_width, width=25
- "row ki height 30 karo" → set_row_height, height=30
- "text ko wrap karo" → wrap_text
- "merge karke center karo" → merge_and_center
- "Arial font lagao" → set_font, font_name="Arial"
- "percentage format karo" → format_percentage
- "borders lagao sab taraf" → borders_all
- "ek naya row add karo" → insert_row
- "row delete karo" → delete_row
- "first row freeze karo" → freeze_top_row
- "filter lagao" → toggle_filter
- "A1 pe jao" → go_to_cell, cell_ref="A1"
- "save karo" → save
- "sort A to Z karo" → sort_ascending
- "sum nikalo" → autosum
- "undo karo" → undo
- "bold aur center karo" → [bold, align_center]
- "header format karo size 14" → format_as_header, size=14
- "currency format karo with borders" → format_currency_borders

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXCEL ACTION LIBRARY (pick action_id from this list):
{_ACTION_MENU}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

DEFAULT_ERROR_PLAN = {
    "plan": "Sorry, I could not understand that command.",
    "requires_confirmation": False,
    "steps": [],
    "action_ids": [],
}


# ─── Main client ─────────────────────────────────────────────────────────────
class N8NClient:
    """Intent classifier + action library executor."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or N8N_WEBHOOK_URL

    def send_command(self, user_text: str, context: str = "") -> dict:
        """Classify intent, look up action library, return executable step plan."""
        # 1. Ask LLM to classify intent
        intent = self._classify_intent(user_text, context)
        if not intent:
            return DEFAULT_ERROR_PLAN

        # 2. Build the execution plan from the action library
        return self._build_plan(intent, user_text)

    def _classify_intent(self, user_text: str, context: str) -> Optional[dict]:
        """Call LLM to get intent JSON. Try providers in order."""
        p = provider_config.provider

        if p == "groq" and provider_config.keys.get("groq"):
            result = self._call_openai_compat(
                url=GROQ_URL,
                key=provider_config.keys["groq"],
                model="llama-3.3-70b-versatile",
                user_text=user_text, context=context,
                provider_name="groq", force_json=True,
            )
            if result: return result

        if p in ("groq", "gemini") and provider_config.keys.get("gemini"):
            result = self._call_gemini(user_text, context)
            if result: return result

        if p == "openai" and provider_config.keys.get("openai"):
            result = self._call_openai_compat(
                url=OPENAI_URL,
                key=provider_config.keys["openai"],
                model="gpt-4o-mini",
                user_text=user_text, context=context,
                provider_name="openai", force_json=True,
            )
            if result: return result

        if p == "custom" and provider_config.custom_url:
            result = self._call_openai_compat(
                url=provider_config.custom_url,
                key=provider_config.keys.get("custom", ""),
                model=provider_config.custom_model,
                user_text=user_text, context=context,
                provider_name="custom", force_json=False,
            )
            if result: return result

        return None

    def _build_plan(self, intent: dict, user_text: str) -> dict:
        """Convert LLM intent JSON → executable step plan using action library."""
        plan_text = intent.get("plan", "Executing command")
        all_steps = []
        all_action_ids = []
        needs_confirm = False

        # Handle single action or multi-action
        if "actions" in intent:
            action_list = intent["actions"]
        elif "action_id" in intent:
            action_list = [{"action_id": intent["action_id"], "params": intent.get("params", {})}]
        else:
            logger.warning("LLM returned no action_id: %s", intent)
            return DEFAULT_ERROR_PLAN

        for item in action_list:
            action_id = item.get("action_id", "")
            params = item.get("params") or {}

            if action_id not in REGISTRY:
                # Try fuzzy match
                action_id = self._fuzzy_match(action_id)
                if not action_id:
                    logger.warning("Unknown action_id: %s", item.get("action_id"))
                    continue

            try:
                steps = get_steps(action_id, **params)
                all_steps.extend(steps)
                all_action_ids.append(action_id)
                if action_requires_confirm(action_id):
                    needs_confirm = True
            except Exception as e:
                logger.error("get_steps(%s, %s) failed: %s", action_id, params, e)

        if not all_steps:
            return {
                "plan": f"I understood '{plan_text}' but couldn't find matching actions.",
                "requires_confirmation": False,
                "steps": [],
                "action_ids": [],
            }

        return {
            "plan": plan_text,
            "requires_confirmation": needs_confirm,
            "steps": all_steps,
            "action_ids": all_action_ids,
        }

    def _fuzzy_match(self, action_id: str) -> Optional[str]:
        """Try to find the closest matching action_id."""
        action_id = action_id.lower().replace(" ", "_").replace("-", "_")
        if action_id in REGISTRY:
            return action_id
        # partial match
        for key in REGISTRY:
            if action_id in key or key in action_id:
                logger.info("Fuzzy matched %r → %r", action_id, key)
                return key
        return None

    def health_check(self) -> bool:
        try:
            return requests.get("http://localhost:5678", timeout=5).status_code == 200
        except Exception:
            return False

    # ── LLM callers ──────────────────────────────────────────────────────────

    def _build_user_message(self, user_text: str, context: str) -> str:
        msg = ""
        if context:
            msg += f"[User preferences]\n{context}\n\n"
        msg += f"User said: {user_text}"
        return msg

    def _call_openai_compat(self, url, key, model, user_text, context,
                             provider_name, force_json=False) -> Optional[dict]:
        if not url or not key:
            return None
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        payload: dict = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": self._build_user_message(user_text, context)},
            ],
            "temperature": 0.0,
            "max_tokens": 512,
        }
        if force_json:
            payload["response_format"] = {"type": "json_object"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            r.raise_for_status()
            data = r.json()
            raw = data["choices"][0]["message"]["content"]
            u = data.get("usage", {})
            usage.record(provider_name,
                u.get("prompt_tokens", len(user_text)//4),
                u.get("completion_tokens", len(raw)//4))
            return self._parse_intent(raw)
        except Exception as e:
            logger.error("%s failed: %s", provider_name, e)
            return None

    def _call_gemini(self, user_text: str, context: str) -> Optional[dict]:
        key = provider_config.keys.get("gemini", GEMINI_API_KEY)
        if not key:
            return None
        full_prompt = SYSTEM_PROMPT + "\n\n" + self._build_user_message(user_text, context)
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": 0.0, "maxOutputTokens": 512},
        }
        try:
            r = requests.post(f"{GEMINI_URL}?key={key}", json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            raw = data["candidates"][0]["content"]["parts"][0]["text"]
            meta = data.get("usageMetadata", {})
            usage.record("gemini",
                meta.get("promptTokenCount", len(user_text)//4),
                meta.get("candidatesTokenCount", len(raw)//4))
            return self._parse_intent(raw)
        except Exception as e:
            logger.error("Gemini failed: %s", e)
            return None

    def _parse_intent(self, raw: str) -> Optional[dict]:
        """Parse LLM JSON response into intent dict."""
        try:
            cleaned = re.sub(r"```json\n?", "", raw).replace("```", "").strip()
            parsed = json.loads(cleaned)
            # Validate it has at least action_id or actions
            if "action_id" not in parsed and "actions" not in parsed:
                logger.warning("LLM response missing action_id/actions: %s", parsed)
                return None
            return parsed
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Parse failed: %s | raw: %.200s", e, raw)
            return None


# ── Standalone test ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s")

    client = N8NClient()
    tests = [
        "bold karo",
        "font size 16 set karo",
        "column ki width autofit karo",
        "row height 30 karo",
        "text ko wrap karo",
        "merge karke center karo",
        "Arial font lagao",
        "borders sab taraf lagao",
        "freeze the top row",
        "A1 pe navigate karo",
        "save karo",
        "undo karo",
        "percentage format karo",
        "new row add karo",
        "bold aur center dono karo",
        "header format karo 14 size mein",
    ]

    print(f"\nProvider: {provider_config.provider} | Actions available: {len(REGISTRY)}\n" + "=" * 70)
    for cmd in tests:
        result = client.send_command(cmd)
        print(f"\n'{cmd}'")
        print(f"  Plan:    {result['plan']}")
        print(f"  Actions: {result.get('action_ids', [])}")
        print(f"  Steps:   {len(result['steps'])} steps")
        print(f"  Confirm: {result['requires_confirmation']}")
