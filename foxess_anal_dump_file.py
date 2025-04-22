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

import json

from foxess_parser_data_tseries import FoxessTSeriesDataParser

CACHE = bytearray()

def analyse_dump_file(fname):
    global CACHE
    parser = FoxessTSeriesDataParser()
    try:
        with open(fname, 'rb') as f:
            while True:
                chunk = f.read(1000)
                if not chunk:
                    break
                CACHE.extend(bytearray(chunk))
                # process all frames in buffer and stop when no more found
                stop = -1
                while len(CACHE) != stop:
                    stop = len(CACHE)
                    CACHE = parser.parse_data(CACHE)
                # print messages found
                messages = parser.get_messages()
                if len(messages)>0:
                    print(json.dumps(messages, indent=4))



    except FileNotFoundError:
        print(f"File '{fname}' not found.")
    except Exception as e:
        print(f"An error occurred while reading file: {e}")


if __name__ == '__main__':
    fname = "arch/data1.bin"
    analyse_dump_file(fname)