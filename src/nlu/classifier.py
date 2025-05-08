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

    def __init__(self, model_path: pathlib.Path = MODEL_PATH, threshold: float = 0.15):
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

        # Sikkerhedstjek for at undgå None-fejl
        if self.vectorizer is None or self.classifier is None:
            logger.error("Vectorizer eller classifier er None - kan ikke forudsige intent")
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
        normalized_text = text.lower()

        # Simpel entitetsudtrækning baseret på intent
        if intent == "open_website":
            # Definér et hierarki af almindelige websites med både forkortelser og fulde navne
            website_map = {
                # Video og medier
                "youtube": ["youtube", "yt", "you tube", "se video", "se videoer"],
                "netflix": ["netflix", "movies", "film", "serier", "series", "se film", "se en film"],
                "tv2": ["tv2", "tv 2", "tv2.dk", "tv 2 play", "nyheder fra tv2", "nyheder på tv2"],
                "dr": ["dr", "dr.dk", "dr1", "dr2", "dr nyheder", "danmarks radio", "dr tv"],
                
                # Sociale medier og kommunikation
                "facebook": ["facebook", "fb", "meta", "sociale medier"],
                "instagram": ["instagram", "insta", "ig", "billeder"], 
                "twitter": ["twitter", "x", "tweet", "tweets"],
                "gmail": ["gmail", "google mail", "e-mail", "email", "mail", "post"],
                
                # Søgning og information
                "google": ["google", "søg", "search", "søgemaskine", "søgning"],
                "wikipedia": ["wiki", "wikipedia", "leksikon", "encyklopædi", "opslagsværk"],
                
                # Shopping
                "amazon": ["amazon", "webshop", "køb", "shopping", "shop"],
                "zalando": ["zalando", "tøj", "køb tøj", "købe tøj"]
            }
            
            # Søg efter matches i teksten
            for site, keywords in website_map.items():
                if any(keyword in normalized_text for keyword in keywords):
                    entities["site"] = site
                    break
            
            # Hvis ingen bestemt side er specificeret, men åbn/vis/gå til hjemmeside er nævnt
            if "site" not in entities:
                for word in ["åbn", "åben", "vis", "start", "browser", "hjemmeside", "internet", "online", "web", "www"]:
                    if word in normalized_text:
                        entities["site"] = "google"
                        break

        elif intent == "save_note":
            # Udtræk notetekst (fjern kommandoordene)
            note_text = normalized_text
            command_words = ["gem", "note", "skriv", "husk", "noter", "påmindelse",
                         "huskeliste", "opret", "tilføj", "lav", "notér", "skriv ned", "husk på"]
            
            # Fjern kommandoord med mellemrum efter
            for word in command_words:
                if word + " " in note_text:
                    note_text = note_text.replace(word + " ", "")
                elif word in note_text:
                    note_text = note_text.replace(word, "")
            
            # Fjern "en" og "et"
            note_text = note_text.replace(" en ", " ").replace(" et ", " ").replace(" at ", " ")
            
            # Fjern "for mig", "til mig", etc.
            for phrase in [" for mig", " til mig", " til senere", " jeg skal"]:
                note_text = note_text.replace(phrase, "")
            
            note_text = note_text.strip()
            if note_text:
                entities["text"] = note_text

        elif intent == "play_music":
            # Udtræk genre hvis angivet med mere avanceret detektion
            genre_map = {
                "pop": ["pop", "popmusik", "populær musik", "hitliste", "top 50", "populært"],
                "rock": ["rock", "rockmusik", "metal", "hard rock", "heavy", "punk"],
                "jazz": ["jazz", "blues", "soul"],
                "klassisk": ["klassisk", "classical", "klassisk musik", "orkester", "symphony", "mozart", "beethoven", "chopin", "bach"],
                "elektronisk": ["elektronisk", "techno", "house", "edm", "dance", "dj", "electro", "trance", "dubstep", "drum and bass", "d&b"],
                "hiphop": ["hip hop", "hiphop", "rap", "hip-hop", "r&b", "rnb"],
                "country": ["country", "western"],
                "folk": ["folk", "folkemusik", "nordisk", "traditionel"],
                "reggae": ["reggae", "dancehall", "jamaica"],
                "ambient": ["ambient", "afslapning", "meditation", "afslappende", "beroligende", "stille"],
                "dansk": ["dansk", "danske hits", "danske sange", "dansk musik", "på dansk"]
            }
            
            # Tjek for genrer
            for genre, keywords in genre_map.items():
                if any(keyword in normalized_text for keyword in keywords):
                    entities["genre"] = genre
                    break
            
            # Tjek for bestemt kunstner/band
            artist_keywords = ["af", "med", "fra", "by", "kunstner", "sanger", "band", "gruppe"]
            
            for keyword in artist_keywords:
                if keyword + " " in normalized_text:
                    parts = normalized_text.split(keyword + " ", 1)
                    if len(parts) > 1 and parts[1].strip():
                        entities["artist"] = parts[1].strip()
                        break
                        
            # Tjek for generel musikafspilning
            general_music = ["musik", "sang", "number", "track", "playlist", "spilleliste", "favorit"]
            if any(word in normalized_text for word in general_music) and "genre" not in entities and "artist" not in entities:
                entities["type"] = "general"

        elif intent == "get_weather":
            # Tid for vejrudsigt - i dag/i morgen/weekend
            time_indicators = {
                "now": ["nu", "lige nu", "i øjeblikket", "i dag", "vejret", "temperaturen", "aktuelle", "aktuelt"],
                "tomorrow": ["i morgen", "næste dag", "kommende dag", "til i morgen"],
                "weekend": ["weekend", "i weekenden", "lørdag", "søndag", "weekenden", "til weekend"],
                "week": ["uge", "ugen", "næste uge", "kommende uge", "de næste dage", "kommende dage", "fremover"]
            }
            
            # Find tid
            for time, keywords in time_indicators.items():
                if any(keyword in normalized_text for keyword in keywords):
                    entities["time"] = time
                    break
                    
            # Hvis ingen tid er angivet, brug "now"
            if "time" not in entities:
                entities["time"] = "now"
                
            # Lokation (ikke implementeret endnu, men forbereder strukturen)
            if "i " in normalized_text and " i " in normalized_text:
                parts = normalized_text.split(" i ")
                if len(parts) > 1:
                    # Tag den sidste del efter "i" som kan indeholde en lokation
                    location_part = parts[-1].strip()
                    # Fjern stopord fra enden
                    for stopword in ["dag", "morgen", "aften", "weekenden", "nu"]:
                        if location_part.endswith(stopword):
                            location_part = location_part[:-len(stopword)].strip()
                    if location_part and len(location_part) > 2:
                        entities["location"] = location_part

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


def predict(text: str, threshold: float = 0.15) -> Tuple[str, float]:
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
