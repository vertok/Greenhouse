"""
This module provides a main function to execute database operations.
"""

import argparse
import time
import RPi.GPIO as GPIO
import dht11

from school_logging.log import ColoredLogger

from greenhouse.database_operations import DatabaseOperations

def parse_args() -> argparse.Namespace:
    """
    Parses command-line arguments for the database operations script.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Database Operations')
    parser.add_argument('--verbose', type=str.upper,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO',
                        help='Set the logging level (case-insensitive)')
    parser.add_argument('--iterations', type=int, default=10,
                        help='Number of measurements to take')
    parser.add_argument('--interval', type=int, default=3,
                        help='Interval between measurements in seconds')
    args = parser.parse_args()
    return args

def main():
    """
    Main function to execute greenhouse control operations.
    """
    args = parse_args()
    log = ColoredLogger(name='greenhouse', verbose=args.verbose)
    
    log.info("Starting Greenhouse Control System")
    log.info("Initializing components...")
    
    try:
        # Initialize database operations with better error handling
        db_ops = None
        try:
            db_ops = DatabaseOperations(log)
        except Exception as e:
            log.error(f"Failed to initialize database operations: {e}")
            return
        
        # Only proceed if database operations are properly initialized
        if db_ops and db_ops.conn:
            # Initialize GPIO and DHT11 sensor
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            instance = dht11.DHT11(pin=db_ops.DHT11_PIN)
            
            # Create database if it doesn't exist
            db_ops.create_database()
            
            # Main measurement loop
            log.info(f"Starting {args.iterations} measurements with {args.interval}s interval")
            for i in range(args.iterations):
                log.info(f"Measurement {i+1}/{args.iterations}")
                
                # Read sensor data
                temperature, humidity = db_ops.read_dht11_sensor(instance)
                log.info(f"Read: Temperature={temperature}°C, Humidity={humidity}%")
                
                # Save measurements to database and get brightness
                brightness = db_ops.save_measurement(temperature, humidity)
                
                # Update all displays
                if brightness is not None:
                    db_ops.update_all_displays(temperature, humidity, brightness)
                
                # Wait before next measurement
                time.sleep(args.interval)
            
            # Print database contents
            db_ops.print_database()
        else:
            log.error("Database connection unavailable, cannot proceed.")

    except KeyboardInterrupt:
        log.info("Greenhouse Control System stopped by user")
        
    except Exception as e:
        log.critical(f"An unexpected error occurred: {e}", exc_info=True)

    finally:
        log.info("Cleaning up resources...")
        if 'db_ops' in locals() and db_ops is not None:
            db_ops.close_connection()
        try:
            GPIO.cleanup()
        except:
            pass
        log.info("Greenhouse Control System stopped")

if __name__ == "__main__":
    main()
