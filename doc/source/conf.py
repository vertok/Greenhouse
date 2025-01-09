# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'greenhouse'  # Your project name
copyright = '2025, Alexey Obukhov'
author = 'Alexey Obukhov'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',  # To generate documentation from docstrings
    'sphinx.ext.viewcode',  # To include "view source" links
    'sphinx.ext.napoleon',  # (Optional) For Google/NumPy style docstrings
    'sphinx.ext.autosummary', # (Optional) For summary tables
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'  # Or choose another theme if you prefer
html_static_path = ['_static']

# -- Path setup --------------------------------------------------------------

# This is crucial for Sphinx to find your school_logging module
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))  # Go up two levels from 'doc/source' to the project root
sys.path.insert(0, os.path.abspath('../../greenhouse'))  # Path to DB module
sys.path.insert(0, os.path.abspath('../../school_logging'))  # Path to the 'school_logging' directory
