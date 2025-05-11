# Jarvis Lite Kildekode

Dette er hovedmappen for Jarvis Lite kildekoden. Her er en oversigt over de vigtigste filer og mapper:

## Hovedfiler
- `jarvis.py` - Hovedprogrammet der samler alle moduler
- `demo.py` - Demonstrationsversion der kan køre uden afhængigheder
- `__init__.py` - Pakkeinitialisering

## Mapper
- `audio/` - Tale-til-tekst (STT) og tekst-til-tale (TTS) funktioner
- `llm/` - Integration med sprogmodeller (Large Language Models)
- `commands/` - Håndtering af brugerkommandoer
- `nlu/` - Natural Language Understanding (intent-klassificering)
- `data/` - Datafiler, intents, konfiguration
- `training/` - Scripts til træning af modeller
- `cache/` - Mappe til at cache TTS-output og modeller

## Hvordan man bruger koden
For at starte Jarvis med fuld funktionalitet:
```python
python src/jarvis.py
```

For at starte demo-versionen uden eksterne afhængigheder:
```python
python src/demo.py
```

## Bemærkninger
- Husk at installere alle afhængigheder fra `requirements.txt` i rod-mappen
- Stemmegenkendelsesfunktionalitet kræver en fungerende mikrofon
- TTS-funktionaliteten kræver internetforbindelse for Google TTS 