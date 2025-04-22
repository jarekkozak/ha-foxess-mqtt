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

def get_foxess_env():
    return {
        FOXESS_DEVICE_NAME:os.getenv(FOXESS_DEVICE_NAME),
        FOXESS_SN:os.getenv(FOXESS_SN),
        FOXESS_MODEL:os.getenv(FOXESS_MODEL),
        FOXESS_MANUFACTURER:os.getenv(FOXESS_MANUFACTURER),
        FOXESS_SW_VERSION:os.getenv(FOXESS_SW_VERSION),
        FOXESS_TIME_ZONE:os.getenv(FOXESS_TIME_ZONE)
    }


def get_mqtt_params():
    return {
        MQTT_BROKER : os.getenv(MQTT_BROKER),
        MQTT_PORT : int(os.getenv(MQTT_PORT,1883)),
        MQTT_TOPIC : os.getenv(MQTT_TOPIC),
        MQTT_USER : os.getenv(MQTT_USER),
        MQTT_PASSWORD : os.getenv(MQTT_PASSWORD),
        MQTT_CLIENT_ID : os.getenv(MQTT_CLIENT_ID,"FoxessT20G3"),
        LOG_LEVEL: os.getenv(LOG_LEVEL,'INFO')
    }

def set_logger_state():
    if get_mqtt_params().get(LOG_LEVEL,'INFO').upper() == 'DEBUG':
        state = logging.DEBUG
    else:
        state = logging.INFO

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    for l in loggers:
        l.setLevel(state)