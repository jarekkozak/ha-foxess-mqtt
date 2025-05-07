# -*- coding: utf-8 -*-

# ha-foxess-mqtt
# Copyright (C) 2025 Jarosław Kozak <jaroslaw.kozak68@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import logging
import sys
import collections
import json




MQTT_BROKER = "MQTT_BROKER"
MQTT_PORT = "MQTT_PORT"
MQTT_TOPIC = "MQTT_TOPIC"
MQTT_USER = "MQTT_USER"
MQTT_PASSWORD = "MQTT_PASSWORD"
MQTT_CLIENT_ID= 'MQTT_CLIENT_ID'


FOXESS_DEVICE_NAME = "FOXESS_DEVICE_NAME"
FOXESS_SN = "FOXESS_SN"
FOXESS_MODEL = "FOXESS_MODEL"
FOXESS_MANUFACTURER = "FOXESS_MANUFACTURER"
FOXESS_SW_VERSION = "FOXESS_SW_VERSION"
FOXESS_TIME_ZONE = "FOXESS_TIME_ZONE"

LOG_LEVEL="LOG_LEVEL"
CURRENT_LOG_LEVEL=None

ENV_FOXESS = {}
ENV_MQTT = {}
MAX_LOG_LINES = 100

# Queue for logs, limited length to preserve memory
log_queue = collections.deque(maxlen=MAX_LOG_LINES)
# --- Custom logging handler saving to the queue ---
class QueueLogHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        # We format the log and add it to the queue
        log_entry = self.format(record)
        self.queue.append(log_entry)


# --- Logging configuration ---
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
queue_handler = QueueLogHandler(log_queue)
queue_handler.setFormatter(log_formatter)

# Handler for the console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)
logger = logging.getLogger("helper")

def set_logger_state(level=None):
    global CURRENT_LOG_LEVEL
    if level is None:
        if ENV_MQTT.get(LOG_LEVEL,'INFO').upper() == 'DEBUG':
            state = logging.DEBUG
        else:
            state = logging.INFO
    else:
        state = level

    if state==10:
        CURRENT_LOG_LEVEL = 'DEBUG'
    else:
        CURRENT_LOG_LEVEL = 'INFO'

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for l in loggers:
        l.setLevel(state)
        l.addHandler(queue_handler)
        l.addHandler(console_handler)
        l.debug("Change logger status %s to s%", l.name,CURRENT_LOG_LEVEL)


def refresh_env_variables():
    global ENV_MQTT,ENV_FOXESS
    ENV_FOXESS = {
            FOXESS_DEVICE_NAME:os.getenv(FOXESS_DEVICE_NAME),
            FOXESS_SN:os.getenv(FOXESS_SN),
            FOXESS_MODEL:os.getenv(FOXESS_MODEL),
            FOXESS_MANUFACTURER:os.getenv(FOXESS_MANUFACTURER),
            FOXESS_SW_VERSION:os.getenv(FOXESS_SW_VERSION),
            FOXESS_TIME_ZONE:os.getenv(FOXESS_TIME_ZONE)
        }
    logger.debug("FoxESS ENVs:%s", json.dumps(ENV_FOXESS, indent=4))

    ENV_MQTT = {
            MQTT_BROKER : os.getenv(MQTT_BROKER),
            MQTT_PORT : int(os.getenv(MQTT_PORT,1883)),
            MQTT_TOPIC : os.getenv(MQTT_TOPIC),
            MQTT_USER : os.getenv(MQTT_USER),
            MQTT_PASSWORD : os.getenv(MQTT_PASSWORD),
            MQTT_CLIENT_ID : os.getenv(MQTT_CLIENT_ID,"FoxessT20G3"),
            LOG_LEVEL: os.getenv(LOG_LEVEL,'INFO'),
            'CURRENT_LOG_LEVEL' : CURRENT_LOG_LEVEL
        }
    logger.debug("MQTT ENVs:%s", json.dumps(ENV_MQTT, indent=4))


def get_foxess_env():
    return ENV_FOXESS

def get_mqtt_params():
    return ENV_MQTT

refresh_env_variables()