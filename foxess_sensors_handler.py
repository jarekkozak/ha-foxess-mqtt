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

import time
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Sensor, SensorInfo, DeviceInfo
import os
import paho.mqtt.client as mqtt
from helper import FOXESS_DEVICE_NAME,FOXESS_SN,FOXESS_SW_VERSION,FOXESS_MODEL,FOXESS_MANUFACTURER,FOXESS_TIME_ZONE
from helper import MQTT_USER,MQTT_PASSWORD,MQTT_CLIENT_ID,MQTT_BROKER,MQTT_PORT,MQTT_TOPIC


SERIAL = "sn"
SERIES = "series"

CLASS_TEMPERATURE = "temperature"
CLASS_FREQUENCY = "frequency"
CLASS_CURRENT = "current"
CLASS_VOLTAGE = "voltage"
CLASS_ENERGY = "energy"
CLASS_POWER = "power"

UNIT_W = "W"

GRID_VOLTAGE_T_VALUE = "grid_voltage_t_value"
GRID_POWER_S_VALUE = "grid_power_s_value"
GRID_FREQUENCY_S_VALUE = "grid_frequency_s_value"
GRID_CURRENT_S_VALUE = "grid_current_s_value"
GRID_VOLTAGE_S_VALUE = "grid_voltage_s_value"


GRID_POWER_R_VALUE = "grid_power_r_value"
GRID_FREQUENCY_R_VALUE = "grid_frequency_r_value"
GRID_CURRENT_R_VALUE = "grid_current_r_value"
GRID_VOLTAGE_R_VALUE = "grid_voltage_r_value"
TOTAL_YIELD_VALUE = "total_yield_value"
TODAY_YIELD_VALUE = "today_yield_value"


GENERATED_POWER_VALUE = "generated_power_value"
LOAD_POWER_VALUE = "load_power_value"
GRID_POWER_VALUE = "grid_power_value"




class FoxessSensorsHandler:
    """
    Handles Foxess data, creating and updating Home Assistant sensors via MQTT.
    """

    def __init__(
        self,
            mqtt_param,
            foxess
    ):
        """
        Initializes the FoxessDataHandler with MQTT settings and device info.

        Args:
            mqtt (dict): MQTT params
        """

        self.name=foxess.get(FOXESS_DEVICE_NAME,None)
        self.identifiers=foxess.get(FOXESS_SN,None)
        self.model=foxess.get(FOXESS_MODEL,None)
        self.manufacturer=foxess.get(FOXESS_MANUFACTURER,None)
        self.sw_version=foxess.get(FOXESS_SW_VERSION,None)
        self.time_zone = foxess.get(FOXESS_TIME_ZONE,'UTC')

        self.broker =  mqtt_param.get(MQTT_BROKER)
        self.port = mqtt_param.get(MQTT_PORT)
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=mqtt_param.get(MQTT_CLIENT_ID))
        self.client.username_pw_set(mqtt_param.get(MQTT_USER),mqtt_param.get(MQTT_PASSWORD))
        self.mqtt_settings = Settings.MQTT(client=self.client)

        self.sensors = {}  # Dictionary to store created sensors
        self.device_info = None

    def _get_id(self, key):
        return "_".join([self.identifiers, key])

    def create_sensor(self, sensor_data_key, sensor_name, unit_of_measurement=None, device_class=None, state_class=None, icon=None, entity_category=None,value_template=None):
        """
        Creates a Home Assistant sensor.
        Args:
            sensor_data_key (str): Key in the data dictionary.
            sensor_name (str): Name of the sensor.
            unit_of_measurement (str): Unit of measurement.
            device_class (str, optional): Device class for Home Assistant. Defaults to None.
            state_class (str, optional): State class for Home Assistant. Defaults to None.
            icon (str, optional): Icon for Home Assistant. Defaults to None.
        """
        unique_id = self._get_id(sensor_data_key)
        sensor_info = SensorInfo(
            name=sensor_name,
            unique_id=unique_id,
            device_class=device_class,
            unit_of_measurement=unit_of_measurement,
            device=self.device_info,
            state_class=state_class,
            icon=icon,
            entity_category=entity_category,
            value_template=value_template,
            object_id=unique_id
        )

        settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
        sensor = Sensor(settings)
        self.sensors[sensor_data_key] = sensor

    def create_text_sensor(self, sensor_data_key, sensor_name, device_class=None, icon=None, entity_category=None):
        """
        Creates a Home Assistant sensor.

        Args:
            sensor_data_key (str): Key in the data dictionary.
            sensor_name (str): Name of the sensor.
            unit_of_measurement (str): Unit of measurement.
            device_class (str, optional): Device class for Home Assistant. Defaults to None.
            state_class (str, optional): State class for Home Assistant. Defaults to None.
            icon (str, optional): Icon for Home Assistant. Defaults to None.
        """
        unique_id = self._get_id(sensor_data_key)
        sensor_info = SensorInfo(
            name=sensor_name,
            unique_id=unique_id,
            device_class=device_class,
            device=self.device_info,
            icon=icon,
            entity_category=entity_category
        )
        settings = Settings(mqtt=self.mqtt_settings, entity=sensor_info)
        text = Sensor(settings)
        self.sensors[sensor_data_key] = text

    def _device_info(self, frame):
        if self.name is None:
            self.name=frame.get("device_name",self.name)
        if self.identifiers is None:
            self.identifiers=frame.get("sn",self.identifiers)

        # those 2 fields are mandatory
        if self.name is None or self.identifiers is None:
            return None

        if self.model is None:
            self.model=frame.get("model",self.model)
        if self.manufacturer is None:
            self.manufacturer=frame.get("manufacturer",self.manufacturer)
        if self.sw_version is None:
            self.sw_version=frame.get("sw_version", self.sw_version)

        return DeviceInfo(name=self.name,
                          identifiers= self.identifiers,
                          model=self.model,
                          manufacturer=self.manufacturer,
                          sw_version=self.sw_version)

    def process_data(self, data):
        """
        Processes the incoming data, creates sensors if they don't exist, and updates their states.

        Args:
            data (dict): Dictionary containing Foxess data.
        """

        self.device_info = self._device_info(data)
        if self.device_info is None:
            return

        self.client.connect(self.broker,self.port,keepalive=60)

        # Create sensors if they don't exist

        if "manufacturer" not in self.sensors:
            self.create_text_sensor("manufacturer", "Manufacturer",entity_category="diagnostic")
        if "model" not in self.sensors:
            self.create_text_sensor("model", "Model",entity_category="diagnostic")
        if SERIAL not in self.sensors:
            self.create_text_sensor(SERIAL, "Serial", entity_category="diagnostic")
        if SERIES not in self.sensors:
            self.create_text_sensor(SERIES, "Series", entity_category="diagnostic")
        if "status" not in self.sensors:
            self.create_text_sensor("status", "Status",entity_category="diagnostic")
        if "fault_messages" not in self.sensors:
            fm = data.get("fault_messages",[])
            if len(fm)>0:
                data["fault_messages"] = ",".join(fm)
            else:
                data["fault_messages"] = ""
            self.create_text_sensor("fault_messages", "Errors", entity_category="diagnostic")
        if "device_time" not in self.sensors:
            self.create_sensor(sensor_data_key="device_time", sensor_name="Device time",device_class="timestamp",value_template="{{ value | int | timestamp_custom('%Y-%m-%dT%H:%M:%S+02:00') }}")
        if GRID_POWER_VALUE not in self.sensors:
            self.create_sensor(sensor_data_key=GRID_POWER_VALUE, sensor_name="Grid Power", unit_of_measurement=UNIT_W, device_class=CLASS_POWER)
        if LOAD_POWER_VALUE not in self.sensors:
            self.create_sensor(LOAD_POWER_VALUE, "Load Power", UNIT_W, device_class=CLASS_POWER)
        if GENERATED_POWER_VALUE not in self.sensors:
            self.create_sensor(GENERATED_POWER_VALUE, "Generated Power", UNIT_W, device_class=CLASS_POWER)
        if TODAY_YIELD_VALUE not in self.sensors:
            self.create_sensor(TODAY_YIELD_VALUE, "Today's Yield", "kWh", device_class=CLASS_ENERGY, state_class="total_increasing")
        if TOTAL_YIELD_VALUE not in self.sensors:
            self.create_sensor(TOTAL_YIELD_VALUE, "Total Yield", "kWh", device_class=CLASS_ENERGY, state_class="total_increasing")
        if GRID_VOLTAGE_R_VALUE not in self.sensors:
            self.create_sensor(GRID_VOLTAGE_R_VALUE, "Grid Voltage R", "V", device_class=CLASS_VOLTAGE)
        if GRID_CURRENT_R_VALUE not in self.sensors:
            self.create_sensor(GRID_CURRENT_R_VALUE, "Grid Current R", "A", device_class=CLASS_CURRENT)
        if GRID_FREQUENCY_R_VALUE not in self.sensors:
            self.create_sensor(GRID_FREQUENCY_R_VALUE, "Grid Frequency R", "Hz", device_class=CLASS_FREQUENCY)
        if GRID_POWER_R_VALUE not in self.sensors:
            self.create_sensor(GRID_POWER_R_VALUE, "Grid Power R", UNIT_W, device_class=CLASS_POWER)
        if GRID_VOLTAGE_S_VALUE not in self.sensors:
            self.create_sensor(GRID_VOLTAGE_S_VALUE, "Grid Voltage S", "V", device_class=CLASS_VOLTAGE)
        if GRID_CURRENT_S_VALUE not in self.sensors:
            self.create_sensor(GRID_CURRENT_S_VALUE, "Grid Current S", "A", device_class=CLASS_CURRENT)
        if GRID_FREQUENCY_S_VALUE not in self.sensors:
            self.create_sensor(GRID_FREQUENCY_S_VALUE, "Grid Frequency S", "Hz", device_class=CLASS_FREQUENCY)
        if GRID_POWER_S_VALUE not in self.sensors:
            self.create_sensor(GRID_POWER_S_VALUE, "Grid Power S", UNIT_W, device_class=CLASS_POWER)
        if GRID_VOLTAGE_T_VALUE not in self.sensors:
            self.create_sensor(GRID_VOLTAGE_T_VALUE, "Grid Voltage T", "V", device_class=CLASS_VOLTAGE)
        if "grid_current_t_value" not in self.sensors:
            self.create_sensor("grid_current_t_value", "Grid Current T", "A", device_class=CLASS_CURRENT)
        if "grid_frequency_t_value" not in self.sensors:
            self.create_sensor("grid_frequency_t_value", "Grid Frequency T", "Hz", device_class=CLASS_FREQUENCY)
        if "grid_power_t_value" not in self.sensors:
            self.create_sensor("grid_power_t_value", "Grid Power T", UNIT_W, device_class=CLASS_POWER)
        if "pv1_voltage_value" not in self.sensors:
            self.create_sensor("pv1_voltage_value", "PV1 Voltage", "V", device_class=CLASS_VOLTAGE)
        if "pv1_current_value" not in self.sensors:
            self.create_sensor("pv1_current_value", "PV1 Current", "A", device_class=CLASS_CURRENT)
        if "pv2_voltage_value" not in self.sensors:
            self.create_sensor("pv2_voltage_value", "PV2 Voltage", "V", device_class=CLASS_VOLTAGE)
        if "pv2_current_value" not in self.sensors:
            self.create_sensor("pv2_current_value", "PV2 Current", "A", device_class=CLASS_CURRENT)
        if "pv3_voltage_value" not in self.sensors:
            self.create_sensor("pv3_voltage_value", "PV3 Voltage", "V", device_class=CLASS_VOLTAGE)
        if "pv3_current_value" not in self.sensors:
            self.create_sensor("pv3_current_value", "PV3 Current", "A", device_class=CLASS_CURRENT)
        if "pv4_voltage_value" not in self.sensors:
            self.create_sensor("pv4_voltage_value", "PV4 Voltage", "V", device_class=CLASS_VOLTAGE)
        if "pv4_current_value" not in self.sensors:
            self.create_sensor("pv4_current_value", "PV4 Current", "A", device_class=CLASS_CURRENT)
        if "boost_temperature_value" not in self.sensors:
            self.create_sensor("boost_temperature_value", "Boost Temperature", "°C", device_class=CLASS_TEMPERATURE)
        if "inverter_temperature_value" not in self.sensors:
            self.create_sensor("inverter_temperature_value", "Inverter Temperature", "°C", device_class=CLASS_TEMPERATURE)
        if "ambient_temperature_value" not in self.sensors:
            self.create_sensor("ambient_temperature_value", "Ambient Temperature", "°C", device_class=CLASS_TEMPERATURE)
        if "pv1_power_value" not in self.sensors:
            self.create_sensor("pv1_power_value", "PV1 Power", UNIT_W, device_class=CLASS_POWER)
        if "pv2_power_value" not in self.sensors:
            self.create_sensor("pv2_power_value", "PV2 Power", UNIT_W, device_class=CLASS_POWER)
        if "pv3_power_value" not in self.sensors:
            self.create_sensor("pv3_power_value", "PV3 Power", UNIT_W, device_class=CLASS_POWER)
        if "pv4_power_value" not in self.sensors:
            self.create_sensor("pv4_power_value", "PV4 Power", UNIT_W, device_class=CLASS_POWER)

        # Update sensor states
        for key, sensor in self.sensors.items():
            if key in data.keys():
                if data.get(key,None) is not None:
                    sensor.set_state(data[key])
                    time.sleep(50/1000)
