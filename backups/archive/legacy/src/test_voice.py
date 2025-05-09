from jarvis_voice import JarvisVoice
import asyncio
import logging

# Set up logging to show more details
logging.basicConfig(level=logging.INFO)

def test_sync():
    print("Testing synchronous speech...")
    # Try to initialize with Helle voice
    voice = JarvisVoice(preferred_voice="helle")
    
    # List available voices
    print("\nAvailable voices:")
    voices = voice.list_voices()
    for v in voices:
        print(f"- {v['name']} ({v['languages']})")
        print(f"  ID: {v['id']}")
    
    current_voice = voice.get_current_voice()
    if current_voice:
        print(f"\nCurrent voice: {current_voice['name']}")
    
    # Test basic speech
    print("\nTesting basic speech...")
    voice.speak("Hej, jeg er Jarvis. Dette er en test af dansk tale.")
    
    # Test voice properties
    print("\nTesting different speech rates...")
    voice.set_voice_properties(rate=120)
    voice.speak("Nu taler jeg lidt langsommere")
    
    voice.set_voice_properties(rate=180)
    voice.speak("Og nu taler jeg lidt hurtigere")
    
    # Reset rate
    voice.set_voice_properties(rate=150)

async def test_async():
    print("\nTesting asynchronous speech...")
    voice = JarvisVoice(preferred_voice="helle")
    await voice.speak_async("Dette er en test af asynkron tale")
    print("Async test completed")

if __name__ == "__main__":
    # Run sync tests
    test_sync()
    
    # Run async tests
    asyncio.run(test_async())
    
    print("\nAll tests completed!") 