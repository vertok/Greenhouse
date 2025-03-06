# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import sys
import os
from unittest.mock import MagicMock

# Define a mock class for all the hardware-related modules
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

# List of modules to mock
MOCK_MODULES = [
    'RPi', 'RPi.GPIO', 
    'dht11', 
    'board', 
    'digitalio', 
    'busio',
    'adafruit_character_lcd', 
    'adafruit_character_lcd.character_lcd_i2c',
    'adafruit_mcp3xxx', 
    'adafruit_mcp3xxx.mcp3008', 
    'adafruit_mcp3xxx.analog_in',
    'adafruit_ht16k33', 
    'adafruit_ht16k33.segments',
    'luma.led_matrix', 
    'luma.led_matrix.device',
    'luma.core.interface.serial',
    'luma.core.render',
    'smbus'
]

# Apply the mocks to the modules
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

# Add the project root directory to the Python path so Sphinx can find the modules
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'greenhouse'  # Your project name
copyright = '2025, Alexey Obukhov'
author = 'Alexey Obukhov'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # To generate documentation from docstrings
    'sphinx.ext.viewcode',     # To include "view source" links
    'sphinx.ext.napoleon',     # (Optional) For Google/NumPy style docstrings
    'sphinx.ext.autosummary',  # (Optional) For summary tables
    'sphinx_simplepdf',
]

# Configure autodoc to handle missing dependencies gracefully
autodoc_mock_imports = MOCK_MODULES

# Ensure imported modules appear in the docs even if they can't be imported
autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
    'imported-members': True,
}

simplepdf_vars = {
    'font-family': 'Times New Roman',
    'cover-subtitle': 'Dokumentation',
    'cover-subtitle-color': '#a0b0c0', 
    'font-size': '12pt',
    'head-font-size': '14pt',
    'left-margin': '2.5cm',
    'right-margin': '2cm',
    'top-margin': '2cm',
    'bottom-margin': '2cm',
    'head-bold': 'true',
}

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'  # Or choose another theme if you prefer
html_static_path = ['_static']

# -- Path setup --------------------------------------------------------------

# This is crucial for Sphinx to find your school_logging module
sys.path.insert(0, os.path.abspath('../../'))  # Go up two levels from 'doc/source' to the project root
sys.path.insert(0, os.path.abspath('../../greenhouse'))  # Path to DB module
sys.path.insert(0, os.path.abspath('../../school_logging'))  # Path to the 'school_logging' directory
