"""
Integration tests for Jarvis-lite.
"""

import pytest
import asyncio
from pathlib import Path
from src.nlu import predict
from src.jarvis_commands import COMMANDS
from src.jarvis_main import transcribe_audio, speak

# Test data
TEST_AUDIO = Path("tests/data/test_audio.wav")
TEST_COMMANDS = [
    "hvad er klokken",
    "åbn youtube",
    "fortæl en joke",
    "gem en note"
]

@pytest.mark.asyncio
async def test_stt_tts_pipeline():
    """Test hele STT -> NLU -> TTS pipeline."""
    # Simuler lydoptagelse
    if not TEST_AUDIO.exists():
        pytest.skip("Test audio file not found")
    
    # Test STT
    text = await transcribe_audio(str(TEST_AUDIO))
    assert text is not None
    assert isinstance(text, str)
    
    # Test NLU
    intent, conf = predict(text)
    assert intent in COMMANDS or intent == "unknown"
    assert 0 <= conf <= 1
    
    # Test TTS
    if intent in COMMANDS:
        response = COMMANDS[intent]()
        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_command_execution():
    """Test udførelse af kommandoer."""
    for cmd in TEST_COMMANDS:
        intent, conf = predict(cmd)
        if conf >= 0.55:  # Kun test kommandoer med høj konfidens
            response = COMMANDS[intent]()
            assert isinstance(response, str)
            assert len(response) > 0

def test_nlu_confidence():
    """Test NLU konfidens-niveauer."""
    # Test kendt intent
    intent, conf = predict("hvad er klokken")
    assert intent == "klokken"
    assert conf >= 0.55
    
    # Test ukendt intent
    intent, conf = predict("superkalifragilistik")
    assert intent == "unknown"
    assert conf < 0.55

@pytest.mark.asyncio
async def test_error_handling():
    """Test fejlhåndtering."""
    # Test med ikke-eksisterende lydfil
    text = await transcribe_audio("nonexistent.wav")
    assert text is None
    
    # Test med tom streng
    intent, conf = predict("")
    assert intent == "unknown"
    assert conf == 0.0 