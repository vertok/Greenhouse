"""
Gewächshaus-Steuerungssystem

Dieses Programm implementiert ein komplettes Überwachungs- und Steuerungssystem für ein Gewächshaus.
Es erfasst und protokolliert Umgebungsdaten wie Temperatur, Luftfeuchtigkeit und Helligkeit
über verschiedene angeschlossene Sensoren und zeigt die Informationen auf mehreren Displays an.

Hauptfunktionen:
- Erfassung von Temperatur- und Luftfeuchtigkeitsdaten über den DHT11-Sensor
- Messung des Umgebungslichts mit einem Helligkeitssensor
- Speicherung aller Messwerte mit Zeitstempel in einer SQLite-Datenbank
- Anzeige der aktuellen Temperatur und Luftfeuchtigkeit auf einem LCD-Display
- Visualisierung von Tag/Nacht-Zuständen über ein 8x8 LED-Matrix-Display
- Anzeige der numerischen Messwerte auf einem 7-Segment-Display
- Umfassende Protokollierung aller Aktivitäten und Fehler

Befehlszeilenargumente:
- --verbose: Legt den Log-Level fest (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- --iterations: Anzahl der durchzuführenden Messungen (Standard: 10)
- --interval: Zeit zwischen den Messungen in Sekunden (Standard: 3)

Verwendung:
  python3 main.py [--verbose LEVEL] [--iterations ANZAHL] [--interval SEKUNDEN]

Beispiel:
  python3 main.py --verbose INFO --iterations 20 --interval 5
"""

import argparse
import time
import RPi.GPIO as GPIO
import dht11

from school_logging.log import ColoredLogger

from greenhouse.database_operations import DatabaseOperations

def parse_args() -> argparse.Namespace:
    """
    Verarbeitet Befehlszeilenargumente für das Datenbankoperationsskript.

    Returns:
        argparse.Namespace: Verarbeitete Befehlszeilenargumente.
    """
    parser = argparse.ArgumentParser(description='Datenbankoperationen')
    parser.add_argument('--verbose', type=str.upper,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Legt den Protokollierungsgrad fest (Groß-/Kleinschreibung wird ignoriert)')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Anzahl der durchzuführenden Messungen')
    parser.add_argument('--interval', type=int, default=3,
                        help='Intervall zwischen Messungen in Sekunden')
    args = parser.parse_args()
    return args

def main():
    """
    Hauptfunktion zur Ausführung der Gewächshaussteuerungs-Operationen.
    """
    args = parse_args()
    log = ColoredLogger(name='greenhouse', verbose=args.verbose)
    
    log.info("Starte Gewächshaus-Kontrollsystem")
    log.info("Initialisiere Komponenten...")
    
    try:
        # Datenbank-Operationen mit besserer Fehlerbehandlung initialisieren
        db_ops = None
        try:
            db_ops = DatabaseOperations(log)
        except Exception as e:
            log.error(f"Fehler bei der Initialisierung der Datenbankoperationen: {e}")
            return
        
        # Nur fortfahren, wenn Datenbankoperationen erfolgreich initialisiert wurden
        if db_ops and db_ops.conn:
            # GPIO und DHT11-Sensor initialisieren
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            instance = dht11.DHT11(pin=db_ops.DHT11_PIN)
            
            # Datenbank erstellen, falls sie nicht existiert
            db_ops.create_database()
            
            # Hauptmessschleife
            log.info(f"Starte {args.iterations} Messungen mit {args.interval}s Intervall")
            for i in range(args.iterations):
                log.info(f"Messung {i+1}/{args.iterations}")
                
                # Sensordaten auslesen
                temperature, humidity = db_ops.read_dht11_sensor(instance)
                log.info(f"Gemessen: Temperatur={temperature}°C, Luftfeuchtigkeit={humidity}%")
                
                # Messungen in Datenbank speichern und Helligkeit erhalten
                brightness = db_ops.save_measurement(temperature, humidity)
                
                # Alle Anzeigen aktualisieren
                if brightness is not None:
                    db_ops.update_all_displays(temperature, humidity, brightness)
                
                # Vor der nächsten Messung warten
                time.sleep(args.interval)
            
            # Datenbankinhalt ausgeben
            db_ops.print_database()
        else:
            log.error("Datenbankverbindung nicht verfügbar, kann nicht fortfahren.")

    except KeyboardInterrupt:
        log.info("Gewächshaus-Kontrollsystem durch Benutzer gestoppt")
        
    except Exception as e:
        log.critical(f"Ein unerwarteter Fehler ist aufgetreten: {e}", exc_info=True)

    finally:
        log.info("Räume Ressourcen auf...")
        if 'db_ops' in locals() and db_ops is not None:
            db_ops.close_connection()
        try:
            GPIO.cleanup()
        except:
            pass
        log.info("Gewächshaus-Kontrollsystem wurde angehalten")

if __name__ == "__main__":
    main()
