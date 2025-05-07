FOXESS_DEVICE_NAME="FoxessT" \
FOXESS_TIME_ZONE="Europe/Warsaw" \
LOG_LEVEL="DEBUG" \
MQTT_BROKER="10.2.93.20" \
MQTT_CLIENT_ID="RS-STANDALONE-1" \
MQTT_PASSWORD="mqtt1234" \
MQTT_PORT="1883" \
MQTT_TOPIC="topic2" \
MQTT_USER="mqtt" \
gunicorn app:app -b 0.0.0.0:8080 -w 1 --log-level info

