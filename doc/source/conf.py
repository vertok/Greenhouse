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

project = 'greenhouse'
copyright = '2025, Alexey Obukhov'
author = 'Alexey Obukhov'
version = '3.0.0'
release = '3.0.0'

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
    'primary': '#336633',  # Example primary color
    'secondary': '#99CC99', # Example secondary color
    'cover': '#FFFFFF',  # Cover background color
    'white': '#FFFFFF',
    'links': '#336633',
    'cover-bg': 'url(ihk.jpg) center', #image inclusion
    'cover-overlay': 'rgba(255, 255, 255, 0.5)', #optional overlay.
    'top-left-content': 'counter(page)',
    'cover-title': '"Gewächshaus-Steuerungssystem"', #title
    'cover-subtitle': '"Technische Dokumentation"', #subtitle
    'cover-version': '"Version 3.0"', #version
    'cover-author': '"Alexey Obukhov"', #author
    'page-margin-left': '2.5cm',
    'page-margin-right':'2cm',
    'page-margin-top':'2cm',
    'page-margin-bottom':'2cm',
    'font-family': '"Times-Roman"',
    'font-size': '12pt',
}


templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'  # Or choose another theme if you prefer
html_static_path = ['_static']

# -- Path setup --------------------------------------------------------------

sys.path.insert(0, os.path.abspath('../../'))  # Go up two levels from 'doc/source' to the project root
sys.path.insert(0, os.path.abspath('../../greenhouse'))  # Path to DB module
sys.path.insert(0, os.path.abspath('../../school_logging'))  # Path to the 'school_logging' directory
