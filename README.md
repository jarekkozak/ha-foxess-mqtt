# ha-foxess-mqtt

Integration of Foxess T-Series photovoltaic inverter (e.g., T20G3) with Home Assistant using MQTT.

This project listens on a specific MQTT topic where raw data from the Foxess inverter is expected (e.g., via an RS485-to-MQTT bridge). It then parses this data, extracts sensor values, and publishes them to Home Assistant using the MQTT Discovery mechanism.

## Acknowledgements

Special thanks to **assembly12** for their work on the [Foxess-T-series-ESPHome-Home-Assistant](https://github.com/assembly12/Foxess-T-series-ESPHome-Home-Assistant) project, which served as an inspiration for this implementation. Their efforts provided a valuable starting point.

## Features

* Parses data frames from Foxess T-Series inverters received via MQTT.
* Integrates with Home Assistant via MQTT Discovery, automatically creating entities.
* Creates sensors for various parameters:
    * Power (Total, Load, Generated, Per phase, PV1-PV4)
    * Energy (Today's Yield, Total Yield)
    * Voltage (Grid R/S/T, PV1-PV4)
    * Current (Grid R/S/T, PV1-PV4)
    * Frequency (Grid R/S/T)
    * Temperature (Boost, Inverter, Ambient)
    * Status (Online/Offline)
    * Fault codes
* Automatically detects the inverter's Online/Offline status based on message timeout.
* Configuration via environment variables.
* Can be run as:
    * A standalone script (`standalone.py`)
    * A Flask web application with health check endpoints (`app.py`), ready for containerization.
    * A Flask web application with a live log viewer (`app1.py`, `templates/index.html`).
* Includes an example Kubernetes deployment configuration (`deployment.yaml`).
* Includes a tool for analyzing binary data dumps (`foxess_anal_dump_file.py`).

## Prerequisites

1.  **Python 3.x**: Installed on the machine where the script will run.
2.  **MQTT Broker**: Accessible on the network, connectable by this application and Home Assistant.
3.  **Home Assistant**: A running instance with the MQTT integration correctly configured.
4.  **MQTT Data Source**: A mechanism (e.g., an RS485-to-MQTT bridge connected to the inverter) sending *raw* binary data from the Foxess inverter to the specified MQTT topic. **This project does *not* implement reading from RS485, only listening on MQTT.**
5.  **Foxess T-Series Inverter**: A compatible inverter (e.g., T20G3).

## Configuration

Configuration is done using environment variables. The `helper.py` file defines the expected variables:

* `MQTT_BROKER`: Address of your MQTT broker (e.g., `192.168.1.100`).
* `MQTT_PORT`: Port of your MQTT broker (e.g., `1883`).
* `MQTT_TOPIC`: **The MQTT topic where the *raw* inverter data is listened to**.
* `MQTT_USER`: Username for the MQTT broker (if required).
* `MQTT_PASSWORD`: Password for the MQTT broker (if required).
* `MQTT_CLIENT_ID`: MQTT client ID for this application (default: `FoxessT20G3`). The second client for HA discovery will have `_ha` appended.
* `FOXESS_DEVICE_NAME`: The device name that will appear in Home Assistant.
* `FOXESS_SN`: **Inverter serial number**. Used as the unique device identifier in HA. **Important to set this!**
* `FOXESS_MODEL`: Inverter model (optional, will appear in device info in HA).
* `FOXESS_MANUFACTURER`: Manufacturer (optional, will appear in device info in HA, might be set by the code by default).
* `FOXESS_SW_VERSION`: Software version (optional, will appear in device info in HA).
* `FOXESS_TIME_ZONE`: Timezone used by the parser to interpret the device time (default 'UTC', e.g., 'Europe/Warsaw').
* `LOG_LEVEL`: Logging level (`INFO` or `DEBUG`, default `INFO`).

**How to set variables:**
You can set them directly in your system (`export VARIABLE_NAME=value`) or use a `.env` file with the `python-dotenv` library (if you install it).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd ha-foxess-mqtt
    ```
2.  **Create a `requirements.txt` file:**
    ```txt
    # requirements.txt
    paho-mqtt
    ha-mqtt-discoverable
    Flask
    pytz
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Set the environment variables** (see Configuration section).
2.  **Choose how to run:**

    * **Standalone script:**
        ```bash
        python standalone.py
        ```
    * **Flask application (with /health, /ready endpoints):**
        Ideal for running in a container or using a WSGI server (e.g., gunicorn).
        ```bash
        python app.py
        # Or with gunicorn:
        # gunicorn --bind 0.0.0.0:8080 app:app
        ```
    * **Flask application (with log viewer):**
        Useful for debugging. Starts the server on port 5000.
        ```bash
        python app.py
        ```
        Open your browser at `http://<machine-ip-address>:5000/`.

After starting, the script will connect to the MQTT broker, subscribe to the specified topic, and begin listening for data. When data is received and parsed, the corresponding entities should automatically appear in Home Assistant thanks to MQTT Discovery.

## Docker / Kubernetes

The project includes a `deployment.yaml` file, which is an example deployment configuration for Kubernetes. It assumes the existence of a container image named `foxess-rs485:latest`.

To build a Docker image, you need to create a `Dockerfile`, for example:

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables here (ENV) or pass them when running the container
ENV MQTT_BROKER=your_broker
ENV MQTT_PORT=1883
ENV MQTT_TOPIC=foxess/raw
ENV FOXESS_SN=YOUR_SERIAL_NUMBER
# ... other variables ...

# Port exposed by app.py
EXPOSE 8080

# Run the Flask app with healthcheck endpoints
CMD ["python", "app.py"]
# Alternatively, for standalone:
# CMD ["python", "standalone.py"]
