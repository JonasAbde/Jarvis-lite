# Jarvis Projekts Navngivningsstandard

For at sikre konsistens på tværs af projektet anvendes følgende navngivningskonventioner:

## Mappenavne
- Alle mappenavne skrives med **snake_case** (små bogstaver med underscore)
- Eksempel: `jarvis_core`, `ml_model`, `notebooks`

## Filnavne
- Python-filer skrives med **snake_case**: `jarvis_assistant.py`, `speech_module.py`
- Markdown-filer skrives med **UPPERCASE_SNAKE_CASE**: `README.md`, `DOKUMENTATION.md`
- Batch-filer skrives med **lowercase_snake_case**: `start_jarvis.bat`, `setup_miljø.bat`
- Jupyter Notebooks skrives med **PascalCase**: `JarvisAssistent.ipynb`, `MlDemonstration.ipynb`

## Hovedmapper og deres formål

1. **jarvis_core/**
   - Kernekode og basisimplementering
   - Indeholder: `assistent.py`, `kommando_håndtering.py`

2. **jarvis_ml/**
   - Machine Learning-baseret implementation
   - Indeholder: `ml_model.py`, `intentgenkendelse.py`

3. **jarvis_eksamens_pakke/**
   - Komplet pakke til eksamen
   - Indeholder: `start.bat`, `readme.md`, osv.

4. **notebooks/**
   - Jupyter Notebooks for demonstration
   - Indeholder: `JarvisDemo.ipynb`, `MlImplementering.ipynb`

5. **docs/**
   - Dokumentation
   - Indeholder: `PROJEKTSTRUKTUR.md`, `VERSIONSOVERSIGT.md`

6. **utils/**
   - Hjælpefunktioner og værktøjer
   - Indeholder: `tale_værktøjer.py`, `fil_håndtering.py`

## Hovedfiler og deres navne

1. **jarvis_basis.py** - Basisimplementering med if/else
2. **jarvis_dict.py** - Dictionary-baseret implementation
3. **jarvis_ml.py** - ML-baseret implementation
4. **JarvisEksamen.ipynb** - Eksamen notebook
5. **README.md** - Projektoversigt
6. **PROJEKTSTRUKTUR.md** - Detaljeret strukturoversigt
7. **start_jarvis.bat** - Startscript
8. **setup_miljø.bat** - Installationsscript

## Ny standardiseret mappestruktur

```
jarvis_projekt/
├── jarvis_core/          # Basisimplementering
├── jarvis_ml/            # ML-implementering
├── jarvis_eksamens_pakke/  # Eksamenspakke
│   ├── scripts/          # Python-scripts
│   ├── notebooks/        # Notebooks
│   └── docs/             # Dokumentation
├── notebooks/            # Alle notebooks
├── docs/                 # Projektdokumentation
├── utils/                # Hjælpeværktøjer
└── tests/                # Testfiler
```

Dette format sikrer navngivningskonsistens på tværs af hele projektet og gør det nemmere at navigere og forstå strukturen.
