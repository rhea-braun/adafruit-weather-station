# MagTag E-Ink Weather Station

An ultra-low-power, battery-optimized desktop weather station built for the Adafruit MagTag (ESP32-S2) using CircuitPython. It fetches real-time local forecasts from the Open-Meteo API and displays current weather parameters along with an upcoming day timeline layout.

## Features

- **Battery Optimized:** Utilizes hardware deep sleep to power down the CPU and Wi-Fi between updates, extending battery life from hours to months.
- **Dual-Trigger Updates:** Automatically wakes up every 15 minutes to refresh data, or updates instantly when you press **Button A**.
- **Formatted Display:** Custom string parsing to output a clean, human-readable date (`Month DD, YYYY`).
- **Secure Configuration:** Separates sensitive data (Wi-Fi credentials, exact GPS coordinates) into a local environment file that won't be pushed to GitHub.

---

## Hardware Requirements

- [Adafruit MagTag - 2.9" Grayscale E-Ink Display](https://www.adafruit.com/product/4800)
- 3.7V Lithium Ion Polymer (LiPoly) Battery (Optional, for true wireless desktop use)
- USB-C Data Cable

---

## Installation & Setup

### 1. Prepare Your MagTag
Ensure your MagTag is flashed with the latest version of **CircuitPython (v8.x or newer)** and contains the necessary libraries in its `lib/` folder (`adafruit_magtag`, `adafruit_miniqr`, etc.).

### 2. Clone the Repository
Clone this repository to your local computer:
```bash
git clone [https://github.com/YOUR_USERNAME/magtag-weather-station.git](https://github.com/YOUR_USERNAME/magtag-weather-station.git)

### 3. Configure Your Environment Secrets
To keep your Wi-Fi credentials and exact location secure, this project uses a settings.toml configuration file.

Create a file named settings.toml in the root directory of your MagTag (CIRCUITPY drive).

Copy the contents of settings.example.toml and fill in your details:

Ini, TOML
CIRCUITPY_WIFI_SSID = "Your_WiFi_Name"
CIRCUITPY_WIFI_PASSWORD = "Your_WiFi_Password"
LATITUDE = "40.7128"
LONGITUDE = "-74.0060"
TIMEZONE = "America/New_York"
Note: The .gitignore file in this repository is pre-configured to ensure your settings.toml file is never tracked or uploaded to GitHub.

### 4. Deploy the Code
Copy the code.py file from this repository directly onto the root of your MagTag's CIRCUITPY drive. The board will automatically reboot and perform its first weather sync!

## How it Works: Deep Sleep Architecture
To maximize battery efficiency, the code avoids standard while True: execution loops. Instead, it runs as a linear script:

Wake Up: The board boots up and checks what woke it (Timer Alarm vs. Physical Button Pin Alarm).

Fetch & Render: Connects to Wi-Fi, streams JSON data from Open-Meteo, updates the e-ink layout buffers, and triggers a hardware screen refresh.

De-init Peripherals: Releases control of physical pins to resolve hardware conflicts.

Deep Sleep: Sets a 15-minute countdown timer, initializes an interrupt listener on BUTTON_A, and completely shuts down the microprocessor to achieve near-zero battery draw.

## Data Provenance
Weather data is dynamically sourced from Open-Meteo's Open-Data API. It automatically aggregates and cross-references high-resolution atmospheric models from global agencies including NOAA (GFS/HRRR) and ECMWF (IFS) based on your exact coordinates.

## License
This project is open-source under the MIT License.