# Tekst-til-tale modul

import pyttsx3
import logging

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self):
        try:
            self.engine = pyttsx3.init()
            # Optional: Konfigurer stemme, rate, volumen her
            # voices = self.engine.getProperty('voices')
            # self.engine.setProperty('voice', voices[0].id) # Vælg en stemme
            # self.engine.setProperty('rate', 150) # Taletempo
            # self.engine.setProperty('volume', 0.9) # Volumen (0.0 til 1.0)
            logger.info("pyttsx3 TTS engine initialiseret.")
        except Exception as e:
            logger.error(f"Kunne ikke initialisere pyttsx3: {e}")
            self.engine = None

    def speak(self, text):
        if self.engine and text:
            try:
                logger.info(f"TTS taler: '{text}'")
                self.engine.say(text)
                self.engine.runAndWait() # Blokker indtil tale er færdig
            except Exception as e:
                logger.error(f"Fejl under afspilning af tale: {e}")
        elif not self.engine:
            logger.warning("TTS engine ikke initialiseret, kan ikke tale.")
