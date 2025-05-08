"""
NLU (Natural Language Understanding) modul for Jarvis-lite.
Håndterer intent-genkendelse med konfidensbaseret tærskelværdi.
"""

from typing import Tuple, Dict, List, Any

# Import hovedfunktionalitet fra vores classifier
from .classifier import predict, analyze, get_available_intents

# Re-export for at gøre tilgængelig ved import fra nlu-modulet
__all__ = ["predict", "analyze", "get_available_intents"]
