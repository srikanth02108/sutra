#!/usr/bin/env python3
"""
Sutra Global Hotkey Tray App
==============================
Runs silently in the Windows system tray.
Press Ctrl+Space ANYWHERE (even when Excel is focused) to start/stop listening.
-> HOTKEY CHANGED TO: Alt+. (Alt + period)

Usage:
    python hotkey_tray.py

This is separate from server.py — run both at the same time:
    Terminal 1: python server.py
    Terminal 2: python hotkey_tray.py   ← this file
    Terminal 3: cd frontend && npm run dev

The tray app talks to the server via HTTP on localhost:8000.
No need to switch to the browser tab to press the mic button.
"""

import os
import sys
import time
import threading
import logging
import webbrowser
from pathlib import Path

import requests
import keyboard
import pystray
from PIL import Image, ImageDraw

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] sutra.tray — %(message)s")
logger = logging.getLogger("sutra.tray")

API_BASE = "http://localhost:8000"
HOTKEY   = "alt+."

# ─── State ───────────────────────────────────────────────────────────────────
_listening  = False
_server_up  = False
_tray_icon  = None


# ─── Server communication ─────────────────────────────────────────────────────
def _get_status() -> dict:
    try:
        r = requests.get(f"{API_BASE}/status", timeout=2)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def _post(endpoint: str) -> bool:
    try:
        r = requests.post(f"{API_BASE}/{endpoint}", timeout=3)
        return r.status_code == 200
    except Exception:
        return False

def _check_server() -> bool:
    try:
        r = requests.get(API_BASE, timeout=2)
        return r.status_code in (200, 404, 422)
    except Exception:
        return False


# ─── Icon drawing ─────────────────────────────────────────────────────────────
def _make_icon(state: str) -> Image.Image:
    """Draw a 64×64 tray icon reflecting agent state."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    colors = {
        "idle":       ("#1a1a2e", "#00d4ff"),   # dark bg, cyan ring
        "listening":  ("#0d2137", "#ff4444"),   # dark bg, red dot
        "processing": ("#0d2137", "#ffaa00"),   # dark bg, amber
        "executing":  ("#0d2137", "#00ff88"),   # dark bg, green
        "offline":    ("#1a1a1a", "#555555"),   # grey
    }
    bg_color, accent = colors.get(state, colors["idle"])

    # Background circle
    draw.ellipse([2, 2, size - 2, size - 2], fill=bg_color, outline=accent, width=3)

    # Center symbol
    cx, cy = size // 2, size // 2
    if state == "idle":
        # Microphone shape
        draw.rounded_rectangle([cx - 8, cy - 16, cx + 8, cy + 4],
                                radius=8, fill=accent)
        draw.arc([cx - 14, cy - 4, cx + 14, cy + 18], 0, 180, fill=accent, width=3)
        draw.line([cx, cy + 18, cx, cy + 26], fill=accent, width=3)
        draw.line([cx - 8, cy + 26, cx + 8, cy + 26], fill=accent, width=3)
    elif state == "listening":
        # Pulsing red dot
        draw.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=accent)
    elif state == "processing":
        # Hourglass-ish spinner arc
        draw.arc([cx - 14, cy - 14, cx + 14, cy + 14], 0, 270, fill=accent, width=4)
    elif state == "executing":
        # Checkmark
        draw.line([cx - 10, cy, cx - 3, cy + 10, cx + 12, cy - 8],
                  fill=accent, width=4)
    else:
        # X for offline
        draw.line([cx - 10, cy - 10, cx + 10, cy + 10], fill=accent, width=4)
        draw.line([cx + 10, cy - 10, cx - 10, cy + 10], fill=accent, width=4)

    return img


# ─── Hotkey handler ───────────────────────────────────────────────────────────
def _on_hotkey():
    global _listening

    if not _server_up:
        logger.warning("Server not running — start server.py first")
        _notify("Sutra", "Backend not running.\nStart: python server.py")
        return

    status = _get_status()
    agent_status = status.get("status", "idle")

    if agent_status == "idle":
        logger.info("Hotkey: starting listen cycle")
        _post("start")
        _notify("Sutra 🎤", "Listening… speak your command")
    else:
        logger.info("Hotkey: stopping (was %s)", agent_status)
        _post("stop")
        _notify("Sutra", "Stopped")


# ─── Desktop notification helper ─────────────────────────────────────────────
def _notify(title: str, message: str):
    """Show a Windows balloon notification via the tray icon."""
    if _tray_icon:
        try:
            _tray_icon.notify(message, title)
        except Exception:
            pass


# ─── Background status poller ────────────────────────────────────────────────
def _status_poll_loop():
    """Poll server every 2 seconds to keep tray icon in sync."""
    global _server_up
    last_state = None

    while True:
        try:
            up = _check_server()
            _server_up = up

            if up:
                data = _get_status()
                state = data.get("status", "idle")
            else:
                state = "offline"

            if state != last_state:
                last_state = state
                _update_tray_icon(state)
                logger.debug("State changed: %s", state)

        except Exception as e:
            logger.debug("Poll error: %s", e)

        time.sleep(2)


def _update_tray_icon(state: str):
    """Update the tray icon image and tooltip."""
    if _tray_icon is None:
        return

    labels = {
        "idle":       "Sutra — Idle (Alt+. to speak)",
        "listening":  "Sutra 🔴 — Listening…",
        "processing": "Sutra ⏳ — Translating…",
        "executing":  "Sutra ⚡ — Executing…",
        "offline":    "Sutra ⚫ — Backend offline",
    }

    try:
        _tray_icon.icon  = _make_icon(state)
        _tray_icon.title = labels.get(state, "Sutra")
    except Exception:
        pass


# ─── Tray menu ────────────────────────────────────────────────────────────────
def _open_dashboard(icon, item):
    webbrowser.open("http://localhost:3000")

def _start_listening(icon, item):
    _on_hotkey()

def _stop_listening(icon, item):
    _post("stop")

def _undo(icon, item):
    if _post("undo"):
        _notify("Sutra", "Undo executed (Ctrl+Z)")

def _quit(icon, item):
    keyboard.unhook_all()
    icon.stop()
    logger.info("Sutra tray exited.")
    sys.exit(0)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    global _tray_icon

    logger.info("Sutra Hotkey Tray starting…")
    logger.info("Hotkey: %s  →  start/stop listening", HOTKEY.upper())
    logger.info("Backend: %s", API_BASE)

    # Register global hotkey
    keyboard.add_hotkey(HOTKEY, _on_hotkey, suppress=False)
    logger.info("Global hotkey registered: %s", HOTKEY)

    # Start background status poller
    poll_thread = threading.Thread(target=_status_poll_loop, daemon=True)
    poll_thread.start()

    # Build tray menu
    menu = pystray.Menu(
        pystray.MenuItem("🎤  Start Listening  (Alt+.)", _start_listening, default=True),
        pystray.MenuItem("⏹  Stop",                          _stop_listening),
        pystray.MenuItem("↩  Undo last action",              _undo),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🌐  Open Dashboard",               _open_dashboard),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✕  Quit Sutra Tray",               _quit),
    )

    # Create tray icon
    icon_image = _make_icon("offline")
    _tray_icon = pystray.Icon(
        name="sutra",
        icon=icon_image,
        title="Sutra — Backend offline",
        menu=menu,
    )

    print("\n" + "=" * 55)
    print("  Sutra Global Hotkey Tray")
    print("=" * 55)
    print(f"  Hotkey : {HOTKEY.upper()} — start/stop listening")
    print(f"  Backend: {API_BASE}")
    print(f"  Tray   : look for the icon in your system tray")
    print("  Right-click the tray icon for more options")
    print("=" * 55 + "\n")

    # Run tray (blocks until quit)
    _tray_icon.run()


if __name__ == "__main__":
    main()
