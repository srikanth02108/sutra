"""Push-to-talk voice listener using Silero VAD.

Captures microphone audio when the user presses Ctrl+Space, applies Voice
Activity Detection via the Silero VAD model, and returns the recorded
utterance as WAV bytes once 1.5 seconds of post-speech silence is detected.
"""

import io
import logging
import os
import sys
import time
import wave
from typing import Optional

import keyboard
import numpy as np
import pyaudio
import torch

# ---------------------------------------------------------------------------
# Ensure the project root is importable so we can pull from the config module
# ---------------------------------------------------------------------------
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from config import (
        SAMPLE_RATE,
        CHANNELS,
        CHUNK_SIZE,
        SILENCE_DURATION,
        VAD_THRESHOLD,
        HOTKEY,
    )
    SILENCE_TIMEOUT = SILENCE_DURATION  # alias for clarity in this module
except ImportError:
    # Fallback defaults when config module is not yet available
    SAMPLE_RATE: int = 16_000
    CHANNELS: int = 1
    CHUNK_SIZE: int = 512
    SILENCE_TIMEOUT: float = 1.5
    VAD_THRESHOLD: float = 0.5
    HOTKEY: str = "alt+."

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Silero VAD setup
# ---------------------------------------------------------------------------
torch.set_num_threads(1)  # Optimal for single-stream real-time inference


def _load_vad_model():
    """Load the Silero VAD model from torch hub (cached after first download)."""
    model, utils = torch.hub.load(
        "snakers4/silero-vad",
        "silero_vad",
        force_reload=False,
        trust_repo=True,
    )
    return model, utils


def int2float(sound: np.ndarray) -> torch.Tensor:
    """Convert int16 PCM audio to float32 tensor normalised to [-1, 1].

    Args:
        sound: NumPy array of int16 samples.

    Returns:
        A 1-D ``torch.Tensor`` of float32 values in the range [-1.0, 1.0].
    """
    abs_max = np.abs(sound).max()
    sound_float = sound.astype(np.float32)
    if abs_max > 0:
        sound_float *= 1.0 / 32768.0
    return torch.from_numpy(sound_float)


# ═══════════════════════════════════════════════════════════════════════════
# VoiceListener
# ═══════════════════════════════════════════════════════════════════════════

class VoiceListener:
    """Push-to-talk voice capture with Silero VAD silence detection.

    Usage::

        listener = VoiceListener()
        audio_wav = listener.listen()   # blocks until speech captured
        listener.cleanup()
    """

    def __init__(self) -> None:
        logger.info("Loading Silero VAD model …")
        self._vad_model, _ = _load_vad_model()
        logger.info("Silero VAD model loaded.")

        self._pa: pyaudio.PyAudio = pyaudio.PyAudio()

        # State tracking
        self._is_recording: bool = False
        self._audio_buffer: list[bytes] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def wait_for_hotkey(self) -> None:
        """Block until the push-to-talk hotkey (Alt+.) is pressed."""
        keyboard.wait(HOTKEY)

    def record_until_silence(self) -> bytes:
        """Record microphone audio, stopping after sustained silence.

        Uses the Silero VAD model to distinguish speech from silence.
        Recording begins when the first speech frame is detected and ends
        after ``SILENCE_TIMEOUT`` seconds of continuous non-speech frames
        following at least one speech frame.

        Returns:
            Complete audio data encoded as WAV bytes (16 kHz, 16-bit, mono).
        """
        stream: Optional[pyaudio.Stream] = None
        try:
            stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE,
            )

            self._is_recording = True
            self._audio_buffer = []

            has_speech: bool = False
            silence_start: Optional[float] = None

            # Reset VAD model state for a fresh utterance
            self._vad_model.reset_states()

            while True:
                raw_chunk: bytes = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_int16 = np.frombuffer(raw_chunk, dtype=np.int16)
                audio_float = int2float(audio_int16)

                # Silero VAD expects (batch, samples) but the single-call API
                # accepts a plain 1-D tensor when sampling_rate is provided.
                speech_prob: float = self._vad_model(
                    audio_float, SAMPLE_RATE
                ).item()

                if speech_prob > VAD_THRESHOLD:
                    # ── Speech detected ──────────────────────────────
                    has_speech = True
                    silence_start = None
                    self._audio_buffer.append(raw_chunk)

                elif has_speech:
                    # ── Post-speech silence ──────────────────────────
                    self._audio_buffer.append(raw_chunk)  # keep trailing audio

                    if silence_start is None:
                        silence_start = time.time()
                    elif time.time() - silence_start >= SILENCE_TIMEOUT:
                        logger.debug(
                            "Silence timeout reached (%.1fs) — ending recording.",
                            SILENCE_TIMEOUT,
                        )
                        break
                # else: pre-speech silence — skip

        except Exception:
            logger.exception("Error during recording")
            raise
        finally:
            if stream is not None:
                stream.stop_stream()
                stream.close()
            self._is_recording = False

        return self._buffer_to_wav()

    def listen(self) -> bytes:
        """Full listen cycle: wait for hotkey, then record until silence.

        Returns:
            WAV audio bytes of the captured utterance.
        """
        print("\n🎤 Press Alt+. to speak...")
        self.wait_for_hotkey()
        print("🔴 Recording... (speak now, will stop after 1.5s silence)")
        audio: bytes = self.record_until_silence()
        print(f"✅ Captured {len(audio)} bytes of audio")
        return audio

    def cleanup(self) -> None:
        """Release PyAudio resources."""
        try:
            self._pa.terminate()
            logger.info("PyAudio terminated.")
        except Exception:
            logger.exception("Error terminating PyAudio")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _buffer_to_wav(self) -> bytes:
        """Pack the raw PCM buffer into an in-memory WAV file.

        Returns:
            WAV-encoded bytes (16 kHz, 16-bit, mono).
        """
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b"".join(self._audio_buffer))
        return buf.getvalue()


# ═══════════════════════════════════════════════════════════════════════════
# Standalone test
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    listener = VoiceListener()
    try:
        wav_data = listener.listen()
        print(f"\n📦 Total WAV size: {len(wav_data)} bytes")

        # Optionally write to disk for inspection
        out_path = os.path.join(_PROJECT_ROOT, "ears", "test_output.wav")
        with open(out_path, "wb") as f:
            f.write(wav_data)
        print(f"💾 Saved to {out_path}")
    finally:
        listener.cleanup()
