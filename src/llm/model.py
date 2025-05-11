"""
LLM-model integration for Jarvis Lite using Microsoft's Phi-2 model.
"""

import os
import torch
import logging
from transformers.models.auto.modeling_auto import AutoModelForCausalLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from typing import List, Dict, Optional

# Konfigurer logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguration
MODEL_NAME = "microsoft/phi-2"  # Brug original model
MAX_HISTORY_TOKENS = 2048
DEFAULT_MAX_TOKENS = 256
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 50
DEFAULT_TOP_P = 0.9
DEFAULT_REPETITION_PENALTY = 1.1

# System prompt
SYSTEM_PROMPT = """Du er en dansk AI-assistent. Du SKAL:
1. Svare på DANSK i alle tilfælde
2. Være præcis og kortfattet
3. Bruge et naturligt dansk sprog
4. Undgå engelske ord medmindre det er nødvendigt
5. Hvis du er i tvivl, så indrøm det ærligt

VIGTIGT: Du må KUN svare på dansk!"""

# Globale model og tokenizer variabler
_model: Optional[AutoModelForCausalLM] = None
_tokenizer: Optional[AutoTokenizer] = None

def is_model_available() -> bool:
    """Tjekker om modellen er indlæst."""
    return _model is not None and _tokenizer is not None

def load_model() -> bool:
    """Indlæser LLM modellen."""
    global _model, _tokenizer
    
    try:
        logger.info(f"Indlæser model '{MODEL_NAME}'...")
        
        # Indlæs tokenizer
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _tokenizer.pad_token = _tokenizer.eos_token
        
        # Indlæs model
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        _model.config.pad_token_id = _tokenizer.pad_token_id
        
        logger.info("Model indlæst og klar.")
        return True
        
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af model: {str(e)}")
        _model = None
        _tokenizer = None
        return False

def format_prompt(messages: List[Dict[str, str]]) -> str:
    """Formaterer beskeder til en prompt."""
    prompt = f"System: {SYSTEM_PROMPT}\n\n"
    
    for msg in messages:
        if msg["role"] == "system":
            prompt += f"System: {msg['content']}\n"
        elif msg["role"] == "user":
            prompt += f"Human: {msg['content']}\n"
        elif msg["role"] == "assistant":
            prompt += f"Assistant: {msg['content']}\n"
    
    prompt += "Assistant: "
    return prompt

def generate_response(
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: float = DEFAULT_TEMPERATURE,
    top_k: int = DEFAULT_TOP_K,
    top_p: float = DEFAULT_TOP_P,
    repetition_penalty: float = DEFAULT_REPETITION_PENALTY
) -> str:
    """Genererer et svar baseret på beskedhistorikken."""
    if not is_model_available():
        if not load_model():
            return "Beklager, jeg kunne ikke indlæse sprogmodellen."
    
    try:
        # Forbered prompt
        prompt = format_prompt(messages)
        
        # Tokenize input
        inputs = _tokenizer(
            prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=MAX_HISTORY_TOKENS
        )
        
        # Generer svar
        outputs = _model.generate(
            **inputs,
            max_new_tokens=max_tokens or DEFAULT_MAX_TOKENS,
            do_sample=True,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
            pad_token_id=_tokenizer.pad_token_id
        )
        
        # Decode og returner svar
        response = _tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        return response
        
    except Exception as e:
        logger.error(f"Fejl ved generering af svar: {str(e)}")
        return "Beklager, der opstod en fejl ved generering af svaret."

if __name__ == '__main__':
    # Simpel test sekvens
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s')
    
    logger.info("Starter LLM model test...")
    if load_model():
        logger.info("Model indlæst. Tester responsgenerering.")
        
        test_history_1 = [{"role": "user", "content": "Hej Jarvis, hvordan har du det i dag?"}]
        response1 = generate_response(test_history_1)
        print(f"\nBruger: {test_history_1[-1]['content']}")
        print(f"Jarvis: {response1}")

        test_history_2 = [
            {"role": "user", "content": "Hvad er hovedstaden i Danmark?"},
            {"role": "assistant", "content": "Hovedstaden i Danmark er København."},
            {"role": "user", "content": "Kan du fortælle mig lidt mere om den?"}
        ]
        response2 = generate_response(test_history_2, max_tokens=80) # Lidt længere svar
        print(f"\nBruger: {test_history_2[-1]['content']}")
        print(f"Jarvis: {response2}")
        
        test_history_3 = [
            {"role": "user", "content": "Skriv et kort digt om en kat."}
        ]
        response3 = generate_response(test_history_3, temperature=0.9, max_tokens=60)
        print(f"\nBruger: {test_history_3[-1]['content']}")
        print(f"Jarvis: {response3}")

        # Test med tomt input (bør håndteres)
        test_history_empty = [{"role": "user", "content": " "}]
        response_empty = generate_response(test_history_empty)
        print(f"\nBruger: (tomt input)")
        print(f"Jarvis: {response_empty}")

    else:
        logger.error("Kunne ikke indlæse modellen. Test afbrudt.") 