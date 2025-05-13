from typing import Dict, Any, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import psutil
import logging
from src.core.conversation_manager import ConversationManager
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(
        self,
        model_name: str = "facebook/opt-350m",
        cache_dir: str = "models/cache",
        quantization_config: Optional[Dict] = None
    ):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir)
        self.quantization_config = quantization_config or {
            "load_in_4bit": False,
            "bnb_4bit_compute_dtype": "float16",
            "bnb_4bit_quant_type": "nf4",
            "bnb_4bit_use_double_quant": False
        }
        self.model = None
        self.tokenizer = None
        self.is_initialized = False
        self.system_load = 0
        self.conversation_manager = ConversationManager()
        
    async def initialize(self):
        """Initialiser LLM modellen"""
        try:
            logger.info(f"Initialiserer LLM model: {self.model_name}")
            
            # Opret cache directory
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Indlæs tokenizer og model
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                padding_side="left",
                truncation_side="left"
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=str(self.cache_dir),
                device_map="auto",
                torch_dtype=torch.float16
            )
            
            self.is_initialized = True
            logger.info("LLM model initialiseret succesfuldt")
            
        except Exception as e:
            logger.error(f"Fejl ved initialisering af LLM: {e}")
            self.is_initialized = False
            raise
    
    def update_system_load(self):
        """Opdater system load"""
        self.system_load = psutil.cpu_percent()
        
    async def generate_response(
        self,
        text: str,
        max_length: int = 200,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.2
    ) -> Dict[str, Any]:
        """Generer et svar ved hjælp af LLM med samtalehukommelse"""
        if not self.is_initialized:
            return {
                "response": "Systemet er ved at starte op. Prøv igen om et øjeblik.",
                "confidence": 0.0
            }
            
        try:
            self.update_system_load()
            
            # Tilføj brugerens besked til samtalehistorikken
            self.conversation_manager.add_message("user", text)
            
            # Generer prompt med kontekst
            prompt = self.conversation_manager.generate_prompt(text)
            
            # Få personlig svarstil
            style = self.conversation_manager.get_personalized_response_style()
            
            # Juster parametre baseret på stil
            if style["response_length"] == "short":
                max_length = 50
            elif style["response_length"] == "long":
                max_length = 300
                
            if style["technical_level"] == "high":
                temperature = 0.6  # Mere præcise svar
            elif style["technical_level"] == "low":
                temperature = 0.8  # Mere kreative svar
            
            # Tokenizer input
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
            
            # Generer svar
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=len(prompt.split()) + max_length,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Dekod svar og fjern prompt
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = response.replace(prompt, "").strip()
            
            # Rens svaret
            response = response.split("Bruger:")[0].split("Human:")[0].strip()
            
            # Tilføj emojis hvis det er passende
            if style["include_emojis"]:
                response += " 😊"
            
            # Gem assistentens svar i historikken
            self.conversation_manager.add_message("assistant", response)
            
            return {
                "response": response,
                "confidence": 0.85,
                "model_name": self.model_name,
                "system_load": self.system_load,
                "conversation_style": style
            }
            
        except Exception as e:
            logger.error(f"Fejl ved generering af LLM svar: {e}")
            return {
                "response": "Beklager, jeg havde problemer med at generere et svar. Prøv igen.",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Hent status for LLM systemet"""
        self.update_system_load()
        return {
            "is_initialized": self.is_initialized,
            "model_name": self.model_name,
            "system_load": self.system_load,
            "conversation_active": len(self.conversation_manager.current_conversation) > 0,
            "cache_dir": str(self.cache_dir),
            "device": str(self.model.device) if self.model else "ikke initialiseret"
        }
        
    def save_conversation(self):
        """Gem den nuværende samtale"""
        self.conversation_manager.save_conversation()
        
    def clear_conversation(self):
        """Ryd den nuværende samtale"""
        self.conversation_manager.clear_current_conversation() 