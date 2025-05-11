#!/usr/bin/env python3
"""
Jarvis-Lite: Hovedmodul der aktiverer stemmeinterface og håndterer brugerinput
"""

import os
import sys # Importeret sys
import time
import logging
import logging.handlers # Tilføjet for RotatingFileHandler
import asyncio
import json
import subprocess # Tilføjet for at køre scripts/apps
import importlib # Tilføjet for dynamisk funktionskald
import random
from typing import List, Dict, Any, Optional
import uuid
from src.nlu.utils import _append_training_example # Importerer hjælpefunktion
from src.nlu.classifier import NLUClassifier, load_training_data as load_nlu_training_data # Importerer NLUClassifier og load_training_data (med nyt navn)

# --- Globale variabler ---
CORE_COMPONENTS_MISSING = True

# --- Global Logger Opsætning ---
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "jarvis_app.log")

def setup_logging(log_level=logging.INFO):
    """Konfigurerer logging til både konsol og fil."""
    os.makedirs(LOG_DIR, exist_ok=True)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s [%(levelname)s] (%(threadName)-10s) - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                LOG_FILE,
                maxBytes=5*1024*1024,  # 5 MB
                backupCount=3,
                encoding='utf-8'
            )
        ]
    )
    # root_logger = logging.getLogger() # Få root logger
    # Sæt et filter for at undgå at logge for meget fra FastAPI/uvicorn hvis de bruges i samme proces
    # class FilterUvicornAccess(logging.Filter):
    #     def filter(self, record):
    #         # Undgå at logge access logs fra uvicorn.access, hvis du vil have færre logs
    #         if record.name == 'uvicorn.access' and 'HTTP/' in record.getMessage():
    #             return False
    #         return True
    # root_logger.addFilter(FilterUvicornAccess())
    
    logger_instance = logging.getLogger(__name__) # Logger for denne fil
    logger_instance.info("Logging konfigureret.")
    return logger_instance

logger = setup_logging() # Kald logger setup globalt

# --- Importer Jarvis Kernekomponenter ---
try:
    # Dynamisk import baseret på hvorfra scriptet køres
    try:
        # Hvis kørt fra rod-mappen
        from src.audio.speech import (
            record_audio_async,
            transcribe_audio_async,
            speak_async,
            stream_speak,
        )
        from src.command_parser import load_commands_from_config, find_matching_command
        from src.nlu.classifier import analyze as analyze_nlu_intent, get_available_intents as get_nlu_intents
        from src.commands.handlers import handle_command as handle_legacy_command
        from src.context_manager import ContextManager
        from src.llm.model import generate_response as llm_generate_response, is_model_available as llm_available
    except ImportError:
        # Hvis kørt fra src-mappen
        from audio.speech import (
            record_audio_async,
            transcribe_audio_async,
            speak_async,
            stream_speak,
        )
        from command_parser import load_commands_from_config, find_matching_command
        from nlu.classifier import analyze as analyze_nlu_intent, get_available_intents as get_nlu_intents
        from commands.handlers import handle_command as handle_legacy_command
        from context_manager import ContextManager
        from llm.model import generate_response as llm_generate_response, is_model_available as llm_available

    # Initialiser globale variabler
    COMMANDS_CONFIG = None
    context_manager = ContextManager()
    logger.info("Kernekomponenter (audio, command_parser, nlu, context_manager) importeret.")
    CORE_COMPONENTS_MISSING = False

except ImportError as e:
    logger.critical(f"KRITISK FEJL: Kunne ikke importere nødvendige moduler: {e}", exc_info=True)
    logger.critical("Jarvis-lite kan muligvis ikke starte korrekt. Tjek dine moduler og stier.")

# --- Konfiguration (globale indstillinger) ---
# CONVERSATION_DIR & FILE håndteres nu af ContextManager
USE_WAKEWORD = False  # Wakeword er ikke implementeret i denne omgang

# --- Globale Variable (tilstand) ---
# CONVERSATION_HISTORY håndteres nu af context_manager
ERROR_COUNT = 0
MAX_ERRORS = 5 # Lidt højere tærskel
# LISTENING_FOR_COMMAND - afhænger af hvordan LiveVoiceAI integreres

# --- Initialisering ved Opstart ---
def initialize_jarvis():
    global COMMANDS_CONFIG
    if CORE_COMPONENTS_MISSING:
        logger.error("Initialisering afbrudt pga. manglende kernekomponenter.")
        return False

    logger.info("Initialiserer Jarvis-lite...")
    COMMANDS_CONFIG = load_commands_from_config() # Indlæs dynamiske kommandoer
    if not COMMANDS_CONFIG:
        logger.warning("Kunne ikke indlæse dynamisk kommando-konfiguration. Kun NLU-baserede intents vil virke.")
    
    # Test NLU-modulet ved at hente intents
    nlu_operational = False
    try:
        available_intents = get_nlu_intents()
        if available_intents:
            logger.info(f"NLU-modul operationelt. Tilgængelige intents: {available_intents}")
            nlu_operational = True
        else:
            logger.error("NLU-modul initialiseret, men ingen intents fundet. Tjek model og træningsdata.")
    except Exception as e:
        logger.error(f"Kritisk fejl under initialisering/test af NLU-modul: {e}", exc_info=True)
        # nlu_operational forbliver False

    if not nlu_operational:
        logger.error("Jarvis-lite initialisering fejlede: NLU-modulet er ikke operationelt.")
        return False # Vigtigt: Returner False hvis NLU ikke er klar

    # Opret nødvendige data/cache mapper (hvis ikke allerede gjort af modulerne selv)
    os.makedirs(os.path.join("data", "notes"), exist_ok=True)
    os.makedirs(os.path.join("src", "cache", "tts"), exist_ok=True)
    # models/nlu oprettes af NLUClassifier hvis den træner

    logger.info("Jarvis-lite initialiseret.")
    
    # --- Start daglig NLU retræning baggrunds-task (Tilføjet) ---
    asyncio.create_task(_daily_retrain())
    logger.info("Daglig NLU retræning baggrunds-task startet.")

    return True

# --- Singleton instans af NLUClassifier og genindlæsningsfunktion (Tilføjet) ---
_classifier_instance: Optional[NLUClassifier] = None

def _get_classifier_instance() -> NLUClassifier:
    """ Returnerer singleton instansen af NLUClassifier, opretter den hvis den ikke findes. """
    global _classifier_instance
    if _classifier_instance is None:
        # Initialiser NLUClassifier. Den vil forsøge at indlæse model ved oprettelse.
        _classifier_instance = NLUClassifier()
    return _classifier_instance

def _reload_classifier() -> None:
    """ Genindlæser NLUClassifier instansen for at loade den seneste model. """
    global _classifier_instance
    logger.info("Genindlæser NLUClassifier for at loade ny model...")
    _classifier_instance = NLUClassifier() # Opretter en ny instans, som indlæser den gemte model
    if _classifier_instance.pipeline and _classifier_instance.intent_labels:
        logger.info("NLUClassifier genindlæst succesfuldt.")
    else:
         logger.warning("NLUClassifier genindlæsning fejlede. Modellen blev ikke indlæst.")

# --- Baggrunds-task for daglig retræning (Tilføjet) ---
async def _daily_retrain():
    logger.info("Starter daglig NLU retræning task.")
    while True:
        # Vent 24 timer
        await asyncio.sleep(24 * 3600) # 24 timer i sekunder
        # await asyncio.sleep(60) # TEST: Retræn hvert minut til test

        logger.info("Udfører daglig NLU retræning.")
        try:
            # Indlæs de seneste træningsdata (nu fra data/nlu_training_data.json)
            # Brug load_training_data fra classifier.py
            patterns, intents = load_nlu_training_data(file_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "nlu_training_data.json"))
            
            if patterns and intents:
                # Opret en ny classifier instans til træning (behøver ikke være singleton)
                trainer_classifier = NLUClassifier() 
                trainer_classifier.train(patterns, intents) # Træner og gemmer modellen
                logger.info("Daglig NLU-model træning fuldført.")
                
                # Genindlæs den nyligt trænede model i singleton-instansen
                _reload_classifier()
            else:
                logger.warning("Ingen træningsdata fundet til daglig retræning. Springer træning over.")

        except Exception as e:
            logger.error(f"Fejl under daglig NLU retræning: {e}", exc_info=True)

# --- Kommando Udførelses Logik ---
async def execute_action(action: Dict[str, Any]):
    """Udfører en handling baseret på den matchede kommando."""
    action_type = action.get("action_type")
    action_details = action.get("action_details")
    params = action.get("extracted_parameters", {})
    response_message = None

    logger.info(f"Udfører handling: Type='{action_type}', Detaljer='{action_details}', Parametre={params}")

    try:
        if not action_details: # Tjek for None action_details
            logger.warning(f"Action details er None for action_type: {action_type}. Kan ikke udføre.")
            return "Jeg mangler detaljer for at udføre denne handling."

        if action_type == "script":
            # Kør eksternt script
            # For sikkerhed, valider action_details og overvej sandboxing
            # Her antager vi, at action_details er en relativ sti fra projektets rod
            script_path = os.path.abspath(str(action_details))
            if not os.path.exists(script_path):
                logger.error(f"Script ikke fundet: {script_path}")
                response_message = f"Jeg kunne ikke finde scriptet {action_details}."
            else:
                # Tilføj parametre som argumenter til scriptet (simpel eksempel)
                cmd_list = [sys.executable if script_path.endswith(".py") else script_path]
                for p_val in params.values():
                    cmd_list.append(str(p_val))
                
                process = await asyncio.create_subprocess_exec(
                    *cmd_list,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Script '{action_details}' udført succesfuldt.")
                    # Du kan evt. fange stdout og bruge som en del af svaret
                    output = stdout.decode().strip()
                    response_message = f"Scriptet '{action_details}' blev udført." 
                    if output:
                        response_message += f" Output: {output[:100]}..." # Begræns output længde
                else:
                    error_output = stderr.decode().strip()
                    logger.error(f"Fejl under kørsel af script '{action_details}': {error_output}")
                    response_message = f"Der opstod en fejl under kørsel af {action_details}."
        
        elif action_type == "function":
            # Kald en Python funktion dynamisk
            module_name, function_name = str(action_details).rsplit('.', 1)
            try:
                module = importlib.import_module(module_name)
                func = getattr(module, function_name)
                
                # Tjek om funktionen er async eller sync
                if asyncio.iscoroutinefunction(func):
                    # Antag at funktionen tager parametre som keyword arguments
                    # Eller en specifik `context` eller `params` dict
                    # Dette er et eksempel, din funktion skal designes til at modtage dem
                    action_result = await func(**params) 
                else:
                    # For synkrone funktioner, kør i executor for at undgå blokering
                    loop = asyncio.get_event_loop()
                    action_result = await loop.run_in_executor(None, lambda: func(**params))
                
                response_message = str(action_result) if action_result is not None else f"Funktionen {function_name} blev kaldt."
                logger.info(f"Funktion '{action_details}' udført. Resultat: {response_message}")

            except ModuleNotFoundError:
                logger.error(f"Modul '{module_name}' ikke fundet for funktion '{action_details}'.")
                response_message = f"Jeg kunne ikke finde modulet til funktionen {function_name}."
            except AttributeError:
                logger.error(f"Funktion '{function_name}' ikke fundet i modul '{module_name}'.")
                response_message = f"Jeg kunne ikke finde funktionen {function_name}."
            except Exception as e:
                logger.error(f"Fejl under udførsel af funktion '{action_details}': {e}", exc_info=True)
                response_message = f"Der skete en fejl med funktionen {function_name}."

        elif action_type == "application":
            # Åbn applikation
            # Dette er platform-specifikt og kan være usikkert
            try:
                # Popen er non-blocking, hvilket er fint her
                subprocess.Popen(str(action_details), shell=True) # shell=True kan være en sikkerhedsrisiko
                response_message = f"Jeg prøver at åbne {action_details}."
                logger.info(f"Forsøger at starte applikation: {action_details}")
            except Exception as e:
                logger.error(f"Fejl ved start af applikation '{action_details}': {e}")
                response_message = f"Jeg kunne ikke åbne {action_details}."
        else:
            logger.warning(f"Ukendt handlingstype: {action_type}")
            response_message = "Jeg er ikke sikker på, hvordan jeg udfører den type handling."

    except Exception as e:
        logger.error(f"Generel fejl i execute_action for '{action_details}': {e}", exc_info=True)
        response_message = "Beklager, der skete en uventet fejl under udførelsen af kommandoen."
    
    return response_message if response_message else "Handlingen blev forsøgt udført."


# --- Hoved Kommando Behandler ---
async def process_input_text(user_input: str) -> str:
    """
    Central funktion til at behandle transskriberet tekst.
    Forsøger først dynamisk kommandohåndtering, derefter NLU-baseret intent.
    """
    if not user_input or user_input.isspace():
        logger.info("Tomt input modtaget.")
        return "Jeg hørte ikke noget. Prøv igen."
    
    logger.info(f"Behandler input: '{user_input}'")
    context_manager.add_interaction(user_input, "", "user_input_received") # Log brugerens input tidligt

    # Initialiser final_response og nlu_result/matched_action for senere logning
    final_response = "Beklager, jeg forstod ikke helt, hvad du mente."
    action_taken = False
    intent_for_log = "unknown" # Default intent for logning
    nlu_result_for_log: Optional[Dict[str, Any]] = None
    matched_action_for_log: Optional[Dict[str, Any]] = None

    # 1. Tjek for forventet respons (f.eks. ja/nej til et tidligere spørgsmål)
    if context_manager.is_awaiting_response():
        expected_type = context_manager.get_expected_response_type()
        metadata = context_manager.get_expected_response_metadata()
        logger.info(f"Input modtaget mens der ventes på respons af type: '{expected_type}' med metadata: {metadata}")
        
        # Simpel ja/nej håndtering for nu
        if expected_type == "yes_no":
            affirmative_responses = ["ja", "jo", "jep", "gerne", "bekræft", "ok", "okay"]
            negative_responses = ["nej", "niks", "afvis", "annuller"]
            
            normalized_input = user_input.lower()
            is_affirmative = any(word in normalized_input for word in affirmative_responses)
            is_negative = any(word in normalized_input for word in negative_responses)

            original_intent = metadata.get("original_intent", "ukendt_kontekst") if metadata else "ukendt_kontekst"
            original_text = metadata.get("original_text", "") # Hent den oprindelige tekst
            
            context_manager.clear_expected_response() # Ryd altid forventningen

            response = "" # Initialiser svar
            intent_for_log = f"clarification_response_{original_intent}" # Log intent for bekræftelse/afvisning

            if is_affirmative and original_intent and original_text:
                # Brugeren bekræftede intentet - gem eksemplet!
                try:
                    # Filstien skal være relativ til projektets rod for utils.py
                    _append_training_example(original_intent, original_text, file_path="data/nlu_training_data.json")
                    response = "Tak! Jeg har gemt det og vil lære af det."
                    logger.info(f"Bruger bekræftede intent '{original_intent}' for tekst '{original_text}'. Eksempel gemt i data/nlu_training_data.json.")
                    
                    # VIGTIGT: Kald _reload_classifier() efter at have gemt nye eksempler,
                    # så den genindlæser den seneste træningsdata. En fuld retræning sker kun dagligt.
                    # Overvej om en umiddelbar mini-retræning er bedre her.
                    # For nu, genindlæs kun data, full train sker dagligt.
                    _reload_classifier() 

                except Exception as e:
                    logger.error(f"Fejl under gemning af træningseksempel med _append_training_example: {e}")
                    response = "Tak for svaret, men der opstod en fejl under forsøget på at gemme eksemplet."
                intent_for_log = f"confirmed_{original_intent}"

            elif is_negative:
                response = f"Okay, jeg annullerer handlingen eller ignorering af '{original_intent}' for nu."
                logger.info(f"Bruger afviste intent '{original_intent}' for tekst '{original_text}'.")
                intent_for_log = f"cancelled_{original_intent}"
            else:
                response = "Jeg forstod ikke dit svar. Prøv igen."
                logger.warning(f"Ugyldigt svar ({user_input}) på forventet ja/nej respons for intent '{original_intent}'.")
                # Overvej at gen-sætte expected_response eller håndtere anderledes
                intent_for_log = "clarification_response_unclear"

            # Gem interaktionen (brugerens svar og Jarvis' respons)
            context_manager.add_interaction(user_input, response, intent_for_log)
            return response
        # Andre expected_types kan tilføjes her

    # 2. Forsøg at matche med dynamiske kommandoer
    if COMMANDS_CONFIG:
        matched_action = find_matching_command(user_input, COMMANDS_CONFIG)
        if matched_action:
            matched_action_for_log = matched_action # Gem til logning
            response_from_action = await execute_action(matched_action)
            if response_from_action:
                final_response = response_from_action
            else:
                # Hvis execute_action ikke returnerer noget specifikt, giv en generel bekræftelse
                final_response = f"Jeg har forsøgt at udføre '{matched_action.get('name', 'kommandoen')}'."
            action_taken = True
            intent_for_log = matched_action.get("name", "dynamic_command")

    # 3. Hvis ingen dynamisk kommando, brug NLU-intent klassifikation
    if not action_taken:
        logger.info("Ingen dynamisk kommando matchede. Forsøger NLU-intent klassifikation...")
        
        # Brug singleton instansen af classifier til analyse
        classifier = _get_classifier_instance()
        nlu_result = classifier.analyze(user_input)
        
        # --- Spørg brugeren ved lav konfidens (Tilføjet) ---
        # Tjek om NLU gav et resultat, intentet ikke er "unknown", og konfidensen er lav
        # Tærskel 0.55 er defineret i NLU classifier, men kan også defineres/bruges her for klarhed
        NLU_CONFIDENCE_THRESHOLD = 0.55 # Matcher tærsklen i classifier.py for nu
        if nlu_result and nlu_result.get("intent") and nlu_result.get("intent") != "unknown" and nlu_result["confidence"] < NLU_CONFIDENCE_THRESHOLD:
            predicted_intent = nlu_result["intent"]
            logger.info(f"Lav NLU konfidens ({nlu_result['confidence']:.2f}) for input '{user_input}'. Foreslår intent '{predicted_intent}'. Spørger brugeren.")
            
            # Stil spørgsmålet til brugeren
            response_to_user = f"Jeg er ikke helt sikker på, hvad du mener. Betød det her '{predicted_intent}'? Svar ja eller nej."
            # Brug stream_speak for at brugeren hører spørgsmålet (hvis muligt i konteksten)
            # Hvis ikke stream_speak er passende (f.eks. i chat interface), send svaret via API/WebSocket
            # I API_server.py håndteres speak_async kaldet efter process_input_text, så vi returnerer bare strengen
            
            # Sæt context_manager til at afvente et ja/nej svar
            context_manager.set_expected_response(
                "yes_no",
                metadata={
                    "original_intent": predicted_intent,
                    "original_text": user_input
                    }
            )
            
            # Gem interaktionen (spørgsmålet til brugeren)
            # Vi gemmer brugerens input og Jarvis' spørgsmål som en del af historikken
            # Dette sker automatisk i API_server efter returnering, men vi logger intent her
            intent_for_log = "clarification_request"
            # context_manager.add_interaction(user_input, response_to_user, intent_for_log) # Undgå dobbelt-logning hvis API_server logger retur-værdi
            
            # Returner spørgsmålet som Jarvis' svar, og vent på næste input
            # API_serveren vil så sende dette tilbage til klienten.
            return response_to_user 

        # --- Fortsæt med normal håndtering hvis konfidens er høj nok eller intent er 'unknown' ---
        # Hvis vi er her, er konfidensen enten høj nok (og != unknown), eller intentet er 'unknown'
        # Den oprindelige logik fortsætter her...

        if nlu_result and nlu_result.get("intent") != "unknown":
            intent = nlu_result["intent"]
            confidence = nlu_result["confidence"]
            logger.info(f"NLU-intent: '{intent}' (Konf.: {confidence:.2f})")

            # Her kan du bruge din eksisterende `handle_legacy_command` eller en ny struktur
            # For nu, et simpelt eksempel:
            if intent == "get_time":
                final_response = f"Klokken er {time.strftime('%H:%M')}."
            elif intent == "get_weather":
                # Dette ville kalde en vejr-funktion
                final_response = "Jeg kan desværre ikke tjekke vejret endnu."
            elif intent == "greeting":
                final_response = "Hej med dig! Hvordan kan jeg hjælpe?"
            elif intent == "goodbye":
                final_response = "Farvel! Hav en god dag."
                # Overvej at tilføje en måde at stoppe Jarvis på her
            else:
                # Brug legacy handler for andre intents, hvis den findes
                try:
                    # CONVERSATION_HISTORY skal nu hentes fra context_manager
                    history_for_legacy = context_manager.get_conversation_history()
                    final_response = await asyncio.to_thread(handle_legacy_command, user_input, history_for_legacy)
                    # handle_legacy_command er muligvis ikke async, så kør i executor
                except NameError:
                    logger.warning(f"handle_legacy_command er ikke defineret, men intent '{intent}' blev fundet.")
                    final_response = f"Jeg genkendte intentet '{intent}', men har ingen handling for det endnu."
            action_taken = True
            intent_for_log = intent
        else:
            logger.info("NLU fandt intet brugbart intent eller konfidens var for lav.")
            intent_for_log = "unknown_nlu"

    # 4. Hvis intet andet virkede (LLM fallback)
    if not action_taken:
        logger.info("Ingen specifik handling eller intent fundet. Prøver LLM-fallback...")
        if 'llm_generate_response' in globals() and llm_available():
            try:
                history_for_llm = context_manager.get_conversation_history()
                final_response = llm_generate_response(user_input, history_for_llm)
                intent_for_log = "llm_fallback"
                action_taken = True
            except Exception as e:  # Denne except hører til try-blokken ovenfor
                logger.error(f"LLM fallback fejlede: {e}")
                final_response = "Beklager, jeg forstod ikke helt, hvad du mente."
        else:
            logger.info("LLM ikke tilgængelig. Giver generisk svar.")
            final_response = "Beklager, jeg forstod ikke helt, hvad du mente."

    # Gem den endelige interaktion i context_manager
    # Vi loggede user_input tidligere, nu opdaterer vi med Jarvis' svar
    # Det er lidt klodset, bedre at gemme når response er endelig.
    # Overvej at flytte context_manager.add_interaction til slutningen af process_command
    # eller have en separat funktion til at opdatere sidste interaktion.
    # For nu: Find sidste user_input og opdater/erstat den.
    history = context_manager.get_conversation_history()
    if history and history[-1]["user"] == user_input and history[-1]["jarvis"] == "":
        history[-1]["jarvis"] = final_response
        history[-1]["intent"] = intent_for_log
        context_manager.current_context["conversation_history"] = history # Direkte opdatering (ikke ideelt)
        context_manager._save_context() # Gem
    else:
        # Hvis der var en fejl, eller flowet var anderledes
        context_manager.add_interaction(user_input, final_response, intent_for_log)

    return final_response


# --- Lytte Loop (Eksempel - skal integreres med LiveVoiceAI) ---
async def continuous_listening_loop():
    """
    Simuleret hovedloop der lytter efter brugerinput.
    Dette skal erstattes/integreres med LiveVoiceAI.
    """
    global ERROR_COUNT
    logger.info("Starter kontinuerlig lytning (simuleret)...")
    await stream_speak("Jarvis er nu aktiv og lytter.", wait_after=True)
    
    # --- Integration med LiveVoiceAI ville se ca. sådan her ud: ---
    # def handle_transcribed_text_from_live_ai(text: str):
    #     logger.info(f"LiveAI transskription: {text}")
    #     # Kør process_input_text asynkront fra denne callback
    #     # Dette kan kræve asyncio.run_coroutine_threadsafe hvis LiveVoiceAI kører i separat tråd
    #     async def process_task(): 
    #         response = await process_input_text(text)
    #         await stream_speak(response)
    #     asyncio.create_task(process_task()) # Eller en mere robust måde at køre det på
    # 
    # live_ai_instance = LiveVoiceAI(on_transcription_result=handle_transcribed_text_from_live_ai)
    # live_ai_instance.start_listening()
    # try:
    #     while True: # Hold hovedtråden i live
    #         await asyncio.sleep(1)
    # except KeyboardInterrupt:
    #     logger.info("Ctrl+C modtaget, stopper LiveVoiceAI...")
    # finally:
    #     live_ai_instance.terminate()
    # --- Slut på LiveVoiceAI integrationseksempel ---

    # Simpel input loop for test uden LiveVoiceAI:
    try:
        while True:
            try:
                # Simuler lydoptagelse og transskription ved at bruge input()
                if CORE_COMPONENTS_MISSING:
                    await asyncio.sleep(5)
                    logger.warning("Kører i begrænset tilstand pga. manglende komponenter.")
                    user_input = await asyncio.to_thread(input, "Du (simuleret input): ") 
                else:
                    # Her ville du typisk vente på callback fra LiveVoiceAI
                    # For nu, brug input() for at simulere
                    # Dette er BLOKERENDE, så ikke godt for en rigtig app
                    # Brug kun til test hvis LiveVoiceAI ikke er integreret.
                    logger.info("Afventer simuleret brugerinput...")
                    user_input = await asyncio.to_thread(input, "Du: ") 
                
                if not user_input.strip():
                    continue

                if user_input.lower() == "stop jarvis":
                    await stream_speak("Okay, jeg lukker ned. Farvel!")
                    break

                response = await process_input_text(user_input)
                await stream_speak(response)
                
                # Simpel pause for at undgå at spamme input prompten
                await asyncio.sleep(0.5)
                
            except (EOFError, KeyboardInterrupt):
                logger.info("Bruger afbrød input.")
                break
            except Exception as e:
                ERROR_COUNT += 1
                logger.error(f"Fejl i hoved-lytteloop: {e}", exc_info=True)
                if ERROR_COUNT >= MAX_ERRORS:
                    logger.critical("For mange fejl i træk. Afslutter Jarvis.")
                    await stream_speak("Jeg har oplevet for mange fejl og må desværre lukke ned.")
                    break
                await stream_speak("Hov, der skete en uventet fejl. Jeg prøver igen.")
                await asyncio.sleep(2) # Vent lidt efter en fejl
    
    finally:
        logger.info("Kontinuerlig lytning (simuleret) stoppet.")

# --- Hovedfunktion --- 
def main():
    if not initialize_jarvis(): # Initialiser Jarvis (indlæs config, modeller etc.)
        logger.critical("Kunne ikke initialisere Jarvis. Afslutter.")
        return
    
    try:
        asyncio.run(continuous_listening_loop())
    except KeyboardInterrupt:
        logger.info("Jarvis afbrudt af bruger (Ctrl+C). Lukker ned...")
    except Exception as e:
        logger.critical(f"Uventet KRITISK fejl i main: {e}", exc_info=True)
    finally:
        logger.info("Jarvis-lite er lukket ned.")
        # Her kan du tilføje yderligere oprydning hvis nødvendigt
        # f.eks. live_ai_instance.terminate() hvis den var global og initialiseret

if __name__ == "__main__":
    main()
