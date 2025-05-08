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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Sti til at gemme model
MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model.joblib"
)

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
        "hvor meget er klokken",
        "hvad siger klokken",
        "hvilket tidspunkt har vi",
        "hvor sent er det",
        "kan du fortælle mig hvad tid det er",
        "hvad er klokken blevet",
        "jeg vil gerne vide hvad klokken er",
        "fortæl mig venligst hvad klokken er",
        "jeg har brug for at vide hvad tid det er",
        "hvad er uret",
        "kender du tiden",
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
        "er det mandag i dag",
        "hvilken dato har vi",
        "hvilken måned er det",
        "hvad er datoen i dag",
        "kan du fortælle mig hvilken dato vi har",
        "hvad er det for en ugedag",
        "fortæl mig hvilken dag det er",
        "hvilken dag i ugen er det",
        "hvilket årstal er det",
        "hvilken dag i måneden har vi",
        "hvilken måned har vi",
        "hvad er det for en dag i ugen",
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
        "vær sjov",
        "fortæl en god joke",
        "kender du nogle vittigheder",
        "jeg vil gerne høre noget sjovt",
        "kan du sige noget morsomt",
        "fortæl mig noget der kan få mig til at grine",
        "jeg har brug for at grine lidt",
        "har du nogle gode jokes",
        "kan du muntre mig op med en vittighed",
        "jeg vil gerne høre en vittighed",
        "gør mig i godt humør med en joke",
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
        "gå til dr.dk",
        "åbn facebook",
        "kan du åbne netflix",
        "gå ind på tv2.dk",
        "åbn min e-mail",
        "kan du åbne gmail",
        "jeg vil gerne tjekke nyhederne på dr.dk",
        "åbn wikipedia",
        "vis mig facebook hjemmesiden",
        "kan du åbne amazon",
        "vis mig instagram",
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
        "hvilke ting kan du gøre",
        "hvordan fungerer du",
        "forklar mig hvordan du virker",
        "vejledning",
        "guide mig",
        "hvordan kan jeg bruge dig",
        "vis mig mulighederne",
        "hvilke opgaver kan du udføre",
        "fortæl mig om dine funktioner",
        "hvad kan jeg spørge dig om",
        "hvad skal jeg gøre for at bruge dig",
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
        "hej med dig",
        "hallo",
        "dav",
        "goddav",
        "mojn",
        "hej jarvis",
        "hej med dig jarvis",
        "god dag til dig",
        "hvordan går det",
        "hvordan har du det",
        "hyggeligt at møde dig",
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
        "luk ned",
        "på gensyn",
        "ses senere",
        "ses i morgen",
        "godnat",
        "tak for hjælpen",
        "slut for i dag",
        "jeg er færdig",
        "jeg skal gå nu",
        "tak for nu",
        "jeg er færdig med at snakke",
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
        "gem teksten",
        "noter dette",
        "lav en huskeseddel",
        "gem en påmindelse om",
        "skriv en note med",
        "tilføj til mine noter",
        "gem dette til senere",
        "jeg har brug for at huske",
        "opret en note med følgende",
        "husk denne besked",
        "kan du skrive en note til mig",
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
        "hvordan fungerer du",
        "fortæl mig om dig selv",
        "hvad er du for en",
        "hvad kan du fortælle om dig selv",
        "hvad er formålet med dig",
        "hvad er din funktion",
        "er du menneskelig",
        "er du en computer",
        "hvad er du",
        "hvordan blev du skabt",
        "hvor gammel er du",
    ],
    "get_weather": [
        "hvordan bliver vejret",
        "hvordan er vejret i dag",
        "hvad siger vejrudsigten",
        "skal jeg tage en paraply med",
        "bliver det regn i dag",
        "hvordan er temperaturen udenfor",
        "bliver det solskin",
        "kommer det til at regne",
        "hvordan er vejret i morgen",
        "skal jeg have en jakke på",
        "bliver det varmt i dag",
        "vejrudsigt for i dag",
        "hvad med vejret i weekenden",
        "fortæl mig om vejret",
        "hvordan er vejrforholdene",
        "er det koldt udenfor",
        "bliver det blæsevejr",
        "hvad er temperaturen lige nu",
        "hvordan er vejrudsigten for i aften",
        "er det godt vejr til en gåtur",
    ],
    "play_music": [
        "spil noget musik",
        "kan du afspille musik",
        "jeg vil høre musik",
        "spil min yndlingssang",
        "spil noget afslapningsmusik",
        "start afspilning af musik",
        "jeg vil gerne høre noget musik",
        "kan du spille en sang",
        "musik",
        "afspil en sang",
        "spil noget jazz",
        "start musikafspiller",
        "afspil min spilleliste",
        "jeg har lyst til at høre musik",
        "kan du afspille noget klassisk",
        "jeg vil gerne have musik i baggrunden",
        "spil den seneste musik",
        "afspil min favoritmusik",
        "start noget musik",
        "jeg trænger til noget musik",
    ],
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
        ngram_range=(1, 3),  # Brug både unigrams, bigrams og trigrams
        min_df=2,
        max_df=0.95,
        analyzer="word",
        sublinear_tf=True,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)

    # Opret og træn LogReg classifier med forbedrede parametre
    classifier = LogisticRegression(
        C=1.5,  # Lidt mindre regulering
        max_iter=300,  # Flere iterationer
        multi_class="ovr",
        solver="liblinear",
        random_state=42,
    )
    classifier.fit(X_train_tfidf, y_train)

    # Evaluér på test data
    X_test_tfidf = vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_tfidf)

    # Vis klassifikationsrapport
    logger.info("\nKlassifikationsrapport:")
    logger.info(classification_report(y_test, y_pred))

    # Test med nogle probabilities
    test_examples = [
        "hvad er klokken",
        "åben youtube",
        "noget helt tilfældigt",
        "hvordan bliver vejret i dag",
        "afspil noget musik",
    ]
    probs = classifier.predict_proba(vectorizer.transform(test_examples))
    for i, prob in enumerate(probs):
        logger.info(
            f"Eksempel {i+1} ('{test_examples[i]}'): "
            f"Max konfidens: {prob.max():.2f}, "
            f"Klasse: {classifier.classes_[np.argmax(prob)]}"
        )

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
