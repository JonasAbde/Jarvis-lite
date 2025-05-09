"""
Sphinx konfiguration for Jarvis-lite dokumentation.
"""

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Jarvis-lite'
copyright = '2025, Jarvis-lite team'
author = 'Jarvis-lite team'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']

# Autodoc indstillinger
autodoc_member_order = 'bysource'
autodoc_typehints = 'description' 