# Simpel neural net chatbot-træner til danske spørgsmål/svar-par
# Kræver: pip install tensorflow scikit-learn

import json
import numpy as np
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# 1. Indlæs data
with open("conversation_pairs.json", "r", encoding="utf-8") as f:
    pairs = json.load(f)

questions = [pair["user"] for pair in pairs]
answers = [pair["jarvis"] for pair in pairs]

# 2. Tekst til tal (tokenizer)
tokenizer = keras.preprocessing.text.Tokenizer(char_level=False)
tokenizer.fit_on_texts(questions)
X = tokenizer.texts_to_sequences(questions)
X = keras.preprocessing.sequence.pad_sequences(X, padding="post")

# 3. Label encode svar
le = LabelEncoder()
y = le.fit_transform(answers)

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 5. Byg og træn model
model = keras.Sequential([
    keras.layers.Embedding(input_dim=len(tokenizer.word_index)+1, output_dim=32, input_length=X.shape[1]),
    keras.layers.GlobalAveragePooling1D(),
    keras.layers.Dense(32, activation="relu"),
    keras.layers.Dense(len(set(y)), activation="softmax")
])
model.compile(loss="sparse_categorical_crossentropy", optimizer="adam", metrics=["accuracy"])
model.fit(X_train, y_train, epochs=100, batch_size=8, validation_data=(X_test, y_test), verbose=1)

# 6. Gem alt
model.save("models/nn_chatbot.h5")
import pickle
with open("models/nn_tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)
with open("models/nn_labelencoder.pkl", "wb") as f:
    pickle.dump(le, f)

print("[INFO] Neural net chatbot er trænet og gemt!")
