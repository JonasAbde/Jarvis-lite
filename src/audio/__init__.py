"""
Lydrelaterede funktioner for Jarvis Lite.
Håndterer tale-til-tekst og tekst-til-tale samt wakeword-detektion.
"""

from .speech import speak, record_audio, transcribe_audio
from .speech import speak_async, record_audio_async, transcribe_audio_async
from .wakeword import initialize_wakeword_detector, stop_wakeword_detector

__all__ = [
    "speak", "record_audio", "transcribe_audio",
    "speak_async", "record_audio_async", "transcribe_audio_async",
    "initialize_wakeword_detector", "stop_wakeword_detector"
]
