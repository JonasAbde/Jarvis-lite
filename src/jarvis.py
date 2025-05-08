#!/usr/bin/env python3
"""
Jarvis Lite - Hovedmodul
En dansk sprogbaseret AI assistent med tale-til-tekst og tekst-til-tale funktionalitet.
"""

import os
import time
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional

# Konfigurer logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/jarvis.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Importer kernekomponenter
try:
    from audio.speech import (
        record_audio_async,
        transcribe_audio_async,
        speak_async,
    )
    from audio.wakeword import (
        initialize_wakeword_detector,
        stop_wakeword_detector,
    )
    from commands.handlers import handle_command

    # NLU-modul til intent-klassificering
    try:
        import nlu as nlu

        NLU_AVAILABLE = True
        logger.info(f"NLU modul indlæst med følgende intents: {nlu.get_available_intents()}")
    except ImportError:
        logger.warning("NLU-modul kunne ikke importeres. Kører med simpel kommandohåndtering.")
        NLU_AVAILABLE = False

    # Forsøg at importere LLM-modellen, men fortsæt selv hvis det fejler
    try:
        from llm.model import is_model_available, generate_response

        LLM_AVAILABLE = is_model_available()
        if LLM_AVAILABLE:
            logger.info("LLM-model indlæst og klar til brug")
        else:
            logger.warning("LLM-model ikke tilgængelig")
    except ImportError:
        logger.warning("LLM-modul kunne ikke importeres. Kører uden LLM.")
        LLM_AVAILABLE = False
except ImportError as e:
    logger.error(f"Kunne ikke importere nødvendige moduler: {e}")
    raise

# Konfiguration
CONVERSATION_DIR = os.path.join("data", "conversations")
CONVERSATION_FILE = os.path.join(CONVERSATION_DIR, "history.json")
MAX_HISTORY = 10  # Maksimalt antal samtaler der gemmes
USE_WAKEWORD = False  # Indstil til False for at deaktivere wakeword-detektion

# Globale variable
CONVERSATION_HISTORY = []
ERROR_COUNT = 0
MAX_ERRORS = 3
LISTENING_FOR_COMMAND = False  # Flag til at styre aktiveringstilstand


def save_conversation(user_input: str, response: str) -> None:
    """
    Gemmer en samtale til historikken
    
    Args:
        user_input: Brugerens input
        response: Systemets svar
    """
    global CONVERSATION_HISTORY

    # Tilføj ny samtale
    CONVERSATION_HISTORY.append(
        {
            "user": user_input,
            "assistant": response,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
    )

    # Begræns historikken
    if len(CONVERSATION_HISTORY) > MAX_HISTORY:
        CONVERSATION_HISTORY = CONVERSATION_HISTORY[-MAX_HISTORY:]

    # Gem til fil
    try:
        os.makedirs(CONVERSATION_DIR, exist_ok=True)
        with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
            json.dump(CONVERSATION_HISTORY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Fejl ved gem af samtalehistorik: {e}")


def load_conversation_history() -> None:
    """Indlæser samtalehistorik fra fil"""
    global CONVERSATION_HISTORY
    try:
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
                CONVERSATION_HISTORY = json.load(f)
                logger.info(f"Indlæst {len(CONVERSATION_HISTORY)} samtaler fra historikken")
    except Exception as e:
        logger.error(f"Fejl ved indlæsning af samtalehistorik: {e}")
        CONVERSATION_HISTORY = []


async def process_command(user_input: str) -> str:
    """
    Behandler en kommando fra brugeren med forbedret kontekstforståelse
    
    Args:
        user_input: Brugerens input
        
    Returns:
        Systemets svar
    """
    if not user_input or user_input.isspace():
        return "Jeg kunne ikke forstå, hvad du sagde. Kan du prøve igen?"

    # Først tjek om det er en fortsættelse af en tidligere samtale
    # ved at se på de seneste indlæg i samtalehistorikken
    is_followup = False
    followup_context = None
    
    if CONVERSATION_HISTORY:
        # Se på det seneste svar
        last_exchange = CONVERSATION_HISTORY[-1]
        last_response = last_exchange.get("assistant", "")
        
        # Tjek for kontekst-markører i brugerinput
        followup_indicators = ["ja", "nej", "det", "den", "de", "hvorfor", "hvordan", 
                              "hvad med", "ok", "fint", "godt", "næste", "fortsæt", 
                              "uddyb", "fortæl mere", "og", "hvad så"]
        
        # Tjek for korte følge-forespørgsler
        if (len(user_input.split()) <= 3 and 
            any(user_input.lower().startswith(ind) for ind in followup_indicators)):
            is_followup = True
            
        # Tjek for uddybningsanmodninger
        elif any(marker in user_input.lower() for marker in ["mere om det", "uddyb", "fortsæt", "fortæl mere"]):
            is_followup = True
            
        # Hvis svaret endte med spørgsmål, behandl input som et svar på det
        if "?" in last_response.split(".")[-1] or "Vil du" in last_response or "Skal jeg" in last_response:
            is_followup = True
            
        # For ja/nej respons til et spørgsmål
        if user_input.lower() in ["ja", "jo", "okay", "yes", "jep", "gerne", "selvfølgelig", "nej", "no", "ikke", "næh"]:
            is_followup = True
            
        if is_followup:
            logger.info(f"Detekteret følgespørgsmål/svar relateret til tidligere kontekst")
            followup_context = {
                "last_user_input": last_exchange.get("user", ""),
                "last_response": last_response
            }

    # Først tjek om det er en NLU-genkendelig kommando
    if NLU_AVAILABLE:
        try:
            nlu_result = nlu.analyze(user_input)
            intent = nlu_result["intent"]
            confidence = nlu_result["confidence"]

            # Log NLU-resultatet
            logger.info(f"NLU: Intent='{intent}', Konfidens={confidence:.2f}")

            # Hvis vi har en intent der ikke er 'unknown', brug kommandohåndtering
            if intent != "unknown":
                logger.info(f"Bruger kommandohåndtering for intent: {intent}")
                
                # Videregivelse af kontekst hvis det er en følgespørgsmål
                if is_followup and followup_context:
                    # Tilføj vores egen kontekstinformation til historikken
                    context_history = CONVERSATION_HISTORY.copy()
                    context_history.append({
                        "followup_context": followup_context,
                        "is_followup": True
                    })
                    return handle_command(user_input, context_history)
                else:
                    return handle_command(user_input, CONVERSATION_HISTORY)
        except Exception as e:
            logger.error(f"Fejl ved NLU-analyse: {e}")

    # Hvis ikke, prøv med LLM for mere avancerede forespørgsler
    if LLM_AVAILABLE:
        try:
            logger.info("Bruger LLM til at generere svar")
            
            # Hvis det er en følgespørgsmål, tilføj kontekst
            if is_followup and followup_context:
                # Forbered udvidet kontekst til LLM
                enriched_input = f"{followup_context['last_user_input']} -> {followup_context['last_response']} -> {user_input}"
                response = generate_response(enriched_input, CONVERSATION_HISTORY)
            else:
                response = generate_response(user_input, CONVERSATION_HISTORY)
                
            if response:
                return response
        except Exception as e:
            logger.error(f"Fejl ved LLM-generering: {e}")

    # Fallback til kommandohåndtering
    logger.info("Bruger kommandohåndtering som fallback")
    try:
        return handle_command(user_input, CONVERSATION_HISTORY)
    except Exception as e:
        logger.error(f"Fejl i kommandohåndtering: {e}")
        # Sidste fallback
        return "Jeg forstod desværre ikke det. Prøv at spørge mig om noget andet, f.eks. tiden, vejret eller en joke."


async def wakeword_detected_callback() -> None:
    """Callback der bliver kaldt når wakeword detekteres"""
    global LISTENING_FOR_COMMAND
    
    LISTENING_FOR_COMMAND = True
    
    # Afspil aktiveringsbekræftelse
    await speak_async("Ja?")
    
    # Start kommandolytning
    await listen_for_command()


async def listen_for_command() -> None:
    """Lytter efter en specifik kommando efter wakeword er aktiveret"""
    global LISTENING_FOR_COMMAND, ERROR_COUNT
    
    try:
        # Optag lyd til kommando
        audio_file_path = await record_audio_async()
        
        if audio_file_path:
            # Konverter til tekst
            user_input = await transcribe_audio_async(audio_file_path)
            
            if user_input:
                logger.info(f"Bruger: {user_input}")
                
                # Behandl kommando
                response = await process_command(user_input)
                
                # Gem samtale
                save_conversation(user_input, response)
                
                # Afspil svar
                if response:
                    logger.info(f"Jarvis: {response}")
                    await speak_async(response)
    
    except Exception as e:
        ERROR_COUNT += 1
        logger.error(f"Fejl i kommandolytning: {e}")
    
    finally:
        # Nulstil lyttetilstand uanset hvad
        LISTENING_FOR_COMMAND = False


async def continuous_listening() -> None:
    """Hovedloop der lytter efter brugerinput eller wakeword"""
    global ERROR_COUNT, LISTENING_FOR_COMMAND
    
    logger.info("Jarvis er klar til at lytte...")
    await speak_async("Jarvis er klar")
    
    # Start wakeword-detektion hvis aktiveret
    if USE_WAKEWORD:
        await initialize_wakeword_detector(wakeword_detected_callback)
        logger.info("Wakeword-detektion startet - sig 'Jarvis' for at aktivere")
    
    try:
        while True:
            try:
                # Hvis wakeword er deaktiveret eller vi lytter direkte efter kommando
                if not USE_WAKEWORD:
                    # Optag lyd
                    audio_file_path = await record_audio_async()
                    
                    if audio_file_path:
                        # Konverter til tekst
                        user_input = await transcribe_audio_async(audio_file_path)
                        
                        if user_input:
                            logger.info(f"Bruger: {user_input}")
                            
                            # Behandl kommando
                            response = await process_command(user_input)
                            
                            # Gem samtale
                            save_conversation(user_input, response)
                            
                            # Afspil svar
                            if response:
                                logger.info(f"Jarvis: {response}")
                                await speak_async(response)
                
                # Vent lidt for at spare CPU
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                logger.info("Afbrudt af bruger (KeyboardInterrupt)")
                break
                
            except Exception as e:
                ERROR_COUNT += 1
                logger.error(f"Fejl i lytteloop: {e}")
                
                if ERROR_COUNT >= MAX_ERRORS:
                    logger.error("For mange fejl, genstarter...")
                    await speak_async("Jeg oplever tekniske problemer og genstarter.")
                    ERROR_COUNT = 0
                    
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        logger.info("Program afbrudt af bruger")
    
    finally:
        # Stop wakeword-detektion
        if USE_WAKEWORD:
            await stop_wakeword_detector()


def main() -> None:
    """Hovedfunktion"""
    try:
        # Indlæs samtalehistorik
        load_conversation_history()
        
        # Opret nødvendige mapper
        os.makedirs(os.path.join("data", "notes"), exist_ok=True)
        os.makedirs(os.path.join("src", "cache"), exist_ok=True)
        os.makedirs(os.path.join("src", "cache", "tts"), exist_ok=True)
        os.makedirs(os.path.join("src", "cache", "models"), exist_ok=True)
        
        # Start lytteloop
        asyncio.run(continuous_listening())
        
    except KeyboardInterrupt:
        logger.info("Afslutter...")
    
    except Exception as e:
        logger.error(f"Kritisk fejl: {e}")
        
    finally:
        logger.info("Jarvis Lite er lukket ned")


if __name__ == "__main__":
    main()
