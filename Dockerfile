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