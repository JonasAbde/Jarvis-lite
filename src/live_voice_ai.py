\"\"\"
Modul til kontinuerlig lydoptagelse, transskription og videresendelse.
\"\"\"
import pyaudio
import wave
import numpy as np
import threading
import asyncio
import logging
import time
import os
from faster_whisper import WhisperModel
from typing import Callable, Optional, Tuple

logger = logging.getLogger(__name__)

# Konfigurationer (kan flyttes til en central config-fil)
AUDIO_FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # Whisper forventer 16kHz
CHUNK_SIZE = 1024
SILENCE_THRESHOLD = 500  # Juster efter behov
SPEECH_TIMEOUT_SECONDS = 2.0 # Maksimal stilhed efter tale før transskription
MAX_RECORDING_SECONDS = 15 # Maksimal længde af en optagelse
MIN_SPEECH_CHUNKS = 5 # Minimum antal chunks med lyd for at betragte det som tale

# Sti til Whisper-model (download den passende model for dansk)
# Eksempel: \"small\", \"medium\", \"large-v2\", eller en finjusteret modelsti
# For offline brug, download modellen og angiv den lokale sti.
# For nu bruger vi \"tiny\" for hurtig test, men \"small\" eller \"medium\" er bedre for dansk.
MODEL_SIZE = \"tiny\" # Eller \"Systran/faster-whisper-small-da\" hvis du har downloadet den.
# Tjek https://huggingface.co/Systran for danske modeller

class LiveVoiceAI:
    \"\"\"
    Håndterer kontinuerlig lydoptagelse, VAD, transskription med Faster-Whisper,
    og kalder en callback funktion med den transskriberede tekst.
    \"\"\"

    def __init__(self, 
                 on_transcription_result: Callable[[str], None], 
                 model_size: str = MODEL_SIZE,
                 device: str = \"cpu\", 
                 compute_type: str = \"int8\", # \"float16\" for GPU, \"int8\" for CPU
                 language_code: str = \"da\"):
        \"\"\"
        Initialiserer LiveVoiceAI.

        Args:
            on_transcription_result: Callback funktion der kaldes med transskriberet tekst.
            model_size: Størrelsen på Whisper-modellen (f.eks. \"tiny\", \"base\", \"small\", \"medium\").
            device: Enhed til modelinferens (\"cpu\" eller \"cuda\").
            compute_type: Beregningstype (f.eks. \"int8\", \"float16\").
            language_code: Sprogkode for transskription (f.eks. \"da\").
        \"\"\"
        self.on_transcription_result = on_transcription_result
        self.language_code = language_code
        self._pa = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._frames_buffer = []
        self._is_listening = False
        self._listening_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._whisper_model: Optional[WhisperModel] = None
        self._model_size = model_size
        self._device = device
        self._compute_type = compute_type
        
        self._load_whisper_model()

    def _load_whisper_model(self):
        \"\"\"Indlæser Faster-Whisper modellen.\"\"\"
        try:
            logger.info(f\"Indlæser Faster-Whisper model: {self._model_size} på {self._device} med {self._compute_type}\")
            # For at bruge en specifik downloadet model, f.eks. fra Systran:
            # self._whisper_model = WhisperModel(\"Systran/faster-whisper-small-da\", device=self._device, compute_type=self._compute_type)
            self._whisper_model = WhisperModel(self._model_size, device=self._device, compute_type=self._compute_type)
            logger.info(\"Faster-Whisper model indlæst succesfuldt.\")
        except Exception as e:
            logger.error(f\"Fejl under indlæsning af Faster-Whisper model: {e}\")
            logger.error(\"Sørg for at modellen \'{self._model_size}\' er tilgængelig eller at du har angivet en korrekt modelsti.\")
            logger.error(\"For offline brug, download modellen manuelt og placer den i den forventede cache-mappe, eller angiv fuld sti.\")
            # Du kan f.eks. downloade fra Hugging Face: https://huggingface.co/openai/whisper-tiny
            # og så specificere stien til mappen der indeholder model.bin, config.json etc.
            # f.eks. self._whisper_model = WhisperModel(\"path/to/your/downloaded/whisper-tiny\", ...)
            self._whisper_model = None # Sæt til None for at undgå yderligere fejl

    def _process_audio_buffer(self):
        \"\"\"
        Kører i en separat tråd for at behandle den indsamlede lydbuffer.
        Konverterer buffer til WAV-format in-memory og transskriberer.
        \"\"\"
        if not self._frames_buffer or not self._whisper_model:
            self._frames_buffer = [] # Ryd buffer
            return

        audio_data = b'\'.join(self._frames_buffer)
        self._frames_buffer = [] # Ryd buffer for næste optagelse

        # Konverter rå PCM data til en numpy array af float32, som Whisper forventer
        try:
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            if audio_np.size == 0:
                logger.warning(\"Lydbufferen var tom efter konvertering.\")
                return

            logger.info(f\"Starter transskription af {len(audio_np)/RATE:.2f} sekunders lyd...\")
            
            segments, info = self._whisper_model.transcribe(
                audio_np, 
                language=self.language_code,
                beam_size=5, # Juster efter behov
                vad_filter=True, # Brug VAD i Whisper
                vad_parameters=dict(min_silence_duration_ms=700) # Juster VAD parametre
            )
            
            transcribed_text = \"\".join(segment.text for segment in segments).strip()
            
            logger.info(f\"Transskription færdig. Sprog: {info.language} (sandsynlighed: {info.language_probability:.2f})\")
            if transcribed_text:
                logger.info(f\"Transskriberet tekst: \'{transcribed_text}\'\")
                self.on_transcription_result(transcribed_text)
            else:
                logger.info(\"Ingen tekst blev transskriberet (muligvis kun stilhed eller støj).\")

        except Exception as e:
            logger.error(f\"Fejl under transskription: {e}\")
        finally:
            # Sørg for at bufferen er ryddet uanset hvad
            self._frames_buffer = []

    def _audio_input_thread_func(self):
        \"\"\"
        Hovedloop for lydoptagelse i en separat tråd.
        Implementerer simpel Voice Activity Detection (VAD).
        \"\"\"
        try:
            self._stream = self._pa.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            logger.info(\"Lydstream åbnet. Lytter efter tale...\")
        except Exception as e:
            logger.error(f\"Kunne ikke åbne lydstream: {e}. Tjek mikrofonindstillinger.\")
            self._is_listening = False # Stop lytning hvis stream ikke kan åbnes
            self._stop_event.set() # Signalér til hovedtråden at stoppe
            return

        currently_speaking = False
        silence_counter = 0
        speech_chunk_counter = 0
        recording_chunk_counter = 0
        max_silence_chunks = int((SPEECH_TIMEOUT_SECONDS * RATE) / CHUNK_SIZE)
        max_recording_chunks = int((MAX_RECORDING_SECONDS * RATE) / CHUNK_SIZE)

        while not self._stop_event.is_set() and self._is_listening:
            try:
                audio_chunk = self._stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_intensity = np.frombuffer(audio_chunk, dtype=np.int16).max()

                if audio_intensity > SILENCE_THRESHOLD:
                    if not currently_speaking:
                        logger.debug(\"Tale detekteret.\")
                        currently_speaking = True
                        self._frames_buffer = [audio_chunk] # Start ny buffer
                        speech_chunk_counter = 1
                        recording_chunk_counter = 1
                        silence_counter = 0
                    else:
                        self._frames_buffer.append(audio_chunk)
                        speech_chunk_counter += 1
                        recording_chunk_counter += 1
                        silence_counter = 0
                elif currently_speaking:
                    # Bruger taler ikke længere, eller der er en pause
                    self._frames_buffer.append(audio_chunk)
                    recording_chunk_counter += 1
                    silence_counter += 1
                    if silence_counter > max_silence_chunks:
                        logger.debug(f\"Stilhed efter tale ({SPEECH_TIMEOUT_SECONDS}s). Afslutter optagelse.\")
                        if speech_chunk_counter >= MIN_SPEECH_CHUNKS:
                            self._process_audio_buffer() # Behandler den indsamlede lyd
                        else:
                            logger.info(\"Optagelse for kort, ignorerer.\")
                            self._frames_buffer = [] # Ryd buffer
                        currently_speaking = False
                        speech_chunk_counter = 0
                        recording_chunk_counter = 0 
                
                if currently_speaking and recording_chunk_counter >= max_recording_chunks:
                    logger.info(f\"Maksimal optagelsestid ({MAX_RECORDING_SECONDS}s) nået. Behandler lyd.\")
                    if speech_chunk_counter >= MIN_SPEECH_CHUNKS:
                         self._process_audio_buffer()
                    else:
                        logger.info(\"Optagelse for kort ved max tid, ignorerer.\")
                        self._frames_buffer = []
                    currently_speaking = False
                    speech_chunk_counter = 0
                    recording_chunk_counter = 0

            except IOError as e:
                if e.errno == pyaudio.paInputOverflowed:
                    logger.warning(\"Input overflowed. Overvejer at øge CHUNK_SIZE eller tjekke system performance.\")
                else:
                    logger.error(f\"IOError under lydoptagelse: {e}\")
                    # Overvej at genstarte streamen her, eller stoppe helt
                    self._is_listening = False # Stop lytning ved vedvarende fejl
            except Exception as e:
                logger.error(f\"Uventet fejl i lyd-inputtråd: {e}\")
                self._is_listening = False
        
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            logger.info(\"Lydstream lukket.\")
        # Hvis der er noget tilbage i bufferen når vi stopper, og vi har talt nok
        if currently_speaking and speech_chunk_counter >= MIN_SPEECH_CHUNKS:
            logger.info(\"Stopper lytning, behandler resterende lydbuffer...\")
            self._process_audio_buffer()
        else:
             self._frames_buffer = [] # Ryd buffer ved stop

    def start_listening(self):
        \"\"\"Starter den kontinuerlige lytteproces i en separat tråd.\"\"\"
        if not self._whisper_model:
            logger.error(\"Kan ikke starte lytning: Whisper-model er ikke indlæst.\")
            return
        if self._is_listening:
            logger.info(\"Lytter allerede.\")
            return

        self._is_listening = True
        self._stop_event.clear()
        self._listening_thread = threading.Thread(target=self._audio_input_thread_func)
        self._listening_thread.daemon = True # Sørger for at tråden lukker med hovedprogrammet
        self._listening_thread.start()
        logger.info(\"Starter lytning...\")

    def stop_listening(self):
        \"\"\"Stopper den kontinuerlige lytteproces.\"\"\"
        if not self._is_listening:
            logger.info(\"Lytning er ikke aktiv.\")
            return

        logger.info(\"Stopper lytning...\")
        self._is_listening = False
        self._stop_event.set()
        if self._listening_thread and self._listening_thread.is_alive():
            self._listening_thread.join(timeout=SPEECH_TIMEOUT_SECONDS + 2) # Giv tid til at afslutte
        if self._listening_thread and self._listening_thread.is_alive():
            logger.warning(\"Lytte-tråd afsluttede ikke korrekt.\")
        self._listening_thread = None
        logger.info(\"Lytning stoppet.\")

    def terminate(self):
        \"\"\"Frigør ressourcer (PyAudio). Skal kaldes ved afslutning.\"\"\"
        self.stop_listening() # Sørg for at lytning er stoppet
        self._pa.terminate()
        logger.info(\"PyAudio termineret.\")

# Eksempel på brug:
def handle_transcription(text: str):
    print(f\"[Jarvis Modtog]: {text}\")
    # Her ville du sende teksten til din NLU/kommandobehandler
    # f.eks. matched_command = command_parser.find_matching_command(text, loaded_commands)
    # if matched_command: ...

if __name__ == \"__main__\":
    # Sørg for at loggeren er konfigureret
    logging.basicConfig(
        level=logging.DEBUG, # Sæt til INFO for mindre output
        format=\"%(asctime)s - %(name)s - %(levelname)s - %(threadName)s - %(message)s\"
    )
    
    # Opret en dummy on_transcription_result for test
    def my_transcription_handler(text: str):
        logger.info(f\"Hovedprogram modtog transskription: {text}\")
        # Her kan du integrere med command_parser eller anden logik

    # Opret LiveVoiceAI instans
    # For CPU: compute_type=\"int8\". For GPU: compute_type=\"float16\" (eller \"int8_float16\")
    # Vælg passende modelstørrelse. \"tiny\" er hurtigst, men mindst præcis.
    # \"small\" eller \"medium\" er gode kompromiser for dansk.
    # Hvis du har en kraftig GPU, kan du prøve \"large-v2\".
    live_ai = LiveVoiceAI(on_transcription_result=my_transcription_handler, 
                          model_size=\"tiny\", # Skift til \"small\" eller \"medium\" for bedre dansk
                          device=\"cpu\", 
                          compute_type=\"int8\")

    if not live_ai._whisper_model:
        logger.error(\"Whisper modellen blev ikke indlæst. Afslutter demo.\")
        exit()

    try:
        live_ai.start_listening()
        print(\"Jarvis lytter... Tryk Ctrl+C for at stoppe.\")
        # Hold hovedtråden i live, mens lytte-tråden kører
        while True:
            time.sleep(0.5) 
    except KeyboardInterrupt:
        print(\"\\nCtrl+C modtaget. Lukker Jarvis-lite live demo...\")
    finally:
        live_ai.terminate()
        print(\"LiveVoiceAI termineret. Farvel!\")

    # For at køre dette eksempel:
    # 1. Installer nødvendige pakker:
    #    pip install faster-whisper pyaudio numpy
    #    (For GPU support med CUDA, se Faster-Whisper dokumentationen for yderligere drivere/biblioteker)
    # 2. Download en Whisper model (f.eks. \"tiny\"). Faster-Whisper vil forsøge at downloade den automatisk første gang.
    #    Hvis automatisk download fejler, download manuelt fra Hugging Face (f.eks. openai/whisper-tiny) og
    #    placer model-filerne (config.json, model.bin, tokenizer.json, vocabulary.txt) i en mappe.
    #    Opdater så `MODEL_SIZE` til stien til denne mappe i koden, eller sørg for at den ligger i
    #    standard Hugging Face cache stien (typisk ~/.cache/huggingface/hub/models--openai--whisper-tiny/snapshots/...).
    # 3. Kør: python src/live_voice_ai.py
    #    Du skal muligvis justere SILENCE_THRESHOLD og SPEECH_TIMEOUT_SECONDS afhængigt af din mikrofon og omgivelser. 