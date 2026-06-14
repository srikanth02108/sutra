#!/usr/bin/env python3
"""
Sutra FastAPI Bridge Server
============================
  ws://localhost:8000/ws          — real-time state events
  POST /start                     — begin listen cycle
  POST /stop                      — abort current cycle
  POST /undo                      — Ctrl+Z immediately
  GET  /status                    — full state snapshot
  GET  /config                    — current provider + key status
  POST /config                    — switch provider / set API keys
  GET  /usage                     — token/request usage per provider
"""

import asyncio
import json
import logging
import os
import sys
import threading
import time
from datetime import datetime
from typing import Optional

import pyautogui
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from ears.vad_listener import VoiceListener
from ears.sarvam_stt import SarvamSTT
from brain.n8n_client import N8NClient, provider_config, usage
from hands.actuator import Actuator
from voice.tts_speaker import TTSSpeaker
from memory.mem0_manager import MemoryManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("sutra.server")
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

app = FastAPI(title="Sutra Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow any origin (Vercel preview URLs, ngrok, localhost)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models for /config POST ─────────────────────────────────────────
class ConfigUpdate(BaseModel):
    provider:      Optional[str] = None   # "groq" | "gemini" | "openai" | "custom"
    groq_key:      Optional[str] = None
    gemini_key:    Optional[str] = None
    openai_key:    Optional[str] = None
    custom_url:    Optional[str] = None
    custom_model:  Optional[str] = None
    custom_key:    Optional[str] = None

# ── global shared state ───────────────────────────────────────────────────────
class AgentState:
    def __init__(self):
        self.status: str = "idle"
        self.command_count: int = 0
        self.last_hindi: str = ""
        self.last_english: str = ""
        self.last_plan: str = ""
        self.last_steps: list = []
        self.memories: list = []
        self.transcript: list = []
        self._abort: bool = False
        self._lock = threading.Lock()

    def set_status(self, s: str):
        with self._lock:
            self.status = s
        if loop and not loop.is_closed():
            asyncio.run_coroutine_threadsafe(broadcast_state(), loop)

    def abort(self):
        with self._lock:
            self._abort = True

    def clear_abort(self):
        with self._lock:
            self._abort = False

    def should_abort(self) -> bool:
        with self._lock:
            return self._abort

    def to_dict(self) -> dict:
        with self._lock:
            cfg = provider_config.get()
            usage_stats = usage.get_all_stats()
            return {
                "type": "state",
                "status": self.status,
                "command_count": self.command_count,
                "last_hindi": self.last_hindi,
                "last_english": self.last_english,
                "last_plan": self.last_plan,
                "last_steps": self.last_steps,
                "memories": self.memories,
                "transcript": self.transcript[-50:],
                "provider": cfg["provider"],
                "keys_set": cfg["keys_set"],
                "usage": usage_stats,
            }


state = AgentState()
loop: asyncio.AbstractEventLoop = None
connected_clients: list[WebSocket] = []

listener:     Optional[VoiceListener] = None
stt:          Optional[SarvamSTT]     = None
brain:        Optional[N8NClient]     = None
actuator:     Optional[Actuator]      = None
speaker:      Optional[TTSSpeaker]    = None
memory:       Optional[MemoryManager] = None
agent_thread: Optional[threading.Thread] = None


# ── broadcast helpers ─────────────────────────────────────────────────────────
async def broadcast_state():
    if not connected_clients:
        return
    msg = json.dumps(state.to_dict())
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in connected_clients:
            connected_clients.remove(ws)


async def broadcast_event(event: dict):
    if not connected_clients:
        return
    msg = json.dumps(event)
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in connected_clients:
            connected_clients.remove(ws)


def emit(event: dict):
    if loop and not loop.is_closed():
        asyncio.run_coroutine_threadsafe(broadcast_event(event), loop)


# ── agent pipeline ────────────────────────────────────────────────────────────
def run_listen_cycle():
    global agent_thread

    if state.status != "idle":
        return

    state.clear_abort()

    try:
        # Step 1 — Listen
        state.set_status("listening")
        emit({"type": "status", "status": "listening"})

        try:
            audio = listener.record_until_silence()
        except Exception as e:
            emit({"type": "error", "message": f"Recording failed: {e}"})
            state.set_status("idle")
            return

        if state.should_abort() or not audio or len(audio) < 1000:
            state.set_status("idle")
            return

        # Step 2 — Translate
        state.set_status("processing")
        emit({"type": "status", "status": "processing"})

        english_text = stt.transcribe_and_translate(audio)
        if not english_text or not english_text.strip():
            emit({"type": "error", "message": "Couldn't hear anything clearly"})
            speaker.speak("I didn't catch that. Please try again.")
            state.set_status("idle")
            return

        with state._lock:
            state.last_english = english_text
            state.last_hindi = english_text

        emit({"type": "transcript_partial", "english": english_text})

        if state.should_abort():
            state.set_status("idle")
            return

        # Step 3 — Memory context
        context = memory.get_context(english_text)
        with state._lock:
            state.memories = memory.get_all_memories()

        # Step 4 — Plan
        plan = brain.send_command(english_text, context)
        plan_text = plan.get("plan", "")
        steps = plan.get("steps", [])
        requires_confirmation = plan.get("requires_confirmation", False)

        with state._lock:
            state.last_plan = plan_text
            state.last_steps = steps

        # Broadcast updated usage after LLM call
        emit({"type": "plan", "plan": plan_text, "steps": steps,
              "requires_confirmation": requires_confirmation,
              "usage": usage.get_all_stats(),
              "provider": provider_config.provider})

        if not steps:
            emit({"type": "error", "message": f"No actions found for: {english_text}"})
            speaker.speak("I understood, but I don't have steps for that.")
            state.set_status("idle")
            return

        if state.should_abort():
            state.set_status("idle")
            return

        # Step 5 — Confirmation for destructive actions
        if requires_confirmation:
            emit({"type": "confirm_required", "plan": plan_text})
            speaker.speak(f"I'm about to {plan_text}. Say yes or no.")
            try:
                confirm_audio = listener.record_until_silence()
                confirm_text = stt.transcribe_and_translate(confirm_audio).lower()
                affirmative = ["yes","yeah","ok","sure","haan","ha","proceed","do it","karo","kar do"]
                confirmed = any(w in confirm_text for w in affirmative)
            except Exception:
                confirmed = False

            if not confirmed:
                emit({"type": "aborted", "reason": "User cancelled"})
                speaker.speak("Okay, cancelled.")
                state.set_status("idle")
                return

        # Step 6 — Execute
        state.set_status("executing")
        emit({"type": "status", "status": "executing"})

        try:
            success = actuator.execute_plan(steps)
        except pyautogui.FailSafeException:
            emit({"type": "error", "message": "Failsafe triggered — mouse moved to corner"})
            state.set_status("idle")
            return
        except Exception as e:
            emit({"type": "error", "message": f"Execution error: {e}"})
            state.set_status("idle")
            return

        # Step 7 — Report + learn
        with state._lock:
            state.command_count += 1
            entry = {
                "id": int(time.time() * 1000),
                "hindi": state.last_hindi,
                "english": english_text,
                "plan": plan_text,
                "steps": steps,
                "success": success,
                "time": datetime.now().strftime("%H:%M:%S"),
            }
            state.transcript.append(entry)

        emit({"type": "transcript_entry", "entry": entry})

        if success:
            speaker.speak("Done!")
            # ── Verification popup ──────────────────────────────────────
            emit({
                "type": "verify",
                "plan": plan_text,
                "action_ids": plan.get("action_ids", []),
                "steps_count": len(steps),
                "message": f"✓ Completed: {plan_text}",
            })
            # Learn from this interaction
            threading.Thread(
                target=lambda: memory.save_from_conversation(english_text, plan_text),
                daemon=True,
            ).start()
            with state._lock:
                state.memories = memory.get_all_memories()
            if loop and not loop.is_closed():
                asyncio.run_coroutine_threadsafe(broadcast_state(), loop)
        else:
            speaker.speak("Some steps failed.")
            emit({"type": "error", "message": "Some steps failed — check that Excel is open and in focus"})

    except Exception as e:
        logger.exception("Pipeline error: %s", e)
        emit({"type": "error", "message": str(e)})
    finally:
        state.set_status("idle")


# ── REST endpoints ────────────────────────────────────────────────────────────
@app.get("/status")
def get_status():
    return state.to_dict()


@app.post("/start")
def start_listening():
    global agent_thread
    if state.status != "idle":
        return {"ok": False, "message": "Already running"}
    agent_thread = threading.Thread(target=run_listen_cycle, daemon=True)
    agent_thread.start()
    return {"ok": True}


@app.post("/stop")
def stop_listening():
    state.abort()
    if speaker:
        speaker.stop()
    state.set_status("idle")
    return {"ok": True}


@app.post("/undo")
def undo_last():
    try:
        actuator.execute_plan([{"action": "hotkey", "keys": ["ctrl", "z"]}])
        emit({"type": "undo", "message": "Undo executed (Ctrl+Z)"})
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "message": str(e)}


@app.get("/config")
def get_config():
    cfg = provider_config.get()
    return {
        "provider": cfg["provider"],
        "keys_set": cfg["keys_set"],
        "custom_url": cfg["custom_url"],
        "custom_model": cfg["custom_model"],
        "available_providers": ["groq", "gemini", "openai", "custom"],
    }


@app.post("/config")
def update_config(body: ConfigUpdate):
    """Switch provider and/or update API keys at runtime — no restart needed."""
    changed = []

    if body.provider:
        provider_config.set_provider(body.provider)
        changed.append(f"provider={body.provider}")

    if body.groq_key is not None:
        provider_config.set_key("groq", body.groq_key)
        changed.append("groq_key")

    if body.gemini_key is not None:
        provider_config.set_key("gemini", body.gemini_key)
        changed.append("gemini_key")

    if body.openai_key is not None:
        provider_config.set_key("openai", body.openai_key)
        changed.append("openai_key")

    if body.custom_url or body.custom_model:
        provider_config.set_custom(
            url=body.custom_url or provider_config.custom_url,
            model=body.custom_model or provider_config.custom_model,
            key=body.custom_key or provider_config.keys.get("custom", ""),
        )
        changed.append("custom")

    # Broadcast updated config to all connected frontends
    emit({"type": "config_changed",
          "provider": provider_config.provider,
          "keys_set": provider_config.get()["keys_set"]})

    return {"ok": True, "changed": changed, "config": provider_config.get()}


@app.get("/usage")
def get_usage():
    return usage.get_all_stats()


# ── WebSocket ─────────────────────────────────────────────────────────────────
@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    logger.info("Frontend connected (%d total)", len(connected_clients))

    # Full state on connect
    await ws.send_text(json.dumps(state.to_dict()))

    try:
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
            except Exception:
                continue

            cmd = msg.get("command")

            if cmd == "start":
                global agent_thread
                if state.status == "idle":
                    agent_thread = threading.Thread(target=run_listen_cycle, daemon=True)
                    agent_thread.start()

            elif cmd == "stop":
                state.abort()
                if speaker:
                    speaker.stop()
                state.set_status("idle")

            elif cmd == "undo":
                threading.Thread(
                    target=lambda: actuator.execute_plan([{"action": "hotkey", "keys": ["ctrl", "z"]}]),
                    daemon=True,
                ).start()
                emit({"type": "undo", "message": "Undo executed"})

            elif cmd == "set_provider":
                provider_config.set_provider(msg.get("provider", "groq"))
                emit({"type": "config_changed",
                      "provider": provider_config.provider,
                      "keys_set": provider_config.get()["keys_set"]})

            elif cmd == "set_key":
                provider_config.set_key(msg.get("provider", ""), msg.get("key", ""))
                emit({"type": "config_changed",
                      "provider": provider_config.provider,
                      "keys_set": provider_config.get()["keys_set"]})

            elif cmd == "set_custom":
                provider_config.set_custom(
                    msg.get("url", ""),
                    msg.get("model", ""),
                    msg.get("key", ""),
                )
                emit({"type": "config_changed",
                      "provider": provider_config.provider,
                      "keys_set": provider_config.get()["keys_set"]})

            elif cmd == "get_usage":
                await ws.send_text(json.dumps({"type": "usage", "data": usage.get_all_stats()}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        if ws in connected_clients:
            connected_clients.remove(ws)
        logger.info("Frontend disconnected (%d total)", len(connected_clients))


# ── startup / shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    global listener, stt, brain, actuator, speaker, memory, loop

    loop = asyncio.get_running_loop()
    logger.info("Initializing Sutra components...")

    try:
        listener = VoiceListener()
        logger.info("✅ VoiceListener (Silero VAD)")
    except Exception as e:
        logger.error("❌ VoiceListener: %s", e)

    stt = SarvamSTT()
    logger.info("✅ SarvamSTT")

    brain = N8NClient()
    logger.info("✅ Brain (%s)", provider_config.provider)

    actuator = Actuator()
    logger.info("✅ Actuator")

    speaker = TTSSpeaker()
    logger.info("✅ TTSSpeaker")

    memory = MemoryManager()
    state.memories = memory.get_all_memories()
    logger.info("✅ Memory (%d facts)", memory.memory_count())

    logger.info("🚀 Ready — http://localhost:8000  |  ws://localhost:8000/ws")


@app.on_event("shutdown")
async def shutdown():
    if listener:
        listener.cleanup()
    logger.info("Sutra stopped.")


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False, log_level="warning")
