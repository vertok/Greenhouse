"""
Messdaten-Modul für das Gewächshaus-Steuerungssystem

Dieses Modul stellt die Kernfunktionalität für das Auslesen von Sensordaten,
die Datenbankverwaltung und die Anzeige von Informationen bereit.

Es bietet Funktionen zum:
- Erfassen von Temperatur- und Luftfeuchtigkeitswerten über den DHT11-Sensor
- Messen der Umgebungshelligkeit über einen Lichtsensor
- Speichern aller Messdaten in einer SQLite-Datenbank
- Anzeigen der Werte auf verschiedenen Display-Typen (LCD, LED-Matrix, 7-Segment)
- Verarbeiten und Auswerten der gesammelten Daten

Dieses Modul bildet das Herzstück des Gewächshaus-Überwachungssystems und
übernimmt die zentrale Steuerung aller Komponenten.
"""

import time
import sqlite3
from typing import Optional
from datetime import datetime, timezone
import ntplib
import requests
import pytz
import RPi.GPIO as GPIO
import board
import digitalio
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_ht16k33.segments
import smbus  # Importieren von smbus für I2C-Kommunikation

from school_logging.log import ColoredLogger

class MeasurementSystem:
    """
    Hauptklasse zur Steuerung des Gewächshaus-Überwachungssystems.
    
    Diese Klasse verwaltet die komplette Funktionalität des Gewächshaus-Systems:
    - Erfassung von Sensor-Messdaten (Temperatur, Luftfeuchtigkeit, Helligkeit)
    - Speicherung der Daten in einer SQLite-Datenbank
    - Anzeige von Informationen auf verschiedenen Display-Typen
    - Überwachung des Tag/Nacht-Zyklus basierend auf Helligkeitsmessungen
    
    Die Klasse initialisiert bei ihrer Erstellung alle benötigten Hardware-Komponenten
    und ermöglicht die zentrale Steuerung sämtlicher Sensoren und Anzeigeelemente.
    
    Attribute:
        conn: Verbindung zur SQLite-Datenbank
        lcd: LCD-Display-Objekt für Textanzeige
        matrix: LED-Matrix-Display für grafische Symbole
        seven_segment: 7-Segment-Display für numerische Werte
        brightness_channel: Kanal für Helligkeitsmessungen
        temperature: Aktuelle Temperatur
        humidity: Aktuelle Luftfeuchtigkeit
    """
    # --- Konfiguration ---
    DATABASE_FILE: str = "greenhouse.db"
    TIME_SERVER: str = '10.254.5.115'  # Bei Bedarf NTP-Server anpassen eg. google '216.239.35.0'
    NUM_ITERATIONS = 3  # Anzahl der Messzyklen für Datenerfassung
    DHT11_PIN = 4  # GPIO-Pin für den DHT11-Sensor
    LCD_COLUMNS = 16
    LCD_ROWS = 2
    LCD_I2C_ADDRESS = 0x21  # I2C-Adresse des LCD-Displays anpassen
    SEVEN_SEGMENT_I2C_ADDRESS = 0x70  # I2C-Adresse des 7-Segment-Displays

    # --- Globale Variablen ---
    log = None  # Globale Logger-Instanz
    temperature, humidity = 0, 0  # Initialisierung der globalen Temperatur und Luftfeuchtigkeit

    def __init__(self, log: ColoredLogger) -> None:
        self.log = log
        self.conn = None
        self.lcd = self.initialize_lcd()
        self.brightness_channel = self.initialize_brightness_sensor()
        self.matrix = self.initialize_matrix_display()
        self.seven_segment = self.initialize_seven_segment()
        self.connect_to_database()

    def connect_to_database(self) -> None:
        """
        Stellt eine Verbindung zur SQLite-Datenbank her.
        """
        try:
            self.conn = sqlite3.connect('greenhouse.db')
            self.log.info("Verbindung zur Datenbank erfolgreich hergestellt.")
        except sqlite3.Error as e:
            self.log.error("Fehler beim Verbinden zur Datenbank: %s", e)
            self.conn = None

    def create_database(self) -> None:
        """
        Erstellt die Datenbanktabelle, falls sie nicht existiert.
        """
        try:
            cursor = self.conn.cursor()

            # Überprüfen, ob die Tabelle existiert
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
            table_exists = cursor.fetchone() is not None

            # Tabelle erstellen, falls sie nicht existiert
            if not table_exists:
                cursor.execute("""
                    CREATE TABLE measurements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        temperature REAL,
                        humidity REAL,
                        brightness INTEGER
                    )
                """)
                self.conn.commit()
                self.log.info("Tabelle 'measurements' wurde erstellt.")
            else:
                # Prüfen, ob die Helligkeitsspalte existiert
                cursor.execute("PRAGMA table_info(measurements)")
                columns = [column[1] for column in cursor.fetchall()]
                
                # Helligkeitsspalte hinzufügen, falls sie nicht existiert
                if 'brightness' not in columns:
                    cursor.execute("ALTER TABLE measurements ADD COLUMN brightness INTEGER")
                    self.conn.commit()
                    self.log.info("Helligkeitsspalte zur bestehenden Tabelle hinzugefügt.")
                else:
                    self.log.info("Tabelle 'measurements' mit Helligkeitsspalte existiert bereits.")
        except sqlite3.Error as e:
            self.log.error("Fehler beim Erstellen/Aktualisieren der Tabelle: %s", e)

    def save_measurement(self, temp: float, hum: float) -> Optional[int]:
        """
        Speichert eine Messung in der Datenbank.

        Args:
            temp (float): Die gemessene Temperatur.
            hum (float): Die gemessene Luftfeuchtigkeit.
        """
        if self.conn is None:
            self.log.error("Datenbankverbindung ist nicht hergestellt.")
            return

        ntp_time = self.get_ntp_time(self.TIME_SERVER)
        if ntp_time is None:
            self.log.error("Konnte keine Zeit vom NTP-Server abrufen. Messung nicht gespeichert.")
            return

        try:
            # Helligkeit auslesen
            brightness = self.read_brightness() 
            self.log.info(f"Helligkeitsmessung: {brightness}")
            
            # In Datenbank speichern
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO measurements (timestamp, temperature, humidity, brightness) VALUES (?, ?, ?, ?)",
                (ntp_time, temp, hum, brightness)
            )
            self.conn.commit()
            self.log.info(f"Messung gespeichert: Temperatur={temp:.1f}, Luftfeuchtigkeit={hum:.1f}, Helligkeit={brightness} um {ntp_time}")
            
            return brightness  # Helligkeit für Anzeigeaktualisierung zurückgeben
            
        except sqlite3.Error as e:
            self.log.error(f"Fehler beim Speichern der Messung: {e}")
            self.conn.rollback()
            self.log.critical("Speichern der Messung fehlgeschlagen. Datenintegrität könnte beeinträchtigt sein.")
            return None

    # --- Sensorauslesen ---

    def read_dht11_sensor(self, instance, max_attempts=10):
        """
        Liest Daten vom DHT11-Sensor und gibt Temperatur und Luftfeuchtigkeit zurück.
        """
        result = instance.read()
        attempts = 0
        while not result.is_valid() and attempts < max_attempts:
            attempts += 1
            result = instance.read()
            time.sleep(0.5)
        
        if not result.is_valid():
            self.log.warning(f"Keine gültigen Werte nach {max_attempts} Versuchen erhalten")
            # Letzte Werte oder Standardwerte zurückgeben
            return self.temperature or 20.0, self.humidity or 50.0
        
        # Werte für zukünftige Verwendung speichern
        self.temperature = result.temperature
        self.humidity = result.humidity
        return result.temperature, result.humidity

    def print_database(self) -> None:
        """
        Gibt den Inhalt der 'measurements'-Tabelle auf der Konsole aus
        ohne Klammern, Anführungszeichen oder andere Sonderzeichen.
        """
        if self.conn is None:
            self.log.error("Datenbankverbindung ist nicht hergestellt.")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM measurements")
        rows = cursor.fetchall()

        if not rows:
            self.log.info("Die Tabelle 'measurements' ist leer.")
            return

        # Spaltennamen holen
        column_names = [description[0] for description in cursor.description]

        # Maximale Breite für jede Spalte berechnen
        column_widths = [len(name) for name in column_names]
        for row in rows:
            for i, value in enumerate(row):
                column_widths[i] = max(column_widths[i], len(str(value)))

        # Überschrift ausgeben
        header = " | ".join(f"{name:<{width}}" for name, width in zip(column_names, column_widths))
        self.log.info(header)
        self.log.info("-" * len(header))

        # Zeilen ausgeben
        for row in rows:
            row_str = " | ".join(f"{value:<{width}}" for value, width in zip(row, column_widths))
            self.log.info(row_str)

    def get_ntp_time(self, ip_address: str) -> Optional[str]:
        """
        Ruft die Serverzeit vom angegebenen NTP-Server ab und konvertiert sie in die lokale Zeitzone.

        Parameter:
        ip_address (str): Die IP-Adresse des NTP-Servers.

        Returns:
        str: Die formatierte lokale Zeit.
        """
        try:
            client = ntplib.NTPClient()
            response = client.request(ip_address, version=3)
            server_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
            
            # Zeitzone für die IP-Adresse abrufen
            try:
                response = requests.get(f"http://ip-api.com/json/{ip_address}")
                data = response.json()
                tz = pytz.timezone(data['timezone'])
            except Exception as e:
                self.log.warning(f"Konnte Zeitzone nicht bestimmen: {e}. Verwende UTC.")
                tz = pytz.UTC
                
            local_time = server_time.astimezone(tz)
            local_time_str = local_time.strftime('%Y-%m-%d %H:%M:%S')
            self.log.info(f"Lokale Zeit: {local_time_str} auf Server: {ip_address}")
            return local_time_str
            
        except Exception as e:
            self.log.error(f"Fehler beim Abrufen der NTP-Zeit: {e}")
            return None

    def close_connection(self) -> None:
        """
        Schließt die Datenbankverbindung.
        """
        if self.conn:
            self.conn.close()
            self.log.info("Datenbankverbindung geschlossen.")
            
    def initialize_lcd(self):
        """
        Initialisiert das LCD-Display.
        
        Returns:
            Character_LCD_I2C: Das initialisierte LCD-Objekt.
        """
        try:
            i2c = board.I2C()
            lcd = character_lcd.Character_LCD_I2C(i2c, self.LCD_COLUMNS, self.LCD_ROWS, self.LCD_I2C_ADDRESS)
            lcd.clear()
            lcd.backlight = True
            self.log.info("LCD erfolgreich initialisiert mit eingeschalteter Hintergrundbeleuchtung.")
            return lcd
        except Exception as e:
            self.log.error(f"Fehler bei LCD-Initialisierung: {e}")
            # Mock-LCD-Objekt zurückgeben, um Abstürze zu vermeiden
            return type('MockLCD', (), {'clear': lambda: None, 'message': ''})

    def display_on_lcd(self, temperature, humidity):
        """
        Zeigt Temperatur und Luftfeuchtigkeit auf dem LCD an.
        
        Args:
            temperature (float): Die anzuzeigende Temperatur.
            humidity (float): Die anzuzeigende Luftfeuchtigkeit.
        """
        try:
            self.lcd.clear()
            self.lcd.message = f"Temp: {temperature:.1f}C\nLuftfeuchte: {humidity:.1f}%"
            self.log.info(f"Angezeigt auf LCD: Temp: {temperature:.1f}C, Luftfeuchte: {humidity:.1f}%")
        except Exception as e:
            self.log.error(f"Fehler bei der Anzeige auf LCD: {e}")

    def initialize_brightness_sensor(self):
        """
        Initialisiert den Helligkeitssensor.
        
        Returns:
            AnalogIn: Der initialisierte Analogeingang für den Helligkeitssensor.
        """
        try:
            spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            cs = digitalio.DigitalInOut(board.D5)
            mcp = MCP.MCP3008(spi, cs)
            channel = AnalogIn(mcp, MCP.P0)
            self.log.info("Helligkeitssensor erfolgreich initialisiert.")
            return channel
        except Exception as e:
            self.log.error(f"Fehler bei der Initialisierung des Helligkeitssensors: {e}")
            # Mock-Sensor zurückgeben, um Abstürze zu vermeiden
            return type('MockSensor', (), {'value': 2000})

    def read_brightness(self):
        """
        Liest den Helligkeitswert vom Sensor aus.
        
        Returns:
            int: Der Helligkeitswert in Lux.
        """
        try:
            # Zuerst versuchen, vom BH1750-Lichtsensor zu lesen
            try:
                # BH1750-Konstanten
                DEVICE = 0x5c  # Standard I2C-Geräteadresse
                ONE_TIME_HIGH_RES_MODE_1 = 0x20  # Hochauflösungsmodus
                
                # Bus basierend auf Raspberry Pi-Version auswählen
                bus = smbus.SMBus(1) if GPIO.RPI_REVISION > 1 else smbus.SMBus(0)
                
                # Daten vom Sensor lesen
                data = bus.read_i2c_block_data(DEVICE, ONE_TIME_HIGH_RES_MODE_1)
                
                # In Lux umrechnen
                lux = ((data[1] + (256 * data[0])) / 1.2)
                lux_int = int(round(lux))
                
                self.log.info(f"Helligkeit: {lux_int} Lux (BH1750-Sensor)")
                return lux_int
                
            except Exception as e:
                # Bei Fehler auf die ursprüngliche MCP3008-Methode zurückfallen
                self.log.warning(f"BH1750-Sensor fehlgeschlagen: {e}. Verwende analogen Sensor.")
                
                # Rohwert und Spannung vom MCP3008 abrufen
                raw_value = self.brightness_channel.value
                voltage = self.brightness_channel.voltage
                
                # Spannung in Lux umrechnen mit der ursprünglichen Formel
                if voltage < 0.1:
                    lux = 0  # Sehr dunkel
                elif voltage < 1.0:
                    lux = int(voltage * 1000)  # Schwaches Licht
                else:
                    lux = int(voltage * 2000)  # Helles Licht
                    
                self.log.info(f"Helligkeit: {lux} Lux (roh: {raw_value}, Spannung: {voltage:.2f}V)")
                return lux
                
        except Exception as e:
            self.log.error(f"Fehler beim Lesen der Helligkeit: {e}")
            return 500  # Standardwert für moderate Helligkeit

    def initialize_matrix_display(self):
        """
        Initialisiert das 8x8 LED-Matrix-Display mit dem MAX7219-Treiber.
        
        Returns:
            max7219 device: Das initialisierte Matrix-Display-Objekt.
        """
        try:
            from luma.led_matrix.device import max7219
            from luma.core.interface.serial import spi, noop

            # SPI-Schnittstelle initialisieren
            serial = spi(port=0, device=1, gpio=noop())
            
            # MAX7219-Gerät erstellen
            device = max7219(serial, cascaded=1, block_orientation=90, rotate=0)
            
            self.log.info("Matrix-Display erfolgreich initialisiert.")
            return device
            
        except Exception as e:
            self.log.error(f"Fehler bei der Initialisierung des Matrix-Displays: {e}")
            return None

    def display_brightness_symbol(self, brightness):
        """
        Zeigt je nach Helligkeitsstufe entweder ein Tages- oder Nachtsymbol auf dem Matrix-Display an.
        Das Symbol bleibt sichtbar bis zum nächsten Aufruf.
        
        Args:
            brightness (int): Der Helligkeitswert vom Sensor.
        """
        # Prüfen, ob Matrix erfolgreich initialisiert wurde
        if self.matrix is None:
            self.log.warning("Matrix-Display ist nicht verfügbar. Symbol kann nicht angezeigt werden.")
            return
            
        try:
            from luma.core.render import canvas
            
            # Sonnen- und Mond-Bitmaps (8x8) definieren
            sun_bitmap = [
                0b00111100,
                0b01111110,
                0b11111111,
                0b11111111,
                0b11111111,
                0b01111110,
                0b00111100,
                0b00000000,
            ]

            moon_bitmap = [
                0b00111100,
                0b01111110,
                0b01110000,
                0b01100000,
                0b01100000,
                0b01110000,
                0b01111110,
                0b00111100,
            ]
            
            # Schwellenwert basierend auf beobachteten Messwerten anpassen
            # Da unsere Werte im Dunkeln unter 10 und mit Taschenlampe unter 300 liegen
            is_day_mode = brightness >= 100
            
            # Symbol zum Anzeigen auswählen
            symbol = sun_bitmap if is_day_mode else moon_bitmap
            
            # Symbol mit dem Canvas zeichnen
            with canvas(self.matrix) as draw:
                for y in range(8):
                    for x in range(8):
                        if symbol[y] & (1 << (7 - x)):
                            draw.point((x, y), fill="white")
            
            if is_day_mode:
                self.log.info(f"Tagessymbol angezeigt auf Matrix (Helligkeit: {brightness})")
            else:
                self.log.info(f"Nachtsymbol angezeigt auf Matrix (Helligkeit: {brightness})")
                
        except Exception as e:
            self.log.error(f"Fehler beim Anzeigen des Helligkeitssymbols: {e}")

    def initialize_seven_segment(self):
        """
        Initialisiert das 7-Segment-Display.
        
        Returns:
            Seg7x4: Das initialisierte 7-Segment-Display-Objekt.
        """
        try:
            i2c = board.I2C()
            display = adafruit_ht16k33.segments.Seg7x4(i2c, address=self.SEVEN_SEGMENT_I2C_ADDRESS)
            display.fill(0)  # Display löschen
            display.brightness = 0.5  # Mittlere Helligkeit
            self.log.info("7-Segment-Display erfolgreich initialisiert.")
            return display
        except Exception as e:
            self.log.error(f"Fehler bei der Initialisierung des 7-Segment-Displays: {e}")
            return None

    def display_measurements_on_seven_segment(self, temperature, humidity):
        """
        Zeigt Temperatur und Luftfeuchtigkeit abwechselnd auf dem 7-Segment-Display an.
        Zeigt Temperatur mit 'C'-Suffix, dann Luftfeuchtigkeit mit '%'-Suffix.
        
        Args:
            temperature (float): Die gemessene Temperatur.
            humidity (float): Die gemessene Luftfeuchtigkeit.
        """
        if self.seven_segment is None:
            self.log.warning("7-Segment-Display ist nicht verfügbar.")
            return
            
        try:
            # Zuerst Temperatur mit C-Suffix anzeigen
            self.seven_segment.fill(0)  # Display löschen
            
            # Temperatur für Anzeige formatieren mit einer Dezimalstelle und 'C'-Suffix
            if temperature < 0 and temperature > -10:  # Negative einstellige Zahl
                temp_str = f"{temperature:.1f}"  # Zeigt etwa "-5.2"
            elif temperature < 10 and temperature >= 0:  # Positive einstellige Zahl
                temp_str = f"{temperature:.1f}C"  # Zeigt etwa "5.2C"
            elif temperature < 100:  # Zweistellige Zahl
                temp_str = f"{temperature:.0f}C"  # Zeigt etwa "25C"
            else:
                temp_str = "99C"  # Maximal anzeigbare Temperatur
                
            self.seven_segment.print(temp_str)
            self.log.info(f"7-Segment-Display zeigt Temperatur: {temp_str}")
            time.sleep(1.0)  # Temperatur 1 Sekunde lang anzeigen
            
            # Dann Luftfeuchtigkeit anzeigen
            self.seven_segment.fill(0)  # Display löschen
            
            # Luftfeuchtigkeit für Anzeige formatieren mit einer Dezimalstelle und '%'-Suffix
            if humidity < 10:
                hum_str = f"{humidity:.1f}%"  # Zeigt etwa "5.2%"
            elif humidity < 100:
                hum_str = f"{humidity:.0f}%"  # Zeigt etwa "45%"
            else:
                hum_str = "99%"  # Maximal anzeigbare Luftfeuchtigkeit
                
            self.seven_segment.print(hum_str)
            self.log.info(f"7-Segment-Display zeigt Luftfeuchtigkeit: {hum_str}")
            
        except Exception as e:
            self.log.error(f"Fehler bei der Anzeige auf 7-Segment-Display: {e}")

    def update_all_displays(self, temp: float, hum: float, brightness: int) -> None:
        """
        Aktualisiert alle Anzeigegeräte mit den aktuellen Messwerten.
        
        Args:
            temp (float): Die gemessene Temperatur.
            hum (float): Die gemessene Luftfeuchtigkeit.
            brightness (int): Die gemessene Helligkeit.
        """
        try:
            # 1. Anzeige auf LCD
            self.display_on_lcd(temp, hum)
            
            # 2. Helligkeitssymbol auf Matrix-Display anzeigen
            self.display_brightness_symbol(brightness)
            
            # 3. Messwerte auf 7-Segment-Display anzeigen
            self.display_measurements_on_seven_segment(temp, hum)
            
            self.log.info("Alle Anzeigen erfolgreich aktualisiert")
            
        except Exception as e:
            self.log.error(f"Fehler beim Aktualisieren der Anzeigen: {e}")
