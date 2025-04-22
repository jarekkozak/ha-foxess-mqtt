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
import sys
import collections
from flask import Flask, render_template, jsonify, Response
from helper import get_mqtt_params, get_foxess_env
from mqtt_handler import MqttHandler

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

# We configure the main logger (root) or a specific application logger
logger = logging.getLogger() # You can use logging.getLogger('my_app') if you prefer
logger.setLevel(logging.INFO) # Set the logging level (e.g., DEBUG, INFO, WARNING)
logger.addHandler(queue_handler)
logger.addHandler(console_handler)

mqtt = get_mqtt_params()
foxess = get_foxess_env()
mqtt_handler = MqttHandler(log=logger, mqtt_param=mqtt, foxess=foxess)

# --- Flask Application ---
app = Flask(__name__)

@app.route('/')
def index():
    env = dict()
    env.update(get_mqtt_params())
    env.update(get_foxess_env())
    return render_template('index.html',env_vars=env)

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
    if mqtt_handler.is_connected() and mqtt_handler.is_message_received() and mqtt_handler.is_thread_running():
        return Response(status=200)
    else:
        return Response(status=500)


if __name__ == '__main__':
    logging.info("Starting Flask Log Viewer application...")
    mqtt_handler.start()
    # do not use debug=True, it causes connection issues
    app.run(debug=False, host='0.0.0.0', port=8080)