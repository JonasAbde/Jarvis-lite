# Jarvis Lite - Eksamensprojekt

**En personlig assistent med Machine Learning-baseret sprogforståelse**

## Overblik

Jarvis Lite er en personlig assistent, der bruger:
* TensorFlow til at **forstå naturligt sprog** via et simpelt neuralt netværk
* Google Text-to-Speech til at **kommunikere med tale**
* Forskellige funktioner til at **udføre opgaver** (fortælle tid, åbne websites, gemme noter)

Dette projekt demonstrerer principper fra kunstig intelligens, beslutningstagning og datastrukturer.

## Installation & Brug

**Lyninstallation:**
1. Dobbeltklik på `setup.bat` for at installere alle nødvendige pakker
2. Vælg enten at:
   * Dobbeltklik på `start_jarvis.bat` for at køre assistenten direkte
   * Dobbeltklik på `start_notebook.bat` for at åbne Jupyter Notebook-versionen

**Krav:**
* Windows-system
* Python 3.9-3.11 installeret
* Internetforbindelse (for gTTS og webbrowser-funktioner)

## Funktionalitet

Jarvis Lite kan:
* **Fortælle tiden**: "Hvad er klokken?", "Hvad tid er det?", etc.
* **Åbne DR**: "Åbn DR", "Jeg vil se DR", etc.
* **Åbne YouTube**: "Start YouTube", "Jeg vil se YouTube", etc.
* **Gemme noter**: "Skriv en note", "Gem dette", etc.
* **Introducere sig selv**: "Hvem er du?", "Fortæl om dig selv", etc.
* **Hilse og sige farvel**: "Hej", "Farvel", etc.

## Teknisk information

Dette projekt demonstrerer:
* **ML-baseret NLU (Natural Language Understanding)** med TensorFlow
* **Neurale netværk** til tekstklassificering
* **Beslutningslogik** baseret på intent-genkendelse
* **Datastrukturer** (dictionaries, arrays)
* **Tekstbehandling** (tokenization)

## Eksamensrelateret

Projektet opfylder disse krav:
* **Beslutningsprocesser**: ML-baseret intent-genkendelse og funktionskald baseret på denne
* **Datastrukturer**: Dictionary af intents, arrays til træningsdata
* **Emojis**: Inkluderet i svar for bedre oplevelse
* **Filhåndtering**: Noter gemmes i en tekstfil
* **webbrowser**: Åbner websites som DR og YouTube
* **Text-to-Speech**: Bruger gTTS til at konvertere tekst til tale

---

*Udviklet som eksamensprojekt af [Jeres navne her]*
