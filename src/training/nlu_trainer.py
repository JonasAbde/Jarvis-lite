import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# Sti til data og model
DATA_PATH = "nlu_commands.json"
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "nlu_model.joblib")
VECTORIZER_PATH = os.path.join(MODEL_DIR, "vectorizer.joblib")

# 1. Indlæs træningsdata
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

X = []
y = []
for intent in data["intents"]:
    for ex in intent["examples"]:
        X.append(ex)
        y.append(intent["intent"])

# 2. Træn model
vectorizer = TfidfVectorizer()
X_vec = vectorizer.fit_transform(X)
model = LogisticRegression(max_iter=1000)
model.fit(X_vec, y)

# 3. Gem model og vectorizer
os.makedirs(MODEL_DIR, exist_ok=True)
joblib.dump(model, MODEL_PATH)
joblib.dump(vectorizer, VECTORIZER_PATH)
print("[INFO] NLU-model og vectorizer gemt!")
