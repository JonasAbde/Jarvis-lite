# Jarvis Restrukturering Guide

## Ny projektstruktur
Vi har nu systematisk organiseret projektet i en klar versionsbaseret struktur. De primære elementer er:

```
jarvis_versions/
├── v1_basis_if_else/         # Basisversion med if/else logik
├── v2_dict_notebook/         # Dictionary-baseret notebook-version
├── v3_ml_tensorflow/         # Machine Learning TensorFlow-version
├── v4_eksamen_komplet/       # Komplet eksamenspakke
│   ├── scripts/              # Python scripts
│   ├── notebooks/            # Jupyter notebooks
│   └── docs/                 # Dokumentation
├── utils/                    # Hjælpeværktøjer og moduler
│   ├── speech_recognition.py # Talegenkendelse
│   ├── test_voice.py         # Test af stemme
│   └── src/                  # Kernekomponenter
├── extensions/               # Udvidelser og ekstra funktionalitet
│   └── jarvis_lite_dashboard/# Dashboard og hardware-integration
├── docs/                     # Generel dokumentation
└── README.md                 # Overblik over versioner
```

## Fjernelse af forældede filer

Nu hvor alt væsentligt indhold er organiseret i `jarvis_versions/`, kan vi fjerne forældede og duplikerede filer. Her er en liste over filer, der trygt kan fjernes:

1. **Gamle projektmapper:**
   - `JarvisLite_Eksamen/`
   - `Jarvis_Eksamen/`
   - `jarvis_basis_if_else/`
   - `jarvis_ml_intentgenkendelse/`
   - `jarvis_eksamen_komplet_ml/`

2. **Duplikerede filer i roden:**
   - `main.py` (nu i `v1_basis_if_else/jarvis_basis.py`)
   - `jarvis_lite_eksamen_ml.py` (nu i `v3_ml_tensorflow/jarvis_ml.py`)
   - `Jarvis_Lite_Eksamen.ipynb` (nu i `v2_dict_notebook/JarvisDict.ipynb`)
   - `PROJECT_STRUCTURE.md` (nu i `docs/`)
   - `NAVNGIVNINGSSTANDARD.md` (nu i `docs/`)

3. **Midlertidige mapper:**
   - `.ipynb_checkpoints/`

## Indhold af de forskellige versioner

### v1: Basis (if/else)
- Enkel tekstbaseret assistent
- Bruger if/else-logik til kommandogenkendelse
- Grundlæggende funktioner: tid, websites, noter

### v2: Dictionary-baseret (Notebook)
- Samme grundfunktionalitet men bedre struktureret
- Dictionary-baseret kommandohåndtering
- Implementeret i Jupyter Notebook format

### v3: Machine Learning (TensorFlow)
- Intentgenkendelse med TensorFlow
- Neurale netværk til tekstklassifikation
- Mere fleksibel kommandofortolkning

### v4: Komplet eksamenspakke
- Fuldt udviklet ML-baseret assistent
- Automatiseret installation og startup scripts
- Komplet dokumentation til eksamen

## Indhold af støttemapper

### utils/
- Hjælpeværktøjer til talegenkendelse
- Tests og eksperimenter
- Kernekomponenter fra src-mappen

### extensions/
- Dashboard-udvidelsen til Jarvis
- Hardware-integration
- Tilføjelsesmoduler

### docs/
- Projektdokumentation
- Teknisk dokumentation
- Standarder og konventioner

## Næste skridt
1. Gennemgå og test hver version for at sikre, at de fungerer korrekt
2. Fjern forældede filer og mapper
3. Opdater stier i scripts hvis nødvendigt
