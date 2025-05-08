"""
LLM-model integration for Jarvis Lite.
Giver mulighed for at generere menneskelige danske svar.
"""

import os
import torch
import logging
import random
from typing import Tuple, List, Dict, Any, Optional

# Logger
logger = logging.getLogger(__name__)

# Konfiguration
MODEL_NAME = "chcaa/gpt2-medium-danish"  # Dansk GPT-2 medium model
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "models")

# Globale variable til at cache modellen
_model = None
_tokenizer = None

# Prompting-skabeloner for mere menneskeligt output
SYSTEM_PROMPT = """Du er Jarvis, en hjælpsom dansk AI-assistent. Du svarer høfligt, præcist og i en venlig tone.
Dine svar er korte, klare og direkte. Når du bliver spurgt om noget, du ikke ved, siger du ærligt, at du ikke ved det.
Hvis du bliver spurgt om at udføre handlinger, der kræver at tilgå internet, siger du, at du ikke kan tilgå internettet lige nu.
"""

# Naturlige danske vendinger til fallback-svar
DANISH_FALLBACKS = [
    "Det kan jeg desværre ikke svare på lige nu. Kan jeg hjælpe med noget andet?",
    "Det er et godt spørgsmål, men jeg har ikke nok information til at svare præcist.",
    "Beklager, jeg er ikke sikker på det. Vil du have, at jeg prøver at svare på noget andet?",
    "Hmm, det er jeg ikke helt med på. Kan du omformulere eller spørge om noget andet?",
    "Det har jeg faktisk ikke et godt svar på lige nu. Er der noget andet, jeg kan hjælpe med?",
    "Interessant spørgsmål! Det vil kræve mere information, end jeg har lige nu.",
    "Det er lidt uden for mit ekspertiseområde, men jeg vil gerne hjælpe med noget andet.",
]

# Menneskelige danske vendinger til at gøre svar mere naturlige
HUMAN_DANISH_PHRASES = [
    "Altså, ", "Hmm, ", "Lad mig se... ", "Godt spørgsmål! ", "Jamen, ", "Tja, ", "Så vidt jeg ved, ",
    "Jeg tror, at ", "Det er et godt spørgsmål. ", "For at være ærlig, ", "Faktisk er det sådan, at ",
]

def load_model() -> Tuple[Any, Any]:
    """
    Indlæser LLM-modellen og tokenizeren
    
    Returns:
        Tuple af (model, tokenizer)
    """
    global _model, _tokenizer
    
    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer
    
    try:
        logger.info(f"Indlæser model: {MODEL_NAME}")
        
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        # Definer device
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Bruger device: {device}")
        
        # Indlæs tokenizer og model
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, cache_dir=CACHE_DIR).to(device)
        
        return _model, _tokenizer
        
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af model: {e}")
        return None, None

def make_response_more_human(response: str) -> str:
    """
    Gør et svar mere menneskeligt ved at tilføje danske vendinger og forbedre sproget
    
    Args:
        response: Original svar
        
    Returns:
        Forbedret, mere menneskeligt svar
    """
    # Hvis svaret er meget kort, tilføj en lille vending
    if len(response.split()) < 5 and random.random() < 0.7:
        response = random.choice(HUMAN_DANISH_PHRASES) + response.lower()
    
    # Sikr at svaret starter med stort bogstav
    if response and response[0].islower():
        response = response[0].upper() + response[1:]
    
    # Sikr at svaret slutter med et punktum, medmindre det er et spørgsmål
    if response and not response.endswith(('.', '!', '?')):
        response += '.'
        
    return response

def generate_response(user_input: str, conversation_history: List[Dict[str, str]]) -> str:
    """
    Genererer et svar baseret på brugerens input og samtalehistorik
    
    Args:
        user_input: Brugerens input
        conversation_history: Liste af tidligere samtaler i formatet [{"user": "...", "assistant": "..."}, ...]
        
    Returns:
        Genereret svar
    """
    try:
        model, tokenizer = load_model()
        
        if model is None or tokenizer is None:
            # Brug mere menneskelige og varierede fallback-svar
            return random.choice(DANISH_FALLBACKS)
        
        # Opbyg prompt med kontekst og system-prompt for bedre output
        prompt = SYSTEM_PROMPT + "\n\n"
        
        # Tilføj tidligere samtaler for kontekst (max 3)
        for entry in conversation_history[-3:]:  # Brug kun de seneste 3 samtaler
            prompt += f"Bruger: {entry['user']}\nJarvis: {entry['assistant']}\n"
        
        # Tilføj aktuel forespørgsel
        prompt += f"Bruger: {user_input}\nJarvis:"
        
        # Klargør input til modellen
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        # Generer svar med højere tilfældighed for mere menneskelighed
        with torch.no_grad():
            output = model.generate(
                inputs["input_ids"],
                max_new_tokens=100,
                do_sample=True,
                temperature=0.85,  # Højere temperatur for mere variation
                top_p=0.92,
                top_k=50,
                repetition_penalty=1.2,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Dekodér output
        full_output = tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Udtræk kun det genererede svar (efter "Jarvis:")
        response_start = full_output.rfind("Jarvis:") + len("Jarvis:")
        response = full_output[response_start:].strip()
        
        # Find hvor bruger-input starter igen, hvis det findes
        if "Bruger:" in response:
            response = response.split("Bruger:")[0].strip()
            
        # Gør svaret mere menneskeligt
        response = make_response_more_human(response)
        
        return response
        
    except Exception as e:
        logger.error(f"Fejl ved generering af svar: {e}")
        # Brug et mere menneskeligt og varieret fallback-svar
        return random.choice(DANISH_FALLBACKS)

def is_model_available() -> bool:
    """
    Tjekker om modellen er tilgængelig
    
    Returns:
        True hvis modellen kan indlæses, ellers False
    """
    model, tokenizer = load_model()
    return model is not None and tokenizer is not None 