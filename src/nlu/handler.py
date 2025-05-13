from typing import Dict, Any
from .intents import GREETING_INTENTS, get_greeting_response
import re

class NLUHandler:
    def __init__(self):
        self.confidence_threshold = 0.7

    def preprocess_text(self, text: str) -> str:
        """Forbehandl tekst til NLU-analyse"""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        return text

    def calculate_confidence(self, text: str, intent_phrases: list) -> float:
        """Beregn konfidensen for et match"""
        text = self.preprocess_text(text)
        max_confidence = 0.0
        
        for phrase in intent_phrases:
            if phrase in text:
                max_confidence = max(max_confidence, 0.85)
            elif any(word in text.split() for word in phrase.split()):
                max_confidence = max(max_confidence, 0.7)
        
        return max_confidence

    def classify_intent(self, text: str) -> Dict[str, Any]:
        """Klassificer brugerens intent"""
        text = self.preprocess_text(text)
        best_intent = None
        max_confidence = 0.0

        for intent, phrases in GREETING_INTENTS.items():
            confidence = self.calculate_confidence(text, phrases)
            if confidence > max_confidence:
                max_confidence = confidence
                best_intent = intent

        if max_confidence >= self.confidence_threshold:
            response = get_greeting_response(best_intent)
        else:
            response = "Jeg er ikke sikker på, hvad du mener. Kan du omformulere det?"
            max_confidence = 0.5

        return {
            "intent": best_intent,
            "confidence": max_confidence,
            "response": response
        } 