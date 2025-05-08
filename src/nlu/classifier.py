"""
Intent klassifikation for Jarvis Lite.
Bruger en trænet TF-IDF + LogisticRegression model.
"""

import os
import logging
import joblib
import pathlib
from typing import Tuple, Dict, Any, List, Optional

# Logger
logger = logging.getLogger(__name__)

# Stier
MODEL_PATH = pathlib.Path(__file__).parent / "model.joblib"


class IntentClassifier:
    """Klassificerer brugerinput til intents med konfidensniveauer"""

    def __init__(self, model_path: pathlib.Path = MODEL_PATH, threshold: float = 0.55):
        """
        Initialiserer intent klassifikatoren

        Args:
            model_path: Sti til den gemte model
            threshold: Minimumstærskel for intentkonfidens
        """
        self.model_path = model_path
        self.threshold = threshold
        self.loaded = False
        self.vectorizer = None
        self.classifier = None
        self.intents = []

        # Forsøg at indlæse modellen med det samme
        self._load_model()

    def _load_model(self) -> bool:
        """
        Indlæser den gemte model

        Returns:
            True hvis indlæsningen lykkedes, ellers False
        """
        try:
            if not self.model_path.exists():
                logger.warning(f"Model ikke fundet: {self.model_path}")
                return False

            self.vectorizer, self.classifier, self.intents = joblib.load(
                self.model_path
            )
            self.loaded = True
            logger.info(f"Model indlæst med {len(self.intents)} intents")
            return True

        except Exception as e:
            logger.error(f"Fejl ved indlæsning af model: {e}")
            self.loaded = False
            return False

    def predict(self, text: str) -> Tuple[str, float]:
        """
        Forudsiger intent for en given tekst

        Args:
            text: Brugerens input

        Returns:
            Tuple af (intent, konfidensscore)
        """
        if not self.loaded and not self._load_model():
            return "unknown", 0.0

        try:
            # Transformér tekst til feature-vektor
            X = self.vectorizer.transform([text.lower()])

            # Hent konfidensscore
            probabilities = self.classifier.predict_proba(X)[0]
            max_confidence = probabilities.max()

            # Check om vi overstiger tærskelværdien
            if max_confidence < self.threshold:
                logger.info(
                    f"Input '{text}' under tærskelværdi: {max_confidence:.2f} < {self.threshold}"
                )
                return "unknown", max_confidence

            # Forudsig intent
            intent = self.classifier.predict(X)[0]
            logger.info(
                f"Klassificeret '{text}' som '{intent}' med konfidens {max_confidence:.2f}"
            )

            return intent, max_confidence

        except Exception as e:
            logger.error(f"Fejl ved klassifikation: {e}")
            return "unknown", 0.0

    def extract_entities(self, text: str, intent: str) -> Dict[str, Any]:
        """
        Udvinder entiteter fra teksten baseret på intent

        Args:
            text: Brugerens input
            intent: Den forudsagte intent

        Returns:
            Dict med entiteter
        """
        entities = {}

        # Simpel entitetsudtrækning baseret på intent
        if intent == "open_website":
            # Forsøg at udtrække hjemmesidenavn
            lower_text = text.lower()
            for site in ["youtube", "google", "dr", "dr.dk"]:
                if site in lower_text:
                    entities["site"] = site
                    break

        elif intent == "save_note":
            # Udtræk notetekst (fjern kommandoordene)
            note_text = text.lower()
            for word in ["gem", "note", "skriv", "husk"]:
                note_text = note_text.replace(word, "")
            note_text = note_text.strip()
            if note_text:
                entities["text"] = note_text

        return entities

    def get_available_intents(self) -> List[str]:
        """
        Returnerer liste over alle tilgængelige intents

        Returns:
            Liste af intent-strenge
        """
        if not self.loaded and not self._load_model():
            return []

        return self.intents

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Analyserer tekst og returnerer intent, konfidens og entiteter

        Args:
            text: Brugerens input

        Returns:
            Dict med analyse-resultater
        """
        intent, confidence = self.predict(text)
        entities = self.extract_entities(text, intent)

        return {
            "text": text,
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
        }


# Global instance for nem import
classifier = IntentClassifier()


def predict(text: str, threshold: float = 0.55) -> Tuple[str, float]:
    """
    Forudsiger intent for en given tekst (global funktion)

    Args:
        text: Brugerens input
        threshold: Minimum konfidensscore

    Returns:
        Tuple af (intent, konfidens)
    """
    # Overskrid klassifikatorens standard-threshold hvis nødvendigt
    if threshold != classifier.threshold:
        old_threshold = classifier.threshold
        classifier.threshold = threshold
        intent, confidence = classifier.predict(text)
        classifier.threshold = old_threshold
        return intent, confidence

    return classifier.predict(text)


def analyze(text: str) -> Dict[str, Any]:
    """
    Analyserer tekst og returnerer intent, konfidens og entiteter (global funktion)

    Args:
        text: Brugerens input

    Returns:
        Dict med analyse-resultater
    """
    return classifier.analyze(text)


def get_available_intents() -> List[str]:
    """
    Returnerer liste over alle tilgængelige intents (global funktion)

    Returns:
        Liste af intent-strenge
    """
    return classifier.get_available_intents()
