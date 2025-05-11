#!/usr/bin/env python3
"""
Demo af Jarvis Lite Context Manager og Stream Speak funktionalitet
"""

import os
import sys
import asyncio
import logging

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Tilføj src-mappen til Python's sys.path så imports virker korrekt
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import moduler
from context_manager import ContextManager
from audio.speech import stream_speak, speak_async

async def demo_context_manager():
    """Demonstrerer Context Manager funktionalitet"""
    print("\n=== DEMO: Context Manager ===\n")
    
    # Opret Context Manager med midlertidig fil
    context_file = "data/demo_context.json"
    cm = ContextManager(context_file)
    
    # Simuler en samtale
    print("Simulerer en samtale med kontekstsporing...")
    
    # Bruger spørger om vejret
    user_input = "hvordan bliver vejret i morgen?"
    print(f"Bruger: {user_input}")
    
    # Jarvis svarer
    response = "I morgen bliver det solrigt med temperaturer mellem 18-22 grader og let vind fra vest."
    print(f"Jarvis: {response}")
    
    # Gem i kontekstmanager
    cm.add_interaction(user_input, response, "get_weather", 0.85)
    await stream_speak(response)
    
    # Simuler en opfølgningsspørgsmål
    followup = "hvad med i weekenden?"
    print(f"Bruger: {followup}")
    
    # Jarvis svarer med kontekstforståelse
    followup_response = "I weekenden falder temperaturerne til omkring 15-18 grader, og der kommer spredte byger lørdag eftermiddag."
    print(f"Jarvis: {followup_response}")
    
    # Gem i kontekstmanager
    cm.add_interaction(followup, followup_response, "get_weather", 0.75)
    await stream_speak(followup_response)
    
    # Vis kontekstinformation
    print("\nSamtalehistorik gemt i kontekstmanager:")
    for idx, interaction in enumerate(cm.get_conversation_history()):
        print(f"{idx+1}. Bruger: '{interaction['user']}'")
        print(f"   Jarvis: '{interaction['jarvis']}'")
        print(f"   Intent: {interaction['intent']} (konfidens: {interaction['confidence']})")
        print()
    
    # Ryddet op
    if os.path.exists(context_file):
        os.remove(context_file)
        print(f"Demo-kontekst fil slettet: {context_file}")

async def demo_yes_no_interaction():
    """Demonstrerer håndtering af ja/nej spørgsmål"""
    print("\n=== DEMO: Ja/Nej Spørgsmål ===\n")
    
    # Opret Context Manager
    cm = ContextManager("data/demo_yes_no.json")
    
    # Bruger vil gemme en note
    user_input = "gem en note om at jeg skal købe mælk"
    print(f"Bruger: {user_input}")
    
    # Jarvis bekræfter og spørger
    response = "Jeg har oprettet en note: 'købe mælk'. Vil du gemme den?"
    print(f"Jarvis: {response}")
    
    # Gem i kontekstmanager og sæt forventning om ja/nej svar
    cm.add_interaction(user_input, response, "save_note", 0.92)
    cm.set_expected_response("yes_no", {
        "context_name": "note_taking",
        "note_text": "købe mælk"
    })
    await stream_speak(response)
    
    # Simuler brugerens "ja" svar
    yes_input = "ja, gem den"
    print(f"Bruger: {yes_input}")
    
    # Håndter ja-svar
    if cm.is_awaiting_response():
        expected_type = cm.get_expected_response_type()
        metadata = cm.get_expected_response_metadata()
        
        print(f"System detekterede forventning af type: {expected_type}")
        print(f"Metadata: {metadata}")
        
        # Nulstil forventning
        cm.clear_expected_response()
        
        # Jarvis bekræfter
        yes_response = "Jeg har gemt noten 'købe mælk'. Er der andet, jeg kan hjælpe med?"
        print(f"Jarvis: {yes_response}")
        
        cm.add_interaction(yes_input, yes_response, "confirmation", 0.95)
        await stream_speak(yes_response)
    
    # Ryd op
    if os.path.exists("data/demo_yes_no.json"):
        os.remove("data/demo_yes_no.json")
        print("Demo-fil slettet")

async def demo_streaming_speech():
    """Demonstrerer streaming tale med pauser"""
    print("\n=== DEMO: Streaming Tale ===\n")
    
    # Kort svar
    kort_svar = "Ja, selvfølgelig!"
    print(f"Kort svar: '{kort_svar}'")
    await stream_speak(kort_svar)
    await asyncio.sleep(1)
    
    # Mellemlangt svar
    mellem_svar = "Det bliver solrigt i morgen med temperaturer omkring 20 grader."
    print(f"Mellemlangt svar: '{mellem_svar}'")
    await stream_speak(mellem_svar)
    await asyncio.sleep(1)
    
    # Langt svar med flere sætninger
    langt_svar = "Jeg har fundet flere oplysninger om emnet. Danmarks hovedstad er København. Den har ca. 1,3 millioner indbyggere i storbyområdet. København blev grundlagt i 1167 af biskop Absalon. Byen er kendt for Tivoli, Den Lille Havfrue og hygge."
    print(f"Langt svar: '{langt_svar}'")
    await stream_speak(langt_svar)
    await asyncio.sleep(1)
    
    # Svar med spørgsmål
    spørgsmål = "Jeg kan hjælpe dig med at finde vejrudsigten. Vil du have vejret for i dag eller for hele ugen?"
    print(f"Svar med spørgsmål: '{spørgsmål}'")
    await stream_speak(spørgsmål)

async def main():
    """Hovedfunktion"""
    print("=== JARVIS LITE DEMO ===")
    print("Demonstrerer nye funktioner i Jarvis Lite")
    
    # Opret nødvendige mapper
    os.makedirs(os.path.join("data"), exist_ok=True)
    os.makedirs(os.path.join("src", "cache", "tts"), exist_ok=True)
    
    try:
        # Demo af Context Manager
        await demo_context_manager()
        
        # Demo af ja/nej interaktion
        await demo_yes_no_interaction()
        
        # Demo af streaming tale
        await demo_streaming_speech()
        
    except Exception as e:
        logger.error(f"Fejl i demo: {e}")
    
    print("\n=== DEMO AFSLUTTET ===")

if __name__ == "__main__":
    # Kør demo
    asyncio.run(main()) 