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

import logging
from flask import Flask, render_template, jsonify, Response, request
from helper import get_mqtt_params, get_foxess_env,set_logger_state,log_queue
from mqtt_handler import MqttHandler

logger = logging.getLogger("livelogviewer") # You can use logging.getLogger('my_app') if you prefer


mqtt = get_mqtt_params()
foxess = get_foxess_env()

# --- Flask Application ---
app = Flask(__name__)

def get_env_vars():
    env = dict()
    env.update(get_mqtt_params())
    env.update(get_foxess_env())
    return env

@app.route('/')
def index():
    return render_template('index.html',env_vars=get_env_vars())

@app.route('/logs')
def get_logs():
    log_content = "\n".join(list(log_queue))
    return jsonify(logs=log_content)

@app.route('/health')
def health():
    if mqtt_handler.is_connected() and mqtt_handler.is_thread_running():
        return Response(status=200)
    else:
        return Response(status=500)

@app.route('/ready')
def ready():
    if mqtt_handler.is_connected() and mqtt_handler.is_thread_running():
        return Response(status=200)
    else:
        return Response(status=500)

@app.route('/set_log_level', methods=['POST'])
def set_log_level():
    level = request.json.get('level', 'INFO').upper()
    if level == 'DEBUG':
        set_logger_state(logging.DEBUG)
        logger.info("Log level set to DEBUG")
    elif level == 'INFO':
        set_logger_state(logging.INFO)
        logger.info("Log level set to INFO")
    # Add other levels if needed (WARNING, ERROR, CRITICAL)
    return jsonify(status="success", level=level)


mqtt_handler = MqttHandler(mqtt_param=mqtt, foxess=foxess)
set_logger_state()

logger.info("Starting Log Viewer application...")
mqtt_handler.start()

if __name__ == '__main__':
    logger.info("Starting Flask server")
    # do not use debug=True, it causes connection issues
    app.run(debug=False, host='0.0.0.0', port=8080)
