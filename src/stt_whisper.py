"""stt_whisper.py
En selvstændig STT-wrapper til Faster-Whisper, optimeret til dansk.

Brug:
    from stt_whisper import load_model, transcribe

    load_model()  # én gang ved opstart
    text = transcribe("path/to/file.wav")
"""

from __future__ import annotations

import time
import traceback
from pathlib import Path
from typing import Optional

import librosa
from faster_whisper import WhisperModel

# Global reference så modellen kun indlæses én gang
_model: Optional[WhisperModel] = None


def load_model(model_size: str = "small", *, prefer_gpu: bool = True, compute_type: str = "int8") -> WhisperModel:
    """Indlæs Whisper-modellen én gang og returnér instansen.

    Parametre
    ----------
    model_size : str
        F.eks. "tiny", "base", "small", "medium", "large".
    prefer_gpu : bool
        Forsøg at køre på CUDA hvis muligt, ellers fald tilbage til CPU.
    compute_type : str
        "int8", "float16" eller "float32".  INT8 giver god hastighed på både CUDA og CPU.
    """
    global _model
    if _model is not None:
        return _model

    device = "cuda" if prefer_gpu else "cpu"
    try:
        _model = WhisperModel(model_size, device=device, compute_type=compute_type)
        print(f"[STT] Whisper '{model_size}' indlæst på {device} med {compute_type}.")
    except Exception as e:
        if device == "cuda":
            print(f"[STT] Kunne ikke indlæse på GPU: {e}. Falder tilbage til CPU...")
            _model = WhisperModel(model_size, device="cpu", compute_type=compute_type)
            print(f"[STT] Whisper '{model_size}' indlæst på CPU.")
        else:
            raise

    return _model


def transcribe(audio_path: str | Path, language: str = "da", beam_size: int = 5) -> Optional[str]:
    """Transskriber en lydfil til tekst.

    Returnerer None hvis transskriptionen fejler eller ingen tekst findes.
    """
    if _model is None:
        raise RuntimeError("Whisper-modellen er ikke indlæst. Kald load_model() først.")

    path = Path(audio_path).expanduser().resolve()
    if not path.exists():
        print(f"[STT] Filen findes ikke: {path}")
        return None

    start = time.time()
    try:
        audio, _ = librosa.load(path.as_posix(), sr=16000, mono=True)
        print(f"[STT] Fil indlæst på {time.time() - start:.2f}s ({len(audio)} samples)")

        segments, _info = _model.transcribe(audio, language=language, beam_size=beam_size)
        text_segments = [seg.text.strip() for seg in segments]
        transcript = " ".join(text_segments).strip()

        if transcript:
            print(f"[STT] Transskription ({len(text_segments)} segmenter) klar på {time.time() - start:.2f}s")
            return transcript
        else:
            print("[STT] Ingen tekst fundet i lydfilen.")
            return None
    except Exception:
        print("[STT] Fejl under transskription:")
        traceback.print_exc()
        return None


# Convenience funktion til hurtig brug uden eksplicit load_model

def transcribe_on_the_fly(audio_path: str | Path, **kw):
    """Loader model ved behov og transskriberer i ét kald."""
    if _model is None:
        load_model()
    return transcribe(audio_path, **kw) 