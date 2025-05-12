#!/usr/bin/env python3
"""
Test af forskellige stemmer i Jarvis Lite
"""
import os
import asyncio
import sys
import logging

# Tilføj src til Python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
if src_path not in sys.path:
    sys.path.append(src_path)

# Konfigurer logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

from src.audio import get_available_voices, set_voice, speak_async, stream_speak

async def main():
    """Hovedfunktion til at teste stemmer"""
    # Hent tilgængelige stemmer
    voices = get_available_voices()
    print(f"Fandt {len(voices)} stemmer:")
    
    for i, voice in enumerate(voices):
        print(f"{i+1}. {voice['name']} (ID: {voice['id']}, Engine: {voice['engine']})")
    
    print("\nTester standard gTTS stemme...")
    await speak_async("Hej, jeg er Jarvis med standard Google TTS stemme.")
    
    # Test hver brugerdefineret stemme
    custom_voices = [v for v in voices if v['id'] != 'default']
    if custom_voices:
        print(f"\nTester {len(custom_voices)} brugerdefinerede stemmer...")
        
        for voice in custom_voices:
            print(f"\nTester {voice['name']} stemme...")
            set_voice(voice['id'])
            await speak_async(f"Hej, jeg er Jarvis med {voice['name']} stemmen.")
            
            # Test mere kompleks tekst med streaming
            complex_text = "Dette er en test af Jarvis stemmesystemet. Jeg kan læse lange tekster op ved at dele dem i mindre sætninger. Fungerer det godt? Det håber jeg!"
            print("\nTester stream_speak med samme stemme...")
            await stream_speak(complex_text)
    else:
        print("\nIngen brugerdefinerede stemmer fundet.")
    
    print("\nStemmetest færdig!")

if __name__ == "__main__":
    asyncio.run(main()) 