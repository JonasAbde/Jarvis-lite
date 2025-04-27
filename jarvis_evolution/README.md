# Jarvis Evolution - Oversigt

Dette projekt indeholder fire forskellige versioner af Jarvis, vores personlige assistent, med stigende kompleksitet og funktionalitet:

## Versioner

### 1. Basis (If/Else)
**Mappe:** `v1_basis_if_else/`

Den simpleste implementation, der bruger if/else-betingelser til at genkende kommandoer.
- **Hovedfil:** `jarvis_basis.py`
- **Funktioner:** Fortæller tid, åbner websites, gemmer noter
- **Teknologi:** Simpel betinget logik

### 2. Dictionary-baseret (Notebook)
**Mappe:** `v2_dict_notebook/`

Forbedret version der bruger et dictionary til at mappe kommandoer til handlinger.
- **Hovedfil:** `JarvisDict.ipynb`
- **Funktioner:** Samme som basis, men bedre struktureret
- **Teknologi:** Dictionary-mapping, funktioner som værdier

### 3. Machine Learning (TensorFlow)
**Mappe:** `v3_ml_tensorflow/`

Avanceret version der bruger TensorFlow til at genkende brugerens intentioner.
- **Hovedfil:** `jarvis_ml.py`
- **Funktioner:** Naturligt sprog forståelse, intentgenkendelse
- **Teknologi:** TensorFlow, neurale netværk, NLU

### 4. Komplet Eksamenspakke
**Mappe:** `v4_eksamen_komplet/`

Komplet pakke klar til eksamen med ML-funktionalitet, dokumentation og nemme installationsscripts.
- **Hovedmappe:** `v4_eksamen_komplet/`
- **Indhold:**
  - `scripts/jarvis_assistent.py` - Hovedprogram
  - `notebooks/` - Jupyter notebooks
  - `docs/` - Dokumentation
  - Setup og start scripts
- **Teknologi:** Alt fra de tidligere versioner + automatisk installation

## Hvordan man kører hver version

### Basis version:
```
python jarvis_evolution/v1_basis_if_else/jarvis_basis.py
```

### Dictionary-notebook:
Åbn i Jupyter Notebook:
```
jupyter notebook jarvis_evolution/v2_dict_notebook/JarvisDict.ipynb
```

### ML version:
```
cd jarvis_evolution/v3_ml_tensorflow
setup_v3.bat
start_jarvis_v3.bat
```

### Eksamenspakke:
Brug de medfølgende scripts:
```
cd jarvis_evolution/v4_eksamen_komplet
setup.bat
start_jarvis.bat
```

---

Denne mappe giver en klar progression fra simple til avancerede implementeringer, og viser forskellige tilgange til at løse det samme problem.
