import time
import sqlite3
from typing import Optional
from datetime import datetime, timezone
import ntplib
import requests
import pytz
import RPi.GPIO as GPIO
import dht11
import board
import digitalio
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import adafruit_ht16k33.segments
import smbus  # Importieren von smbus für I2C-Kommunikation

from school_logging.log import ColoredLogger

class DatabaseOperations:
    # --- Konfiguration ---
    DATABASE_FILE: str = "greenhouse.db"
    TIME_SERVER: str = '216.239.35.0'  # Bei Bedarf NTP-Server anpassen '10.254.5.115'
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
        """Reads data from the DHT11 sensor and returns temperature and humidity."""
        result = instance.read()
        attempts = 0
        while not result.is_valid() and attempts < max_attempts:
            attempts += 1
            result = instance.read()
            time.sleep(0.5)
        
        if not result.is_valid():
            self.log.warning(f"Failed to get valid reading after {max_attempts} attempts")
            # Return last values or defaults if never read successfully before
            return self.temperature or 20.0, self.humidity or 50.0
        
        # Store values for future use if sensor fails
        self.temperature = result.temperature
        self.humidity = result.humidity
        return result.temperature, result.humidity

    def print_database(self) -> None:
        """
        Prints the contents of the 'measurements' table to the console
        without brackets, quotes, or other special characters.
        """
        if self.conn is None:
            self.log.error("Database connection is not established.")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM measurements")
        rows = cursor.fetchall()

        if not rows:
            self.log.info("The 'measurements' table is empty.")
            return

        # Get column names
        column_names = [description[0] for description in cursor.description]

        # Calculate maximum width for each column
        column_widths = [len(name) for name in column_names]
        for row in rows:
            for i, value in enumerate(row):
                column_widths[i] = max(column_widths[i], len(str(value)))

        # Print header
        header = " | ".join(f"{name:<{width}}" for name, width in zip(column_names, column_widths))
        self.log.info(header)
        self.log.info("-" * len(header))

        # Print rows
        for row in rows:
            row_str = " | ".join(f"{value:<{width}}" for value, width in zip(row, column_widths))
            self.log.info(row_str)

    def get_ntp_time(self, ip_address: str) -> Optional[str]:
        """
        Fetches the server time from the given IP address and converts it to the local time zone.

        Parameters:
        ip_address (str): The IP address of the NTP server.

        Returns:
        str: The formatted local time.
        """
        try:
            client = ntplib.NTPClient()
            response = client.request(ip_address, version=3)
            server_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
            
            # Fetch the time zone for the IP address using a free service
            try:
                response = requests.get(f"http://ip-api.com/json/{ip_address}")
                data = response.json()
                tz = pytz.timezone(data['timezone'])
            except Exception as e:
                self.log.warning(f"Could not determine timezone: {e}. Using UTC.")
                tz = pytz.UTC
                
            local_time = server_time.astimezone(tz)
            local_time_str = local_time.strftime('%Y-%m-%d %H:%M:%S')
            self.log.info(f"Local time: {local_time_str} on server: {ip_address}")
            return local_time_str
            
        except Exception as e:
            self.log.error(f"Error getting NTP time: {e}")
            return None

    def close_connection(self) -> None:
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.log.info("Database connection closed.")
            
    def initialize_lcd(self):
        """
        Initializes the LCD display.
        
        Returns:
            Character_LCD_I2C: The initialized LCD object.
        """
        try:
            i2c = board.I2C()
            lcd = character_lcd.Character_LCD_I2C(i2c, self.LCD_COLUMNS, self.LCD_ROWS, self.LCD_I2C_ADDRESS)
            lcd.clear()
            lcd.backlight = True
            self.log.info("LCD initialized successfully with backlight on.")
            return lcd
        except Exception as e:
            self.log.error(f"Failed to initialize LCD: {e}")
            # Return a mock LCD object to prevent crashes if hardware is not available
            return type('MockLCD', (), {'clear': lambda: None, 'message': ''})

    def display_on_lcd(self, temperature, humidity):
        """
        Displays temperature and humidity on the LCD.
        
        Args:
            temperature (float): The temperature to display.
            humidity (float): The humidity to display.
        """
        try:
            self.lcd.clear()
            self.lcd.message = f"Temp: {temperature:.1f}C\nHumidity: {humidity:.1f}%"
            self.log.info(f"Displayed on LCD: Temp: {temperature:.1f}C, Humidity: {humidity:.1f}%")
        except Exception as e:
            self.log.error(f"Failed to display on LCD: {e}")

    def initialize_brightness_sensor(self):
        """
        Initializes the brightness sensor.
        
        Returns:
            AnalogIn: The initialized analog input for brightness sensor.
        """
        try:
            spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)
            cs = digitalio.DigitalInOut(board.D5)
            mcp = MCP.MCP3008(spi, cs)
            channel = AnalogIn(mcp, MCP.P0)
            self.log.info("Brightness sensor initialized successfully.")
            return channel
        except Exception as e:
            self.log.error(f"Failed to initialize brightness sensor: {e}")
            # Return a mock sensor object to prevent crashes if hardware is not available
            return type('MockSensor', (), {'value': 2000})

    def read_brightness(self):
        """
        Reads the brightness value from the sensor.
        
        Returns:
            int: The brightness value in lux.
        """
        try:
            # First try to read from BH1750 light sensor if available
            try:
                # BH1750 constants
                DEVICE = 0x5c  # Standard I2C device address
                ONE_TIME_HIGH_RES_MODE_1 = 0x20  # High resolution mode
                
                # Select bus based on Raspberry Pi version
                bus = smbus.SMBus(1) if GPIO.RPI_REVISION > 1 else smbus.SMBus(0)
                
                # Read data from the sensor
                data = bus.read_i2c_block_data(DEVICE, ONE_TIME_HIGH_RES_MODE_1)
                
                # Convert to lux
                lux = ((data[1] + (256 * data[0])) / 1.2)
                lux_int = int(round(lux))
                
                self.log.info(f"Brightness: {lux_int} lux (BH1750 sensor)")
                return lux_int
                
            except Exception as e:
                # Fall back to the original MCP3008 method if BH1750 fails
                self.log.warning(f"BH1750 sensor failed: {e}. Falling back to analog sensor.")
                
                # Get raw value and voltage from the MCP3008
                raw_value = self.brightness_channel.value
                voltage = self.brightness_channel.voltage
                
                # Convert voltage to lux using the original formula
                if voltage < 0.1:
                    lux = 0  # Very dark
                elif voltage < 1.0:
                    lux = int(voltage * 1000)  # Low light
                else:
                    lux = int(voltage * 2000)  # Bright light
                    
                self.log.info(f"Brightness: {lux} lux (raw: {raw_value}, voltage: {voltage:.2f}V)")
                return lux
                
        except Exception as e:
            self.log.error(f"Failed to read brightness: {e}")
            return 500  # Default value representing moderate light

    def initialize_matrix_display(self):
        """
        Initializes the 8x8 LED matrix display using the MAX7219 driver.
        
        Returns:
            max7219 device: The initialized matrix display object.
        """
        try:
            from luma.led_matrix.device import max7219
            from luma.core.interface.serial import spi, noop

            # Initialize the SPI interface
            serial = spi(port=0, device=1, gpio=noop())
            
            # Create the MAX7219 device
            device = max7219(serial, cascaded=1, block_orientation=90, rotate=0)
            
            self.log.info("Matrix display initialized successfully.")
            return device
            
        except Exception as e:
            self.log.error(f"Failed to initialize matrix display: {e}")
            return None

    def display_brightness_symbol(self, brightness):
        """
        Displays either day or night symbol on the matrix display based on the brightness level.
        Symbol will remain visible until next call.
        
        Args:
            brightness (int): The brightness value from the sensor.
        """
        # Check if matrix was successfully initialized
        if self.matrix is None:
            self.log.warning("Matrix display is not available. Cannot display symbol.")
            return
            
        try:
            from luma.core.render import canvas
            
            # Define sun and moon bitmaps (8x8)
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
            
            # Adjust threshold based on your observed readings
            # Since your readings are below 10 in the dark and below 300 with a flashlight
            is_day_mode = brightness >= 100
            
            # Choose the symbol to display
            symbol = sun_bitmap if is_day_mode else moon_bitmap
            
            # Draw the symbol using the canvas
            with canvas(self.matrix) as draw:
                for y in range(8):
                    for x in range(8):
                        if symbol[y] & (1 << (7 - x)):
                            draw.point((x, y), fill="white")
            
            if is_day_mode:
                self.log.info(f"Day symbol displayed on matrix (brightness: {brightness})")
            else:
                self.log.info(f"Night symbol displayed on matrix (brightness: {brightness})")
                
        except Exception as e:
            self.log.error(f"Failed to display brightness symbol: {e}")

    def initialize_seven_segment(self):
        """
        Initializes the 7-segment display.
        
        Returns:
            Seg7x4: The initialized 7-segment display object.
        """
        try:
            i2c = board.I2C()
            display = adafruit_ht16k33.segments.Seg7x4(i2c, address=self.SEVEN_SEGMENT_I2C_ADDRESS)
            display.fill(0)  # Clear the display
            display.brightness = 0.5  # Medium brightness
            self.log.info("7-segment display initialized successfully.")
            return display
        except Exception as e:
            self.log.error(f"Failed to initialize 7-segment display: {e}")
            return None

    def display_measurements_on_seven_segment(self, temperature, humidity):
        """
        Displays temperature and humidity alternately on the 7-segment display.
        Shows temperature with 'C' suffix, then humidity with '%' suffix.
        
        Args:
            temperature (float): The measured temperature.
            humidity (float): The measured humidity.
        """
        if self.seven_segment is None:
            self.log.warning("7-segment display is not available.")
            return
            
        try:
            # First show temperature with C suffix
            self.seven_segment.fill(0)  # Clear the display
            
            # Format temperature for display with one decimal place and 'C' suffix
            if temperature < 0 and temperature > -10:  # Negative single digit
                temp_str = f"{temperature:.1f}"  # Will show something like "-5.2"
            elif temperature < 10 and temperature >= 0:  # Positive single digit
                temp_str = f"{temperature:.1f}C"  # Will show something like "5.2C"
            elif temperature < 100:  # Double digit
                temp_str = f"{temperature:.0f}C"  # Will show something like "25C"
            else:
                temp_str = "99C"  # Max displayable temperature
                
            self.seven_segment.print(temp_str)
            self.log.info(f"7-segment display showing temperature: {temp_str}")
            time.sleep(1.0)  # Show temperature for 1 second
            
            # Then show humidity
            self.seven_segment.fill(0)  # Clear the display
            
            # Format humidity for display with one decimal place and '%' suffix
            if humidity < 10:
                hum_str = f"{humidity:.1f}%"  # Will show something like "5.2%"
            elif humidity < 100:
                hum_str = f"{humidity:.0f}%"  # Will show something like "45%"
            else:
                hum_str = "99%"  # Max displayable humidity
                
            self.seven_segment.print(hum_str)
            self.log.info(f"7-segment display showing humidity: {hum_str}")
            
        except Exception as e:
            self.log.error(f"Failed to display on 7-segment: {e}")

    def update_all_displays(self, temp: float, hum: float, brightness: int) -> None:
        """
        Updates all display devices with the current measurements.
        
        Args:
            temp (float): The measured temperature.
            hum (float): The measured humidity.
            brightness (int): The measured brightness level.
        """
        try:
            # 1. Display on LCD
            self.display_on_lcd(temp, hum)
            
            # 2. Display brightness symbol on matrix display
            self.display_brightness_symbol(brightness)
            
            # 3. Display measurements as scrolling text on 7-segment display
            self.display_measurements_on_seven_segment(temp, hum)
            
            self.log.info("All displays updated successfully")
            
        except Exception as e:
            self.log.error(f"Error updating displays: {e}")
