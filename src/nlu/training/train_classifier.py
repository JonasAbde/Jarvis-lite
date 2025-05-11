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
        "kan du sige hvad klokken er",
        "må jeg høre hvad klokken er",
        "hvad viser uret",
        "jeg skal vide hvad klokken er",
        "hvad er tiden lige nu",
        "hvad er klokken på dette tidspunkt",
        "hvor langt er vi på dagen",
        "hvad er klokken blevet",
        "hvilket klokkeslæt har vi",
        "sig mig venligst hvad klokken er",
        # Nye eksempler
        "kan du tjekke klokken",
        "hvad er den",
        "hvad er klokken lige nu",
        "er den meget",
        "tiden nu",
        "fortæl mig hvad klokken er",
        "hvad tid er det nu",
        "hvad er uret lige nu",
        "jeg vil vide hvad klokken er",
        "fortæl tiden",
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
        "hvilken dato skriver vi",
        "hvad er det for en måned",
        "hvilken årstid er det",
        "hvilken dag har vi i dag",
        "er det weekend",
        "er det en helligdag i dag",
        "hvilken dag er det i morgen",
        "hvilken dato er det i dag",
        "kan du fortælle mig hvilken dag i ugen det er",
        "er det fredag i dag",
        # Nye eksempler
        "hvad er dagen i dag",
        "hvilken ugedag har vi",
        "er det tirsdag",
        "hvilken dato er det",
        "fortæl mig datoen",
        "hvilken dag har vi",
        "hvad er dagens dato",
        "er vi i juni måned",
        "hvilket år har vi",
        "er vi i 2025",
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
        "fortæl mig en sjov historie",
        "kender du en vittighed",
        "har du nogle jokes på lager",
        "jeg kunne godt bruge noget at grine af",
        "kan du fortælle en joke",
        "giv mig noget at grine af",
        "fortæl mig den sjoveste joke du kender",
        "har du en sjov vittighed at fortælle",
        "jeg vil gerne have en vittighed",
        "kan du få mig til at smile med en joke",
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
        "start browseren",
        "åbn min email",
        "jeg vil gerne tjekke min e-mail",
        "kan du vise mig tv2's hjemmeside",
        "kan du åbne min netbank",
        "åbn dr1",
        "åbn min favorit hjemmeside",
        "jeg vil gerne se youtube",
        "åbn en ny browser",
        "kan du starte min internet browser",
        # Nye eksempler
        "vis mig google",
        "jeg vil tjekke facebook",
        "jeg vil på youtube",
        "start youtube",
        "start google",
        "start facebook", 
        "kan du åbne en hjemmeside for mig",
        "søg på google",
        "søg på youtube",
        "gå til min e-mail",
        "åben browser",
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
        "jeg ved ikke hvad jeg skal spørge om",
        "giv mig en liste over dine kommandoer",
        "hvad kan du svare på",
        "vis en hjælpeguide",
        "fortæl mig hvordan du kan hjælpe mig",
        "hvordan virker du",
        "hvad er dine muligheder",
        "jeg forstår ikke hvordan man bruger dig",
        "hvad kan du bruges til",
        "hvilke spørgsmål kan du besvare",
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
        "godmorgen jarvis",
        "godaften jarvis",
        "god eftermiddag jarvis",
        "hej hej",
        "hejsa med dig",
        "god dag",
        "heyhey",
        "hej du",
        "hej hej med dig",
        "hyg",
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
        "tak for denne gang",
        "tak og farvel",
        "vi snakkes ved",
        "jeg er færdig for nu",
        "jeg går nu",
        "lukker ned",
        "jeg vil sige farvel nu",
        "tak for en god snak",
        "ses snart",
        "jeg kommer igen senere",
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
        "skriv dette ned for mig",
        "gem en huskeliste",
        "skriv en besked til mig selv",
        "jeg vil gerne gemme en note",
        "husk mig på",
        "skriv ned i min kalender",
        "opret en huskeliste",
        "noter følgende punkter",
        "vil du skrive en note til mig",
        "gem dette som en påmindelse",
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
        "hvilken AI er du",
        "beskriv dig selv",
        "hvad er din historie",
        "hvad er din oprindelse",
        "hvad er din baggrund",
        "hvad er dit formål",
        "hvordan virker du",
        "hvad er dine egenskaber",
        "er du en chatbot",
        "hvem kontrollerer dig",
        # Nye eksempler
        "fortæl hvem du er",
        "kan du fortælle mig om dig selv",
        "introducer dig selv", 
        "hvad er du for en størrelse",
        "hvem eller hvad er du",
        "er du en AI",
        "er du en assistent",
        "hvad er dit job",
        "hvad går du ud på",
        "hvem skabte dig",
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
        "hvordan er vejret i dag",
        "hvor varmt bliver det",
        "hvad er temperaturen",
        "skal jeg tage min regnjakke med",
        "bliver det overskyet",
        "er det tørvejr i dag",
        "vil det regne senere",
        "hvad er vejrudsigten for weekenden",
        "bliver det et dejligt vejr",
        "fortæl mig om vejrsituationen",
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
        "kan du afspille en god sang",
        "afspil musik fra min playliste",
        "sæt noget musik på",
        "spil en sang for mig",
        "jeg vil gerne have noget musik",
        "kan du give mig noget at lytte til",
        "spil noget roligt musik",
        "jeg har brug for musik",
        "afspil populær musik",
        "spil en dejlig melodi",
    ],
}


def prepare_data() -> Tuple[List[str], List[str]]:
    """
    Forbereder træningsdata med dataaugmentering

    Returns:
        X, y: Input tekster og deres labels
    """
    X = []
    y = []

    # Tilføj træningseksempler
    for intent, phrases in TRAINING_DATA.items():
        for phrase in phrases:
            # Original phrase
            X.append(phrase.lower())
            y.append(intent)
            
            # Dataaugmentering: Tilføj variationer med simple fejl
            # Tilføj version uden tegnsætning
            if any(c in phrase for c in ",.?!"):
                X.append(phrase.lower().replace(",", "").replace(".", "").replace("?", "").replace("!", ""))
                y.append(intent)
            
            # Tilføj version med skiftende store/små bogstaver, hvis ikke en meget kort sætning
            if len(phrase) > 5:
                X.append(phrase.lower().capitalize())  # Stort begyndelsesbogstav
                y.append(intent)
                
            # Tilføj version med små stavefejl for længere sætninger (mere end 3 ord)
            if len(phrase.split()) > 3:
                words = phrase.lower().split()
                # Simuler tilfældig stavefejl ved at bytte om på to bogstaver
                if len(words[0]) > 3:  # Kun længere ord
                    mod_word = list(words[0])
                    i = min(len(mod_word)-2, 1)  # Sikrer at vi ikke går ud over grænserne
                    mod_word[i], mod_word[i+1] = mod_word[i+1], mod_word[i]  # Byt om på bogstaver
                    words[0] = ''.join(mod_word)
                    X.append(' '.join(words))
                    y.append(intent)

    return X, y


def train_classifier() -> Tuple[TfidfVectorizer, LogisticRegression, List[str]]:
    """
    Træner en TF-IDF + LogReg klassifikator med bedre hyperparametre

    Returns:
        vectorizer, classifier, intents: De trænede modeller og intent-listen
    """
    logger.info("Forbereder træningsdata...")
    X, y = prepare_data()

    # Liste over unikke intents
    intents = list(TRAINING_DATA.keys())

    # Split data med stratificering for at sikre balanceret fordeling
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    logger.info(f"Træner på {len(X_train)} eksempler, tester på {len(X_test)} eksempler")

    # Opret og træn TF-IDF vectorizer med bedre parametre
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 3),  # Brug både unigrams, bigrams og trigrams
        min_df=1,  # Inkluder ord der forekommer mindst én gang
        max_df=0.95,
        analyzer="char_wb",  # Character n-grams på ordgrænser, robust over for stavefejl
        sublinear_tf=True,
    )
    X_train_tfidf = vectorizer.fit_transform(X_train)

    # Opret og træn LogReg classifier med forbedrede parametre
    classifier = LogisticRegression(
        C=1.0,  # Reguleringsparameter
        max_iter=1000,  # Flere iterationer for at sikre konvergens
        multi_class="ovr",
        solver="liblinear",
        class_weight="balanced",  # Hjælper med ubalancerede klasser
        random_state=42,
    )
    classifier.fit(X_train_tfidf, y_train)

    # Evaluér på test data
    X_test_tfidf = vectorizer.transform(X_test)
    y_pred = classifier.predict(X_test_tfidf)

    # Vis klassifikationsrapport
    logger.info("\nKlassifikationsrapport:")
    logger.info(classification_report(y_test, y_pred))

    # Test med nogle eksempler, inklusive stavefejl
    test_examples = [
        "hvad er klokken",
        "åben youtube",  # Stavefejl
        "noget helt tilfældigt",
        "fortæll om dig selv",  # Stavefejl
        "aafspil noget musik",  # Stavefejl
        "hej med dig",
        "jeg vil gernne høre en joke",  # Stavefejl
        "jeg ville gerne vide hvad datoen er i dag",
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
 