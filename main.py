#!/usr/bin/env python3
"""
Sutra — Voice-Controlled Desktop Automation Agent
Main orchestration loop that ties all components together.

Usage:
    python main.py

Press Alt+. (Alt + period) to speak a command in Hindi/Marathi.
The agent translates, plans, and executes desktop actions automatically.
Press Ctrl+C to exit.
"""

import sys
import os
import logging
import time
import json
from datetime import datetime

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from config import (
    SARVAM_API_KEY, GEMINI_API_KEY, N8N_WEBHOOK_URL,
    HOTKEY, TTS_VOICE_EN, TTS_VOICE_HI
)
from ears.vad_listener import VoiceListener
from ears.sarvam_stt import SarvamSTT
from brain.n8n_client import N8NClient
from hands.actuator import Actuator
from voice.tts_speaker import TTSSpeaker
from memory.mem0_manager import MemoryManager

# ─── Logging Setup ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(name)-20s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("sutra.main")

# Suppress noisy loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("pyaudio").setLevel(logging.WARNING)


# ─── Console Dashboard ──────────────────────────────────────────────────────

BANNER = r"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ███████╗██╗   ██╗████████╗██████╗  █████╗                ║
║     ██╔════╝██║   ██║╚══██╔══╝██╔══██╗██╔══██╗               ║
║     ███████╗██║   ██║   ██║   ██████╔╝███████║               ║
║     ╚════██║██║   ██║   ██║   ██╔══██╗██╔══██║               ║
║     ███████║╚██████╔╝   ██║   ██║  ██║██║  ██║               ║
║     ╚══════╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝               ║
║                                                              ║
║     Voice-Controlled Desktop Automation Agent                ║
║     Speak in Hindi/Marathi → Actions in Excel                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

def print_status(state: str, details: str = ""):
    """Print a formatted status line."""
    icons = {
        "LISTENING": "🎤",
        "RECORDING": "🔴",
        "TRANSLATING": "🗣️",
        "THINKING": "🧠",
        "CONFIRMING": "❓",
        "EXECUTING": "🖱️",
        "SPEAKING": "🔊",
        "DONE": "✅",
        "ERROR": "❌",
        "READY": "⚡",
    }
    icon = icons.get(state, "▶")
    timestamp = datetime.now().strftime("%H:%M:%S")
    detail_str = f" │ {details}" if details else ""
    print(f"\n  {icon}  [{timestamp}] {state}{detail_str}")


def print_separator():
    print("  " + "─" * 58)


# ─── Confirmation Flow ───────────────────────────────────────────────────────

def get_voice_confirmation(listener: VoiceListener, stt: SarvamSTT, speaker: TTSSpeaker, plan_text: str) -> bool:
    """Ask user for voice confirmation of a destructive action.
    
    Returns True if user confirms, False otherwise.
    """
    # Speak the plan
    speaker.speak(f"I'm about to: {plan_text}. Should I proceed? Say yes or no.")
    
    print_status("CONFIRMING", "Say 'yes/haan' to confirm or 'no/nahi' to cancel")
    
    # Listen for response
    try:
        audio = listener.listen()
        if not audio:
            return False
        
        response = stt.transcribe_and_translate(audio)
        response_lower = response.lower().strip()
        
        # Check for affirmative responses (English + Hindi transliterations)
        affirmative = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed",
                       "go ahead", "do it", "confirm", "haan", "ha", "theek hai",
                       "kar do", "karo"]
        
        for word in affirmative:
            if word in response_lower:
                print_status("DONE", f"Confirmed: '{response}'")
                return True
        
        print_status("DONE", f"Denied: '{response}'")
        return False
    
    except Exception as e:
        logger.error(f"Confirmation error: {e}")
        return False


# ─── Main Loop ───────────────────────────────────────────────────────────────

def run():
    """Main application loop."""
    print(BANNER)
    
    # ── Initialize Components ──
    print("  Initializing components...")
    print_separator()
    
    try:
        listener = VoiceListener()
        print("  ✅ Voice Listener (Silero VAD + PyAudio)")
    except Exception as e:
        print(f"  ❌ Voice Listener failed: {e}")
        print("  ⚠️  Make sure PyAudio is installed and a microphone is connected.")
        sys.exit(1)
    
    stt = SarvamSTT()
    print(f"  ✅ Sarvam STT (API key: ...{SARVAM_API_KEY[-8:]})")
    
    brain = N8NClient()
    print(f"  ✅ n8n Client ({N8N_WEBHOOK_URL})")
    
    actuator = Actuator()
    print("  ✅ Actuator (PyAutoGUI)")
    
    speaker = TTSSpeaker()
    print(f"  ✅ TTS Speaker ({TTS_VOICE_EN})")
    
    memory = MemoryManager()
    print("  ✅ Memory Manager (stubbed)")
    
    print_separator()
    
    # ── Check n8n ──
    if brain.health_check():
        print("  ✅ n8n is running!")
    else:
        print("  ⚠️  n8n is not reachable at localhost:5678")
        print("  ⚠️  Start n8n with: n8n")
        print("  ⚠️  Import workflow from: n8n_workflow/sutra_workflow.json")
        print("  ⚠️  Continuing anyway (will retry on each command)...")
    
    print_separator()
    print(f"\n  ⚡ READY! Press {HOTKEY.upper()} to speak a command.")
    print("  Press Ctrl+C to exit.\n")
    
    # Startup greeting
    speaker.speak("Sutra is ready. Press control space to give a command.")
    
    # ── Command Counter ──
    command_count = 0
    
    # ── Main Loop ──
    try:
        while True:
            # ── Step 1: Listen ──
            print_status("LISTENING", f"Press {HOTKEY.upper()} to speak (command #{command_count + 1})")
            
            try:
                audio = listener.listen()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                print_status("ERROR", f"Recording failed: {e}")
                speaker.speak("Sorry, I couldn't hear you. Please try again.")
                continue
            
            if not audio or len(audio) < 1000:
                print_status("ERROR", "No audio captured or too short")
                continue
            
            # ── Step 2: Translate ──
            print_status("TRANSLATING", "Sending to Sarvam AI...")
            
            try:
                english_text = stt.transcribe_and_translate(audio)
            except Exception as e:
                print_status("ERROR", f"Translation failed: {e}")
                speaker.speak("Sorry, I couldn't understand that. Please try again.")
                continue
            
            if not english_text or english_text.strip() == "":
                print_status("ERROR", "Empty transcription")
                speaker.speak("I didn't catch anything. Please try again.")
                continue
            
            print_status("TRANSLATING", f"Heard: \"{english_text}\"")
            
            # ── Step 3: Memory Context ──
            context = memory.get_context(english_text)
            
            # ── Step 4: Think (send to n8n) ──
            print_status("THINKING", f"Sending to n8n: \"{english_text}\"")
            
            try:
                plan = brain.send_command(english_text, context)
            except Exception as e:
                print_status("ERROR", f"n8n error: {e}")
                speaker.speak("Sorry, I couldn't plan that action. Is n8n running?")
                continue
            
            steps = plan.get("steps", [])
            plan_text = plan.get("plan", "Unknown plan")
            requires_confirmation = plan.get("requires_confirmation", False)
            
            print_status("THINKING", f"Plan: {plan_text}")
            print(f"         Steps: {json.dumps(steps, indent=2)}")
            
            if not steps:
                print_status("ERROR", "No actionable steps in plan")
                speaker.speak(f"I understood: {plan_text}, but I don't have specific actions to perform.")
                continue
            
            # ── Step 5: Confirmation (if needed) ──
            if requires_confirmation:
                confirmed = get_voice_confirmation(listener, stt, speaker, plan_text)
                if not confirmed:
                    print_status("DONE", "Action cancelled by user")
                    speaker.speak("Okay, cancelled.")
                    continue
            
            # ── Step 6: Execute ──
            print_status("EXECUTING", f"Running {len(steps)} steps...")
            
            try:
                success = actuator.execute_plan(steps)
            except Exception as e:
                print_status("ERROR", f"Execution failed: {e}")
                speaker.speak("Sorry, something went wrong while executing.")
                continue
            
            # ── Step 7: Report ──
            command_count += 1
            
            if success:
                print_status("DONE", f"✅ {plan_text}")
                speaker.speak("Done!")
            else:
                print_status("ERROR", f"Some steps failed: {plan_text}")
                speaker.speak("I completed partially, but some steps failed.")
            
            print_separator()
    
    except KeyboardInterrupt:
        print("\n")
        print_separator()
        print(f"  👋 Sutra shutting down. Executed {command_count} commands.")
        print_separator()
        speaker.speak("Goodbye!")
        listener.cleanup()
        sys.exit(0)


if __name__ == "__main__":
    run()
