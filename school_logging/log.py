"""
Protokollierungs-Modul für das Gewächshaus-Steuerungssystem

Dieses Modul stellt erweiterte Protokollierungsfunktionen bereit, die für die 
Überwachung und Fehlerdiagnose des Gewächshaus-Systems verwendet werden.

Es bietet:
- Farbige Konsolenausgabe für verschiedene Protokollierungsstufen
- Automatische Speicherung aller Protokolle in Dateien mit Zeitstempeln
- Programmbeendigung bei kritischen Fehlern
- Anpassbare Protokollierungsstufen über Befehlszeilenargumente

Die Protokollierung unterstützt verschiedene Detailstufen (DEBUG, INFO, WARNING, ERROR, CRITICAL)
und hilft bei der effektiven Überwachung des Systems im Betrieb und bei der Fehlersuche.
"""

import logging
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, Any

# Farben für die verschiedenen Log-Stufen definieren
LOG_COLORS: Dict[str, str] = {
    'DEBUG':    '\033[94m',  # Blau
    'INFO':     '\033[92m',  # Grün
    'WARNING':  '\033[93m',  # Gelb
    'ERROR':    '\033[91m',  # Rot
    'CRITICAL': '\033[95m'   # Magenta
}

# Farbe zurücksetzen
RESET_COLOR: str = '\033[0m'

class CriticalExitHandler(logging.Handler):
    """
    Benutzerdefinierter Handler, der das Programm beendet, wenn ein Log der Stufe CRITICAL erzeugt wird.
    
    Dieser Handler überwacht alle Protokolleinträge und beendet das Programm automatisch,
    wenn ein kritischer Fehler auftritt, um weitere Schäden zu vermeiden.
    """
    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= logging.CRITICAL:
            sys.exit(1)

class ColoredFormatter(logging.Formatter):
    """
    Formatiert Protokolleinträge mit Farben entsprechend ihrem Schweregrad.
    
    Diese Klasse erweitert den Standard-Formatter, um Protokollmeldungen farbig 
    darzustellen und so die Unterscheidung verschiedener Protokollstufen zu erleichtern.
    """
    def __init__(self, fmt=None, datefmt=None, style='%', colored: bool = True):
        super().__init__(fmt, datefmt, style)
        self.colored = colored

    def format(self, record: logging.LogRecord) -> str:
        log_color = LOG_COLORS.get(record.levelname, RESET_COLOR)
        message = super().format(record)
        return f"{log_color}{message}{RESET_COLOR}" if self.colored else message

class ColoredLogger:
    """
    Eine benutzerdefinierte Logger-Klasse, die farbige Ausgabe bietet und das Programm bei kritischen Fehlern beendet.
    
    Diese Klasse kapselt die Komplexität der Protokollkonfiguration und bietet eine 
    einfache Schnittstelle für die Protokollierung von Meldungen mit verschiedenen 
    Schweregraden. Sie richtet automatisch die Protokollierung sowohl in die Konsole 
    (mit Farben) als auch in Dateien (ohne Farben) ein.
    
    Attribute:
        name (str): Name des Loggers, normalerweise der Modulname
        level (int): Numerische Protokollierungsstufe (z.B. logging.INFO)
        logger (logging.Logger): Das konfigurierte Logger-Objekt
    
    Beispiel:
        log = ColoredLogger('gewächshaus', 'INFO')
        log.info('System gestartet')
        log.error('Sensorfehler aufgetreten')
    """
    def __init__(self, name: str, verbose: str = 'INFO') -> None:
        """
        Initialisiert einen neuen farbigen Logger.
        
        Args:
            name (str): Name des Loggers
            verbose (str): Protokollierungsstufe als String (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.name = name
        self.level = self._map_log_level(verbose)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """
        Richtet den Logger mit Konsolenausgabe und Dateiprotokollierung ein.
        
        Returns:
            logging.Logger: Der konfigurierte Logger
        """
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        if not logger.handlers:
            # Konsolenhandler (farbige Ausgabe)
            ch = logging.StreamHandler()
            ch.setLevel(self.level)
            ch.setFormatter(ColoredFormatter(
                '%(asctime)s - %(filename)s - %(name)s - [%(levelname)s] - %(message)s',
                colored=True
            ))
            logger.addHandler(ch)

            # Dateihandler (alle Stufen, keine Farben, gespeichert mit Zeitstempel)
            log_dir = 'logging'
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_file_path = os.path.join(log_dir, f'logs_{timestamp}.log')
            fh = logging.FileHandler(log_file_path)
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(ColoredFormatter(
                '%(asctime)s - %(filename)s - %(name)s - [%(levelname)s] - %(message)s',
                colored=False
            ))
            logger.addHandler(fh)

            # CriticalExitHandler hinzufügen
            logger.addHandler(CriticalExitHandler())

        return logger

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Protokolliert eine Debug-Nachricht.
        
        Args:
            msg (str): Die zu protokollierende Nachricht
            *args: Zusätzliche Positionsargumente für die Formatierung
            **kwargs: Zusätzliche Schlüsselwortargumente für die Formatierung
        """
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Protokolliert eine Info-Nachricht.
        
        Args:
            msg (str): Die zu protokollierende Nachricht
            *args: Zusätzliche Positionsargumente für die Formatierung
            **kwargs: Zusätzliche Schlüsselwortargumente für die Formatierung
        """
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Protokolliert eine Warnungsnachricht.
        
        Args:
            msg (str): Die zu protokollierende Nachricht
            *args: Zusätzliche Positionsargumente für die Formatierung
            **kwargs: Zusätzliche Schlüsselwortargumente für die Formatierung
        """
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Protokolliert eine Fehlermeldung.
        
        Args:
            msg (str): Die zu protokollierende Nachricht
            *args: Zusätzliche Positionsargumente für die Formatierung
            **kwargs: Zusätzliche Schlüsselwortargumente für die Formatierung
        """
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """
        Protokolliert eine kritische Nachricht und löst einen CriticalError aus.
        Das Programm wird nach dieser Nachricht automatisch beendet.
        
        Args:
            msg (str): Die zu protokollierende Nachricht
            *args: Zusätzliche Positionsargumente für die Formatierung
            **kwargs: Zusätzliche Schlüsselwortargumente für die Formatierung
        """
        self.logger.critical(msg, *args, **kwargs)

    def _map_log_level(self, verbose: str) -> int:
        """
        Ordnet den verbose-String einer numerischen Protokollierungsstufe zu.

        Args:
            verbose (str): Die Ausführlichkeitsstufe als String (z.B. 'DEBUG', 'INFO').

        Returns:
            int: Entsprechende Logging-Level-Konstante.
        """
        log_level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return log_level_mapping.get(verbose.upper(), logging.INFO)
