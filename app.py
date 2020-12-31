#!/usr/bin/env python3

# Hack to allow relative import above top level package
import sys
import os

folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

from flask import Flask, abort
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json
from pytradfri.const import ATTR_ID, ATTR_NAME

import asyncio
import uuid
import argparse
import traceback
import json as j
import jsonpickle as jp

app = Flask(__name__)

# Global scope variables
api_factory = None
api = None
gateway = None
devices = None
lights = None
groups = None

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/turnon')
def turnon():
    try:
        api(groups[3].set_state(True))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Lights are on!', 200

@app.route('/turnoff')
def turnoff():
    try:
        api(groups[3].set_state(False))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Lights are off!', 200

@app.route('/setcolor/<int:color_temp>')
def setcolor(color_temp):
    # Ensure color temp value is within allowed range of (250,454)
    if (color_temp < 250): color_temp = 250
    if (color_temp > 454): color_temp = 454    

    try:
        api(groups[3].set_color_temp(color_temp))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Color set to:'+str(color_temp), 200

@app.route('/group')
def group():
    groups_dict = list(map(lambda group: {"id": str(group.raw.get(ATTR_ID)), "name": str(group.raw.get(ATTR_NAME))}, groups))
    return jp.encode(groups_dict, unpicklable=False), 200



if __name__ == '__main__':
    CONFIG_FILE = "tradfri_standalone_psk.conf"
    IP_ADDRESS = "192.168.1.145"
    
    try:
        conf = load_json(CONFIG_FILE)
        app.logger.warning("Config file contents: '")    
        app.logger.warning(conf)
        app.logger.warning("'")
        identity = conf[IP_ADDRESS].get("identity")
        psk = conf[IP_ADDRESS].get("key")
    
        api_factory = APIFactory(IP_ADDRESS, identity, psk)        
        api = api_factory.request
        gateway = Gateway()

        app.logger.warning("-- LIGHTS --")
        devices_command = api(gateway.get_devices())
        devices = api(devices_command)
        lights = [dev for dev in devices if dev.has_light_control]
        app.logger.warning(lights)

        app.logger.warning("-- GROUPS --")
        groups_command = api(gateway.get_groups())
        groups = api(groups_command)     
        app.logger.warning(groups)        
    except Exception as e:
        app.logger.error(traceback.format_exc())   

    app.run(host="0.0.0.0", port=5000)
