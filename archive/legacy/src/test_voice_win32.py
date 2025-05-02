from jarvis_voice_win32 import JarvisVoiceWin32
import time
import logging

# Set up logging to show more details
logging.basicConfig(level=logging.INFO)

def test_voices():
    print("Testing JarvisVoiceWin32...")
    
    # Initialize with Helle voice
    voice = JarvisVoiceWin32(preferred_voice="Microsoft Helle")
    
    # List available voices
    print("\nAvailable voices:")
    voices = voice.list_voices()
    for v in voices:
        print(f"- {v['name']} (ID: {v['id']})")
    
    # Test basic speech
    print("\nTesting basic speech...")
    voice.speak("Hej, jeg er Jarvis. Dette er en test af dansk tale.")
    
    # Test different rates
    print("\nTesting different speech rates...")
    voice.set_voice_properties(rate=-5)  # Slower
    voice.speak("Nu taler jeg lidt langsommere")
    
    voice.set_voice_properties(rate=5)  # Faster
    voice.speak("Og nu taler jeg lidt hurtigere")
    
    # Test async speech
    print("\nTesting asynchronous speech...")
    voice.speak_async("Dette er asynkron tale")
    time.sleep(2)  # Wait a bit while the async speech happens
    
    # Reset rate
    voice.set_voice_properties(rate=0)
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_voices() 