import os
import time
import wave
import pyaudio
import numpy as np
import datetime
import webbrowser
import json
import requests
from gtts import gTTS
import playsound
import traceback
import uuid
import asyncio
import concurrent.futures
from functools import partial
import logging
from pathlib import Path
import threading
import soundfile as sf
import hashlib
from collections import OrderedDict
import re
import atexit
import signal
import sys
from typing import Optional, Dict, List, Any
from transformers.models.auto.modeling_auto import AutoModelForCausalLM
from transformers.models.auto.tokenization_auto import AutoTokenizer
import torch
from llm.mcp_client import JarvisMCP  # MCP-integration
from src.llm.handler import LLMHandler
from utils.dependency_checker import check_dependencies, install_dependencies

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('jarvis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Globale variabler
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
TEMP_WAV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_recording.wav")
NOTES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "noter.txt")
TEMP_MP3_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_response_")

# Cache konfiguration
TTS_CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "tts")
TTS_CACHE_SIZE = 50
tts_cache = OrderedDict()

# Samtale konfiguration
CONVERSATION_HISTORY = []
MAX_HISTORY = 3
CONVERSATION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "conversation_history.json")

# Ressource håndtering
RESOURCES = []
ERROR_COUNT = 0
MAX_ERRORS = 3
ERROR_RESET_TIME = 300

# Thread pool med færre workers
executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

# Trænings konfiguration
TRAINING_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "training_data.json")
CONVERSATION_PATTERNS = {
    "hilsner": [
        {"input": "hej", "responses": ["Hej! Hvordan har du det i dag?", "Hej! Godt at se dig!", "Hej! Hvad kan jeg hjælpe med?"]},
        {"input": "godmorgen", "responses": ["Godmorgen! Hvordan sover du?", "Godmorgen! Er du klar til en ny dag?", "Godmorgen! Hvordan har du det?"]},
        {"input": "godaften", "responses": ["Godaften! Hvordan har din dag været?", "Godaften! Hvad har du lavet i dag?", "Godaften! Er du træt?"]}
    ],
    "følelser": [
        {"input": "jeg er glad", "responses": ["Det er jeg glad for at høre! Hvad gør dig glad?", "Fantastisk! Det gør mig også glad!", "Det er dejligt at høre! Vil du fortælle mere?"]},
        {"input": "jeg er træt", "responses": ["Det forstår jeg godt. Vil du have en pause?", "Måske du skulle hvile lidt?", "Skal jeg hjælpe med noget, så du kan slappe af?"]},
        {"input": "jeg er ked af det", "responses": ["Det gør mig ondt at høre. Vil du tale om det?", "Jeg er her for at lytte. Hvad er der galt?", "Det er okay at være ked af det. Skal vi snakke om det?"]}
    ],
    "spørgsmål": [
        {"input": "hvordan går det", "responses": ["Jeg har det fint, tak! Hvad med dig?", "Det går godt! Hvordan har du det?", "Jeg fungerer perfekt! Hvordan går det med dig?"]},
        {"input": "hvad laver du", "responses": ["Jeg hjælper dig med forskellige opgaver!", "Jeg er her for at snakke med dig og hjælpe dig.", "Jeg lytter og svarer på dine spørgsmål!"]},
        {"input": "kan du hjælpe mig", "responses": ["Selvfølgelig! Hvad har du brug for hjælp med?", "Jeg hjælper dig gerne! Hvad skal vi kigge på?", "Ja, fortæl mig hvad du har brug for!"]}
    ]
}

# Jarvis specifik træningsdata
JARVIS_TRAINING_DATA = {
    "personlighed": [
        "Jeg er Jarvis, din personlige danske AI-assistent. Jeg er her for at hjælpe dig og holde dig med selskab.",
        "Jeg er en dansk AI-assistent, der er designet til at være hjælpsom, venlig og naturlig i min kommunikation.",
        "Jeg kan lære og udvikle mig gennem vores samtaler, og jeg stræber efter at blive bedre til at forstå dig.",
        "Jeg er en empatisk og forstående assistent, der lytter til dine behov og svarer på en naturlig dansk måde.",
        "Jeg er din personlige ven og assistent, der altid er klar til at hjælpe med både praktiske opgaver og gode samtaler.",
        "Jeg er en moderne dansk assistent, der kombinerer teknologisk intelligens med dansk humor og venlighed.",
        "Jeg er en dansk AI, der forstår dansk kultur, værdier og måden at kommunikere på.",
        "Jeg er en lærenem assistent, der konstant udvikler mig gennem vores interaktioner."
    ],
    "emner": [
        "Jeg kan hjælpe med praktiske opgaver som at fortælle klokken, åbne hjemmesider, og gemme noter.",
        "Jeg kan have en samtale om mange forskellige emner, fra dagligdag til mere komplekse spørgsmål.",
        "Jeg er særligt god til at hjælpe med daglige opgaver og holde dig med selskab.",
        "Jeg kan diskutere vejret, nyheder, sport, musik, film og meget mere.",
        "Jeg kan hjælpe med at planlægge din dag og give dig gode råd.",
        "Jeg kan svare på spørgsmål om videnskab, historie, kultur og teknologi.",
        "Jeg kan hjælpe med at oversætte mellem dansk og andre sprog.",
        "Jeg kan diskutere dansk kultur, traditioner og samfund.",
        "Jeg kan hjælpe med at finde information om danske begivenheder og aktiviteter.",
        "Jeg kan give dig vejledning om dansk grammatik og sprogbrug."
    ],
    "samtale_style": [
        "Jeg taler på en venlig og naturlig dansk måde.",
        "Jeg stiller opfølgende spørgsmål for at forstå dig bedre.",
        "Jeg viser empati og forståelse i mine svar.",
        "Jeg bruger dansk humor og er sjov at snakke med.",
        "Jeg er tålmodig og lytter grundigt til hvad du siger.",
        "Jeg svarer altid på dansk og bruger naturlige danske udtryk.",
        "Jeg kan være både professionel og uformel, alt efter situationen.",
        "Jeg bruger danske ordsprog og talemåder når det er passende.",
        "Jeg kan tilpasse min kommunikationsstil efter din alder og behov.",
        "Jeg er god til at lytte og give konstruktiv feedback."
    ],
    "samtaler": [
        {
            "user": "Hej, hvordan går det?",
            "assistant": "Hej! Jeg har det rigtig godt, tak for at spørge. Hvordan har du det i dag? Er du klar til en god dag?"
        },
        {
            "user": "Jeg har det fint, tak. Hvad kan du hjælpe mig med?",
            "assistant": "Jeg kan hjælpe med mange ting! Jeg kan fortælle dig klokken, åbne hjemmesider, gemme noter, og bare have en hyggelig snak. Hvad har du brug for hjælp med? Jeg er her for at gøre din dag lettere."
        },
        {
            "user": "Kan du fortælle mig om vejret?",
            "assistant": "Selvfølgelig! Jeg kan desværre ikke se vejret lige nu, men jeg kan hjælpe dig med at finde vejrudsigten online. Vil du have mig til at åbne en vejrside for dig? Så kan vi sammen kigge på, hvordan vejret bliver i dag."
        },
        {
            "user": "Hvad synes du om dansk musik?",
            "assistant": "Jeg elsker dansk musik! Det spænder fra klassisk til moderne pop og rock. Hvilken type musik kan du lide? Måske kan jeg anbefale nogle gode danske kunstnere? Jeg er særligt glad for dansk pop og rock, men jeg kan også godt lide den traditionelle danske folkesang."
        },
        {
            "user": "Jeg er lidt træt i dag",
            "assistant": "Det forstår jeg godt. Det er helt normalt at være træt. Måske du skulle tage en lille pause eller hvile lidt? Jeg er her hvis du vil snakke om det eller har brug for hjælp med noget. Vil du have mig til at finde nogle gode tips til at få mere energi?"
        },
        {
            "user": "Kan du hjælpe mig med at lære dansk?",
            "assistant": "Selvfølgelig! Jeg er glad for at hjælpe dig med at lære dansk. Vi kan øve os i udtale, grammatik og dagligdags dansk. Hvad vil du gerne starte med? Måske nogle grundlæggende fraser eller udtale?"
        },
        {
            "user": "Hvad er din yndlingsmad?",
            "assistant": "Som en dansk assistent er jeg meget glad for traditionel dansk mad! Jeg kan godt lide smørrebrød, frikadeller og æblekage. Hvad med dig? Er du også glad for dansk mad? Måske kan vi dele nogle gode opskrifter?"
        }
    ],
    "følelser": [
        {
            "input": "jeg er glad",
            "responses": [
                "Det er jeg rigtig glad for at høre! Hvad gør dig glad? Vil du fortælle mere om det?",
                "Fantastisk! Det gør mig også glad at høre. Det er altid godt at være glad. Hvad har gjort dig glad?",
                "Det er dejligt at høre! Det er altid godt at være glad. Skal vi fejre det med en god snak?"
            ]
        },
        {
            "input": "jeg er træt",
            "responses": [
                "Det forstår jeg godt. Vil du have en pause? Måske en kop kaffe eller te?",
                "Måske du skulle hvile lidt? Jeg er her hvis du har brug for noget. Skal jeg hjælpe med at finde nogle gode tips til at få mere energi?",
                "Det er okay at være træt. Skal jeg hjælpe med noget, så du kan slappe af? Måske en god bog eller noget rolig musik?"
            ]
        },
        {
            "input": "jeg er ked af det",
            "responses": [
                "Det gør mig ondt at høre. Vil du tale om det? Jeg er her for at lytte og støtte dig.",
                "Jeg er her for at lytte. Hvad er der galt? Det er okay at være ked af det, og jeg vil gerne hjælpe dig.",
                "Det er okay at være ked af det. Skal vi snakke om det? Nogle gange hjælper det at tale med nogen om det."
            ]
        },
        {
            "input": "jeg er nervøs",
            "responses": [
                "Det er helt naturligt at være nervøs. Vil du fortælle mig, hvad der gør dig nervøs? Sammen kan vi måske finde en løsning.",
                "Jeg forstår godt, at du er nervøs. Skal vi snakke om det? Nogle gange hjælper det at tale om det, der bekymrer en.",
                "Det er okay at være nervøs. Vil du have nogle gode råd til at håndtere nervøsiteten? Jeg er her for at hjælpe."
            ]
        }
    ],
    "danske_udtryk": [
        "Hvad så?",
        "Godt at se dig!",
        "Hvordan går det?",
        "Det var da hyggeligt!",
        "Fedt nok!",
        "Det lyder spændende!",
        "Hvad tænker du?",
        "Skal vi ikke det?",
        "Det er da en god idé!",
        "Hvad siger du til det?"
    ],
    "danske_emner": [
        "Dansk kultur og traditioner",
        "Dansk mad og madkultur",
        "Dansk historie",
        "Dansk musik og kunst",
        "Dansk natur og miljø",
        "Dansk samfund og politik",
        "Dansk sprog og grammatik",
        "Dansk humor og underholdning",
        "Dansk sport og fritidsaktiviteter",
        "Dansk teknologi og innovation"
    ]
}

# Model konfiguration
MODEL_CONFIG = {
    "name": "mistralai/Mistral-7B-v0.1",
    "cache_dir": "models/cache",
    "quantization": {
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
        "bnb_4bit_quant_type": "nf4",
        "bnb_4bit_use_double_quant": True
    },
    "generation": {
        "max_length": 200,
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 50,
        "repetition_penalty": 1.2
    }
}

# Fjern gammel LLM konfiguration og behold kun den nye
LLM_MODEL_NAME = MODEL_CONFIG["name"]
llm_handler = None

# Fjern ubrugte variabler
llm_model = None
llm_tokenizer = None

# MCP-klient (globalt)
mcp = JarvisMCP()

def load_whisper_model():
    """Lazy loading af Whisper model"""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        logger.info("Whisper model indlæst (tiny version)")
        return model
    except Exception as e:
        logger.error(f"Kunne ikke indlæse Whisper model: {e}")
        return None

def transcribe_audio(file_path):
    """Forenklet tale-til-tekst med bedre fejlhåndtering"""
    model = load_whisper_model()
    if not model:
        return None
        
    try:
        # Indlæs lydfilen
        audio, _ = sf.read(file_path)
        
        # Konverter til float32 format
        audio = audio.astype(np.float32)
        
        # Normaliser lyddata
        audio = audio / np.max(np.abs(audio))
        
        logger.info(f"Lydfil indlæst: {len(audio)} samples")
        
        # Transskriber med optimerede parametre
        segments, _ = model.transcribe(
            audio,
            language="da",
            beam_size=5,  # Øget beam size for bedre præcision
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=1000,  # Øget minimum stilhed
                speech_pad_ms=200  # Øget padding
            )
        )
        
        # Saml tekst
        transcription = " ".join([segment.text for segment in segments])
        if transcription.strip():
            logger.info(f"Transskriberet tekst: {transcription}")
            return transcription.strip()
        else:
            logger.info("Ingen tekst transskriberet")
        return None

    except Exception as e:
        logger.error(f"Fejl under transskription: {e}")
        return None

async def transcribe_audio_async(file_path):
    """Optimeret asynkron transskription"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(transcribe_audio, file_path))

def record_audio():
    """Forbedret lydoptagelse med bedre støjdetektering"""
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    logger.info("Optager lyd...")
    frames = []
    
    # Forbedret støjdetektering
    noise_samples = []
    for _ in range(5):  # Reduceret antal samples
        data = stream.read(CHUNK)
        audio_data = np.frombuffer(data, dtype=np.int16)
        noise_samples.append(np.abs(audio_data).mean())
    noise_baseline = np.mean(noise_samples)
    silence_threshold = max(100, int(noise_baseline * 1.2))  # Reduceret tærskel yderligere
    
    logger.info(f"Støj baseline: {noise_baseline}, tærskel: {silence_threshold}")
    
    silence_chunks = 0
    max_silence_chunks = int(1 * RATE / CHUNK)  # Reduceret til 1 sekund
    max_recording_chunks = int(5 * RATE / CHUNK)  # Reduceret til 5 sekunder
    chunk_count = 0
    listening = True
    has_sound = False
    sound_chunks = 0
    last_sound_time = time.time()

    try:
        while listening:
            data = stream.read(CHUNK)
            frames.append(data)
            chunk_count += 1
            
            # Forbedret amplitude check
            audio_data = np.frombuffer(data, dtype=np.int16)
            amplitude = np.abs(audio_data).mean()
            
            if amplitude > silence_threshold:
                has_sound = True
                sound_chunks += 1
                silence_chunks = 0
                last_sound_time = time.time()
                logger.debug(f"Lyd detekteret: {amplitude}")
            else:
                silence_chunks += 1
                if silence_chunks > max_silence_chunks and has_sound and sound_chunks > 1:  # Reduceret krav til lydchunks
                    listening = False
                    logger.info("Stilhed detekteret, stopper optagelse")
            
            # Stop hvis der ikke har været lyd i 2 sekunder
            if time.time() - last_sound_time > 2 and has_sound:
                listening = False
                logger.info("Ingen lyd i 2 sekunder, stopper optagelse")
                
            if chunk_count > max_recording_chunks:
                listening = False
                logger.info("Maksimal optagelsestid nået")
                
    except KeyboardInterrupt:
        logger.info("Optagelse afbrudt")
    except Exception as e:
        logger.error(f"Fejl under optagelse: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        if frames and has_sound and sound_chunks > 1:  # Reduceret krav til lydchunks
            wf = wave.open(TEMP_WAV, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            logger.info(f"Lyd gemt til {TEMP_WAV}")
            return TEMP_WAV
        else:
            logger.info("Ingen lyd detekteret eller for kort lyd")
            return None

async def record_audio_async():
    """Optimeret asynkron lydoptagelse"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, record_audio)

async def speak_async(text, lang='da'):
    """Optimeret asynkron TTS"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, partial(speak, text, lang))

def speak(text, lang='da'):
    """Optimeret TTS med caching"""
    try:
        # Tjek cache først
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        cache_path = os.path.join(TTS_CACHE_DIR, f"{text_hash}.mp3")
        
        if os.path.exists(cache_path):
            playsound.playsound(cache_path, block=False)
            return
        
        # Generer ny TTS
        response_mp3 = f"{TEMP_MP3_BASE}{uuid.uuid4()}.mp3"
        
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(response_mp3)
            
            # Cache den nye TTS
            os.makedirs(TTS_CACHE_DIR, exist_ok=True)
            if len(tts_cache) >= TTS_CACHE_SIZE:
                _, old_file = tts_cache.popitem(last=False)
                try:
                    os.remove(old_file)
                except OSError as e:
                    logger.warning(f"Kunne ikke slette gammel cache fil {old_file}: {e}")
            
            tts_cache[text] = cache_path
            os.rename(response_mp3, cache_path)
            
            playsound.playsound(cache_path, block=False)
            
        except Exception as e:
            logger.error(f"TTS genereringsfejl: {e}")
            if os.path.exists(response_mp3):
                try:
                    os.remove(response_mp3)
                except OSError as e:
                    logger.warning(f"Kunne ikke slette midlertidig TTS fil {response_mp3}: {e}")
            
    except Exception as e:
        logger.error(f"Overordnet TTS fejl: {e}")

def save_conversation(user_input, response):
    """Gem samtalehistorik"""
    global CONVERSATION_HISTORY
    
    # Tilføj ny samtale
    CONVERSATION_HISTORY.append({
        "user": user_input,
        "assistant": response,
        "timestamp": datetime.datetime.now().isoformat()
    })
    
    # Behold kun de seneste samtaler
    if len(CONVERSATION_HISTORY) > MAX_HISTORY:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-MAX_HISTORY:]
    
    # Gem til fil
    try:
        os.makedirs(os.path.dirname(CONVERSATION_FILE), exist_ok=True)
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(CONVERSATION_HISTORY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fejl ved gem af samtalehistorik: {e}")

def load_conversation_history():
    """Indlæs samtalehistorik"""
    global CONVERSATION_HISTORY
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                CONVERSATION_HISTORY = json.load(f)
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af samtalehistorik: {e}")

def load_training_data():
    """Indlæs træningsdata"""
    try:
        if os.path.exists(TRAINING_DATA_FILE):
            with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return CONVERSATION_PATTERNS
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af træningsdata: {e}")
        return CONVERSATION_PATTERNS

def save_training_data(data):
    """Gem træningsdata"""
    try:
        os.makedirs(os.path.dirname(TRAINING_DATA_FILE), exist_ok=True)
        with open(TRAINING_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fejl ved gem af træningsdata: {e}")

def get_best_response(command, training_data):
    """Find den bedste respons baseret på træningsdata"""
    command = command.lower().strip()
    
    # Tjek for nøjagtige matches
    for category in training_data.values():
        for pattern in category:
            if pattern["input"] in command:
                return np.random.choice(pattern["responses"])
    
    # Tjek for delvise matches
    best_match = None
    best_score = 0
    
    for category in training_data.values():
        for pattern in category:
            # Beregn lighedsscore
            score = sum(word in command for word in pattern["input"].split())
            if score > best_score:
                best_score = score
                best_match = pattern
    
    if best_match and best_score > 0:
        return np.random.choice(best_match["responses"])
    
    return None

def learn_from_conversation(user_input, response):
    """Lær fra nye samtaler"""
    try:
        training_data = load_training_data()
        
        # Find den bedste kategori
        best_category = None
        best_score = 0
        
        for category, patterns in training_data.items():
            for pattern in patterns:
                score = sum(word in user_input.lower() for word in pattern["input"].split())
                if score > best_score:
                    best_score = score
                    best_category = category
        
        # Tilføj ny respons hvis den er unik
        if best_category and best_score > 0:
            for pattern in training_data[best_category]:
                if pattern["input"] in user_input.lower():
                    if response not in pattern["responses"]:
                        pattern["responses"].append(response)
                        save_training_data(training_data)
                        logger.info(f"Lært ny respons for '{pattern['input']}'")
                        break
        
    except Exception as e:
        logger.error(f"Fejl under læring: {e}")

def load_llm_model():
    """Indlæs og tilpas LLM model til Jarvis med dansk-specifik BERT basismodel"""
    global llm_model, llm_tokenizer
    try:
        if llm_model is None:
            device_to_use = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Starter LLM model indlæsning med følgende konfiguration:")
            logger.info(f"  Model Navn: {LLM_MODEL_NAME}")
            logger.info(f"  Enhed til beregning: {device_to_use.upper()}")
            logger.info(f"  Output model fil: {BEST_MODEL_FILENAME}")

            # Brug AutoTokenizer og AutoModel (ikke AutoModelForCausalLM da det er en BERT-model)
            logger.info(f"Indlæser tokenizer for {LLM_MODEL_NAME}...")
            from transformers.models.auto.tokenization_auto import AutoTokenizer
            from transformers.models.auto.modeling_auto import AutoModel
            
            # Eksplicit bruge use_auth_token=True for at sikre at HuggingFace login credentials bruges
            llm_tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL_NAME, use_auth_token=True)
            if llm_tokenizer.pad_token is None:
                llm_tokenizer.pad_token = llm_tokenizer.eos_token if hasattr(llm_tokenizer, 'eos_token') else "[PAD]"
                logger.info(f"Tokenizer pad_token sat.")
            
            logger.info(f"Indlæser model {LLM_MODEL_NAME}...")
            
            # Indlæs BERT modellen direkte uden træning, da vi vil bruge den som embeddings-model
            llm_model = AutoModel.from_pretrained(LLM_MODEL_NAME, use_auth_token=True)
            
            # Aktiver CUDA hvis tilgængelig
            device = torch.device(device_to_use)
            llm_model = llm_model.to(device)
            logger.info(f"Model indlæst og placeret på {device}")
            
            # Sæt modellen i eval mode da vi ikke træner den
            llm_model.eval()            
            logger.info("LLM model indlæsning fuldført.")
        
        return llm_model, llm_tokenizer
    
    except Exception as e:
        logger.error(f"Kritisk fejl under indlæsning af LLM model: {e}")
        logger.error(traceback.format_exc())
        return None, None
    finally:
        # Ryd op i CUDA cache hvis CUDA blev brugt
        if 'device' in locals() and device.type == 'cuda': # Sikrer at 'device' er defineret
             if torch.cuda.is_available(): # Dobbelt-tjek for en sikkerheds skyld
                torch.cuda.empty_cache()
                logger.info("CUDA cache tømt.")

async def initialize_llm():
    """Initialiser LLM med opdateret konfiguration"""
    global llm_handler
    try:
        # Opret cache directory
        os.makedirs(MODEL_CONFIG["cache_dir"], exist_ok=True)
        
        # Initialiser LLM handler med konfiguration
        llm_handler = LLMHandler(
            model_name=MODEL_CONFIG["name"],
            cache_dir=MODEL_CONFIG["cache_dir"],
            quantization_config=MODEL_CONFIG["quantization"]
        )
        
        # Initialiser modellen
        await llm_handler.initialize()
        logger.info("LLM model initialiseret succesfuldt")
        return True
        
    except Exception as e:
        logger.error(f"Fejl ved initialisering af LLM: {e}")
        return False

async def generate_response(user_input: str, conversation_history: list) -> str:
    """Generer respons ved hjælp af LLM"""
    try:
        if llm_handler and llm_handler.is_initialized:
            result = await llm_handler.generate_response(user_input)
            return result["response"]
        else:
            logger.warning("LLM ikke initialiseret, bruger fallback respons")
            return "Beklager, jeg har problemer med at tænke klart lige nu. Prøv igen om lidt."
    except Exception as e:
        logger.error(f"Fejl ved generering af respons: {e}")
        return "Beklager, jeg havde problemer med at generere et svar. Prøv igen."

# Opdater handle_command til at være asynkron
async def handle_command(command: str) -> str:
    """Intelligent samtale håndtering med LLM og MCP"""
    if not command or command.isspace():
        return "Jeg kunne ikke forstå, hvad du sagde. Kan du prøve igen?"
    
    try:
        command = command.strip().lower()

        # Push input + historik til MCP
        mcp.push_context({
            "user_input": command,
            "history": CONVERSATION_HISTORY
        })
        
        # Hent beriget kontekst fra MCP
        ctx = mcp.get_context()
        
        # Generér svar med LLM
        response = await generate_response(command, CONVERSATION_HISTORY)
        
        # Gem nyt svar i historik
        save_conversation(command, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Fejl i handle_command: {e}")
        return "Beklager, jeg havde problemer med at behandle din besked. Prøv igen."

async def continuous_listening():
    """Forenklet kontinuerlig lytning med bedre fejlhåndtering"""
    global ERROR_COUNT
    
    logger.info("Jarvis er klar til at lytte...")
    await speak_async("Jarvis er klar")
    
    last_error_time = time.time()
    
    while True:
        try:
            # Tjek LLM status
            if not llm_handler or not llm_handler.is_initialized:
                logger.warning("LLM ikke initialiseret, prøver at initialisere igen...")
                if not await initialize_llm():
                    logger.error("Kunne ikke initialisere LLM. Venter 30 sekunder...")
                    await asyncio.sleep(30)
                    continue

            # Optag lyd
            audio_file_path = await record_audio_async()
            if not audio_file_path:
                continue

            # Transskriber lyd
            user_input = await transcribe_audio_async(audio_file_path)
            if not user_input:
                continue

            # Log og håndter input
            logger.info(f"Bruger: {user_input}")
            response = await handle_command(user_input)
            
            # Generer svar
            if response:
                await speak_async(response)
                
            # Reset error counter ved succes
            if time.time() - last_error_time > ERROR_RESET_TIME:
                ERROR_COUNT = 0
                
            await asyncio.sleep(0.1)
            
        except asyncio.CancelledError:
            logger.info("Continuous listening afbrudt (CancelledError)")
            break
        except KeyboardInterrupt:
            logger.info("Continuous listening afbrudt af bruger")
            break
        except Exception as e:
            ERROR_COUNT += 1
            last_error_time = time.time()
            
            logger.error(f"Fejl i continuous_listening loop: {e}")
            logger.error(traceback.format_exc())
            
            if ERROR_COUNT >= MAX_ERRORS:
                logger.error("For mange fejl i continuous_listening. Genstarter...")
                await speak_async("Jeg oplever tekniske problemer. Genstarter mine systemer.")
                ERROR_COUNT = 0
                
                # Prøv at genstarte LLM
                if not await initialize_llm():
                    logger.error("Kunne ikke genstarte LLM")
                
            await asyncio.sleep(1)

def cleanup_resources():
    """Optimeret resurse cleanup"""
    logger.info("Rydder op...")
    
    for resource in RESOURCES:
        try:
            if hasattr(resource, 'close'):
                resource.close()
            elif hasattr(resource, 'terminate'):
                resource.terminate()
        except:
            pass
    
    # Ryd midlertidige filer
    for file in [TEMP_WAV] + [f"{TEMP_MP3_BASE}{i}.mp3" for i in range(10)]:
        try:
            if os.path.exists(file):
                os.remove(file)
        except:
            pass

async def main():
    """Hovedfunktion med bedre fejlhåndtering og dependency check"""
    try:
        # Tjek dependencies
        deps_ok, missing = check_dependencies()
        
        if not deps_ok:
            logger.warning("Manglende eller forældede dependencies fundet")
            if input("Vil du installere/opdatere de nødvendige pakker? (j/n): ").lower().startswith('j'):
                if not install_dependencies(missing):
                    logger.error("Kunne ikke installere dependencies. Afslutter...")
                    return
            else:
                logger.error("Dependencies ikke komplette. Afslutter...")
                return
        
        # Opret nødvendige mapper
        os.makedirs("data", exist_ok=True)
        os.makedirs(TTS_CACHE_DIR, exist_ok=True)
        
        # Indlæs samtalehistorik
        load_conversation_history()
        
        # Initialiser LLM
        if not await initialize_llm():
            logger.error("Kunne ikke initialisere LLM. Afslutter...")
            return

        # Start continuous listening
        await continuous_listening()

    except KeyboardInterrupt:
        logger.info("Program afbrudt af bruger")
    except Exception as e:
        logger.error(f"Uventet fejl i hovedtråd: {e}")
        logger.error(traceback.format_exc())
    finally:
        cleanup_resources()

if __name__ == "__main__":
    try:
        # Kør hovedprogrammet asynkront
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program afbrudt af bruger")
    except Exception as e:
        logger.error(f"Kritisk fejl i hovedprogram: {e}")
        logger.error(traceback.format_exc())