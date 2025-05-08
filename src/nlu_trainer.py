"""
Træn den danske intent-klassifikator for Jarvis-lite.
Outputter (vectorizer, kalibreret klassifikator, intent-liste) → model.joblib
"""

import json
import pathlib
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

# Definer stier
ROOT = pathlib.Path(__file__).resolve().parent
DATA = ROOT / "data" / "nlu_commands.json"
MODEL_PATH = ROOT / "nlu" / "model.joblib"

def train_nlu():
    """Træn og gem NLU-modellen."""
    print("[INFO] Indlæser træningsdata...")
    with DATA.open(encoding="utf-8") as fp:
        samples = json.load(fp)

    # Forbered data
    texts, labels = [], []
    for intent, utterances in samples.items():
        for u in utterances:
            texts.append(u.lower())
            labels.append(intent)

    print(f"[INFO] Træner på {len(texts)} eksempler med {len(set(labels))} intents")
    
    # Træn vectorizer
    vec = TfidfVectorizer(
        ngram_range=(1, 2),
        analyzer="char",
        lowercase=True
    )
    X = vec.fit_transform(texts)
    
    # Træn og kalibrer klassifikator
    base = LogisticRegression(max_iter=1000, solver="lbfgs")
    clf = CalibratedClassifierCV(base)  # Aktiverer predict_proba
    clf.fit(X, labels)
    
    # Gem model
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump((vec, clf, sorted(set(labels))), MODEL_PATH)
    print(f"✅ Model gemt i {MODEL_PATH.relative_to(ROOT)}")

if __name__ == "__main__":
    train_nlu()
