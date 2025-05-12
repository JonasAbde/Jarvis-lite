"""
Neural NLU Model - TensorFlow-baseret NLU implementation.
"""
import tensorflow as tf
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import json
import datetime

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeuralNLU:
    """
    Neural Network baseret NLU model med TensorFlow.
    Bruger LSTM og attention mekanismer til intent klassificering.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Standard konfiguration
        self.config = {
            "vocab_size": 10000,
            "embedding_dim": 128,
            "lstm_units": 64,
            "dense_units": 64,
            "dropout_rate": 0.5,
            "learning_rate": 0.001,
            "batch_size": 32,
            "epochs": 100,
            "early_stopping_patience": 5
        }
        
        if config:
            self.config.update(config)
        
        # Initialiser model
        self.model = self._build_model()
        self.tokenizer = tf.keras.preprocessing.text.Tokenizer(
            num_words=self.config["vocab_size"]
        )
        
        # Training metrics
        self.history = []
        self.best_accuracy = 0.0
        
        # Model status
        self._is_ready = False
    
    def _build_model(self) -> tf.keras.Model:
        """Byg neural network modellen."""
        model = tf.keras.Sequential([
            # Embedding lag
            tf.keras.layers.Embedding(
                self.config["vocab_size"],
                self.config["embedding_dim"]
            ),
            
            # Bidirectional LSTM med attention
            tf.keras.layers.Bidirectional(
                tf.keras.layers.LSTM(
                    self.config["lstm_units"],
                    return_sequences=True
                )
            ),
            
            # Self-attention mekanisme
            tf.keras.layers.MultiHeadAttention(
                num_heads=4,
                key_dim=self.config["lstm_units"]
            ),
            tf.keras.layers.GlobalAveragePooling1D(),
            
            # Dense lag med dropout
            tf.keras.layers.Dense(
                self.config["dense_units"],
                activation="relu"
            ),
            tf.keras.layers.Dropout(self.config["dropout_rate"]),
            
            # Output lag
            tf.keras.layers.Dense(1, activation="sigmoid")
        ])
        
        # Kompiler model
        model.compile(
            optimizer=tf.keras.optimizers.Adam(
                learning_rate=self.config["learning_rate"]
            ),
            loss="binary_crossentropy",
            metrics=["accuracy"]
        )
        
        return model
    
    def train(self, texts: List[str], labels: List[int]) -> Dict:
        """
        Træn modellen med nye data.
        
        Args:
            texts: Liste af input tekster
            labels: Liste af labels (0 eller 1)
            
        Returns:
            Dict med trænings metrikker
        """
        # Fit tokenizer
        self.tokenizer.fit_on_texts(texts)
        
        # Konverter tekst til sekvenser
        sequences = self.tokenizer.texts_to_sequences(texts)
        
        # Pad sekvenser
        max_length = max(len(seq) for seq in sequences)
        padded_sequences = tf.keras.preprocessing.sequence.pad_sequences(
            sequences,
            maxlen=max_length,
            padding="post"
        )
        
        # Early stopping callback
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=self.config["early_stopping_patience"],
            restore_best_weights=True
        )
        
        # Træn model
        history = self.model.fit(
            padded_sequences,
            np.array(labels),
            batch_size=self.config["batch_size"],
            epochs=self.config["epochs"],
            validation_split=0.2,
            callbacks=[early_stopping]
        )
        
        # Opdater metrics
        self.history.extend(history.history["accuracy"])
        current_accuracy = max(history.history["val_accuracy"])
        if current_accuracy > self.best_accuracy:
            self.best_accuracy = current_accuracy
        
        self._is_ready = True
        
        return {
            "accuracy": self.best_accuracy,
            "history": self.history,
            "epochs_trained": len(history.history["accuracy"])
        }
    
    def predict(self, text: str) -> Tuple[int, float]:
        """
        Forudsig intent for en given tekst.
        
        Args:
            text: Input tekst
            
        Returns:
            Tuple af (predicted_class, confidence)
        """
        if not self._is_ready:
            raise RuntimeError("Model er ikke trænet endnu")
        
        # Konverter tekst til sekvens
        sequence = self.tokenizer.texts_to_sequences([text])
        padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(
            sequence,
            maxlen=self.config["vocab_size"],
            padding="post"
        )
        
        # Foretag forudsigelse
        prediction = self.model.predict(padded_sequence)[0][0]
        predicted_class = 1 if prediction > 0.5 else 0
        confidence = float(prediction if prediction > 0.5 else 1 - prediction)
        
        return predicted_class, confidence
    
    def save_model(self, path: str = "models/nlu") -> bool:
        """Gem model og tokenizer."""
        try:
            save_path = Path(path)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # Gem model
            self.model.save(str(save_path / "model"))
            
            # Gem tokenizer
            tokenizer_config = {
                "word_index": self.tokenizer.word_index,
                "word_counts": self.tokenizer.word_counts,
                "document_count": self.tokenizer.document_count,
                "index_docs": self.tokenizer.index_docs,
                "index_word": self.tokenizer.index_word
            }
            
            with open(save_path / "tokenizer.json", "w") as f:
                json.dump(tokenizer_config, f)
            
            return True
            
        except Exception as e:
            logger.error(f"Fejl under gem af model: {e}")
            return False
    
    def load_model(self, path: str = "models/nlu") -> bool:
        """Indlæs gemt model og tokenizer."""
        try:
            load_path = Path(path)
            
            # Indlæs model
            self.model = tf.keras.models.load_model(str(load_path / "model"))
            
            # Indlæs tokenizer
            with open(load_path / "tokenizer.json", "r") as f:
                tokenizer_config = json.load(f)
            
            self.tokenizer = tf.keras.preprocessing.text.Tokenizer()
            self.tokenizer.word_index = tokenizer_config["word_index"]
            self.tokenizer.word_counts = tokenizer_config["word_counts"]
            self.tokenizer.document_count = tokenizer_config["document_count"]
            self.tokenizer.index_docs = tokenizer_config["index_docs"]
            self.tokenizer.index_word = tokenizer_config["index_word"]
            
            self._is_ready = True
            return True
            
        except Exception as e:
            logger.error(f"Fejl under indlæsning af model: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Tjek om modellen er klar til brug."""
        return self._is_ready
    
    def get_embeddings(self, text: str) -> np.ndarray:
        """
        Hent embeddings for en given tekst.
        Bruges til visualisering.
        """
        if not self._is_ready:
            raise RuntimeError("Model er ikke trænet endnu")
        
        # Konverter tekst til sekvens
        sequence = self.tokenizer.texts_to_sequences([text])
        padded_sequence = tf.keras.preprocessing.sequence.pad_sequences(
            sequence,
            maxlen=self.config["vocab_size"],
            padding="post"
        )
        
        # Hent embedding lag
        embedding_layer = self.model.layers[0]
        embeddings = embedding_layer(padded_sequence)
        
        return embeddings.numpy() 