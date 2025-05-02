# Jarvis Lite – Brugervejledning

## Start assistenten
```powershell
.\.venv\Scripts\activate  # hvis ikke aktiv
python jarvis_main.py
```
Når du ser `=== Jarvis Lite er klar! ===` taler du efter prompten “Jarvis lytter…”.
Stop med **Ctrl+C**.

## Kommandoer (standard)
| Intent | Eksempel på sætning | Handling |
|--------|--------------------|----------|
| `klokken` | “Hvad er klokken?” | Siger det aktuelle klokkeslæt |
| `youtube` | “Åbn YouTube” | Åbner youtube.com i standardbrowser |
| `gem note` | “Gem Husk at øve Python” | Tilføjer linje til `noter.txt` |

Tilføj flere i `jarvis_commands.py` og retræn NLU hvis nødvendigt.

## Læring af nye spørgsmål/svar
* Ukendte sætninger skrives til `ukendte_sætninger.txt`.
* Tilføj matchende svar i `conversation_pairs.json` og kør `nn_chatbot_trainer.py`.

## Retræning af NLU
1. Redigér `nlu_commands.json` (intents + eksempler)
2. Kør:
```powershell
python nlu_trainer.py
```
Modellen gemmes i `models/` og indlæses automatisk ved næste Jarvis-start.
