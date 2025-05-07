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
# ## Acknowledgements
#
# more information about handling offline status here
# https://github.com/assembly12/Foxess-T-series-ESPHome-Home-Assistant

import datetime
import json
from time import sleep
from foxess_parser_data_tseries import FoxessTSeriesDataParser, STATUS_OFFLINE, STATUS_ONLINE
from foxess_sensors_handler import FoxessSensorsHandler
import paho.mqtt.client as mqtt
import threading
from datetime import datetime, timedelta
from helper import MQTT_CLIENT_ID,MQTT_USER,MQTT_PASSWORD,MQTT_PORT,MQTT_TOPIC,MQTT_BROKER,FOXESS_TIME_ZONE
import collections
import logging

logger = logging.getLogger("mqtt_handler")

# timeout when inverter goes off line
TIMEOUT = 3600
MAX_HISTORY_BUFFER = 10

class MqttHandler:

    def __init__(self, mqtt_param,foxess={}):
        self.broker = mqtt_param.get(MQTT_BROKER)
        self.port = mqtt_param.get(MQTT_PORT)
        self.topic = mqtt_param.get(MQTT_TOPIC)
        self.client_id =  mqtt_param.get(MQTT_CLIENT_ID)
        self.user = mqtt_param.get(MQTT_USER)
        self.password =mqtt_param.get(MQTT_PASSWORD)
        self.connected = False
        self.message_received = False
        self.thread_running = False
        self.CACHE = bytearray()
        self.status = STATUS_ONLINE
        self.last_message_timestamp = datetime.now()
        self.history = collections.deque(maxlen=MAX_HISTORY_BUFFER)
        self.foxess = foxess
        # for sensors
        self.mqtt_sensor = mqtt_param
        self.mqtt_sensor[MQTT_CLIENT_ID] = self.mqtt_sensor[MQTT_CLIENT_ID] + "_ha"
        self.sensors = None
        self.parser = None

    def on_connect(self, client, userdata, flags, rc, prop):
        if rc == 0:
            logger.info( "Connected to MQTT")
            self.connected = True
            client.subscribe(self.topic)
        else:
            logger.error(f"Error, not connected  to MQTT:{rc}")

    def on_disconnect(self, client, flags, userdata, rc, properties=None):  # properties dla V2 API
        logger.warning(f"Disconnected with result code: {rc}")
        self.connected = False

    def on_message(self, client, userdata, msg):
        logger.debug(f"Message received:{msg.payload.hex()}")
        # health data
        self.message_received = True
        self.last_message_timestamp = datetime.now()

        self.CACHE.extend(msg.payload)
        self.CACHE = self.parser.parse_data(self.CACHE)

        if self.parser is None:
            return

        parsed_frames = self.parser.get_messages()

        self.status = STATUS_ONLINE
        if len(parsed_frames)>0:
            for f in parsed_frames:
                if self.sensors is not None:
                    self.sensors.process_data(f)
                logger.info(f"data processed {f}")
                self.history.append(f)

    def check_status(self):
        while True:
            logger.debug("Start check status loop:%s",datetime.now())
            if (self.last_message_timestamp + timedelta(seconds=TIMEOUT)) < datetime.now() and self.status == STATUS_ONLINE:
                logger.debug("Inverter is offline, last message received at {}".format(self.last_message_timestamp))
                logger.info("Inverter is offline")
                self.sensors.process_data(self.parser.get_message_offline())
                self.status = STATUS_OFFLINE

            # self.client.connect(self.broker, self.port, 60)
            # self.client.loop_start()
            sleep(60)
            # self.client.loop_stop()

    def mqtt_thread(self):
        self.thread_running = True
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.client_id)
        self.client.username_pw_set(self.user,self.password)

        self.client.on_connect = lambda client, userdata, flags, rc, prop: self.on_connect(client, userdata, flags, rc, prop)
        self.client.on_disconnect = lambda client,flags,userdata,rc, prop: self.on_disconnect(client, flags, userdata, rc, prop )
        self.client.on_message = lambda client, userdata, msg: self.on_message(client, userdata, msg)

        self.parser = FoxessTSeriesDataParser(timezone=self.foxess.get(FOXESS_TIME_ZONE,'UTC'))
        self.sensors= FoxessSensorsHandler(self.mqtt_sensor,foxess=self.foxess)

        try:
            self.client.connect(host=self.broker, port=self.port, keepalive=60)
            #self.client.loop_forever()
            self.client.loop_start()
            self.check_status()
            self.client.loop_stop()

        except Exception as e:
            logger.error(f"Error in thread:{e}")
            self.thread_running = False
        finally:
            self.thread_running = False

    def start(self):
        threading.Thread(target=self.mqtt_thread).start()

    def is_connected(self):
        return self.connected

    def is_message_received(self):
        return self.message_received

    def is_thread_running(self):
        return self.thread_running
