"""
This module provides a set of operations for interacting with an SQLite database 
to store and manage sensor data, specifically temperature and humidity measurements. 
It includes functionalities to establish a database connection, create tables, 
save sensor readings, and retrieve the current time from an NTP server.

The module uses a `ColoredLogger` for logging messages, providing clear and 
color-coded output to the console. It is designed to be used as part of a 
larger application, such as a greenhouse monitoring system, where real-time 
sensor data needs to be logged and stored in a persistent manner.

Classes:
    DatabaseOperations: Encapsulates the database operations.

Functions:
    parse_args: Parses command-line arguments.
"""
import argparse
import sqlite3
import time
import ntplib
import pytz
import requests
import RPi.GPIO as GPIO
import dht11
from typing import Optional
from datetime import datetime, timezone
from school_logging.log import ColoredLogger

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
    DATABASE_FILE: str = "/app/db_data/measurements.db"
    TIME_SERVER: str = '216.239.35.0'  # Replace with required NTP server '10.254.5.115'
# --- Configuration ---
    LCD_COLUMNS = 16
    LCD_ROWS = 2
    LCD_I2C_ADDRESS = 0x21  # I2C address of the LCD
    DHT11_PIN = 4          # GPIO pin connected to the DHT11 sensor
    SEVEN_SEGMENT_I2C_ADDRESS = 0x70  # I2C address of the 7-segment display
    # TIME_SERVER: str = 'time.google.com'  # '10.254.5.115'  # NTP server to use
    NUM_ITERATIONS = 10  # Number of iterations for data collection

    # --- Globals ---
    log = None  # Global logger instance
    temperature, humidity = 0.0, 0.0  # Initialize global temperature and humidity

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
            self.conn = sqlite3.connect(self.DATABASE_FILE)
            self.log.info("Connected to database: %s", self.DATABASE_FILE)
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
            sensor_name (str): The name of the sensor.
            value (float): The measured value.
        """
        if self.conn is None:
            self.log.error("Database connection is not established.")
            return

        ntp_time = self.get_ntp_time(self.TIME_SERVER)
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

    # --- Sensor Reading ---

    def read_dht11_sensor(self, instance):
        """Reads data from the DHT11 sensor and returns temperature and humidity."""
        result = instance.read()
        while not result.is_valid():
            result = instance.read()
            time.sleep(2)
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

    def read_sensor(self) -> None:
        """
        Simulates reading sensors and returns temperature and humidity.
        #todo replace with real data
        """
        temperature = 20 + 10 * time.time() % 10  # Simulate temperature readings between 20 and 30 degrees
        humidity = 40 + 30 * time.time() % 30  # Simulate humidity readings between 40 and 70 percent
        return temperature, humidity

    def get_ntp_time(self, ip_address: str) -> Optional[datetime]:
        """
        Fetches the server time from the given IP address and converts it to the local time zone.

        Parameters:
        ip_address (str): The IP address of the NTP server.

        Returns:
        datetime
        """
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

    def close_connection(self) -> None:
        """
        Closes the database connection.
        """
        if self.conn:
            self.conn.close()
            self.log.info("Database connection closed.")

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
    log: ColoredLogger = ColoredLogger(name='data', verbose=args.verbose)
    db_ops = DatabaseOperations(log)

    # Initialize GPIO and DHT11 sensor
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    instance = dht11.DHT11(pin=db_ops.DHT11_PIN)

    try:
        db_ops.create_database()
        for _ in range(db_ops.NUM_ITERATIONS):
            temperature, humidity = db_ops.read_dht11_sensor(instance)
            db_ops.save_measurement(temperature, humidity)
            log.info("data saved in db successfully")
            time.sleep(2)
        # Printing generated table
        db_ops.print_database()

    except Exception as e:
        log.critical("An unexpected error occurred: %s", e)

    finally:
       db_ops.close_connection()
