"""tts_engine.py
Wrapper til dansk TTS.  Standard: Piper (offline).  Fallback: gTTS (kræver internet).

Brug:
    from tts_engine import speak
    speak("Hej verden")
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import playsound  # simple cross-platform afspilning

# --- Piper (foretrukken) ----------------------------------------------------
try:
    from piper import PiperVoice  # type: ignore

    _has_piper = True
except ImportError:
    _has_piper = False

# --- gTTS fallback ----------------------------------------------------------
try:
    from gtts import gTTS

    _has_gtts = True
except ImportError:
    _has_gtts = False

TEMP_DIR = Path(__file__).resolve().parent


class PiperTTS:
    """Simpel wrapper omkring piper-cli via ``piper`` python-bindingen eller subprocess."""

    def __init__(self, voice: str = "da-sv-natalie-low"):
        if _has_piper:
            self.voice_name = voice
            self.voice = PiperVoice.load(voice)
        else:
            raise RuntimeError("Piper er ikke installeret (pip install piper-tts).")

    def speak(self, text: str, *, blocking: bool = True) -> Path:
        wav_path = TEMP_DIR / f"tts_{uuid.uuid4()}.wav"
        audio_bytes = self.voice.synthesis(text)
        wav_path.write_bytes(audio_bytes)
        _play(wav_path, blocking=blocking)
        return wav_path


class GTTS:
    """Fallback TTS som bruger Googles gTTS (kræver internet)."""

    def __init__(self, lang: str = "da"):
        if not _has_gtts:
            raise RuntimeError("gTTS ikke tilgængelig – installér med pip install gTTS")
        self.lang = lang

    def speak(self, text: str, *, blocking: bool = True) -> Path:
        mp3_path = TEMP_DIR / f"tts_{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=self.lang)
        tts.save(mp3_path.as_posix())
        _play(mp3_path, blocking=blocking)
        return mp3_path


# Dobbelt instans (piper først, ellers gTTS)
if _has_piper:
    _engine = PiperTTS()
elif _has_gtts:
    _engine = GTTS()
else:
    _engine = None  # type: ignore


def speak(text: str, *, blocking: bool = True):
    """Taler teksten højt. Returnerer stien til lydfilen.

    Hvis ingen TTS-engine er tilgængelig, hæves RuntimeError.
    """
    if _engine is None:
        raise RuntimeError("Ingen TTS-engine tilgængelig. Installér 'piper-tts' eller 'gTTS'.")
    return _engine.speak(text, blocking=blocking)


def _play(path: Path, *, blocking: bool = True):
    """Afspil en lydfil med playsound (blocking som standard)."""
    if blocking:
        playsound.playsound(path.as_posix())
    else:
        # Start et nyt subprocess-kald for at spille i baggrunden (platform-afhængigt)
        subprocess.Popen(["python", "-m", "playsound", path.as_posix()]) 