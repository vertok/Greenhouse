# Project: Greenhouse Control System Enhancement for Floristik GmbH

## Project Description

This project aims to commission and enhance an existing greenhouse control system for **Floristik GmbH**. The initial system provides basic temperature monitoring using a DHT11 sensor and displays the temperature on a 7-segment LED display. However, it is currently not operational.

## Project Usage

1. First please clone the Greenhouse git project via
   git clone https://github.com/vertok/Greenhouse.git
2. Jump to project directory via:
   cd Greenhouse
3. .\scripts\shell\install_dependencies.sh
4. .//.venv//Scripts//activate 
5. Add logging git submodule via:
   git submodule add https://github.com/vertok/school_logging.git school_logging
6. Make sure submodule project is on the newest stage via:
   git submodule update --init --recursive


## Key Tasks

The project involves the following key tasks:

-   **Commissioning:** Bring the existing system into an operational state, enabling basic temperature monitoring and display.
-   **Expansion:** Iteratively expand the system's capabilities by integrating new sensors (e.g., humidity, soil moisture, light) and actuators (e.g., ventilation, irrigation).
-   **Software Development:** Develop Python scripts to:
    -   Manage hardware components.
    -   Implement control logic based on sensor readings.
    -   Log data to an SQLite database.
-   **Database Integration:** Utilize an SQLite database to store sensor readings for analysis and future use in control algorithms.
-   **Documentation:** Provide comprehensive documentation, including:
    -   Flowcharts/Structure Charts (PAP)
    -   Well-commented Python code
    -   Wiring diagrams and other relevant technical details

## Development Approach

The project will follow an iterative development approach, with each version building upon the previous one.

-   **Version 1.0:** Focuses on commissioning the initial system and implementing basic temperature logging to the database.
-   **Subsequent Versions:** Will introduce additional sensors, control features, and enhanced database functionality.

## Client

**Floristik GmbH**
Kaditzer Straße 4-10
01139 Dresden
