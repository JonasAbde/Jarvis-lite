"""
Tests for NLU (Natural Language Understanding) modulet.
"""

import pytest
from src.nlu import predict, get_available_intents

def test_predict_known_intent():
    """Test at kendte intents bliver korrekt genkendt."""
    intent, conf = predict("hvad er klokken")
    assert intent == "klokken"
    assert conf > 0.55  # Konfidens over tærskelværdi

def test_predict_unknown_intent():
    """Test at ukendte sætninger returnerer 'unknown'."""
    intent, conf = predict("superkalifragilistik")
    assert intent == "unknown"
    assert conf < 0.55  # Konfidens under tærskelværdi

def test_predict_empty_input():
    """Test håndtering af tom input."""
    intent, conf = predict("")
    assert intent == "unknown"
    assert conf == 0.0

def test_get_available_intents():
    """Test at vi kan hente liste over tilgængelige intents."""
    intents = get_available_intents()
    assert isinstance(intents, list)
    assert len(intents) > 0
    assert "klokken" in intents
    assert "youtube" in intents 