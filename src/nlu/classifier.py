"""
NLU Klassifikationsmodul for Jarvis-lite.
Håndterer træning, lagring, og forudsigelse af intents.
"""
import json
import nltk # Bruges til tokenisering og potentielt stopord/stemming
import numpy as np
import os
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
import joblib # Til at gemme og loade modellen
from typing import Tuple, Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Stier (kan gøres mere konfigurerbare)
DATA_FILE_PATH = "data/nlu_training_data.json" # Sti til din JSON-fil med intents og patterns
# MODEL_DIR = "models/nlu"
# MODEL_FILE_PATH = os.path.join(MODEL_DIR, "nlu_model.joblib")
MODEL_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.joblib")
VECTORIZER_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorizer.joblib")
LABELS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "labels.joblib")

# Download nødvendige NLTK data hvis de ikke allerede findes
# Dette er for tokenisering. Stopord og stemming kan kræve yderligere downloads.
try:
    nltk.data.find('tokenizers/punkt')
except Exception:  # Bruger generisk exception i stedet for specifik nltk.downloader.DownloadError
    logger.info("Downloader NLTK 'punkt' tokenizer...")
    nltk.download('punkt', quiet=True)

# Simple danske stopord (kan udvides eller erstattes med en mere komplet liste)
DANISH_STOP_WORDS = [
    'og', 'i', 'jeg', 'det', 'at', 'en', 'den', 'til', 'er', 'som', 'på', 'de', 'med', 'han', 'af',
    'for', 'ikke', 'der', 'vil', 'hvis', 'så', 'men', 'et', 'mig', 'dig', 'hans', 'min',
    'har', 'havde', 'hun', 'hende', 'sig', 'man', 'mange', 'også', 'skal', 'kan', 'kunne',
    'ville', 'være', 'været', 'fra', 'ham', 'om', 'op', 'ned', 'ud', 'ind', 'din', 'dit',
    'sine', 'sit', 'nogen', 'noget', 'alle', 'alt', 'anden', 'andet', 'andre', 'blev', 'blive',
    'bliver', 'da', 'denne', 'dette', 'dog', 'efter', 'eller', 'end', 'flere', 'fordi',
    'før', 'god', 'godt', 'gør', 'gøre', 'gørende', 'hende', 'hendes', 'her', 'hvordan',
    'hvorfor', 'hvilken', 'hvilke', 'hvilket', 'hvor', 'igen', 'imod', 'ingen', 'intet',
    'jo', 'kom', 'komme', 'kommer', 'lav', 'lidt', 'lige', 'meget', 'mere', 'må', 'måske',
    'næste', 'når', 'nyt', 'over', 'selv', 'siden', 'skulle', 'stor', 'store', 'synes',
    'siger', 'tilbage', 'under', 'var', 'vi', 'ved', 'vore', 'vores'
]


def preprocess_text_danish(text: str) -> str:
    """
    Forbehandler dansk tekst: tokenisering, lowercase, fjern tegnsætning.
    Simpel version uden stemming/lemmatisering for nu.
    """
    if not isinstance(text, str):
        logger.warning(f"Forventede str til preproces_text_danish, fik {type(text)}. Returnerer tom streng.")
        return ""
        
    # Tokenize
    tokens = nltk.word_tokenize(text.lower(), language='danish')
    
    # Fjern tegnsætning og stopord
    # Beholder kun alfanumeriske tokens (fjerner tegnsætning)
    # og fjerner stopord
    processed_tokens = [
        word for word in tokens 
        if word.isalnum() and word not in DANISH_STOP_WORDS
    ]
    
    return " ".join(processed_tokens)


def load_training_data(file_path: str = DATA_FILE_PATH) -> Tuple[List[str], List[str]]:
    """Indlæser træningsdata (patterns og intents) fra JSON fil."""
    patterns = []
    intents = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for intent_data in data.get("intents", []):
            tag = intent_data.get("tag")
            if not tag:
                logger.warning("Skipping intent uden 'tag' i træningsdata.")
                continue
            for pattern in intent_data.get("patterns", []):
                if isinstance(pattern, str) and pattern.strip():
                    patterns.append(preprocess_text_danish(pattern))
                    intents.append(tag)
                else:
                    logger.warning(f"Skipping ugyldigt pattern for intent '{tag}': {pattern}")

        if not patterns or not intents:
            logger.error("Ingen gyldige patterns eller intents fundet i træningsdata.")
            return [], []
            
        logger.info(f"Indlæst {len(patterns)} patterns for {len(set(intents))} unikke intents fra {file_path}.")
        return patterns, intents
    except FileNotFoundError:
        logger.error(f"Træningsdatafil {file_path} ikke fundet.")
        return [], []
    except json.JSONDecodeError:
        logger.error(f"Fejl ved dekodning af JSON fra {file_path}.")
        return [], []
    except Exception as e:
        logger.error(f"Uventet fejl under indlæsning af træningsdata: {e}")
        return [], []


class NLUClassifier:
    def __init__(self, model_path: str = MODEL_FILE_PATH, 
                 vectorizer_path: str = VECTORIZER_FILE_PATH,
                 labels_path: str = LABELS_FILE_PATH):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.labels_path = labels_path
        self.pipeline: Optional[Pipeline] = None
        self.intent_labels: Optional[List[str]] = None
        self._load_model()

    def _create_pipeline(self) -> Pipeline:
        """Opretter en scikit-learn pipeline for NLU."""
        # TF-IDF Vectorizer
        tfidf_vectorizer = TfidfVectorizer(
            preprocessor=preprocess_text_danish, # Brug vores forbehandlingsfunktion
            tokenizer=nltk.word_tokenize, # NLTK tokenizer
            stop_words=DANISH_STOP_WORDS, # Brug vores danske stopordsliste
            ngram_range=(1, 2), # Overvej både unigrams og bigrams
            max_df=0.9, # Ignorer termer der optræder i mere end 90% af dokumenterne
            min_df=2, # Ignorer termer der optræder i færre end 2 dokumenter
            use_idf=True,
            smooth_idf=True,
            norm='l2' # L2 normalisering
        )
        
        # Klassifikator (Logistic Regression er et godt startpunkt)
        classifier = LogisticRegression(
            solver='liblinear', # God til mindre datasæt
            C=1.0, # Regulariseringsstyrke
            random_state=42,
            class_weight='balanced' # Håndter ubalancerede klasser
        )
        
        return Pipeline([
            ('tfidf', tfidf_vectorizer),
            ('clf', classifier)
        ])

    def train(self, training_patterns: List[str], training_intents: List[str], perform_grid_search: bool = False):
        """Træner NLU modellen og gemmer den."""
        if not training_patterns or not training_intents:
            logger.error("Træning afbrudt: Ingen træningsdata leveret.")
            return

        self.pipeline = self._create_pipeline()
        
        # Gem de unikke intent labels for senere brug ved forudsigelse
        self.intent_labels = sorted(list(set(training_intents)))
        
        logger.info("Starter træning af NLU-model...")
        
        if perform_grid_search:
            logger.info("Udfører GridSearchCV for at finde optimale parametre...")
            # Definer parameter grid (eksempel)
            # Pas på: GridSearchCV kan være tidskrævende
            param_grid = {
                'tfidf__ngram_range': [(1, 1), (1, 2)],
                'tfidf__max_df': [0.75, 0.9, 0.95],
                'clf__C': [0.1, 1, 10],
                'clf__solver': ['liblinear', 'saga'] # saga kan være langsommere men bedre
            }
            grid_search = GridSearchCV(self.pipeline, param_grid, cv=3, n_jobs=-1, verbose=1, scoring='accuracy')
            try:
                grid_search.fit(training_patterns, training_intents)
                self.pipeline = grid_search.best_estimator_
                logger.info(f"GridSearchCV bedste parametre: {grid_search.best_params_}")
                logger.info(f"GridSearchCV bedste score: {grid_search.best_score_:.4f}")
            except Exception as e:
                logger.error(f"Fejl under GridSearchCV: {e}. Bruger standard pipeline.")
                # Fallback til standard pipeline hvis GridSearchCV fejler
                self.pipeline.fit(training_patterns, training_intents)

        else:
            self.pipeline.fit(training_patterns, training_intents)
            
        logger.info("NLU-model trænet succesfuldt.")
        self._save_model()

    def _save_model(self):
        """Gemmer den trænede model, vectorizer og labels."""
        if self.pipeline and self.intent_labels:
            try:
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                joblib.dump(self.pipeline, self.model_path)
                # Gem labels separat for at sikre vi kan mappe outputs til intent navne
                joblib.dump(self.intent_labels, self.labels_path)
                logger.info(f"NLU-model og labels gemt i {os.path.dirname(self.model_path)}")
                logger.info(f"Modellen kender {len(self.intent_labels)} intents: {self.intent_labels}")
            except Exception as e:
                logger.error(f"Fejl under gemning af NLU-model: {e}")
        else:
            logger.warning("Ingen model at gemme (pipeline eller labels mangler).")

    def _load_model(self):
        """Indlæser en gemt NLU-model, vectorizer og labels."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.labels_path):
                self.pipeline = joblib.load(self.model_path)
                self.intent_labels = joblib.load(self.labels_path)
                logger.info(f"NLU-model og labels indlæst fra {os.path.dirname(self.model_path)}")
            else:
                logger.info("Ingen pre-trænet NLU-model fundet. Modellen skal trænes først.")
                self.pipeline = None
                self.intent_labels = None
        except Exception as e:
            logger.error(f"Fejl under indlæsning af NLU-model: {e}")
            self.pipeline = None
            self.intent_labels = None
            
    def predict(self, text: str, confidence_threshold: float = 0.55) -> Optional[Dict[str, Any]]:
        """
        Forudsiger intent for en given tekst (alias til analyze for kompatibilitet).
        Returnerer intent, konfidens og alle sandsynligheder hvis modellen er indlæst.

        Args:
            text: Teksten der skal analyseres
            confidence_threshold: Minimumsværdi for konfidens (default: 0.55)

        Returns:
            Dict med intent, konfidens og alle sandsynligheder, eller None hvis fejl
        """
        return self.analyze(text, confidence_threshold)

    def analyze(self, text: str, confidence_threshold: float = 0.55) -> Optional[Dict[str, Any]]:
        """
        Forudsiger intent for en given tekst.
        Returnerer intent, konfidens og alle sandsynligheder hvis modellen er indlæst.
        """
        if not self.pipeline or not self.intent_labels:
            logger.warning("NLU-model er ikke indlæst eller trænet. Kan ikke forudsige.")
            # Fallback til simpel keyword matching hvis ingen model er loadet
            # Dette er en placeholder, din `command_parser` vil være bedre her
            if "klokken" in text.lower() or "tid" in text.lower():
                 return {"intent": "get_time", "confidence": 0.99, "all_probabilities": [{"intent": "get_time", "confidence": 0.99}]} # Dummy
            return None

        if not isinstance(text, str) or not text.strip():
            logger.debug("Tom input tekst til predict, returnerer None.")
            return None # Tilføjet eksplicit None return for klarhed

        try:
            # Forbehandl teksten
            processed_text = preprocess_text_danish(text)
            if not processed_text:
                logger.debug(f"Input tekst gav tom forbehandlet tekst: '{text}'. Kan ikke forudsige.")
                # Selvom forbehandling gav tom streng, kan vi stadig logge den oprindelige tekst med lav konfidens
                predicted_intent_tag = "no_tokens"
                confidence = 0.0
                # Log lav-konfidens forudsigelser for senere gennemgang/træning
                LOW_CONF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "low_confidence_log.txt") # Korrekt sti
                try:
                    os.makedirs(os.path.dirname(LOW_CONF_FILE), exist_ok=True)
                    with open(LOW_CONF_FILE, "a", encoding="utf-8") as f:
                        log_entry = {"text": text,
                                     "guess": predicted_intent_tag,
                                     "confidence": float(confidence)}
                        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                    logger.debug(f"Logged low confidence prediction for '{text}': {predicted_intent_tag} ({confidence:.2f})")
                except Exception as e:
                    logger.error(f"Fejl under logning til low_confidence_log.txt: {e}")

                return None # Returner None da ingen meningsfuld forudsigelse kunne laves
                
            # Anvend pipeline til at få sandsynligheder for hver intent
            probabilities = self.pipeline.predict_proba([processed_text])[0] # predict_proba forudsiger sandsynligheder

            # Find intent med højeste sandsynlighed
            max_prob_index = np.argmax(probabilities)
            predicted_intent_tag = self.intent_labels[max_prob_index]
            confidence = probabilities[max_prob_index]

            # Opret liste af alle intents med deres sandsynligheder
            all_probabilities = [
                {"intent": self.intent_labels[i], "confidence": float(probabilities[i])}
                for i in range(len(self.intent_labels))
            ]
            
            # Log lav-konfidens forudsigelser for senere gennemgang/træning
            LOW_CONF_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "low_confidence_log.txt") # Korrekt sti
            if confidence < confidence_threshold:
                 try:
                     os.makedirs(os.path.dirname(LOW_CONF_FILE), exist_ok=True)
                     with open(LOW_CONF_FILE, "a", encoding="utf-8") as f:
                         # Sørg for at predicted_intent_tag er defineret. 
                         # Hvis prediction fejler eller confidence er lav, er der måske ikke en tag.
                         # Brug 'unknown' eller predicted_intent_tag hvis den findes.
                         predicted_intent_tag_to_log = predicted_intent_tag if predicted_intent_tag else "unknown"

                         log_entry = {"text": text, 
                                      "guess": predicted_intent_tag_to_log, 
                                      "confidence": float(confidence)}
                         f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                     logger.debug(f"Logged low confidence prediction for '{text}': {predicted_intent_tag_to_log} ({confidence:.2f})")
                 except Exception as e:
                     logger.error(f"Fejl under logning til low_confidence_log.txt: {e}")

            # Returner intent og konfidens hvis konfidensen er over tærsklen
            if confidence >= confidence_threshold:
                logger.info(f"Intent genkendt: '{predicted_intent_tag}' med konfidens {confidence:.2f}")
                return {"intent": predicted_intent_tag, "confidence": confidence, "all_probabilities": all_probabilities}
            else:
                logger.info(f"Lav konfidens for intent '{predicted_intent_tag}' ({confidence:.2f} < {confidence_threshold:.2f}). Returnerer ukendt.")
                return {"intent": "unknown", "confidence": confidence, "all_probabilities": all_probabilities}

        except Exception as e:
            logger.error(f"Fejl under NLU analyse af tekst '{text}': {e}", exc_info=True)
            return None # Returner None ved fejl

    def get_available_intents(self) -> List[str]:
        """Returnerer en liste over de kendte intent labels."""
        return self.intent_labels if self.intent_labels else []

# Funktioner til at blive kaldt fra andre moduler (som i din __init__.py)
_classifier_instance: Optional[NLUClassifier] = None

def _get_classifier_instance() -> NLUClassifier:
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = NLUClassifier()
    return _classifier_instance

def analyze(text: str, confidence_threshold: float = 0.55) -> Optional[Dict[str, Any]]:
    """Analyserer tekst og returnerer forudsagt intent og konfidens."""
    instance = _get_classifier_instance()
    return instance.analyze(text, confidence_threshold)

def get_available_intents() -> List[str]:
    """Henter listen over tilgængelige intents fra den trænede model."""
    instance = _get_classifier_instance()
    return instance.get_available_intents()

def predict(text: str, confidence_threshold: float = 0.55) -> Optional[Dict[str, Any]]:
    """
    Forudsiger intent for en given tekst (alias til analyze for kompatibilitet).
    Returnerer intent, konfidens og alle sandsynligheder hvis modellen er indlæst.

    Args:
        text: Teksten der skal analyseres
        confidence_threshold: Minimumsværdi for konfidens (default: 0.55)

    Returns:
        Dict med intent, konfidens og alle sandsynligheder, eller None hvis fejl
    """
    return analyze(text, confidence_threshold)

def train_nlu_model_from_file(data_file: str = DATA_FILE_PATH, grid_search: bool = False):
    """Hjælpefunktion til at starte træning fra en datafil."""
    logger.info(f"Starter NLU træningsproces fra datafil: {data_file}")
    patterns, intents = load_training_data(data_file)
    if patterns and intents:
        # Split data for evaluering (valgfrit, men god praksis)
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                patterns, intents, test_size=0.2, random_state=42, 
                stratify=intents if len(set(intents)) > 1 else None
            )
        except ValueError as e:
            # Håndter fejl når datasættet er for lille til at opdele
            logger.warning(f"Kunne ikke opdele datasæt: {e}. Bruger hele datasættet til træning.")
            X_train, y_train = patterns, intents
            X_test, y_test = [], []
        
        classifier = NLUClassifier() # Opret ny instans for træning
        classifier.train(X_train, y_train, perform_grid_search=grid_search)
        
        # Evaluer på test sæt
        if classifier.pipeline and X_test and y_test:
            logger.info("\nEvalueringsrapport på test-sæt:")
            try:
                y_pred = classifier.pipeline.predict(X_test)
                print(classification_report(y_test, y_pred, zero_division=0))
            except Exception as e:
                logger.error(f"Kunne ikke generere klassifikationsrapport: {e}")
        return classifier # Returner den trænede instans
    else:
        logger.error("Kunne ikke indlæse træningsdata. Træning afbrudt.")
        return None

if __name__ == '__main__':
    # Konfigurer logging for direkte kørsel
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 1. Opret dummy træningsdatafil hvis den ikke findes
    if not os.path.exists(DATA_FILE_PATH):
        logger.info(f"Opretter dummy træningsdatafil: {DATA_FILE_PATH}")
        os.makedirs(os.path.dirname(DATA_FILE_PATH), exist_ok=True)
        dummy_data = {
            "intents": [
                {"tag": "greeting", "patterns": ["hej", "goddag", "hallo", "davs"], "responses": ["Hej!", "Goddag!"]},
                {"tag": "goodbye", "patterns": ["farvel", "vi ses", "på gensyn"], "responses": ["Farvel!", "Vi ses!"]},
                {"tag": "get_time", "patterns": ["hvad er klokken", "hvad er tiden", "tiden tak"], "responses": ["Klokken er..."]},
                {"tag": "get_weather", "patterns": ["hvordan er vejret", "vejret i dag", "solskin?"], "responses": ["Jeg tjekker vejret..."]}
            ]
        }
        with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(dummy_data, f, ensure_ascii=False, indent=2)

    # 2. Træn modellen (kan tage lidt tid, især med grid search)
    # Sæt grid_search=True for at prøve at finde bedre parametre (langsommere)
    # Første gang du kører, vil modellen blive trænet og gemt.
    # Efterfølgende gange vil den indlæse den gemte model, medmindre du eksplicit træner igen.
    
    # Tjek om model allerede er trænet
    if not os.path.exists(MODEL_FILE_PATH):
        logger.info("NLU model ikke fundet. Starter træning...")
        trained_classifier = train_nlu_model_from_file(grid_search=False) # Sæt til True for grundigere træning
        if not trained_classifier:
             logger.error("NLU træning fejlede. Tjek logs.")
             exit()
    else:
        logger.info("Pre-trænet NLU model fundet. Indlæser...")
        # Opdater _classifier_instance, så den bruger den friskloadede model
        _classifier_instance = NLUClassifier() 
        if not _classifier_instance.pipeline: # Hvis indlæsning fejlede
            logger.warning("Indlæsning af pre-trænet model fejlede. Prøver at træne igen...")
            trained_classifier = train_nlu_model_from_file(grid_search=False)
            if not trained_classifier:
                logger.error("NLU træning fejlede efter mislykket load. Tjek logs.")
                exit()


    # 3. Test forudsigelser
    logger.info("\nTester NLU forudsigelser:")
    test_sætninger = [
        "hej med dig",
        "hvad er klokken min ven?",
        "hvordan er vejret i København",
        "farvel for nu",
        "sæt en alarm", # Burde give 'unknown' hvis ikke trænet
        "spil noget musik" # Burde give 'unknown'
    ]

    nlu_predictor = _get_classifier_instance() # Få den (potentielt trænede/loadede) instans

    for sætning in test_sætninger:
        prediction = nlu_predictor.analyze(sætning)
        if prediction:
            print(f"Tekst: '{sætning}' -> Intent: {prediction['intent']} (Konfidens: {prediction['confidence']:.2f})")
            # print(f"  Alle sandsynligheder: {prediction['all_probabilities'][:2]}") # Vis top 2
        else:
            print(f"Tekst: '{sætning}' -> Kunne ikke forudsige intent.")
            
    print(f"\nTilgængelige intents ifølge modellen: {get_available_intents()}")

    # For at køre dette eksempel:
    # 1. Sørg for at NLTK, scikit-learn og joblib er installeret:
    #    pip install nltk scikit-learn joblib
    # 2. Kør: python src/nlu/classifier.py
    #    Første gang vil den oprette en dummy datafil, træne modellen og gemme den.
    #    Efterfølgende kørsler vil indlæse den gemte model.
