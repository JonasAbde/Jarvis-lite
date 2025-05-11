"""
Forbereder dansk træningsdata til finjustering af Phi-2 modellen.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_conversation_format(question: str, answer: str) -> Dict[str, List[Dict[str, str]]]:
    """Opretter en samtale i det korrekte format."""
    return {
        "conversations": [
            {"role": "system", "content": "Du er en hjælpsom dansk assistent. Svar altid på dansk."},
            {"role": "human", "content": question},
            {"role": "assistant", "content": answer}
        ]
    }

def generate_training_data() -> List[Dict[str, List[Dict[str, str]]]]:
    """Genererer træningsdata med danske spørgsmål og svar."""
    training_data = []
    
    # Grundlæggende spørgsmål og svar
    qa_pairs = [
        ("Hvad er hovedstaden i Danmark?", "København er Danmarks hovedstad."),
        ("Hvordan er vejret i dag?", "Jeg kan desværre ikke se vejret i realtid, men jeg kan hjælpe dig med at finde en vejrudsigt."),
        ("Fortæl mig om H.C. Andersen", "H.C. Andersen var en verdensberømt dansk forfatter, kendt for sine eventyr som 'Den grimme ælling' og 'Den lille havfrue'."),
        ("Hvad er en typisk dansk ret?", "Stegt flæsk med persillesovs er Danmarks nationalret. Andre populære retter inkluderer smørrebrød og frikadeller."),
        ("Hvordan har du det?", "Jeg har det godt, tak! Hvordan kan jeg hjælpe dig i dag?"),
        ("Hvad er kunstig intelligens?", "Kunstig intelligens er computersystemer, der kan efterligne menneskelig intelligens og udføre opgaver som at lære, ræsonnere og problemløse."),
        ("Kan du hjælpe mig med at lave mad?", "Ja, jeg kan hjælpe dig med opskrifter og madlavningstips. Hvad kunne du tænke dig at lave?"),
        ("Hvad er Danmarks største by?", "København er Danmarks største by med over 1,3 millioner indbyggere i hovedstadsområdet."),
        ("Fortæl om det danske vejr", "Danmark har et tempereret klima med milde vintre og kølige somre. Det regner ofte, og vejret kan skifte hurtigt."),
        ("Hvad er en god dansk film?", "Der er mange gode danske film, for eksempel 'Druk' af Thomas Vinterberg eller 'Festen' af Lars von Trier.")
    ]
    
    for question, answer in qa_pairs:
        training_data.append(create_conversation_format(question, answer))
    
    return training_data

def save_training_data(data: List[Dict[str, List[Dict[str, str]]]], output_file: str):
    """Gemmer træningsdata i JSONL format."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    logger.info(f"Træningsdata gemt i {output_file}")

if __name__ == "__main__":
    # Generer og gem træningsdata
    output_file = "src/llm/training/data/danish_conversations.jsonl"
    training_data = generate_training_data()
    save_training_data(training_data, output_file)
    logger.info(f"Genererede {len(training_data)} træningseksempler") 