# Jarvis Lite – Projektstatus pr. 2025-05-01

## Hvor langt er vi?
- **Whisper STT**: Kører nu med "small"-modellen (meget bedre kvalitet) og bruger GPU (RTX 4070) hvis muligt. Fallback til CPU hvis nødvendigt.
- **Robust lydindlæsning**: Koden bruger Whisper's egen loader for hastighed, og librosa som backup.
- **Alle modeller**: Indlæses kun én gang ved opstart for maksimal performance.
- **NN-chatbot**: Trænet og fungerer. Kan besvares og lære nye svar live.
- **NLU (scikit-learn)**: Fungerer og trænes på egne intents.
- **JSON-fejl**: Rettet i `conversation_pairs.json`.
- **Koden er optimeret til Windows og lokal/offline brug.**

## Hvad mangler/kan forbedres?
- Whisper small-model skal downloades færdig første gang (vent på download, afbryd ikke).
- Forbedre og udvide `conversation_pairs.json` for bedre svar og NLU-præcision.
- Overvej at udbygge intents og NN-chatbotten med flere eksempler og naturlig sprogvariation.
- Test Jarvis grundigt med flere danske kommandoer og samtaler.
- (Valgfrit) Skift TTS fra gTTS/playsound til pyttsx3 for endnu bedre offline TTS på Windows.
- (Valgfrit) Automatisk logning af ukendte kommandoer for nemmere retræning.
- (Valgfrit) Udbyg wake word med Porcupine for mere robust aktivering.

## Næste skridt
1. Vent på Whisper small-model download og test Jarvis på GPU.
2. Udvid træningsdata og retræn NLU/NN-chatbot.
3. Overvej flere features (noter, websøgning, flere kommandoer).

---
**Alt kode og data er committet til GitHub.**

Kontakt for hjælp til retræning, optimering eller nye features!
