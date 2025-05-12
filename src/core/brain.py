"""
Jarvis Brain - Hovedkomponent der styrer al AI-logik i systemet.
"""
import logging
import asyncio
from typing import Optional, Dict, List, Any
try:
    import tensorflow as tf  # type: ignore
except ImportError:
    logging.warning("TensorFlow ikke tilgængelig - bruger fallback")
    tf = None
import numpy as np
from pathlib import Path
import json
import datetime

from nlu.model import NeuralNLU
from audio.speech import SpeechHandler

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JarvisBrain:
    """
    Hovedklasse der koordinerer alle AI-komponenter i Jarvis.
    Håndterer:
    - NLU (Natural Language Understanding)
    - Konteksthåndtering
    - LLM integration
    - Self-learning
    - Token/embedding visualisering
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Standard konfiguration
        self.config = {
            "model_path": "models",
            "training_data_path": "data/training",
            "confidence_threshold": 0.55,
            "max_context_length": 10,
            "auto_learn": True
        }
        
        if config:
            self.config.update(config)
        
        # Opret nødvendige mapper
        self.model_path = Path(self.config["model_path"])
        self.training_data_path = Path(self.config["training_data_path"])
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.training_data_path.mkdir(parents=True, exist_ok=True)
        
        # Initialiser komponenter
        self.nlu = NeuralNLU()
        self.speech = SpeechHandler()
        
        # Samtale kontekst
        self.context = []
        
        # Training metrics
        self.training_data = []
        self.training_metrics = {
            "total_examples": 0,
            "successful_predictions": 0,
            "last_training": None,
            "accuracy_history": []
        }
        
        # Indlæs eksisterende model hvis tilgængelig
        self._load_brain()
    
    async def process_input(self, text: str) -> Dict[str, Any]:
        """
        Behandl bruger input og generer respons.
        
        Args:
            text: Bruger input tekst
            
        Returns:
            Dict med respons og metadata
        """
        try:
            # NLU processing
            intent_class, confidence = self.nlu.predict(text)
            
            # Hvis confidence er over threshold
            if confidence >= self.config["confidence_threshold"]:
                # TODO: Implementer intent handling
                response = f"Jeg forstod din intention med {confidence:.2%} sikkerhed"
                
                # Gem succesfuld prediction
                self.training_metrics["successful_predictions"] += 1
                
            else:
                response = "Jeg er ikke sikker på hvad du mener. Kan du omformulere det?"
                
                # Gem til senere træning hvis auto_learn er aktiveret
                if self.config["auto_learn"]:
                    self.training_data.append({
                        "text": text,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "confidence": confidence
                    })
            
            # Opdater kontekst
            self._update_context(text, response)
            
            # Opdater metrics
            self.training_metrics["total_examples"] += 1
            
            # Hent embeddings til visualisering
            embeddings = self.nlu.get_embeddings(text)
            
            return {
                "response": response,
                "confidence": float(confidence),
                "intent_class": intent_class,
                "tokens": embeddings.tolist(),
                "context": self.context[-5:]  # Returner sidste 5 beskeder for kontekst
            }
            
        except Exception as e:
            logger.error(f"Fejl under behandling af input: {e}")
            return {
                "response": "Beklager, der skete en fejl under behandlingen af din besked",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def train(self) -> Dict[str, Any]:
        """
        Træn NLU model med nye data.
        
        Returns:
            Dict med trænings metrikker
        """
        try:
            # Indlæs træningsdata
            training_data = self._load_training_data()
            
            if not training_data:
                return {
                    "success": False,
                    "error": "Ingen træningsdata tilgængelig"
                }
            
            # Træn model
            metrics = self.nlu.train(
                texts=[d["text"] for d in training_data],
                labels=[d["label"] for d in training_data]
            )
            
            # Opdater metrics
            self.training_metrics["accuracy_history"].append(metrics["accuracy"])
            self.training_metrics["last_training"] = datetime.datetime.now().isoformat()
            
            # Gem model og metrics
            self._save_brain()
            
            return {
                "success": True,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Fejl under træning: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _update_context(self, user_input: str, response: str):
        """Opdater samtale kontekst."""
        self.context.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        self.context.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.now().isoformat()
        })
        
        # Behold kun de sidste N beskeder
        if len(self.context) > self.config["max_context_length"]:
            self.context = self.context[-self.config["max_context_length"]:]
    
    def _load_training_data(self) -> List[Dict]:
        """Indlæs træningsdata fra disk."""
        try:
            data_file = self.training_data_path / "training_data.json"
            if data_file.exists():
                with open(data_file, "r") as f:
                    return json.load(f)
            return []
            
        except Exception as e:
            logger.error(f"Fejl under indlæsning af træningsdata: {e}")
            return []
    
    def _save_brain(self):
        """Gem model, metrics og træningsdata."""
        try:
            # Gem NLU model
            self.nlu.save_model(str(self.model_path / "nlu"))
            
            # Gem metrics
            metrics_file = self.model_path / "metrics.json"
            with open(metrics_file, "w") as f:
                json.dump(self.training_metrics, f)
            
            # Gem træningsdata
            data_file = self.training_data_path / "training_data.json"
            with open(data_file, "w") as f:
                json.dump(self.training_data, f)
            
            logger.info("Brain gemt succesfuldt")
            
        except Exception as e:
            logger.error(f"Fejl under gem af brain: {e}")
    
    def _load_brain(self):
        """Indlæs gemt model og metrics."""
        try:
            # Indlæs NLU model
            self.nlu.load_model(str(self.model_path / "nlu"))
            
            # Indlæs metrics hvis de findes
            metrics_file = self.model_path / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file, "r") as f:
                    self.training_metrics = json.load(f)
            
            logger.info("Brain indlæst succesfuldt")
            
        except Exception as e:
            logger.error(f"Fejl under indlæsning af brain: {e}")
    
    def get_training_metrics(self) -> Dict[str, Any]:
        """Hent trænings metrikker."""
        return {
            "total_examples": self.training_metrics["total_examples"],
            "successful_predictions": self.training_metrics["successful_predictions"],
            "accuracy_history": self.training_metrics["accuracy_history"],
            "last_training": self.training_metrics["last_training"]
        }
    
    async def import_training_data(self, data: List[Dict]) -> bool:
        """
        Importer ekstern træningsdata.
        
        Args:
            data: Liste af træningseksempler
            
        Returns:
            bool: Success status
        """
        try:
            # Valider data format
            for example in data:
                if "text" not in example or "label" not in example:
                    raise ValueError("Ugyldigt data format")
            
            # Tilføj til eksisterende træningsdata
            self.training_data.extend(data)
            
            # Gem opdateret træningsdata
            self._save_brain()
            
            return True
            
        except Exception as e:
            logger.error(f"Fejl under import af træningsdata: {e}")
            return False 