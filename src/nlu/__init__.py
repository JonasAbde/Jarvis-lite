"""
NLU (Natural Language Understanding) modul for Jarvis-lite.
Håndterer intent-genkendelse med konfidensbaseret tærskelværdi.
"""

import pathlib
import joblib
from typing import Tuple, List

MODEL_PATH = pathlib.Path(__file__).parent / "model.joblib"

# Indlæs modellen ved import
try:
    _vectorizer, _clf, _intents = joblib.load(MODEL_PATH)
except FileNotFoundError:
    print(f"[ADVARSEL] NLU model ikke fundet i {MODEL_PATH}")
    _vectorizer = _clf = _intents = None

def predict(text: str, threshold: float = 0.55) -> Tuple[str, float]:
    """
    Forudsig intent for en given tekst med konfidensscore.
    
    Args:
        text: Teksten der skal analyseres
        threshold: Minimum konfidensscore for at acceptere en intent (default: 0.55)
    
    Returns:
        Tuple af (intent, konfidensscore)
    """
    if _clf is None:
        return "unknown", 0.0
        
    X = _vectorizer.transform([text.lower()])
    proba = _clf.predict_proba(X)[0]
    max_proba = proba.max()
    
    if max_proba < threshold:
        return "unknown", max_proba
        
    intent = _clf.predict(X)[0]
    return intent, max_proba

def get_available_intents() -> List[str]:
    """Returner liste over alle tilgængelige intents."""
    return list(_intents) if _intents else [] 