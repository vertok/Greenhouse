"""
This module provides a main function to execute database operations.
"""

import argparse
import time

from school_logging.log import ColoredLogger

from greenhouse.database_operations import DatabaseOperations  # Import from database_operations.py

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
    args = parser.parse_args()
    return args

def main():
    """
    Main function to execute database operations.
    """
    args = parse_args()
    log: ColoredLogger = ColoredLogger(name='data', verbose=args.verbose)
    log.debug(args)
    db_ops = DatabaseOperations(log)
    try:
        db_ops.create_database()
        for _ in range(10):
            temperature, humidity = db_ops.read_sensor()
            db_ops.save_measurement(temperature, humidity)
            log.info("Data saved in db successfully")
            time.sleep(1)
        # Printing generated table
        db_ops.print_database()

    except Exception as e:
        log.critical("An unexpected error occurred: %s", e)

    finally:
        db_ops.close_connection()

if __name__ == "__main__":
    main()
