#!/usr/bin/env python3
"""
Test af NLU-modulet for Jarvis Lite.
"""

import os
import sys
import unittest
import logging
from pathlib import Path

# Tilføj src-mappen til Python-stien
sys.path.insert(0, str(Path(__file__).parent.parent))

# Deaktiver logging under tests
logging.disable(logging.CRITICAL)

class TestNLU(unittest.TestCase):
    """Test af NLU-funktionalitet"""
    
    def setUp(self):
        """Kør før hver test"""
        # Træn en model hvis den ikke findes endnu
        from src.nlu.training.train_classifier import train_classifier, save_model, MODEL_PATH
        if not os.path.exists(MODEL_PATH):
            print(f"Træner test-model til {MODEL_PATH}")
            vectorizer, classifier, intents = train_classifier()
            save_model(vectorizer, classifier, intents)
    
    def test_predict_intent(self):
        """Test af intent-klassifikation"""
        from src.nlu import predict
        
        # Test med høj konfidens
        intent, confidence = predict("hvad er klokken")
        self.assertEqual(intent, "get_time")
        self.assertGreater(confidence, 0.5)
        
        intent, confidence = predict("fortæl mig en joke")
        self.assertEqual(intent, "tell_joke")
        self.assertGreater(confidence, 0.5)
        
        # Test med lav konfidens
        intent, confidence = predict("xyzabc123")
        self.assertEqual(intent, "unknown")
        
    def test_analyze(self):
        """Test af tekstanalyse med entities"""
        from src.nlu import analyze
        
        # Test med entitetsudtrækning
        result = analyze("åbn youtube")
        self.assertEqual(result["intent"], "open_website")
        self.assertEqual(result["entities"].get("site"), "youtube")
        
        result = analyze("gem en note husk at købe mælk")
        self.assertEqual(result["intent"], "save_note")
        self.assertIn("text", result["entities"])
        
    def test_get_intents(self):
        """Test af tilgængelige intents"""
        from src.nlu import get_available_intents
        
        intents = get_available_intents()
        self.assertIsInstance(intents, list)
        self.assertGreater(len(intents), 0)
        
        # Tjek for forventede intents
        expected_intents = ["get_time", "get_date", "tell_joke"]
        for intent in expected_intents:
            self.assertIn(intent, intents)

if __name__ == "__main__":
    unittest.main() 