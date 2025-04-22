FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variables here (ENV) or pass them when running the container
# ENV MQTT_BROKER=your_broker
# ENV MQTT_PORT=1883
# ENV MQTT_TOPIC=foxess/raw
# ENV MQTT_USER=your_user
# ENV MQTT_PASSWORD=your_password # avoid add password here
# ENV MQTT_CLIENT_ID=FoxessMQTTAddon
# ENV FOXESS_SN=YOUR_SERIAL_NUMBER # Important but could be read from inverter
# ENV FOXESS_DEVICE_NAME="Foxess MQTT"
# ENV LOG_LEVEL=INFO
# ENV FOXESS_TIME_ZONE=Europe/Warsaw


# Port exposed by app.py
EXPOSE 8080

# Run the Flask app with healthcheck endpoints
CMD ["python", "app.py"]
# Alternatively, for standalone:
# CMD ["python", "standalone.py"]