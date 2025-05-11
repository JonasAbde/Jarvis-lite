#!/usr/bin/env python3
"""Test imports af moduler for Jarvis-lite"""

import sys
import os
import traceback
import importlib

# Tjek for NumPy source directory problem
if os.path.exists('numpy'):
    print("ADVARSEL: Der er en 'numpy' mappe i den aktuelle sti, hvilket kan forårsage importproblemer.")

# Tilføj src til Python path - men fjern den aktuelle mappe for at undgå source directory problemer
if '.' in sys.path:
    sys.path.remove('.')
sys.path.insert(0, os.path.abspath('src'))

def test_import(module_name):
    """Tester import af et modul og rapporterer resultatet"""
    try:
        module = importlib.import_module(module_name)
        print(f"✅ {module_name} importeret korrekt")
        # Vis moduleversionen hvis tilgængelig
        if hasattr(module, '__version__'):
            print(f"   Version: {module.__version__}")
        return True
    except Exception as e:
        print(f"❌ Fejl ved import af {module_name}: {type(e).__name__}: {e}")
        # Vis traceback for at diagnosticere problemet
        print("\nTraceback:")
        traceback.print_exc(limit=3)
        print()  # Tom linje for bedre læsbarhed
        return False

# Test individuelle pakker
print("\nTester individuelle pakker:")
individual_packages = [
    'numpy',
    'nltk',
    'joblib',
    'sklearn',
    'regex'
]

for package in individual_packages:
    test_import(package)

# Test Jarvis moduler
print("\nTester Jarvis-lite moduler:")
modules_to_test = [
    'audio.speech',
    'nlu.classifier',
    'jarvis'
]

success_count = 0
for module in modules_to_test:
    if test_import(module):
        success_count += 1

print(f"\nResultat: {success_count}/{len(modules_to_test)} Jarvis-moduler importeret korrekt")

# Vis python path
print("\nPython søgesti:")
for path in sys.path:
    print(f"- {path}")

if __name__ == "__main__":
    # Koden kører kun hvis scriptet køres direkte
    pass 