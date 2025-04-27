# Jarvis Lite Eksamenspakke

Dette er den komplette eksamenspakke for Jarvis Lite projektet, der indeholder alle komponenter nødvendige for præsentation, demonstration og evaluering.

## Indhold

- **ML-baseret assistent:** Komplet implementation af Jarvis med TensorFlow NLU
- **Jupyter Notebook:** Interaktiv notebook med forklaringer og kode
- **Automatisk installation:** Setup script der opretter virtuelt miljø og installerer afhængigheder
- **Start-scripts:** Nemme måder at starte assistenten eller notebooken
- **Dokumentation:** Projektbeskrivelse, historik og teknisk dokumentation

## Mappestruktur

- **`scripts/`**: Python-kode for Jarvis assistenten
- **`notebooks/`**: Jupyter notebooks til interaktiv demonstration
- **`docs/`**: Dokumentation og forklaringer

## Installation

Kør følgende kommando for at installere alle nødvendige pakker:

```
setup.bat
```

Dette vil:
1. Oprette et virtuelt Python-miljø (.venv)
2. Installere alle nødvendige pakker fra requirements.txt
3. Konfigurere systemet til at køre Jarvis

## Kør Jarvis

Efter installation kan du starte Jarvis på to måder:

1. **Som script (ML-version):**
   ```
   start_jarvis.bat
   ```

2. **Som Jupyter Notebook:**
   ```
   start_notebook.bat
   ```

## Funktioner

- **Talegengivelse:** Jarvis taler via gTTS (Google Text-to-Speech)
- **Intentgenkendelse:** Bruger TensorFlow til at forstå kommandoer
- **Kommandoer:**
  - Fortælle tid med varierende svar baseret på tid på dagen
  - Åbne websites (YouTube, DR)
  - Gemme noter med tidsstempel
  - Personlige hilsner og afskedshilsner
  - Præsentere sig selv

## Tekniske Detaljer

- **Python 3.11** anbefales (testet med 3.9-3.11)
- **TensorFlow** for machine learning-komponenter
- **Virtuelt miljø** for isoleret og reproducerbar kørsel
- **gTTS** for taleoutput
- **playsound** for afspilning af lydfiler

---

*Denne pakke er sammensat til eksamensformål og demonstrerer progression fra simpel if/else logik til avanceret ML-baseret intentgenkendelse.*
