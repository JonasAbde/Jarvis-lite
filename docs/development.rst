Udviklerguide
============

Dette dokument beskriver hvordan du udvikler på Jarvis-lite.

Projektstruktur
-------------

::

   Jarvis-lite/
   ├── src/                    # Kildekode
   │   ├── nlu/               # Intent-genkendelse
   │   ├── data/              # Træningsdata
   │   ├── jarvis_main.py     # Hovedprogram
   │   ├── jarvis_commands.py # Kommandoer
   │   └── nlu_trainer.py     # NLU-træning
   ├── tests/                 # Unit tests
   ├── docs/                  # Dokumentation
   └── notebooks/             # Jupyter notebooks

Udviklingsmiljø
-------------

1. Opret virtuelt miljø:

   .. code-block:: bash

      python -m venv .venv
      .\.venv\Scripts\activate  # Windows
      source .venv/bin/activate # Linux/Mac

2. Installer dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

3. Installer udviklings-dependencies:

   .. code-block:: bash

      pip install pytest pytest-cov sphinx sphinx-rtd-theme

Tests
-----

Kør tests:

.. code-block:: bash

   pytest --cov=src tests/

Dokumentation
-----------

Byg dokumentation:

.. code-block:: bash

   cd docs
   make html

Tilføj ny kommando
----------------

1. Tilføj funktion i `jarvis_commands.py`
2. Tilføj intent i `nlu_commands.json`
3. Træn NLU-modellen:

   .. code-block:: bash

      python src/nlu_trainer.py

4. Test kommandoen
5. Opdater dokumentation

Kodekvalitet
----------

* Brug type hints
* Dokumenter funktioner
* Skriv tests
* Følg PEP 8
* Brug async/await for I/O 