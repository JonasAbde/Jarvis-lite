import json
import os
import logging

logger = logging.getLogger(__name__)

def _append_training_example(tag: str, pattern: str,
                             file_path="data/nlu_training_data.json"):
    """
    Tilføjer et træningseksempel til den angivne intent i JSON-filen.
    Opretter intenten hvis den ikke findes.
    Ignorerer eksemplet hvis det allerede eksisterer for intenten.
    """
    full_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), file_path)
    
    # Sikr at mappen eksisterer
    os.makedirs(os.path.dirname(full_file_path), exist_ok=True)

    data = {"intents": []} # Standard struktur hvis filen ikke findes

    # Indlæs eksisterende data hvis filen findes
    if os.path.exists(full_file_path):
        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "intents" not in data or not isinstance(data["intents"], list):
                 logger.warning(f"Ugyldigt format i træningsdatafil {full_file_path}. Fortsætter med tom struktur.")
                 data = {"intents": []}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Fejl ved indlæsning af træningsdata fra {full_file_path}: {e}. Starter med tom struktur.")
            data = {"intents": []}

    # Find eller opret intent-blok
    intent_found = False
    for intent in data.get("intents", []):
        if intent.get("tag") == tag:
            # Tilføj eksemplet hvis det ikke allerede findes
            patterns = intent.get("patterns", [])
            if pattern not in patterns:
                patterns.append(pattern)
                intent["patterns"] = patterns # Sikr at listen gemmes tilbage
                logger.info(f"Tilføjede nyt eksempel for intent '{tag}': '{pattern}'")
                intent_found = True
            else:
                logger.info(f"Eksempel '{pattern}' findes allerede for intent '{tag}'. Ignorerer.")
                intent_found = True
            break

    # Hvis intenten ikke findes, opret den
    if not intent_found:
        logger.info(f"Opretter ny intent '{tag}' og tilføjer eksempel '{pattern}'.")
        data["intents"].append({"tag": tag,
                                "patterns": [pattern],
                                "responses": [] # Tilføj responses key for konsistens
                               })

    # Gem de opdaterede træningsdata
    try:
        with open(full_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Træningsdata gemt til {full_file_path}.")
    except Exception as e:
        logger.error(f"Fejl under gemning af træningsdata til {full_file_path}: {e}")

# Tilføjet en dummy for at matche den forventede filsti i classifier.py indtil videre
def preprocess_text_danish(text): # Dummy funktion
     return text

def load_training_data(file_path="data/nlu_training_data.json"):
    """ Dummy load_training_data for utils - skal ikke bruges i Jarvis """
    logger.warning("Dummy load_training_data i utils.py kaldt.")
    return [], [] 