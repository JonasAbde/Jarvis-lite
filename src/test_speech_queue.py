#!/usr/bin/env python3
"""
Test af Jarvis Lite lydafspilnings-kø
"""

import asyncio
import os
import sys
import logging

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tilføj src-mappen til Python's sys.path så imports virker korrekt
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Opret nødvendige mapper
os.makedirs("cache/tts", exist_ok=True)

# Import audio moduler
from audio.speech import speak_async, stream_speak

async def test_overlapping_speech():
    """Test af overlappende tale - Jarvis skal nu vente med ny tale indtil forrige er færdig"""
    print("\n=== TEST: Overlappende tale ===")
    print("Tester at tale ikke overlapper hinanden...")
    
    # Prøv at få Jarvis til at sige flere korte sætninger hurtigt
    sentences = [
        "Dette er den første sætning.",
        "Dette er den anden.",
        "Dette er den tredje sætning som kommer straks efter.",
        "Til sidst kommer denne fjerde sætning, som bør komme efter den tredje.",
    ]
    
    # Start alle taleafsplinger samtidig, men køsystemet bør sikre sekventiel afspilning
    print("Sender alle sætninger samtidig, men kø-systemet bør håndtere dem sekventielt:")
    
    # Opret tasks for alle sætninger
    tasks = []
    for sentence in sentences:
        task = asyncio.create_task(speak_async(sentence))
        tasks.append(task)
    
    # Vent på at alle er færdige
    await asyncio.gather(*tasks)
    
    print("Test gennemført! Sætningerne bør være afspillet i rækkefølge uden overlap.")

async def test_streaming_speech():
    """Test af stream_speak funktionaliteten"""
    print("\n=== TEST: Streaming tale ===")
    print("Tester at streaming-tale afspiller sætninger i rækkefølge med pauser...")
    
    # Lang tekst med flere sætninger
    lang_tekst = (
        "Dette er en test af streaming-tale. "
        "Denne funktion bør opdele talen i sætninger. "
        "Mellem hver sætning bør der være en naturlig pause. "
        "Dette gør Jarvis' tale mere naturlig og behagelig at lytte til. "
        "Vil du køre flere tests efter denne?"
    )
    
    print(f"Stream-speak af lang tekst: '{lang_tekst}'")
    await stream_speak(lang_tekst)
    
    print("Test gennemført!")

async def main():
    """Hovedfunktion"""
    print("=== JARVIS LITE SPEECH QUEUE TEST ===")
    print("Tester den nye lydafspilnings-kø funktion")
    
    try:
        # Test overlappende tale
        await test_overlapping_speech()
        
        # Kort pause
        await asyncio.sleep(1)
        
        # Test streaming-tale
        await test_streaming_speech()
        
    except Exception as e:
        logger.error(f"Fejl i test: {e}")
    
    print("\n=== TEST AFSLUTTET ===")

if __name__ == "__main__":
    # Kør test
    asyncio.run(main()) 