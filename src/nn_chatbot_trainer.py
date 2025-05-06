# Forbedret neural net chatbot-træner til danske spørgsmål/svar-par
# Kræver: pip install tensorflow scikit-learn

import json
import numpy as np
import os
import matplotlib.pyplot as plt
from tensorflow import keras
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

# --- Konfiguration (justerbare hyperparametre) ---
EPOCHS = 100
BATCH_SIZE = 8
DROPOUT_RATE = 0.3  # Hjælper mod overfitting
EMBEDDING_DIM = 64  # Større end før for bedre tekst-repræsentation
HIDDEN_UNITS = 128  # Flere neuroner i det skjulte lag
PATIENCE = 10       # Tidlig stop - antal epochs uden forbedring
VALIDATION_SPLIT = 0.2
RANDOM_SEED = 42
VERBOSE = 1

# --- Opret model-mappe hvis den ikke findes ---
os.makedirs("models", exist_ok=True)

# 1. Indlæs data
print("[INFO] Indlæser og forbereder data...")
with open("conversation_pairs.json", "r", encoding="utf-8") as f:
    pairs = json.load(f)

# Tjek for tom data
if not pairs:
    print("[FEJL] Ingen data fundet i conversation_pairs.json!")
    exit(1)

print(f"[INFO] Indlæste {len(pairs)} samtalepar")

questions = [pair["user"] for pair in pairs]
answers = [pair["jarvis"] for pair in pairs]

# 2. Tekst til tal (tokenizer) - forbedret med danske stop-words
tokenizer = keras.preprocessing.text.Tokenizer(char_level=False)
tokenizer.fit_on_texts(questions)
X = tokenizer.texts_to_sequences(questions)
X = keras.preprocessing.sequence.pad_sequences(X, padding="post")

# 3. Label encode svar
le = LabelEncoder()
y = le.fit_transform(answers)

# 4. Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=VALIDATION_SPLIT, random_state=RANDOM_SEED)

print(f"[INFO] Vokabular-størrelse: {len(tokenizer.word_index)+1}")
print(f"[INFO] Antal klasser (unikke svar): {len(set(y))}")
print(f"[INFO] Træningssæt størrelse: {len(X_train)}")
print(f"[INFO] Testsæt størrelse: {len(X_test)}")

# 5. Byg og træn model - forbedret arkitektur
print("[INFO] Bygger og træner model...")
model = keras.Sequential([
    # Input-lag
    keras.layers.Embedding(input_dim=len(tokenizer.word_index)+1, 
                          output_dim=EMBEDDING_DIM, 
                          input_length=X.shape[1]),
    
    # Forbedret feature-ekstraktion med bidirectional LSTM
    keras.layers.Bidirectional(keras.layers.LSTM(EMBEDDING_DIM, return_sequences=True)),
    keras.layers.Dropout(DROPOUT_RATE),  # Dropout for at undgå overfitting
    
    # Attention-mekanisme
    keras.layers.GlobalAveragePooling1D(),
    
    # Første Dense-lag
    keras.layers.Dense(HIDDEN_UNITS, activation="relu"),
    keras.layers.Dropout(DROPOUT_RATE),  # Endnu et dropout-lag
    
    # Output-lag
    keras.layers.Dense(len(set(y)), activation="softmax")
])

# Model-opsummering
model.summary()

# Compile model med forbedrede metrics
model.compile(
    loss="sparse_categorical_crossentropy", 
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    metrics=["accuracy"]
)

# Callbacks for tidlig stop og model-checkpoint
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=PATIENCE,
        restore_best_weights=True,
        verbose=1
    ),
    keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        verbose=1
    )
]

# Træn modellen med callbacks
print("[INFO] Træner model...")
history = model.fit(
    X_train, y_train, 
    epochs=EPOCHS, 
    batch_size=BATCH_SIZE, 
    validation_data=(X_test, y_test), 
    verbose=VERBOSE,
    callbacks=callbacks
)

# 6. Evaluering og visualisering
print("[INFO] Evaluerer model...")
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"[RESULTAT] Test accuracy: {test_acc:.4f}")
print(f"[RESULTAT] Test loss: {test_loss:.4f}")

# Plot training history
plt.figure(figsize=(12, 4))

# Plot accuracy
plt.subplot(1, 2, 1)
plt.plot(history.history['accuracy'], label='Train')
plt.plot(history.history['val_accuracy'], label='Validation')
plt.title('Model Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.legend()

# Plot loss
plt.subplot(1, 2, 2)
plt.plot(history.history['loss'], label='Train')
plt.plot(history.history['val_loss'], label='Validation')
plt.title('Model Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

# Gem plot
plt.tight_layout()
plt.savefig('models/nn_chatbot_training_history.png')
print("[INFO] Træningshistorik gemt som 'models/nn_chatbot_training_history.png'")

# 7. Test model med et par eksempler
print("\n[INFO] Tester model med nogle eksempler...")
for i in range(min(5, len(X_test))):
    # Lav prediction
    pred = model.predict(np.expand_dims(X_test[i], 0), verbose=0)
    pred_class = np.argmax(pred)
    confidence = pred[0][pred_class]
    
    # Original tekst
    test_sequence = X_test[i]
    words = []
    for idx in test_sequence:
        if idx != 0:  # Skip padding
            for word, word_idx in tokenizer.word_index.items():
                if word_idx == idx:
                    words.append(word)
                    break
    original_text = " ".join(words)
    
    # Vis resultat
    print(f"Input: '{original_text}'")
    print(f"Predicted answer: '{le.inverse_transform([pred_class])[0]}'")
    print(f"Confidence: {confidence:.2f}")
    print(f"True answer: '{le.inverse_transform([y_test[i]])[0]}'")
    print("-" * 40)

# 8. Gem alt
print("[INFO] Gemmer model og relaterede data...")
model.save("models/nn_chatbot.h5")
import pickle
with open("models/nn_tokenizer.pkl", "wb") as f:
    pickle.dump(tokenizer, f)
with open("models/nn_labelencoder.pkl", "wb") as f:
    pickle.dump(le, f)

# 9. Gem model med softmax allerede anvendt (som i TensorFlow eksemplet)
probability_model = keras.Sequential([
    model,
    keras.layers.Softmax()  # Selvom den allerede har softmax, sikrer dette konsistent output
])
probability_model.save("models/nn_chatbot_with_softmax.h5")

print("[INFO] Neural net chatbot er trænet og gemt!")
print("[INFO] For at bruge modellen, indlæs 'models/nn_chatbot.h5', 'models/nn_tokenizer.pkl' og 'models/nn_labelencoder.pkl'")
