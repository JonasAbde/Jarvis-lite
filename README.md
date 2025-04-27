# Jarvis Lite

![Jarvis Logo](https://img.shields.io/badge/Jarvis%20Lite-Personlig%20Assistent-blue)
![Version](https://img.shields.io/badge/Version-4.0-green)
![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11-yellow)

En personlig assistent med stigende kompleksitet - fra simpel if/else-logik til avanceret Machine Learning. Dette projekt viser forskellige implementeringer af samme assistent, med fokus på evolution i programmering og kunstig intelligens.

## Projektstruktur

Dette projekt er organiseret i **Jarvis Evolution** - en samling af forskellige versioner af Jarvis, arrangeret efter kompleksitet:

```
jarvis_evolution/
├── v1_basis_if_else/      # Simpel if/else-logik
├── v2_dict_notebook/      # Dictionary-baseret (Jupyter Notebook)
├── v3_ml_tensorflow/      # Machine Learning med TensorFlow
├── v4_eksamen_komplet/    # Komplet eksamenspakke
├── utils/                 # Hjælpeværktøjer og moduler
├── extensions/            # Udvidelser (dashboard, hardware)
└── docs/                  # Dokumentation
```

## Fra Simple til Avanceret

Projektet demonstrerer fire forskellige tilgange til at bygge den samme assistent:

1. **Basis (v1)**: Simpel implementation med if/else-betingelser
2. **Dictionary (v2)**: Forbedret struktur med dictionary-baseret kommandomapping
3. **Machine Learning (v3)**: Avanceret intentgenkendelse med TensorFlow
4. **Komplet Pakke (v4)**: Fuldt udviklet eksamenspakke med dokumentation og installation

## Funktioner

Assistenten har følgende kernefunktioner:

- **Tidsinformation**: Fortæller klokken med kontekstuel variation
- **Webnavigation**: Åbner websites som YouTube og DR
- **Noter**: Gemmer brugernoter med tidsstempel
- **Personlighed**: Varierede svar baseret på tidspunkt og tilfældighed
- **Tale**: Tekst-til-tale med gTTS
- **Naturlig Sprogforståelse**: ML-baseret intentgenkendelse (i v3 og v4)

## Kom i Gang

Der er to måder at komme i gang med Jarvis Lite:

### Nem metode (Anbefalet)

1. **Installation**: Kør `setup.bat` i roden
   - Vælg 'Basis' for minimal installation (v1 og v2)
   - Vælg 'Fuld' for komplet installation inkl. TensorFlow (alle versioner)

2. **Start Jarvis**: Kør `start_jarvis.bat` i roden
   - Vælg hvilken version du vil køre fra menuen

### Manuel metode (Pr. version)

#### Version 1 (Basis)
```
cd jarvis_evolution/v1_basis_if_else
start_jarvis_v1.bat
```
eller
```
cd jarvis_evolution/v1_basis_if_else
python jarvis_basis.py
```

#### Version 2 (Dictionary Notebook)
```
cd jarvis_evolution/v2_dict_notebook
start_jarvis_v2.bat
```
eller
```
cd jarvis_evolution/v2_dict_notebook
jupyter notebook JarvisDict.ipynb
```

#### Version 3 (ML/TensorFlow)
```
cd jarvis_evolution/v3_ml_tensorflow
setup_v3.bat
start_jarvis_v3.bat
```

#### Version 4 (Eksamenspakke)
```
cd jarvis_evolution/v4_eksamen_komplet
setup.bat
start_jarvis.bat
```

## Teknologi

- **Python 3.9-3.11** (anbefaler 3.11)
- **TensorFlow** (til ML-versionerne)
- **gTTS** (Google Text-to-Speech)
- **Jupyter Notebook** (til notebook-versionen)

## Krav

Se `requirements.txt` i hver versionsmappe for specifikke krav. Generelt anbefales:

```
tensorflow
numpy
gtts
playsound==1.2.2
jupyter
```

## Dokumentation

Hver version har sin egen README.md med detaljerede instruktioner.

---

Projektet er udviklet som en demonstration af progression i programmeringsteknikker
og anvendelsen af kunstig intelligens i personlige assistenter.
