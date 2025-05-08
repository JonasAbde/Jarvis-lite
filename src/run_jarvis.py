#!/usr/bin/env python3
"""
Run script for Jarvis Lite.
Løser problemer med imports ved at køre fra den korrekte mappe.
"""

import os
import sys

# Tilføj src-mappen til Python's sys.path så imports virker korrekt
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import og kør jarvis.py's main-funktion
from jarvis import main

if __name__ == "__main__":
    print("Starter Jarvis Lite...")
    main() 