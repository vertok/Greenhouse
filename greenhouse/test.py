#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import board
import busio
import adafruit_character_lcd.character_lcd_i2c as character_lcd
import RPi.GPIO as GPIO
import dht11
from Adafruit_LED_Backpack import SevenSegment
import threading
import sqlite3
import ntplib
import pytz
import requests
from typing import Optional
from datetime import datetime, timezone
from school_logging.log import ColoredLogger
import argparse

# --- Configuration ---
LCD_COLUMNS = 16
LCD_ROWS = 2
LCD_I2C_ADDRESS = 0x21  # I2C address of the LCD
DHT11_PIN = 4          # GPIO pin connected to the DHT11 sensor
SEVEN_SEGMENT_I2C_ADDRESS = 0x70  # I2C address of the 7-segment display
DATABASE_FILE: str = "measurements.db"
TIME_SERVER: str = 'pool.ntp.org'  # NTP server to use

# --- Globals ---
log = None  # Global logger instance
temperature, humidity = 0.0, 0.0 # Initialize global temperature and humidity

# --- Database Operations ---
class DatabaseOperations:
    """
    Provides methods to interact with an SQLite database.
    This class encapsulates database operations such as creating a database,
    saving measurements, and handling the database connection. It is designed to
    work with an SQLite database and uses a ColoredLogger instance for logging.

    Attributes:
        DATABASE_FILE (str): The path to the SQLite database file.
        log (ColoredLogger): Logger instance for logging messages.
        conn (Optional[sqlite3.Connection]): Database connection object.
    """

    def __init__(self, log: ColoredLogger) -> None:
        """
        Initializes the DatabaseOperations class with a logger and establishes a database connection.
        """
        self.log: ColoredLogger = log
        self.conn: Optional[sqlite3.Connection] = None
        self.connect_to_database()

    def connect_to_database(self) -> None:
        """
        Establishes a connection to the SQLite database.
        """
        try:
            self.conn = sqlite3.connect(DATABASE_FILE)
            self.log.info("Connected to database: %s", DATABASE_FILE)
        except sqlite3.Error as e:
            self.log.error("Error connecting to database: %s", e)
            self.log.critical("Failed to establish database connection.")

    def create_database(self) -> None:
        """
        Creates the database table if it doesn't exist.
        """
        try:
            cursor = self.conn.cursor()

            # Check if the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='measurements'")
            table_exists = cursor.fetchone() is not None

            # Create the table if it doesn't exist
            if not table_exists:
                cursor.execute("""
                    CREATE TABLE measurements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        temperature REAL,
                        humidity REAL
                    )
                """)
                self.conn.commit()
                self.log.info("Table 'measurements' created.")
            else:
                self.log.info("Table 'measurements' already exists.")
        except sqlite3.Error as e:
            self.log.error("Error creating table: %s", e)

    def save_measurement(self, temp: float, hum: float) -> None:
        """
        Saves a measurement to the database.

        Args:
            temp (float): The temperature value.
            hum (float): The humidity value.
        """
        if self.conn is None:
            self.log.error("Database connection is not established.")
            return

        ntp_time = self.get_ntp_time(TIME_SERVER)
        if ntp_time is None:
            self.log.error("Could not get time from NTP server. Measurement not saved.")
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO measurements (timestamp, temperature, humidity) VALUES (?, ?, ?)",
                (ntp_time, temp, hum)
            )
            self.conn.commit()
            self.log.info("Measurement saved: temperature=%f, humidity=%f at %s", temp, hum, ntp_time)
        except sqlite3.Error as e:
            self.log.error("Error saving measurement: %s", e)
            self.conn.rollback()
            self.log.critical("Failed to save measurement. Data integrity might be compromised.")

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

    def get_ntp_time(self, ip_address: str) -> Optional[datetime]:
        """
        Fetches the server time from the given IP address and converts it to the local time zone.

        Parameters:
        ip_address (str): The IP address of the NTP server.

        Returns:
        datetime
        """
        try:
          client = ntplib.NTPClient()
          response = client.request(ip_address, version=3)
          server_time = datetime.fromtimestamp(response.tx_time, timezone.utc)
          # Fetch the time zone for the IP address using a free service
          response = requests.get(f"http://ip-api.com/json/{ip_address}")
          data = response.json()
          tz = pytz.timezone(data['timezone'])
          local_time = server_time.astimezone(tz)
          local_time = local_time.strftime('%Y-%m-%d %H:%M:%S')
          self.log.info("Local time: %s on server: %s", local_time, ip_address)
          return local_time
        except:
          self.log.error("error while getting ntp time")

    def close_connection(self) -> None:
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.log.info("Database connection closed.")

# --- Display Functions ---

def display_on_lcd(lcd, temperature, humidity):
    """Displays temperature and humidity on the LCD."""
    lcd.clear()
    lcd.message = f"Temp: {temperature:.1f}C\nHum: {humidity:.0f}%"

def display_on_seven_segment(segment, value, label):
    """Displays the temperature or humidity on the 7-segment display."""
    segment.clear()

    if label == "C":
        formatted_value = "{:4.1f}".format(value)
        for i, char in enumerate(formatted_value):
            segment.set_digit(i, char)
        segment.set_digit_raw(3, 0b01001110) # "C"

    elif label == "%":
        formatted_value = "{:4.0f}".format(value)
        for i, char in enumerate(formatted_value):
            segment.set_digit(i, char)
        segment.set_digit_raw(2, 0b01100110) # "%"
        segment.set_digit_raw(3, 0b01100110) # "%"

    segment.write_display()

# --- Sensor Reading ---

def read_dht11_data(instance):
    """Reads data from the DHT11 sensor and returns temperature and humidity."""
    result = instance.read()
    while not result.is_valid():
        result = instance.read()
        time.sleep(0.5)
    return result.temperature, result.humidity

# --- Thread Functions ---

def lcd_thread_function(lcd, data_lock):
    """Thread function for updating the LCD."""
    global temperature, humidity
    while True:
        with data_lock:
            display_on_lcd(lcd, temperature, humidity)
        time.sleep(5)

def seven_segment_thread_function(segment, data_lock):
    """Thread function for updating the 7-segment display."""
    global temperature, humidity
    while True:
        with data_lock:
            display_on_seven_segment(segment, temperature, "C")
            time.sleep(2.5)
            display_on_seven_segment(segment, humidity, "%")
            time.sleep(2.5)

# --- Main ---

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the database operations script.
    """
    parser = argparse.ArgumentParser(description='Database Operations')
    parser.add_argument('--verbose', type=str.upper,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Set the logging level (case-insensitive)')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    log = ColoredLogger(name='data', verbose=args.verbose)
    # Initialize data lock
    data_lock = threading.Lock()

    # Initialize I2C bus for LCD and 7-segment
    i2c = busio.I2C(board.SCL, board.SDA)

    # Initialize LCD
    lcd = character_lcd.Character_LCD_I2C(i2c, LCD_COLUMNS, LCD_ROWS, LCD_I2C_ADDRESS)
    lcd.clear()
    lcd.backlight = True
    lcd.message = "Initializing..."

    # Initialize GPIO and DHT11 sensor
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    instance = dht11.DHT11(pin=DHT11_PIN)

    # Initialize 7-segment display
    segment = SevenSegment.SevenSegment(address=SEVEN_SEGMENT_I2C_ADDRESS)
    segment.begin()
    segment.clear()
    segment.write_display()

    print("Initialization complete.")

    # Initialize database operations
    db_ops = DatabaseOperations(log)
    db_ops.create_database()

    # Start display threads
    lcd_thread = threading.Thread(target=lcd_thread_function, args=(lcd, data_lock))
    seven_segment_thread = threading.Thread(target=seven_segment_thread_function, args=(segment, data_lock))

    lcd_thread.daemon = True
    seven_segment_thread.daemon = True

    lcd_thread.start()
    seven_segment_thread.start()

    try:
        while True:
            # Read sensor data
            temperature, humidity = read_dht11_data(instance)

            # Acquire lock before accessing shared variables
            with data_lock:
                # Save to database using the read values
                db_ops.save_measurement(temperature, humidity)

            log.info("data saved in db successfully")

            time.sleep(60) # Adjust the sleep time as needed

    except KeyboardInterrupt:
        print("Program stopped by user.")

    finally:
        lcd.clear()
        lcd.backlight = False
        segment.clear()
        segment.write_display()
        GPIO.cleanup()
        db_ops.close_connection()
        print("Resources cleaned up.")
