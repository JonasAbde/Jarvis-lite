# Jarvis-lite: Dansk Stemmeassistent

## Projektoversigt

### Teknisk Stack
- **STT**: Faster-Whisper
- **TTS**: Google Text-to-Speech
- **NLU**: scikit-learn + TF-IDF
- **AI**: Kalibreret klassifikator

### Hovedfunktioner
1. Tale-til-tekst konvertering
2. Intent-genkendelse
3. Kommando-udførelse
4. Text-to-speech svar

## Arkitektur

### Dataflow
1. Lydoptagelse → STT
2. Tekst → NLU
3. Intent → Kommando
4. Svar → TTS

### Komponenter
- `src/nlu/`: Intent-genkendelse
- `src/jarvis_commands.py`: Kommandoer
- `src/jarvis_main.py`: Hovedprogram

## Demo

### Live Demo
1. Start programmet
2. Test kommandoer:
   - "Hvad er klokken?"
   - "Åbn YouTube"
   - "Fortæl en joke"

### Tekniske Detaljer
- Konfidensbaseret tærskelværdi
- Asynkron lydhåndtering
- Fejlhåndtering og recovery

## Fremtidige Forbedringer
1. Wake word detection
2. Offline TTS
3. Flere kommandoer
4. Hukommelse mellem sessioner

## Kvalitetssikring
- Unit tests
- CI/CD pipeline
- Dokumentation
- Code coverage 