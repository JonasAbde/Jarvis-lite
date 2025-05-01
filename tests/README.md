# Tests for Jarvis Lite 🧪

Dette er test-suiten for Jarvis Lite. Her kan du teste om alle funktioner virker som de skal!

## 📋 Hvordan kører jeg testene?

1. Åbn en terminal/kommandoprompt
2. Naviger til projektets rodmappe
3. Kør følgende kommando:

```bash
python -m unittest tests/test_jarvis_core.py -v
```

## 🔍 Hvad tester vi?

Vi tester følgende funktioner i `jarvis_core.py`:

- `get_time()`: Tjekker om tiden returneres i korrekt format
- `save_note()`: Tjekker om noter kan gemmes korrekt
- `read_notes()`: Tjekker om gemte noter kan læses
- `motivate()`: Tjekker om motiverende beskeder returneres korrekt

## 💡 Tips til testning

- Hver test starter med en ren notes.txt fil
- Efter hver test ryddes notes.txt op
- Du kan se detaljerede testresultater med `-v` flagget
- Hvis en test fejler, får du en besked om hvorfor

## 🚀 Eksempel på test output

```
test_get_time (tests.test_jarvis_core.TestJarvisCore) ... ok
test_motivate (tests.test_jarvis_core.TestJarvisCore) ... ok
test_read_notes (tests.test_jarvis_core.TestJarvisCore) ... ok
test_save_note (tests.test_jarvis_core.TestJarvisCore) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.001s

OK
```

## 📝 Tilføj flere tests

Hvis du vil tilføje flere tests:
1. Åbn `test_jarvis_core.py`
2. Tilføj en ny test metode med `def test_navn(self):`
3. Brug `self.assertTrue()` eller andre assert metoder til at teste
4. Kør testene igen for at se om de virker 