from src.jarvis_voice import JarvisVoice

def test_voices():
    """Test forskellige stemmer og vis information"""
    
    print("🎯 Test af Jarvis Lite stemme-system")
    print("=====================================")
    
    # Test med standard stemme (Helle)
    print("\n1. Test med standard dansk stemme:")
    voice = JarvisVoice()
    print(f"Aktiv stemme: {voice.get_current_voice()}")
    voice.speak("Hej, jeg er Jarvis Lite med standard stemme!")
    
    # Test med specifik stemme
    print("\n2. Test med specifik stemme (Microsoft Helle):")
    voice.speak("Nu prøver jeg at tale med Helle stemmen!", "helle")
    
    # Test med engelsk fallback
    print("\n3. Test med engelsk fallback:")
    voice.speak("Dette er en test af engelsk fallback stemme", "english")
    
    print("\nTest afsluttet! ✨")

if __name__ == "__main__":
    test_voices() 