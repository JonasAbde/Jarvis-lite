"""
NLU-modul til Jarvis
Håndterer Natural Language Understanding og intent-klassificering
"""
import asyncio
import logging
import json
import os
import random
from typing import Any, Dict, List, Optional

# Denne import metode forhindrer cirkulære imports
import sys
# Tilføj projekt root til sys.path hvis den ikke allerede er der
project_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
# Direkte import af kun basisklassen fra hovedprogrammet
from jarvis_main import JarvisModule

# Fjernet torch afhængighed helt - bruger simpel regel-baseret NLU i stedet
logger = logging.getLogger(__name__)

class NLUModule(JarvisModule):
    """NLU-modul til Jarvis - håndterer forståelse af naturligt sprog"""
    
    # Metadata
    name = "nlu"
    description = "NLU-modul til Jarvis - håndterer intent-klassificering"
    version = "1.0.0"
    dependencies = []  # Fjernet torch-afhængighed
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.intents = []
        self.training_data = []
        self.new_examples_count = 0
        
    async def initialize(self) -> bool:
        """Initialiserer NLU-modulet"""
        logger.info("Initialiserer NLU-modul")
        
        try:
            # Her ville vi normalt lade en NLU-model
            await asyncio.sleep(0.5)  # Simulerer loading af model
            
            # Mock intents for demonstration
            self.intents = [
                "greeting", "weather", "time", "date", 
                "play_music", "stop_music", "set_reminder",
                "general_question", "unknown"
            ]
            
            # Load træningsdata hvis det findes
            await self._load_training_data()
            
            # Informer om status
            logger.info("NLU-modulet kører med simpel regelbaseret model - ingen ML-funktionalitet")
            
            self.active = True
            logger.info("NLU-modul initialiseret")
            return True
        except Exception as e:
            logger.error(f"Fejl ved initialisering af NLU-modul: {e}")
            return False
    
    async def shutdown(self) -> bool:
        """Lukker NLU-modulet"""
        logger.info("Lukker NLU-modul")
        
        try:
            # Gem træningsdata
            await self._save_training_data()
            
            # Frigør resourcer
            self.model = None
            
            self.active = False
            return True
        except Exception as e:
            logger.error(f"Fejl ved nedlukning af NLU-modul: {e}")
            return False
    
    async def _load_training_data(self):
        """Indlæser træningsdata fra disk"""
        training_file = "data/nlu_training.json"
        if os.path.exists(training_file):
            try:
                with open(training_file, 'r', encoding='utf-8') as f:
                    self.training_data = json.load(f)
                logger.info(f"Indlæste {len(self.training_data)} træningseksempler")
            except Exception as e:
                logger.error(f"Kunne ikke indlæse træningsdata: {e}")
                self.training_data = []
        else:
            logger.info("Ingen træningsdata fundet")
            self.training_data = []
    
    async def _save_training_data(self):
        """Gemmer træningsdata til disk"""
        training_dir = os.path.dirname("data/nlu_training.json")
        os.makedirs(training_dir, exist_ok=True)
        
        try:
            with open("data/nlu_training.json", 'w', encoding='utf-8') as f:
                json.dump(self.training_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Gemte {len(self.training_data)} træningseksempler")
        except Exception as e:
            logger.error(f"Kunne ikke gemme træningsdata: {e}")
    
    async def predict_intent(self, text: str) -> Dict[str, Any]:
        """Forudsiger intent ud fra tekst"""
        if not self.active:
            logger.warning("NLU-modul er ikke aktivt")
            return {"intent": "unknown", "confidence": 0.0}
            
        # Dette er en simpel regelbaseret implementering
        text = text.lower()
        logger.info(f"Analyserer tekst: {text}")
        
        if "hej" in text or "goddag" in text or "hallo" in text or "dav" in text:
            return {"intent": "greeting", "confidence": 0.92}
        elif "vejr" in text or "regn" in text or "sol" in text or "temperatur" in text:
            return {"intent": "weather", "confidence": 0.85}
        elif "tid" in text and not "dato" in text:
            return {"intent": "time", "confidence": 0.8}
        elif "dato" in text or "dag" in text or "måned" in text:
            return {"intent": "date", "confidence": 0.82}
        elif "musik" in text and ("afspil" in text or "start" in text or "spil" in text):
            return {"intent": "play_music", "confidence": 0.78}
        elif "stop" in text and "musik" in text:
            return {"intent": "stop_music", "confidence": 0.9}
        elif "påmindelse" in text or "reminder" in text or "husk" in text:
            return {"intent": "set_reminder", "confidence": 0.75}
        else:
            # Random confidence for demonstration
            confidence = random.uniform(0.3, 0.6)
            intent = "general_question" if len(text.split()) > 3 else "unknown"
            logger.info(f"Tekst matchede ingen regler - faldt tilbage til {intent} med confidence {confidence:.2f}")
            return {"intent": intent, "confidence": confidence}
    
    async def add_training_example(self, text: str, intent: str):
        """Tilføjer et træningseksempel"""
        if intent not in self.intents:
            logger.warning(f"Intent '{intent}' findes ikke i de kendte intents")
            return False
            
        # Tilføj til træningsdata
        self.training_data.append({
            "text": text,
            "intent": intent
        })
        self.new_examples_count += 1
        
        logger.info(f"Tilføjede træningseksempel: '{text}' med intent '{intent}'")
        
        # Overvej gentræning hvis vi har nok nye eksempler
        if self.new_examples_count >= 5:
            await self.retrain_model()
        
        return True
    
    async def retrain_model(self):
        """Gentræner modellen med alle træningsdata"""
        logger.info("Gentræner NLU model...")
        
        # Simpel implementering, ingen reel træning uden torch
        logger.info("Bruger simpel regelbaseret model - ingen reel træning udføres")
        await asyncio.sleep(1)  # Simulerer træning
        
        self.new_examples_count = 0
        logger.info("NLU model opdateret")
        
        return True
    
    def get_available_intents(self):
        """Returnerer tilgængelige intents"""
        return self.intents
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """Returnerer liste af API endpoints for dette modul"""
        return [
            {
                "path": "/api/nlu/predict",
                "method": "POST",
                "handler": self.handle_predict_endpoint
            },
            {
                "path": "/api/nlu/train",
                "method": "POST",
                "handler": self.handle_train_endpoint
            },
            {
                "path": "/api/nlu/intents",
                "method": "GET",
                "handler": self.handle_intents_endpoint
            }
        ]
    
    def get_ui_components(self) -> List[Dict[str, Any]]:
        """Returnerer liste af UI komponenter for dette modul"""
        return [
            {
                "type": "panel",
                "id": "intent-panel",
                "label": "Intent Oversigt",
                "location": "training"
            },
            {
                "type": "table",
                "id": "training-data-table",
                "label": "Træningsdata",
                "location": "training"
            }
        ]
    
    async def handle_predict_endpoint(self, request):
        """API endpoint handler for intent prediction"""
        body = await request.json()
        text = body.get("text", "")
        prediction = await self.predict_intent(text)
        return prediction
    
    async def handle_train_endpoint(self, request):
        """API endpoint handler for tilføjelse af træningsdata"""
        body = await request.json()
        text = body.get("text", "")
        intent = body.get("intent", "")
        
        if not text or not intent:
            return {"success": False, "error": "Manglende tekst eller intent"}
            
        success = await self.add_training_example(text, intent)
        return {"success": success}
    
    async def handle_intents_endpoint(self, request):
        """API endpoint handler for at hente tilgængelige intents"""
        return {"intents": self.get_available_intents()} 