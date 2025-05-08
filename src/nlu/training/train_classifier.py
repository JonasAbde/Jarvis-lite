#!/usr/bin/env python3
"""
Træning af intent-klassifikator for Jarvis Lite.
Bruger TF-IDF feature extraction og LogisticRegression til klassifikation.
"""

import os
import joblib
import logging
import numpy as np
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sti til at gemme model
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.joblib")

# Træningsdata - repræsentative danske forespørgsler
TRAINING_DATA = {
    "get_time": [
        "hvad er klokken", 
        "kan du fortælle mig hvad klokken er", 
        "hvad er tidspunktet", 
        "fortæl mig tiden", 
        "klokken", 
        "tid",
        "hvad er den nu",
        "har du et ur",
        "ved du hvad klokken er",
        "hvor meget er klokken"
    ],
    "get_date": [
        "hvilken dag er det i dag", 
        "hvad er datoen", 
        "fortæl mig dagens dato", 
        "hvad er det for en dag i dag", 
        "dato",
        "hvilken dag er det",
        "hvilken ugedag er det",
        "hvad er det for en dag",
        "er det mandag i dag"
    ],
    "tell_joke": [
        "fortæl mig en joke", 
        "kan du fortælle en vittighed", 
        "sig noget sjovt", 
        "fortæl en vittighed", 
        "fortæl noget morsomt",
        "jeg trænger til at grine",
        "kender du en god joke",
        "kan du få mig til at grine",
        "har du en vittighed",
        "vær sjov"
    ],
    "open_website": [
        "åbn youtube", 
        "kan du åbne google", 
        "åbn dr", 
        "gå til youtube", 
        "åbn en hjemmeside",
        "vis mig dr.dk",
        "kan du vise youtube",
        "jeg vil gerne på google",
        "åbn en browser",
        "gå til dr.dk"
    ],
    "get_help": [
        "hvad kan du", 
        "hvad kan du hjælpe med", 
        "hvilke kommandoer forstår du",
        "hvad skal jeg sige", 
        "hvordan bruger jeg dig", 
        "hjælp",
        "jeg har brug for hjælp",
        "hvad er dine funktioner",
        "vis mig en liste over kommandoer",
        "hvilke ting kan du gøre"
    ],
    "greeting": [
        "hej", 
        "goddag", 
        "godmorgen", 
        "godaften", 
        "hejsa",
        "halløj",
        "davs",
        "god eftermiddag",
        "hilser",
        "hej med dig"
    ],
    "goodbye": [
        "farvel", 
        "vi ses", 
        "hav en god dag", 
        "tak for i dag", 
        "vi tales ved",
        "hej hej",
        "farveller",
        "jeg går nu",
        "afslut",
        "luk ned"
    ],
    "save_note": [
        "gem en note", 
        "skriv ned", 
        "husk at", 
        "vil du huske", 
        "gem denne note",
        "skriv i min notesbog",
        "jeg vil gerne notere følgende",
        "lav et notat med",
        "kan du gemme denne information",
        "gem teksten"
    ],
    "about_you": [
        "hvem er du", 
        "fortæl om dig selv", 
        "hvad hedder du", 
        "hvad er dit navn", 
        "er du en robot",
        "er du kunstig intelligens",
        "hvem har lavet dig",
        "hvordan er du lavet",
        "hvilken type AI er du",
        "hvordan fungerer du"
    ]
}

def prepare_data() -> Tuple[List[str], List[str]]:
    """
    Forbereder træningsdata
    
    Returns:
        X, y: Input tekster og deres labels
    """
    X = []
    y = []
    
    # Tilføj træningseksempler
    for intent, phrases in TRAINING_DATA.items():
        for phrase in phrases:
            X.append(phrase.lower())
            y.append(intent)
    
    return X, y

def train_classifier() -> Tuple[TfidfVectorizer, LogisticRegression, List[str]]:
    """
    Træner en TF-IDF + LogReg klassifikator
    
    Returns:
        vectorizer, classifier, intents: De trænede modeller og intent-listen
    """
    logger.info("Forbereder træningsdata...")
    X, y = prepare_data()
    
    # Liste over unikke intents
    intents = list(TRAINING_DATA.keys())
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    logger.info(f"Træner på {len(X_train)} eksempler, tester på {len(X_test)} eksempler")
    
    # Opret og træn TF-IDF vectorizer
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.95,
        analyzer='word',
        sublinear_tf=True
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)
    
    # Opret og træn LogReg classifier
    classifier = LogisticRegression(
        C=1.0,
        max_iter=200,
        multi_class='ovr',
        solver='liblinear',
        random_state=42
    )
    classifier.fit(X_train_tfidf, y_train)
    
    # Evaluér på test data
    X_test_tfidf = vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_tfidf)
    
    # Vis klassifikationsrapport
    logger.info("\nKlassifikationsrapport:")
    logger.info(classification_report(y_test, y_pred))
    
    # Test med nogle probabilities
    probs = classifier.predict_proba(vectorizer.transform(["hvad er klokken", "åben en hjemmeside", "noget helt tilfældigt"]))
    for i, prob in enumerate(probs):
        logger.info(f"Eksempel {i+1}: Max konfidens: {prob.max():.2f}, Klasse: {classifier.classes_[np.argmax(prob)]}")
    
    return vectorizer, classifier, intents

def save_model(vectorizer, classifier, intents):
    """
    Gemmer den trænede model til en fil
    
    Args:
        vectorizer: TF-IDF vectorizer
        classifier: Trænet classifier
        intents: Liste over intents
    """
    logger.info(f"Gemmer model til {MODEL_PATH}")
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump((vectorizer, classifier, intents), MODEL_PATH)
    logger.info("Model gemt!")

if __name__ == "__main__":
    logger.info("Starter træning af intent-klassifikator for Jarvis Lite...")
    vectorizer, classifier, intents = train_classifier()
    save_model(vectorizer, classifier, intents)
    logger.info("Træning fuldført!") 