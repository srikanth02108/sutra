"""
Sutra Configuration Module
===========================

Centralized configuration for the Sutra voice-controlled desktop automation agent.
All settings — API keys, audio parameters, VAD thresholds, TTS voices, and UI
automation tweaks — live here so every other module can simply
``from config import ...``.

API keys are loaded from environment variables with hardcoded fallback defaults
for local development.  In production, set the corresponding env vars instead.
"""

import os
import logging
from pathlib import Path

# Load .env file if present (before anything else reads os.environ)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API Keys (loaded from environment variables — set in .env or system env)
# ---------------------------------------------------------------------------
SARVAM_API_KEY: str = os.environ.get("SARVAM_API_KEY", "")
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
GROQ_API_KEY:   str = os.environ.get("GROQ_API_KEY", "")
OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")

# LLM provider: "groq" (recommended) or "gemini" or "openai" or "custom"
LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "groq")

if not SARVAM_API_KEY:
    logger.warning("SARVAM_API_KEY not set — STT will not work")
if not GROQ_API_KEY and not GEMINI_API_KEY:
    logger.warning("Neither GROQ_API_KEY nor GEMINI_API_KEY set — brain will not work")

# ---------------------------------------------------------------------------
# n8n Configuration
# ---------------------------------------------------------------------------
N8N_WEBHOOK_URL: str = os.environ.get(
    "N8N_WEBHOOK_URL", "http://localhost:5678/webhook/sutra"
)
N8N_TIMEOUT: int = 30  # seconds

# ---------------------------------------------------------------------------
# Audio Configuration
# ---------------------------------------------------------------------------
SAMPLE_RATE: int = 16000
CHUNK_SIZE: int = 512
AUDIO_FORMAT: str = "paInt16"  # PyAudio format constant name
CHANNELS: int = 1

# ---------------------------------------------------------------------------
# VAD (Voice Activity Detection) Configuration
# ---------------------------------------------------------------------------
VAD_THRESHOLD: float = 0.5       # Speech probability threshold
SILENCE_DURATION: float = 1.5    # Seconds of silence before ending recording
MIN_SPEECH_DURATION: float = 0.5  # Minimum speech duration in seconds

# ---------------------------------------------------------------------------
# Push-to-Talk
# ---------------------------------------------------------------------------
HOTKEY: str = "alt+."  # Activation hotkey

# ---------------------------------------------------------------------------
# TTS (Text-to-Speech) Configuration
# ---------------------------------------------------------------------------
TTS_VOICE_EN: str = "en-US-JennyNeural"
TTS_VOICE_HI: str = "hi-IN-SwaraNeural"
TTS_RATE: int = 24000  # edge-tts output sample rate

# ---------------------------------------------------------------------------
# PyAutoGUI / Desktop Automation Configuration
# ---------------------------------------------------------------------------
MOUSE_DURATION: float = 0.5      # Seconds for mouse movement animations
TYPING_INTERVAL: float = 0.05    # Seconds between keystrokes
ACTION_DELAY_MIN: float = 0.3    # Min delay between sequential actions
ACTION_DELAY_MAX: float = 0.7    # Max delay between sequential actions

# ---------------------------------------------------------------------------
# Sarvam AI Configuration
# ---------------------------------------------------------------------------
SARVAM_MODEL: str = "saaras:v3"
SARVAM_STT_MODE: str = "translate"  # translate = Hindi -> English directly


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask(secret: str, visible: int = 4) -> str:
    """Return a masked version of *secret*, showing only the last *visible* chars."""
    if len(secret) <= visible:
        return "****"
    return "*" * (len(secret) - visible) + secret[-visible:]


def print_config() -> None:
    """Display the current configuration to the console, masking API keys."""
    config_lines = f"""
╔══════════════════════════════════════════════════════╗
║              SUTRA — Current Configuration           ║
╠══════════════════════════════════════════════════════╣
║  API Keys                                            ║
║    SARVAM_API_KEY   : {_mask(SARVAM_API_KEY):<32s}║
║    GEMINI_API_KEY   : {_mask(GEMINI_API_KEY):<32s}║
║                                                      ║
║  n8n                                                 ║
║    Webhook URL      : {N8N_WEBHOOK_URL:<32s}║
║    Timeout          : {N8N_TIMEOUT:<32d}║
║                                                      ║
║  Audio                                               ║
║    Sample Rate      : {SAMPLE_RATE:<32d}║
║    Chunk Size       : {CHUNK_SIZE:<32d}║
║    Format           : {AUDIO_FORMAT:<32s}║
║    Channels         : {CHANNELS:<32d}║
║                                                      ║
║  VAD                                                 ║
║    Threshold        : {VAD_THRESHOLD:<32.2f}║
║    Silence Duration : {SILENCE_DURATION:<32.2f}║
║    Min Speech Dur.  : {MIN_SPEECH_DURATION:<32.2f}║
║                                                      ║
║  Hotkey             : {HOTKEY:<32s}║
║                                                      ║
║  TTS                                                 ║
║    Voice (EN)       : {TTS_VOICE_EN:<32s}║
║    Voice (HI)       : {TTS_VOICE_HI:<32s}║
║    Output Rate      : {TTS_RATE:<32d}║
║                                                      ║
║  Automation                                          ║
║    Mouse Duration   : {MOUSE_DURATION:<32.2f}║
║    Typing Interval  : {TYPING_INTERVAL:<32.2f}║
║    Action Delay     : {ACTION_DELAY_MIN:.2f}–{ACTION_DELAY_MAX:.2f}s{'':<25s}║
║                                                      ║
║  Sarvam AI                                           ║
║    Model            : {SARVAM_MODEL:<32s}║
║    STT Mode         : {SARVAM_STT_MODE:<32s}║
╚══════════════════════════════════════════════════════╝
"""
    print(config_lines)
    logger.info("Configuration printed to console.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print_config()
