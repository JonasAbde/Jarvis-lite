"""
Modul til dynamisk håndtering af stemmekommandoer defineret i en ekstern fil.
"""
import yaml
import logging
import re
import os
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

def load_commands_from_config(config_path: str = "config/commands.yaml") -> Optional[Dict[str, Any]]:
    """
    Indlæser og parser kommandoer fra en YAML-konfigurationsfil.

    Args:
        config_path: Sti til YAML-konfigurationsfilen.

    Returns:
        En dictionary med de indlæste kommandoer, eller None ved fejl.
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            commands_config = yaml.safe_load(f)
        logger.info(f"Kommandoer indlæst succesfuldt fra {config_path}")
        return commands_config
    except FileNotFoundError:
        logger.error(f"Konfigurationsfilen {config_path} blev ikke fundet.")
        return None
    except yaml.YAMLError as e:
        logger.error(f"Fejl under parsing af YAML-konfigurationsfilen {config_path}: {e}")
        return None
    except Exception as e:
        logger.error(f"En uventet fejl opstod under indlæsning af kommandoer fra {config_path}: {e}")
        return None

def extract_parameters(phrase_template: str, actual_phrase: str) -> Optional[Dict[str, str]]:
    """
    Ekstraherer parametre fra en faktisk frase baseret på en skabelon.
    Simpel implementering baseret på placeholder {parameter_navn}.

    Args:
        phrase_template: Skabelonfrasen med placeholders (f.eks. "sæt en timer til {duration}").
        actual_phrase: Den faktiske transskriberede frase.

    Returns:
        En dictionary med ekstraherede parametre, eller None hvis ingen match.
    """
    # Normaliser begge strenge til lowercase for case-insensitive matching
    template_lower = phrase_template.lower()
    actual_lower = actual_phrase.lower()

    # Find alle parameter-navne i skabelonen
    param_names = re.findall(r"\{(.*?)\}", template_lower)
    if not param_names: # Ingen parametre defineret i skabelonen
        if template_lower == actual_lower:
            return {} # Returner tom dict hvis fraserne matcher uden parametre
        return None

    # Erstat placeholders i skabelonen med regex capture groups
    # Escape specielle regex tegn i skabelonen, undtagen vores placeholders
    regex_template = template_lower
    for param_name in param_names:
        regex_template = regex_template.replace(f"{{{param_name}}}", r"(.*?)", 1)

    # Sørg for at matche hele strengen
    regex_template = f"^{regex_template}$"

    match = re.match(regex_template, actual_lower)

    if match:
        extracted_values = match.groups()
        if len(extracted_values) == len(param_names):
            return dict(zip(param_names, [value.strip() for value in extracted_values]))
    return None


def find_matching_command(transcribed_text: str, commands_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Finder en matchende kommando for den transskriberede tekst.

    Args:
        transcribed_text: Den transskriberede tekst fra Whisper.
        commands_config: Dictionary med kommando-konfigurationen.

    Returns:
        En dictionary med den matchende kommando og eventuelle parametre, ellers None.
    """
    if not commands_config or "commands" not in commands_config:
        logger.warning("Kommando-konfiguration er tom eller mangler 'commands' nøgle.")
        return None

    normalized_text = transcribed_text.lower().strip()

    for command in commands_config["commands"]:
        for phrase_template in command.get("phrases", []):
            parameters = extract_parameters(phrase_template, normalized_text)
            if parameters is not None: # Betyder at frasen matcher, med eller uden parametre
                action_to_perform = command.copy() # Undgå at modificere original config
                action_to_perform["extracted_parameters"] = parameters
                logger.info(f"Kommando '{command['name']}' matchede med tekst: '{transcribed_text}'. Parametre: {parameters}")
                return action_to_perform
    
    logger.info(f"Ingen matchende kommando fundet for: '{transcribed_text}'")
    return None

# Eksempel på brug (kan flyttes til din hovedlogik):
if __name__ == "__main__":
    # Sørg for at loggeren er konfigureret, hvis du kører denne fil direkte
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Opret en dummy konfigurationsfil for test
    dummy_config_content = {
        "commands": [
            {
                "name": "set_timer",
                "phrases": ["sæt en timer til {duration}", "start timer {duration}"],
                "action_type": "function",
                "action_details": "timers.set_timer",
                "parameters": [{"name": "duration"}]
            },
            {
                "name": "play_music_artist",
                "phrases": ["spil musik af {artist}"],
                "action_type": "function",
                "action_details": "music.play_artist",
                "parameters": [{"name": "artist"}]
            },
            {
                "name": "lights_on",
                "phrases": ["tænd lyset", "lys på"],
                "action_type": "script",
                "action_details": "smarthome/lights_on.sh"
            }
        ]
    }
    # Opret mappen 'config' hvis den ikke findes
    os.makedirs("config", exist_ok=True)
    with open("config/commands.yaml", 'w', encoding='utf-8') as f_yaml:
        yaml.dump(dummy_config_content, f_yaml, allow_unicode=True)

    # Test indlæsning
    config = load_commands_from_config()
    if config:
        test_phrases = [
            "sæt en timer til 5 minutter",
            "start timer 10 sekunder",
            "spil musik af Queen",
            "tænd lyset",
            "sluk computeren" # Skal ikke matche
        ]
        for phrase in test_phrases:
            print(f"\nTester frase: '{phrase}'")
            matched_action = find_matching_command(phrase, config)
            if matched_action:
                print(f"  Handling fundet: {matched_action['name']}")
                print(f"  Action type: {matched_action['action_type']}")
                print(f"  Action details: {matched_action['action_details']}")
                if matched_action.get("extracted_parameters"):
                    print(f"  Parametre: {matched_action['extracted_parameters']}")
            else:
                print("  Ingen handling fundet.")
    else:
        print("Kunne ikke indlæse kommando-konfiguration.")

    # For at køre dette eksempel:
    # 1. Sørg for at PyYAML er installeret: pip install PyYAML
    # 2. Kør: python src/command_parser.py
    # Dette vil oprette en dummy config/commands.yaml og teste parseren. 