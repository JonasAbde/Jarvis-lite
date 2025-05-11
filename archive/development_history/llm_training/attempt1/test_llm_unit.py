#!/usr/bin/env python3
"""
Test af LLM-modulet for Jarvis Lite.
Tester Microsoft Phi-2 model integration.
"""

import pytest
from src.llm.model import load_model, generate_response, is_model_available

def test_model_loading():
    """Test at modellen kan indlæses korrekt"""
    # Test model indlæsning
    assert load_model() == True
    assert is_model_available() == True

def test_response_generation():
    """Test at modellen kan generere svar"""
    # Sikr at modellen er indlæst
    if not is_model_available():
        load_model()
    
    # Test simpel forespørgsel
    messages = [{"role": "user", "content": "Hvad er hovedstaden i Danmark?"}]
    response = generate_response(messages)
    assert isinstance(response, str)
    assert len(response) > 0
    assert "København" in response.lower()

def test_conversation_context():
    """Test at modellen kan håndtere samtalekontekst"""
    if not is_model_available():
        load_model()
    
    # Test samtale med kontekst
    messages = [
        {"role": "user", "content": "Hvad er hovedstaden i Danmark?"},
        {"role": "assistant", "content": "Hovedstaden i Danmark er København."},
        {"role": "user", "content": "Hvor mange indbyggere har den?"}
    ]
    response = generate_response(messages)
    assert isinstance(response, str)
    assert len(response) > 0
    # Svaret bør indeholde et tal (indbyggertal)
    assert any(char.isdigit() for char in response)

def test_generation_parameters():
    """Test forskellige generationsparametre"""
    if not is_model_available():
        load_model()
    
    messages = [{"role": "user", "content": "Skriv et kort digt."}]
    
    # Test med forskellige temperaturer
    response_creative = generate_response(messages, temperature=0.9)
    response_focused = generate_response(messages, temperature=0.3)
    assert len(response_creative) > 0
    assert len(response_focused) > 0
    assert response_creative != response_focused

def test_error_handling():
    """Test fejlhåndtering"""
    # Test med tom beskedliste
    messages = []
    response = generate_response(messages)
    assert isinstance(response, str)
    assert "fejl" in response.lower() or "beklager" in response.lower()
    
    # Test med ugyldig beskedformat
    invalid_messages = [{"invalid": "format"}]
    response = generate_response(invalid_messages)
    assert isinstance(response, str)
    assert "fejl" in response.lower() or "beklager" in response.lower()

if __name__ == "__main__":
    pytest.main([__file__]) 