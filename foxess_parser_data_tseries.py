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

# more information about parsing frames
# https://github.com/assembly12/Foxess-T-series-ESPHome-Home-Assistant

from datetime import datetime, timedelta
import binascii
import re
import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

STATUS_ONLINE = "ONLINE"
STATUS_OFFLINE = "OFFLINE"

class FoxessTSeriesDataParser:
    """
    Parses data from a Foxess inverter.
    """
    OFFLINE_TIME = 3600

    # Text data addresses
    SERIES_DATA = [33, 39]
    MODEL_DATA = [41,66]
    SN_DATA = [6,36]

    # Sensors data addresses, 2B - 2 bytes, 4B - 4 bytes - big endian
    DEVICE_TIME = 1
    GRID_POWER_2B = 7
    CURRENT_POWER_2B = 9
    LOAD_POWER_2B = 11
    TODAY_YIELD_2B = 67
    TOTAL_YIELD_4B = 69

    GRID_VOLTAGE_R_2B = 13
    GRID_CURRENT_R_2B = 15
    GRID_FREQUENCY_R_2B = 17
    GRID_POWER_R_2B = 19

    GRID_VOLTAGE_S_2B = 21
    GRID_CURRENT_S_2B = 23
    GRID_FREQUENCY_S_2B = 25
    GRID_POWER_S_2B = 27

    GRID_VOLTAGE_T_2B = 29
    GRID_CURRENT_T_2B = 31
    GRID_FREQUENCY_T_2B = 33
    GRID_POWER_T_2B = 35

    PV1_VOLTAGE_2B = 37
    PV1_CURRENT_2B = 39

    PV2_VOLTAGE_2B = 43
    PV2_CURRENT_2B = 45

    PV3_VOLTAGE_2B = 49
    PV3_CURRENT_2B = 51

    PV4_VOLTAGE_2B = 55
    PV4_CURRENT_2B = 57

    BOST_TEMP_2B = 61
    INVERTER_TEMP_2B = 63
    AMBIENT_TEMP_2B = 65

    # Fault messages addresses, each 4 byte big endian
    FAULT_MESSAGES = [123, 127, 131, 135, 139, 143, 147, 149]


    def __init__(self,timezone='UTC'):
        self.SERIES = None
        self.MODEL = None
        self.SN = None
        self.tz = timezone
        self.messages = []
        self.latest_message = {}  # Store the latest parsed message
        logger.debug(f"Foxess Timezone {timezone}")


    @staticmethod
    def _string_zero_terminated(data):
        index = data.find(0x00)
        if index == -1:
            return data.decode()
        return data[:index].decode()

    @staticmethod
    def _big_endian4(data, position):
        return (data[position] << 24) + (data[position + 1] << 16) + (data[position + 2] << 8) + data[position + 3]

    @staticmethod
    def _big_endian2(data, position):
        return (data[position] << 8) + data[position + 1]

    @staticmethod
    def _calculate_precision(value, precision):
        value = value * 1 / 10 ** precision
        return round(value, precision)
    @staticmethod
    def _timestamp_to_local_iso_string(timestamp):
        dt_naive_local = datetime.datetime.fromtimestamp(timestamp)
        dt_aware_local = dt_naive_local.astimezone()
        iso_string = dt_aware_local.isoformat()
        return iso_string

    @staticmethod
    def crc_check(frame):
        crc = binascii.crc32(frame[:-2]) & 0xFFFF
        crc_frame = frame[-2:]
        crc_bytes = crc.to_bytes(2, byteorder='big')
        print(crc_frame.hex(), crc_bytes.hex())
        return crc_frame == crc_bytes

    @staticmethod
    def crc16_modbus(data: bytearray):
        if data is None:
            return 0
        offset = 0
        length = len(data)
        crc = 0xFFFF
        for i in range(length):
            crc ^= data[offset + i]
            for j in range(8):
                # print(crc)
                if ((crc & 0x1) == 1):
                    # print("bb1=", crc)
                    crc = int((crc / 2)) ^ 40961
                    # print("bb2=", crc)
                else:
                    crc = int(crc / 2)
        return crc & 0xFFFF

    @staticmethod
    def local_to_utc(local_timestamp, local_timezone_str ):
        try:
            local_timezone = pytz.timezone(local_timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Uknown timezone: {local_timezone_str}")
            return None
        local_datetime_naive = datetime.datetime.fromtimestamp(local_timestamp)
        offset_direct = local_timezone.utcoffset(local_datetime_naive).total_seconds()
        return local_timestamp-offset_direct

    def parse_data(self, data):
        """
        Parse cache to find inverter data
        :param data: bytes
        :return: bytes
        """
        # find a begining of frame
        frame_pattern = b'\x00\x00\x00\x00\x00(.)\x7E\x7E([\x01\x02\x06])'
        match = re.search(frame_pattern, data)
        #print(data.hex())
        if not match:
            return data
        header_index = match.start()
        frame_type = int.from_bytes(match.group(2), 'big')
        frame_length = header_index+ 6 + int.from_bytes(match.group(1), 'big')
        frame = data[header_index:frame_length]
        # if there is not enouch data
        if len(frame)<frame_length:
            return data

        frame_data = frame[8:-2]
        crc = int.from_bytes(frame[-2:],'little')
        crc_check = self.crc16_modbus(frame_data)

        #drop invalid frame
        if crc != crc_check:
            return data[header_index+frame_length:]

        message = {}
        match frame_type:
            case 1:
                message = self._parse_frame_1(frame_data)
            case 2:
                message = self._parse_frame_2(frame_data)
            case 6:
                message = self._parse_frame_6(frame_data)
            case _:
                message = {}
                logger.error(f"unknown frame type - {frame_type}")
        message.update(self._parse_time(frame_data))
        self.messages.append(message)
        # if there is more messages in buffer
        return self.parse_data(data[header_index+frame_length:])

    def _parse_time(self,frame_data):
        return {
            "device_time": self.local_to_utc(self._big_endian4(frame_data, self.DEVICE_TIME),self.tz)
        }

    def _parse_frame_2(self, frame_data):
        message = {
            "grid_power_value": self._big_endian2(frame_data, self.GRID_POWER_2B),
            "load_power_value": self._big_endian2(frame_data, self.LOAD_POWER_2B),
            "generated_power_value": self._big_endian2(frame_data, self.CURRENT_POWER_2B),
            "today_yield_value": self._calculate_precision(self._big_endian2(frame_data, self.TODAY_YIELD_2B),1),
            "total_yield_value": self._calculate_precision(self._big_endian4(frame_data, self.TOTAL_YIELD_4B), 1),

            "grid_voltage_r_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_VOLTAGE_R_2B), 1),
            "grid_current_r_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_CURRENT_R_2B), 1),
            "grid_frequency_r_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_FREQUENCY_R_2B), 2),
            "grid_power_r_value": self._big_endian2(frame_data, self.GRID_POWER_R_2B),

            "grid_voltage_s_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_VOLTAGE_S_2B), 1),
            "grid_current_s_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_CURRENT_S_2B), 1),
            "grid_frequency_s_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_FREQUENCY_S_2B), 2),
            "grid_power_s_value": self._big_endian2(frame_data, self.GRID_POWER_S_2B),

            "grid_voltage_t_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_VOLTAGE_T_2B), 1),
            "grid_current_t_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_CURRENT_T_2B), 1),
            "grid_frequency_t_value": self._calculate_precision(self._big_endian2(frame_data, self.GRID_FREQUENCY_T_2B), 2),
            "grid_power_t_value": self._big_endian2(frame_data, self.GRID_POWER_T_2B),

            "pv1_voltage_value": self._calculate_precision(self._big_endian2(frame_data, self.PV1_VOLTAGE_2B), 1),
            "pv1_current_value": self._calculate_precision(self._big_endian2(frame_data, self.PV1_CURRENT_2B), 1),

            "pv2_voltage_value": self._calculate_precision(self._big_endian2(frame_data, self.PV2_VOLTAGE_2B), 1),
            "pv2_current_value": self._calculate_precision(self._big_endian2(frame_data, self.PV2_CURRENT_2B), 1),

            "pv3_voltage_value": self._calculate_precision(self._big_endian2(frame_data, self.PV3_VOLTAGE_2B), 1),
            "pv3_current_value": self._calculate_precision(self._big_endian2(frame_data, self.PV3_CURRENT_2B), 1),

            "pv4_voltage_value": self._calculate_precision(self._big_endian2(frame_data, self.PV4_VOLTAGE_2B), 1),
            "pv4_current_value": self._calculate_precision(self._big_endian2(frame_data, self.PV4_CURRENT_2B), 1),

            "boost_temperature_value": self._big_endian2(frame_data, self.BOST_TEMP_2B),
            "inverter_temperature_value": self._big_endian2(frame_data, self.INVERTER_TEMP_2B),
            "ambient_temperature_value": self._big_endian2(frame_data, self.AMBIENT_TEMP_2B),
            "status" : STATUS_ONLINE
        }

        message["pv1_power_value"] = int(message.get("pv1_voltage_value") * message.get("pv1_current_value"))
        message["pv2_power_value"] = int(message.get("pv2_voltage_value") * message.get("pv2_current_value"))
        message["pv3_power_value"] = int(message.get("pv3_voltage_value") * message.get("pv3_current_value"))
        message["pv4_power_value"] = int(message.get("pv4_voltage_value") * message.get("pv4_current_value"))

        fault_messages = []
        for x in self.FAULT_MESSAGES:
            code = self._big_endian4(frame_data, x)
            if code == 0:
                continue
            fault = {
                "id": x,
                "code": code
            }
            fault_messages.append(fault)
        message["fault_messages"] = fault_messages
        return message

    def _parse_frame_1(self, frame_data):
        """
        Parse series & model of inverter
        :param frame_data:
        :return:
        """
        return {
                "series": self._string_zero_terminated(frame_data[self.SERIES_DATA[0]:self.SERIES_DATA[1]]),
                "model": self._string_zero_terminated(frame_data[self.MODEL_DATA[0]:self.MODEL_DATA[1]])
        }

    def _parse_frame_6(self, frame_data):
        """
        Parse serial number
        :param frame_data:
        :return:
        """
        return  {
            "sn": self._string_zero_terminated(frame_data[self.SN_DATA[0]:self.SN_DATA[1]])
        }

    def get_messages(self,flush=True):
        ret = self.messages
        if flush:
            self.messages = []
        return ret

    def get_message_offline(self):
        empty_frame = bytearray(260)
        message = self._parse_frame_2(empty_frame)
        message["status"] = STATUS_OFFLINE
        message["today_yield_value"] = None
        message["total_yield_value"] = None
        return message
