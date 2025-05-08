import unittest
import os
import datetime
from src.jarvis_core import JarvisCore

class TestJarvisCore(unittest.TestCase):
    """Test klasse for JarvisCore funktionaliteter"""
    
    def setUp(self):
        """Kør før hver test - opretter en ny JarvisCore instans"""
        self.jarvis = JarvisCore()
        # Sikrer at vi har en ren notes.txt fil til test
        if os.path.exists(self.jarvis.notes_file):
            os.remove(self.jarvis.notes_file)
    
    def tearDown(self):
        """Kør efter hver test - rydder op"""
        if os.path.exists(self.jarvis.notes_file):
            os.remove(self.jarvis.notes_file)
    
    def test_get_time(self):
        """Test om get_time() returnerer en gyldig tid streng"""
        time_str = self.jarvis.get_time()
        # Tjek om strengen starter med "Klokken er"
        self.assertTrue(time_str.startswith("Klokken er"))
        # Tjek om strengen indeholder et tidspunkt i formatet HH:MM
        self.assertRegex(time_str, r"Klokken er \d{2}:\d{2}")
    
    def test_save_note(self):
        """Test om save_note() kan gemme en note korrekt"""
        test_note = "Dette er en test note"
        # Gem note
        self.assertTrue(self.jarvis.save_note(test_note))
        # Tjek om filen eksisterer
        self.assertTrue(os.path.exists(self.jarvis.notes_file))
        # Læs filen og tjek indhold
        with open(self.jarvis.notes_file, "r", encoding="utf-8") as file:
            content = file.read()
            self.assertIn(test_note, content)
    
    def test_read_notes(self):
        """Test om read_notes() kan læse gemte noter"""
        test_notes = ["Note 1", "Note 2", "Note 3"]
        # Gem flere noter
        for note in test_notes:
            self.jarvis.save_note(note)
        # Læs noter
        notes = self.jarvis.read_notes()
        # Tjek om alle noter er blevet læst
        for note in test_notes:
            self.assertTrue(any(note in n for n in notes))
    
    def test_motivate(self):
        """Test om motivate() returnerer en gyldig motiverende besked"""
        motivation = self.jarvis.motivate()
        # Tjek om beskeden ikke er tom
        self.assertTrue(len(motivation) > 0)
        # Tjek om beskeden indeholder et emoji
        self.assertTrue(any(char in motivation for char in "💪🚀🌟😊🌈"))

if __name__ == '__main__':
    unittest.main() 