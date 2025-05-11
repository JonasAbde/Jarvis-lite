#!/usr/bin/env python3
"""
Script til at træne NLU-modellen til Jarvis-Lite med flere eksempler.
Dette script giver dig mulighed for at tilføje flere træningseksempler og forbedre modellens
evne til at forstå brugerinput og klassificere intentioner korrekt.
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Tilføj projektets rod-mappe til Python-stien
# Find den rigtige root_dir sti
script_dir = os.path.dirname(os.path.abspath(__file__))
nlu_dir = os.path.dirname(script_dir)
src_dir = os.path.dirname(nlu_dir)
root_dir = os.path.dirname(src_dir)
logger.info(f"Script directory: {script_dir}")
logger.info(f"NLU directory: {nlu_dir}")
logger.info(f"SRC directory: {src_dir}")
logger.info(f"Root directory: {root_dir}")

sys.path.append(root_dir)

# Stier
TRAINING_DATA_PATH = os.path.join(root_dir, "data", "nlu_training_data.json")
MODEL_OUTPUT_PATH = os.path.join(nlu_dir, "model.joblib")
LABELS_OUTPUT_PATH = os.path.join(nlu_dir, "labels.joblib")
logger.info(f"Training data path: {TRAINING_DATA_PATH}")
logger.info(f"Model output path: {MODEL_OUTPUT_PATH}")
logger.info(f"Labels output path: {LABELS_OUTPUT_PATH}")

# Grundlæggende træningsdata
BASIC_TRAINING_DATA = {
    "intents": [
        {
            "intent": "greeting",
            "examples": [
                "hej", "goddag", "godmorgen", "godaften", "hejsa", "davs", "halløj", 
                "hej med dig", "hej jarvis", "goddag jarvis", "hej du", "hello", "hi", 
                "hej igen", "jeg er hjemme", "jeg er tilbage"
            ]
        },
        {
            "intent": "farewell",
            "examples": [
                "farvel", "hej hej", "vi ses", "på gensyn", "tak for nu", "ses senere",
                "farvel jarvis", "sluk dig selv", "jeg går nu", "jeg er færdig",
                "det var alt", "tak for hjælpen", "vi snakkes ved", "hav en god dag"
            ]
        },
        {
            "intent": "thanks",
            "examples": [
                "tak", "mange tak", "tusind tak", "tak skal du have", "jeg er taknemmelig",
                "det sætter jeg pris på", "dejligt", "tak for hjælpen", "super", "perfekt", 
                "det var lige hvad jeg havde brug for", "godt arbejde", "tak jarvis"
            ]
        },
        {
            "intent": "help",
            "examples": [
                "hjælp", "jeg har brug for hjælp", "kan du hjælpe mig", "hjælp mig",
                "hvad kan du", "hvilke kommandoer forstår du", "hvad kan jeg spørge om",
                "hvad kan du hjælpe med", "vis mig hvad du kan", "hvilke funktioner har du",
                "hvordan bruger jeg dig", "jeg ved ikke hvad jeg skal spørge om"
            ]
        },
        {
            "intent": "time",
            "examples": [
                "hvad er klokken", "hvad tid er det", "klokken", "tidspunkt", "kan du fortælle mig hvad klokken er",
                "fortæl mig tiden", "hvad siger klokken", "hvad er tiden", "hvor meget er klokken",
                "har du et ur", "vis mig tiden"
            ]
        },
        {
            "intent": "date",
            "examples": [
                "hvilken dag er det", "hvad er datoen", "hvilken dato er det", "hvad er det for en dag i dag",
                "hvilken ugedag er det", "hvornår er vi", "hvilken dag i ugen er det", "hvilken måned er det",
                "dato", "kalender", "hvilken dag er det i dag"
            ]
        },
        {
            "intent": "weather",
            "examples": [
                "hvordan er vejret", "vejrudsigt", "regner det", "vil det regne i dag", "er det solskin",
                "hvad er temperaturen", "er det godt vejr", "bliver det godt vejr i dag", "hvordan bliver vejret",
                "bliver det regnvejr", "skinner solen", "vejr", "vil det regne", "hvor varmt er det"
            ]
        },
        {
            "intent": "identity",
            "examples": [
                "hvem er du", "hvad hedder du", "hvad er dit navn", "fortæl mig om dig selv",
                "hvad er du", "er du en robot", "er du et menneske", "er du en ai", "hvad kan du fortælle om dig selv",
                "hvordan virker du", "hvem har lavet dig", "hvordan blev du skabt", "hvad er din rolle"
            ]
        },
        {
            "intent": "capabilities",
            "examples": [
                "hvad kan du", "hvad er dine evner", "hvad er dine funktioner", "hvad kan du gøre for mig",
                "hvad kan du hjælpe mig med", "hvad er dine muligheder", "fortæl mig hvad du kan",
                "kan du besvare spørgsmål", "kan du hjælpe mig med noget", "hvad er dine begrænsninger",
                "kan du gøre noget for mig", "hvad kan jeg bruge dig til"
            ]
        },
        {
            "intent": "jokes",
            "examples": [
                "fortæl en joke", "fortæl mig noget sjovt", "kan du fortælle en vittighed", "sig noget sjovt",
                "får du mig til at grine", "kender du nogen jokes", "har du en god vittighed", "jeg kunne godt bruge et grin",
                "fortæl mig en vittighed", "noget til at muntre mig op"
            ]
        },
        {
            "intent": "search",
            "examples": [
                "søg efter", "find information om", "google", "kan du finde", "søg på nettet efter",
                "slå op", "jeg leder efter information om", "kan du søge efter", "internettet", "wiki",
                "find data om", "søg på", "har du information om", "hvad ved du om"
            ]
        },
        {
            "intent": "music",
            "examples": [
                "spil musik", "spil noget musik", "spil en sang", "kan du spille noget musik",
                "start musikafspiller", "jeg vil gerne høre musik", "sæt noget musik på", "spil min yndlingssang",
                "afspil musik", "start afspilning", "afspil den næste sang", "afspil mit album"
            ]
        },
        {
            "intent": "notes",
            "examples": [
                "tag et notat", "skriv ned", "husk", "lav en note", "lav en påmindelse",
                "påmind mig om", "gem denne information", "kan du notere", "tilføj til listen",
                "skriv på min liste", "gem et notat om", "lav en huskeliste"
            ]
        },
        {
            "intent": "alarm",
            "examples": [
                "sæt en alarm", "væk mig", "sæt en timer", "påmind mig om", "sæt en påmindelse",
                "alarm til", "vække", "vækur", "vækkeur", "timer", "nedtælling",
                "sæt en alarm til klokken", "vækketid"
            ]
        },
        {
            "intent": "news",
            "examples": [
                "hvad er de seneste nyheder", "nyheder", "hvad sker der i verden", "fortæl mig om nyhederne",
                "seneste begivenheder", "opdatering på nyhederne", "hvad er der sket", "i nyhederne",
                "breaking news", "nyheder i dag", "aktuelle begivenheder"
            ]
        },
        {
            "intent": "volume",
            "examples": [
                "skru op", "skru ned", "højere", "lavere", "lydstyrke op", "lydstyrke ned",
                "skru op for lyden", "skru ned for lyden", "mute", "slå lyden fra", "slå lyden til",
                "maksimal lydstyrke", "minimum lydstyrke"
            ]
        },
        {
            "intent": "repeat",
            "examples": [
                "gentag det", "sig det igen", "hvad sagde du", "kan du gentage det", "jeg hørte ikke hvad du sagde",
                "gentag venligst", "hvad var det du sagde", "jeg forstod ikke", "hvad var det sidste du sagde", 
                "gentag dit svar", "hvad mente du"
            ]
        },
        {
            "intent": "training",
            "examples": [
                "lær mere", "bliv bedre", "træn dig selv", "kan du lære", "kan du blive bedre",
                "bliv bedre til at forstå mig", "bliv smartere", "forbedring", "træn din model",
                "hvordan bliver du trænet", "kan jeg hjælpe dig med at lære", "jeg vil gerne træne dig"
            ]
        }
    ]
}

def load_training_data():
    """Indlæser træningsdata fra fil, eller bruger grundlæggende data hvis filen ikke findes"""
    try:
        if os.path.exists(TRAINING_DATA_PATH):
            with open(TRAINING_DATA_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Indlæste træningsdata fra {TRAINING_DATA_PATH}")
                return data
        else:
            logger.info(f"Træningsdatafil ikke fundet. Bruger grundlæggende træningsdata.")
            # Opret mappen, hvis den ikke findes
            os.makedirs(os.path.dirname(TRAINING_DATA_PATH), exist_ok=True)
            # Gem grundlæggende træningsdata til fremtidig brug
            with open(TRAINING_DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(BASIC_TRAINING_DATA, f, ensure_ascii=False, indent=2)
            return BASIC_TRAINING_DATA
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af træningsdata: {e}")
        return BASIC_TRAINING_DATA

def prepare_data(data):
    """Forbereder træningsdata til modellen"""
    X = []  # Input tekst
    y = []  # Intent labels
    
    for intent_data in data["intents"]:
        intent = intent_data["intent"]
        examples = intent_data["examples"]
        
        for example in examples:
            X.append(example)
            y.append(intent)
    
    return X, y

def train_model(X, y):
    """Træner NLU-modellen med optimerede parametre"""
    # Split data i trænings- og testsæt
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Opret pipeline
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.85)),
        ('classifier', LogisticRegression(max_iter=1000, C=10.0, class_weight='balanced'))
    ])
    
    # Træn modellen
    logger.info("Træner NLU-modellen...")
    pipeline.fit(X_train, y_train)
    
    # Evaluer modellen
    y_pred = pipeline.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)
    
    logger.info(f"Model træningsnøjagtighed: {accuracy:.4f}")
    print("\nKlassifikationsrapport:\n", report)

    # Gem unikke intent labels
    # Det er vigtigt at bruge de labels, modellen er trænet på (y_train), eller endnu bedre, alle unikke labels fra det oprindelige y datasæt.
    # For at være sikker på at alle mulige labels er med, selvom de ikke ender i y_train pga. split, er det bedst at tage unikke fra hele y.
    unique_labels = sorted(list(set(y))) # Brug hele y for at få alle mulige labels
    try:
        os.makedirs(os.path.dirname(LABELS_OUTPUT_PATH), exist_ok=True)
        joblib.dump(unique_labels, LABELS_OUTPUT_PATH)
        logger.info(f"Unikke intent labels gemt til: {LABELS_OUTPUT_PATH}")
        logger.info(f"Modellen er trænet med følgende {len(unique_labels)} labels: {unique_labels}")
    except Exception as e:
        logger.error(f"Fejl under gemning af labels.joblib: {e}")

    # Gem modellen
    try:
        os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
        joblib.dump(pipeline, MODEL_OUTPUT_PATH)
        logger.info(f"Model gemt til: {MODEL_OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Fejl under gemning af model.joblib: {e}")

    return pipeline

def add_training_examples():
    """Interaktiv funktion til at tilføje flere træningseksempler"""
    data = load_training_data()
    
    print("\n=== TILFØJ TRÆNINGSEKSEMPLER TIL JARVIS-LITE ===")
    print("Dette vil hjælpe med at forbedre Jarvis' forståelse af dine kommandoer.")
    
    # Vis tilgængelige intents
    print("\nTilgængelige intentioner:")
    for i, intent_data in enumerate(data["intents"]):
        print(f"{i+1}. {intent_data['intent']} ({len(intent_data['examples'])} eksempler)")
    
    print("\nIndtast 'ny' for at tilføje en ny intention, eller et nummer for at tilføje eksempler til en eksisterende.")
    print("Indtast 'afslut' for at gemme og afslutte.")
    
    while True:
        choice = input("\nVælg en mulighed: ").strip().lower()
        
        if choice == 'afslut':
            break
        
        if choice == 'ny':
            new_intent = input("Indtast navnet på den nye intention (uden mellemrum, kun små bogstaver): ").strip().lower()
            if not new_intent or ' ' in new_intent:
                print("Ugyldigt intentionsnavn. Prøv igen.")
                continue
                
            # Tjek om intentionen allerede findes
            exists = False
            for intent_data in data["intents"]:
                if intent_data["intent"] == new_intent:
                    exists = True
                    break
            
            if exists:
                print(f"Intentionen '{new_intent}' findes allerede. Vælg et andet navn.")
                continue
                
            # Tilføj den nye intention
            data["intents"].append({
                "intent": new_intent,
                "examples": []
            })
            intent_index = len(data["intents"]) - 1
            print(f"Ny intention '{new_intent}' tilføjet. Nu kan du tilføje eksempler.")
        else:
            try:
                intent_index = int(choice) - 1
                if intent_index < 0 or intent_index >= len(data["intents"]):
                    print("Ugyldigt valg. Prøv igen.")
                    continue
            except ValueError:
                print("Ugyldigt valg. Indtast et nummer, 'ny' eller 'afslut'.")
                continue
        
        # Tilføj eksempler til den valgte intention
        intent_name = data["intents"][intent_index]["intent"]
        print(f"\nTilføjer eksempler til intentionen '{intent_name}'.")
        print("Indtast et eksempel pr. linje. Indtast en tom linje for at afslutte.")
        
        while True:
            example = input("Eksempel: ").strip()
            if not example:
                break
                
            # Tjek om eksemplet allerede findes
            if example in data["intents"][intent_index]["examples"]:
                print("Dette eksempel findes allerede. Prøv et andet.")
                continue
                
            data["intents"][intent_index]["examples"].append(example)
            print(f"Eksempel tilføjet. Antal eksempler for '{intent_name}': {len(data['intents'][intent_index]['examples'])}")
    
    # Gem de opdaterede træningsdata
    with open(TRAINING_DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nTræningsdata gemt i {TRAINING_DATA_PATH}.")
    return data

def main():
    """Hovedfunktion til at træne NLU-modellen"""
    # Tjek om brugeren vil tilføje eksempler
    if len(sys.argv) > 1 and sys.argv[1] == '--add-examples':
        data = add_training_examples()
    else:
        data = load_training_data()
    
    # Vis statistik
    total_examples = sum(len(intent["examples"]) for intent in data["intents"])
    logger.info(f"Træningsdata: {len(data['intents'])} intentioner, {total_examples} eksempler i alt")
    
    # Forbereder data og træner modellen
    X, y = prepare_data(data)
    model = train_model(X, y)
    
    # Gem modellen
    joblib.dump(model, MODEL_OUTPUT_PATH)
    logger.info(f"Model gemt til {MODEL_OUTPUT_PATH}")
    
    print("\n=== MODEL TRÆNING FULDFØRT ===")
    print(f"NLU-modellen er trænet med {total_examples} eksempler fordelt på {len(data['intents'])} intentioner.")
    print(f"Modellen er gemt til {MODEL_OUTPUT_PATH} og er klar til brug i Jarvis-Lite.")
    print("\nFor at forbedre modellen yderligere, kør scriptet med '--add-examples':")
    print("python train_model.py --add-examples")

if __name__ == "__main__":
    main() 