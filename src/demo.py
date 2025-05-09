#!/usr/bin/env python3
"""
Jarvis Lite Demo - Simulerer funktionaliteten uden eksterne afhængigheder.
"""

import os
import logging
import asyncio
import datetime
import random
import time
import json
from typing import Optional, Dict, List, Any

# Konfigurer logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jarvis_demo.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Demo-versioner af kernefunktionerne
async def speak_async(text: str) -> None:
    """Simuleret tekst-til-tale"""
    logger.info(f"Jarvis siger: {text}")
    print(f"🔊 Jarvis: {text}")
    # Simuler tid det tager at udtale teksten (ca. 100 ms per ord)
    words = len(text.split())
    await asyncio.sleep(max(1, words * 0.1))

async def record_audio_async() -> Optional[str]:
    """Simuleret lydoptagelse"""
    logger.info("Lytter efter brugerens tale...")
    print("🎤 Lytter...")
    # Simuler optagetid
    await asyncio.sleep(1.5)
    return "demo_audio.wav"

async def transcribe_audio_async(audio_file: str) -> Optional[str]:
    """Simuleret tale-til-tekst"""
    # Liste over demo-kommandoer der "genkendes" tilfældigt
    demo_commands = [
        "hej jarvis",
        "hvad kan du hjælpe mig med",
        "hvad er klokken",
        "hvilken dag er det i dag",
        "fortæl mig en joke",
        "hvem er du",
        "tak for hjælpen"
    ]
    # Vælg en tilfældig kommando
    command = random.choice(demo_commands)
    logger.info(f"Genkender: '{command}'")
    return command

def handle_command(command: str) -> str:
    """Simpel kommandohåndtering"""
    command = command.strip().lower()
    
    if "hej" in command:
        return "Hej! Hvordan kan jeg hjælpe dig i dag?"
    
    elif "hvad kan du" in command:
        return "Jeg kan fortælle dig klokken, datoen, fortælle jokes, og besvare simple spørgsmål. Hvad kan jeg hjælpe med?"
    
    elif "klokken" in command:
        now = datetime.datetime.now()
        return f"Klokken er {now.hour}:{now.minute:02d}"
    
    elif "dag" in command:
        now = datetime.datetime.now()
        return f"I dag er det {now.strftime('%d. %B %Y')}"
    
    elif "joke" in command:
        jokes = [
            "Hvorfor gik computeren til lægen? Den havde en virus!",
            "Hvad kalder man en gruppe musikalske hvaler? Et orkester!",
            "Hvorfor kunne skelettet ikke gå til festen? Det havde ingen krop at gå med!"
        ]
        return random.choice(jokes)
    
    elif "hvem er du" in command:
        return "Jeg er Jarvis, en dansk AI-assistent. Jeg er designet til at hjælpe dig med forskellige opgaver og information."
    
    elif "tak" in command:
        return "Det var så lidt! Er der andet, jeg kan hjælpe med?"
    
    else:
        fallback_responses = [
            "Det forstod jeg ikke helt. Kan du omformulere det?",
            "Jeg er ikke sikker på, hvordan jeg skal svare på det. Kan du prøve at spørge på en anden måde?",
            "Det har jeg ikke et godt svar på lige nu. Er der noget andet, jeg kan hjælpe med?"
        ]
        return random.choice(fallback_responses)

async def main_loop() -> None:
    """Hovedloop for demo-versionen"""
    logger.info("Jarvis Demo starter...")
    
    # Velkomstbesked
    await speak_async("Jarvis Demo er klar. Jeg lytter nu efter kommandoer.")
    
    # Simuler kontinuerlig lytning
    try:
        for _ in range(10):  # Kør 10 runder med demo-kommandoer
            # Simuler optagelse
            audio_file = await record_audio_async()
            
            if audio_file:
                # Simuler genkendt tale
                user_input = await transcribe_audio_async(audio_file)
                
                if user_input:
                    print(f"👤 Bruger: {user_input}")
                    
                    # Behandl kommandoen
                    response = handle_command(user_input)
                    
                    # Giv svar
                    await speak_async(response)
            
            # Pause mellem iterations
            await asyncio.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("Demo afbrudt af bruger")
    except Exception as e:
        logger.error(f"Fejl i demo: {e}")
    finally:
        await speak_async("Jarvis Demo afsluttes. Tak for i dag!")

def main() -> None:
    """Starter demo-programmet"""
    try:
        # Kør asynkront hovedloop
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        print("\nDemo afbrudt af bruger. Afslutter...")
    finally:
        print("Jarvis Demo er afsluttet.")

if __name__ == "__main__":
    main() 