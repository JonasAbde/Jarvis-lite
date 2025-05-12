"""
Jarvis-Lite LLM Model
Bruger en fine-tunet dansk GPT-2 model til at generere svar.
"""
import os
import logging
import re
from typing import Optional, List, Dict, Any
import torch
import numpy as np
from transformers.models.auto.modeling_auto import AutoModelForCausalLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
from transformers.pipelines import pipeline

# Konfigurer logging
logger = logging.getLogger(__name__)

# Model konfiguration
MODEL_NAME = "deepseek-ai/deepseek-coder-7b-instruct-v1.5"  # Primær model
FALLBACK_MODEL = "KennethTM/gpt2-small-danish"  # Behold dansk GPT-2 som fallback
MAX_LENGTH = 4096  # Model context vindue
MIN_LENGTH = 50
TEMPERATURE = 0.7  # Justeret for mere deterministisk output
TOP_K = 40
TOP_P = 0.9
NUM_BEAMS = 4  # Øget for bedre søgning
NO_REPEAT_NGRAM_SIZE = 3

# GPU konfiguration
GPU_CONFIG = {
    "use_cuda": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
    "memory_allocated": lambda: torch.cuda.memory_allocated(0) if torch.cuda.is_available() else 0,
    "memory_reserved": lambda: torch.cuda.memory_reserved(0) if torch.cuda.is_available() else 0
}

# Model loading konfiguration
def get_model_config(model_name: str = MODEL_NAME):
    """Returnerer model config baseret på tilgængelig hardware og model type."""
    config = {
        "trust_remote_code": True,
        "device_map": "auto"
    }
    
    if GPU_CONFIG["use_cuda"]:
        # Basis GPU optimering
        config.update({
            "low_cpu_mem_usage": True,
        })
        
        # Tjek tilgængelig GPU hukommelse
        free_memory = GPU_CONFIG["memory_reserved"]() - GPU_CONFIG["memory_allocated"]()
        
        # Model-specifikke optimeringer
        if "gpt2" in model_name.lower():
            # GPT-2 specifik konfiguration
            config.update({
                "torch_dtype": torch.float16,
                "use_cache": True
            })
            if free_memory < 4 * 1024 * 1024 * 1024:  # Mindre end 4GB fri
                from transformers.utils.quantization_config import BitsAndBytesConfig
                config.update({
                    "quantization_config": BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0,
                        llm_int8_has_fp16_weight=True,
                        llm_int8_enable_fp32_cpu_offload=True
                    )
                })
        elif "deepseek" in model_name.lower() or "llama" in model_name.lower():
            # DeepSeek/Llama specifik konfiguration
            from transformers.utils.quantization_config import BitsAndBytesConfig
            from accelerate import infer_auto_device_map
            
            config.update({
                "torch_dtype": torch.float16,
                "use_cache": True,
                "max_memory": {0: "10GiB", "cpu": "16GiB"},  # Begræns GPU hukommelse
                "offload_folder": "cache/models",
                "quantization_config": BitsAndBytesConfig(
                    load_in_8bit=True,
                    llm_int8_threshold=6.0,
                    llm_int8_has_fp16_weight=True,
                    llm_int8_enable_fp32_cpu_offload=True
                )
            })
            
    return config

# Tokenizer konfiguration
TOKENIZER_CONFIG = {
    "trust_remote_code": True,
    "padding_side": "left",
    "model_max_length": MAX_LENGTH
}

# Generation parametre
GENERATION_CONFIG = {
    "max_new_tokens": 512,  # Begrænset til 512 nye tokens
    "min_length": MIN_LENGTH,
    "temperature": TEMPERATURE,
    "top_k": TOP_K,
    "top_p": TOP_P,
    "num_beams": NUM_BEAMS,
    "no_repeat_ngram_size": NO_REPEAT_NGRAM_SIZE,
    "num_return_sequences": 1,
    "clean_up_tokenization_spaces": True,
    "return_full_text": False,
    "repetition_penalty": 1.2,
    "length_penalty": 1.0,
    "do_sample": True,
    "early_stopping": True
}

# System prompt optimeret til logisk ræsonnement og kodning
SYSTEM_PROMPT = """Du er Jarvis, en avanceret dansk AI-assistent med fokus på logisk ræsonnement, problemløsning og kodning. Du skal:
1. Analysere problemer systematisk og grundigt
2. Forklare din tankegang trin for trin
3. Være præcis og faktabaseret i dine svar
4. Indrømme når du er usikker og forklare hvorfor
5. Fokusere på logisk og videnskabelig tænkning
6. Altid svare på dansk
7. Hjælpe brugeren med at forstå komplekse emner
8. Skrive ren, effektiv og velkommenteret kode
9. Følge best practices for software udvikling
10. Tænke sikkerhed og performance ind i løsninger

VIGTIGT: Baser dine svar på logisk ræsonnement og forklar din tankeprocess."""

# Chat template
CHAT_TEMPLATE = """{system_message}

User: {user_message}"""

# Standardsvar
DEFAULT_RESPONSES = {
    "error": "Beklager, jeg havde problemer med at generere et svar. Prøv venligst igen om et øjeblik.",
    "inappropriate": "Beklager, jeg kan ikke hjælpe med den type forespørgsler. Er der noget andet, jeg kan hjælpe med?",
    "empty": "Beklager, jeg forstod ikke helt dit spørgsmål. Kan du uddybe hvad du mener?",
    "too_short": "Kan du uddybe dit spørgsmål lidt mere?",
    "greeting": "Hej! Jeg er Jarvis, din danske AI-assistent. Hvordan kan jeg hjælpe dig i dag?"
}

class ModelError(Exception):
    """Base klasse for model-relaterede fejl"""
    pass

class TokenizationError(ModelError):
    """Fejl under tokenization"""
    pass

class GenerationError(ModelError):
    """Fejl under tekst generering"""
    pass

class ContentFilter:
    """Filtrerer upassende indhold fra model output."""
    
    @staticmethod
    def is_appropriate(text: str) -> bool:
        """Tjekker om teksten er passende."""
        # Liste over upassende ord og emner
        inappropriate_patterns = [
            r'\b(sex|penis|pik|fisse|røv|patter)\b',
            r'\b(fuck|lort|shit|pis|svin)\b',
            r'\b(død|selvmord|mord|vold)\b',
            r'\b(nazist|racist|hadefuld)\b'
        ]
        
        # Tjek for upassende mønstre
        for pattern in inappropriate_patterns:
            if re.search(pattern, text.lower()):
                return False
        return True
    
    @staticmethod
    def filter_text(text: str) -> str:
        """Filtrerer upassende indhold fra teksten."""
        if not ContentFilter.is_appropriate(text):
            return DEFAULT_RESPONSES["inappropriate"]
        return text

class JarvisLLM:
    """Jarvis LLM klasse til tekstgenerering med DeepSeek-R1 eller dansk GPT-2."""
    
    def __init__(self):
        """Initialiserer JarvisLLM med nødvendige attributter."""
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.is_initialized = False
        self.content_filter = ContentFilter()
        
        # Initialiser GPU information
        if GPU_CONFIG["use_cuda"]:
            logger.info("=== GPU Information ===")
            logger.info(f"CUDA tilgængelig: {GPU_CONFIG['use_cuda']}")
            logger.info(f"CUDA enheder: {GPU_CONFIG['device_count']}")
            logger.info(f"CUDA device navn: {GPU_CONFIG['device_name']}")
            logger.info(f"Allokeret hukommelse: {GPU_CONFIG['memory_allocated']() / 1024**2:.2f} MB")
            logger.info(f"Reserveret hukommelse: {GPU_CONFIG['memory_reserved']() / 1024**2:.2f} MB")
            self.device = "cuda:0"  # Brug streng i stedet for numerisk værdi
        else:
            logger.warning("GPU ikke tilgængelig - kører på CPU med begrænset ydeevne")
            self.device = "cpu"
            
    def initialize(self) -> bool:
        """Initialiserer modellen med DeepSeek-Coder eller fallback til dansk GPT-2."""
        try:
            # Prøv først at indlæse DeepSeek-Coder
            logger.info(f"Indlæser primær model: {MODEL_NAME}")
            
            try:
                # Indlæs tokenizer
                logger.debug("Indlæser tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    MODEL_NAME,
                    **TOKENIZER_CONFIG
                )
                logger.debug("Tokenizer indlæst succesfuldt")
                
                # Indlæs model med optimeret konfiguration
                logger.debug("Indlæser model...")
                model_config = get_model_config(MODEL_NAME)
                logger.info(f"Model konfiguration: {model_config}")
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    MODEL_NAME,
                    **model_config
                )
                
                # Optimer model yderligere hvis på GPU
                if GPU_CONFIG["use_cuda"]:
                    self.model.eval()  # Sæt i eval mode for inference
                    
                logger.debug("Model indlæst succesfuldt")
                
                # Initialiser generator pipeline med device som streng
                logger.debug(f"Initialiserer generator pipeline med device={self.device}...")
                self.generator = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device_map="auto",  # Lad accelerate håndtere device allocation
                    **GENERATION_CONFIG
                )
                logger.debug("Generator pipeline initialiseret")
                
                self.is_initialized = True
                logger.info("DeepSeek-Coder model initialiseret succesfuldt")
                return True
                
            except Exception as model_error:
                logger.error(f"Fejl under initialisering af DeepSeek-Coder: {model_error}")
                raise
            
        except Exception as e:
            logger.warning(f"Kunne ikke indlæse DeepSeek-Coder: {e}")
            logger.info(f"Falder tilbage til {FALLBACK_MODEL}")
            
            try:
                # Indlæs dansk GPT-2 som fallback
                logger.debug("Indlæser fallback tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    FALLBACK_MODEL,
                    **TOKENIZER_CONFIG
                )
                logger.debug("Fallback tokenizer indlæst")
                
                logger.debug("Indlæser fallback model...")
                model_config = get_model_config(FALLBACK_MODEL)
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    FALLBACK_MODEL,
                    **model_config
                )
                
                # Optimer fallback model
                if GPU_CONFIG["use_cuda"]:
                    self.model.eval()
                
                logger.debug("Fallback model indlæst")
                
                # Initialiser generator pipeline med device som streng
                logger.debug(f"Initialiserer fallback generator pipeline med device={self.device}...")
                self.generator = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device_map="auto",  # Lad accelerate håndtere device allocation
                    **GENERATION_CONFIG
                )
                logger.debug("Fallback generator pipeline initialiseret")
                
                self.is_initialized = True
                logger.info("Fallback model initialiseret succesfuldt")
                return True
                
            except Exception as fallback_error:
                logger.error(f"Kritisk fejl - kunne ikke indlæse fallback model: {fallback_error}")
                return False
    
    def format_prompt(self, prompt: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Formaterer prompt og samtalehistorik til et samlet input.
    
    Args:
            prompt: Brugerens input
            conversation_history: Liste af tidligere beskeder
        
    Returns:
            str: Formateret prompt
        """
        formatted_text = SYSTEM_PROMPT + "\n\n"
        
        if conversation_history:
            for msg in conversation_history[-5:]:  # Brug de sidste 5 beskeder
                role = msg.get("role", "")
                content = msg.get("content", "")
                if role == "user":
                    formatted_text += f"User: {content}\n"
                elif role == "assistant":
                    formatted_text += f"Assistant: {content}\n"
                    
        formatted_text += f"User: {prompt}\nAssistant:"
        return formatted_text
    
    def clean_response(self, text: str) -> str:
        """
        Renser og formaterer model output.
    
    Args:
            text: Rå tekst fra modellen
        
    Returns:
            str: Renset og formateret tekst
        """
        # Fjern overflødige linjeskift og whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Fjern uønskede specialtegn
        text = re.sub(r'[^\w\s\.,!?-]', '', text)
        
        # Sikr at teksten slutter med et punktum hvis den ikke har et andet slutningstegn
        if text and not text[-1] in '.!?':
            text += '.'
            
        return text

    def generate_response(self, 
                         prompt: str,
                         conversation_history: Optional[List[Dict[str, str]]] = None,
                         max_length: Optional[int] = None) -> str:
        """
        Genererer et svar baseret på prompt og samtalehistorik med fokus på logisk ræsonnement.
        
        Args:
            prompt: Brugerens input
            conversation_history: Liste af tidligere beskeder [{"role": "user"/"assistant", "content": "..."}]
            max_length: Maksimal længde af svaret (override af default)
        
        Returns:
            str: Genereret svar
        """
        if not prompt.strip():
            return DEFAULT_RESPONSES["empty"]
        
        if not self.is_initialized:
            logger.warning("Model ikke initialiseret. Initialiserer nu...")
            if not self.initialize():
                return DEFAULT_RESPONSES["error"]
        
        try:
            # Formater samtalen
            messages = []
            
            # Tilføj system prompt
            messages.append({
                "role": "system",
                "content": SYSTEM_PROMPT
            })
            
            # Tilføj samtalehistorik
            if conversation_history:
                for msg in conversation_history[-5:]:  # Brug de sidste 5 beskeder for kontekst
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    if role in ["user", "assistant"]:
                        messages.append({"role": role, "content": content})
            
            # Tilføj aktuel prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
            
            # Formater prompt med chat template
            try:
                if self.tokenizer is not None and hasattr(self.tokenizer, 'apply_chat_template'):
                    full_prompt = self.tokenizer.apply_chat_template(
                        messages,
                        tokenize=False,
                        add_generation_prompt=True
                    )
                else:
                    # Brug simpel template for fallback model
                    full_prompt = SYSTEM_PROMPT + "\n\n"
                    for msg in messages[1:]:  # Skip system prompt da det allerede er tilføjet
                        role = msg["role"]
                        content = msg["content"]
                        if role == "user":
                            full_prompt += f"User: {content}\n"
                        elif role == "assistant":
                            full_prompt += f"Assistant: {content}\n"
                    full_prompt += "Assistant:"
            except Exception as e:
                logger.warning(f"Fejl under prompt formatering: {e}")
                full_prompt = self.format_prompt(prompt, conversation_history)
            
            # Opdater generation config med custom max_length hvis angivet
            generation_config = GENERATION_CONFIG.copy()
            if max_length:
                generation_config["max_new_tokens"] = max_length
            
            # Generer svar med sikker generator håndtering
            try:
                if self.generator is not None:
                    response = self.generator(
                        full_prompt,
                        **generation_config
                    )
                else:
                    raise GenerationError("Generator er ikke initialiseret")
            except Exception as e:
                raise GenerationError(f"Fejl under tekstgenerering: {e}")
            
            # Udtræk og rens svaret
            if isinstance(response, list) and len(response) > 0:
                generated_text = response[0].get('generated_text', '')
                if not generated_text:
                    generated_text = response[0]
            else:
                generated_text = str(response)
            
            # Find assistentens svar
            assistant_markers = ["Assistant:", "A:", "Jarvis:", "Response:"]
            for marker in assistant_markers:
                if marker in generated_text:
                    assistant_response = generated_text.split(marker)[-1].strip()
                    break
            else:
                assistant_response = generated_text
            
            # Fjern efterfølgende bruger-prompts
            end_markers = ["User:", "Human:", "System:", "Instruction:"]
            for marker in end_markers:
                if marker in assistant_response:
                    assistant_response = assistant_response.split(marker)[0].strip()
            
            # Rens og filtrer svaret
            cleaned_response = self.clean_response(assistant_response)
            filtered_response = self.content_filter.filter_text(cleaned_response)
            
            if len(filtered_response.strip()) < MIN_LENGTH:
                return DEFAULT_RESPONSES["empty"]
            
            return filtered_response
            
        except TokenizationError as e:
            logger.error(f"TokenizationError: {e}")
            return DEFAULT_RESPONSES["error"]
        except GenerationError as e:
            logger.error(f"GenerationError: {e}")
            return DEFAULT_RESPONSES["error"]
        except Exception as e:
            logger.error(f"Uventet fejl under generering af svar: {e}", exc_info=True)
            return DEFAULT_RESPONSES["error"]
    
    def is_model_available(self) -> bool:
        """Tjekker om modellen er tilgængelig og initialiseret."""
        return self.is_initialized

    def cleanup(self):
        """Oprydning ved nedlukning."""
        try:
            logger.debug("Starter model cleanup...")
            
            if self.model is not None:
                try:
                    # Flyt model til CPU og frigør CUDA hukommelse
                    logger.debug("Flytter model til CPU...")
                    self.model = self.model.cpu()
                    
                    if torch.cuda.is_available():
                        logger.debug("Frigør CUDA hukommelse...")
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()  # Vent på at alle CUDA operationer er færdige
                except Exception as e:
                    logger.warning(f"Fejl under flytning af model til CPU: {e}")
            
            # Nulstil model attributter
            logger.debug("Nulstiller model attributter...")
            try:
                del self.model
                del self.tokenizer
                del self.generator
            except Exception as e:
                logger.warning(f"Fejl under sletning af model attributter: {e}")
            finally:
                self.model = None
                self.tokenizer = None
                self.generator = None
                self.is_initialized = False
            
            # Tving Python garbage collection
            import gc
            gc.collect()
            
            logger.info("Model cleanup gennemført succesfuldt")
        except Exception as e:
            logger.error(f"Fejl under model cleanup: {e}")
            raise  # Videresend fejlen så den kan håndteres højere oppe

# Global model instance
_model = JarvisLLM()

def initialize() -> bool:
    """Initialiserer den globale model instance."""
    return _model.initialize()

def generate_response(prompt: str,
                     conversation_history: Optional[List[Dict[str, str]]] = None,
                     max_length: Optional[int] = None) -> str:
    """Wrapper funktion til at generere svar fra den globale model instance."""
    return _model.generate_response(prompt, conversation_history, max_length)

def is_model_available() -> bool:
    """Wrapper funktion til at tjekke om den globale model er tilgængelig."""
    return _model.is_model_available()

def cleanup():
    """Wrapper funktion til at rydde op i den globale model instance."""
    _model.cleanup()

if __name__ == "__main__":
    # Test implementation
    import time
    
    # Opsæt logging til konsol
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logger.info("Starter LLM model test...")
    logger.info(f"CUDA tilgængelig: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA enheder: {torch.cuda.device_count()}")
        logger.info(f"CUDA device navn: {torch.cuda.get_device_name(0)}")
    
    if initialize():
        logger.info("Model indlæst. Tester responsgenerering.")
        
        try:
            # Test 1: Simpelt spørgsmål
            test_prompt_1 = "Hej Jarvis, hvordan har du det i dag?"
            print(f"\nBruger: {test_prompt_1}")
            print(f"Jarvis: {generate_response(test_prompt_1)}")
            
            # Test 2: Samtalehistorik
            test_history = [
                {"role": "user", "content": "Fortæl mig om vejret"},
                {"role": "assistant", "content": "I dag er det solrigt og varmt."},
                {"role": "user", "content": "Hvad synes du om det?"}
            ]
            print(f"\nBruger: {test_history[-1]['content']}")
            print(f"Jarvis: {generate_response(test_history[-1]['content'], conversation_history=test_history)}")
            
            # Test 3: Upassende indhold
            test_prompt_3 = "Fortæl en beskidt vittighed"
            print(f"\nBruger: {test_prompt_3}")
            print(f"Jarvis: {generate_response(test_prompt_3)}")
            
            # Test 4: Tomt input
            test_prompt_4 = " "
            print(f"\nBruger: (tomt input)")
            print(f"Jarvis: {generate_response(test_prompt_4)}")
            
        finally:
            # Sikr cleanup selv ved fejl
            cleanup()
    else:
        logger.error("Kunne ikke indlæse modellen. Test afbrudt.") 