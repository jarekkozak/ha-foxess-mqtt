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

from mqtt_handler import MqttHandler
from helper import get_mqtt_params, get_foxess_env
import logging

logger = logging.getLogger("foxess-standalone")

if __name__ == '__main__':
    mqtt = get_mqtt_params()
    foxess = get_foxess_env()

    logger.info("Start reading mqtt messages")
    handler = MqttHandler(mqtt_param=mqtt, foxess=foxess)
    handler.start()
