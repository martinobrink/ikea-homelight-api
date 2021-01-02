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
from pytradfri.const import ATTR_ID, ATTR_NAME, ATTR_DEVICE_STATE, ATTR_LIGHT_DIMMER, ATTR_LIGHT_MIREDS

import asyncio
import uuid
import argparse
import traceback
import json as j
import jsonpickle as jp

app = Flask(__name__)

# Global scope variables serving as in-memory db of lights and groups
# (ugly but simple solution)
api_factory = None
api = None
gateway = None
devices = None
lights = None
groups = None

# TODO
# add API overview index page at route '/'

@app.route('/light', methods=['GET'])
def get_lights():
    lights_dict = list(map(lambda light: 
        {   "id": str(light.raw.get(ATTR_ID)), 
            "name": str(light.raw.get(ATTR_NAME)),
            "state": str(light.light_control.raw[0].get(ATTR_DEVICE_STATE)),
            "level": str(light.light_control.raw[0].get(ATTR_LIGHT_DIMMER)),
            "color": str(light.light_control.raw[0].get(ATTR_LIGHT_MIREDS)) 
        }, 
        lights))
    return jp.encode(lights_dict, unpicklable=False), 200, {'Content-Type': 'application/json'}

@app.route('/group', methods=['GET'])
def get_groups():
    groups_dict = list(map(lambda group: 
        {   "id": str(group.raw.get(ATTR_ID)), 
            "name": str(group.raw.get(ATTR_NAME)),
            "state": str(group.raw.get(ATTR_DEVICE_STATE)),
            "level": str(group.raw.get(ATTR_LIGHT_DIMMER)),
            "color": str(group.raw.get(ATTR_LIGHT_MIREDS))        
        }, 
        groups))
    return jp.encode(groups_dict, unpicklable=False), 200, {'Content-Type': 'application/json'}

@app.route('/group/<group_id>/state/<state_on_off>', methods=['PUT'])
def set_group_state(group_id, state_on_off):
    if (state_on_off.lower() != 'on' and state_on_off.lower() != 'off'): return 400

    state_boolean = True if (state_on_off.lower() == 'on') else False
    filtered_groups = list(filter(lambda group: str(group.raw.get(ATTR_ID)) == group_id, groups))
    if not filtered_groups: return 404 #group with submitted id was not found
    
    try:        
        api(filtered_groups[0].set_state(state_boolean))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Group state set to: ' + state_on_off, 200

@app.route('/group/<group_id>/color/<int:color_temp>', methods=['PUT'])
def set_group_color(group_id, color_temp):
    # Ensure color temp value is within allowed range of (250, 454)
    if (color_temp < 250): color_temp = 250
    if (color_temp > 454): color_temp = 454  

    filtered_groups = list(filter(lambda group: str(group.raw.get(ATTR_ID)) == group_id, groups))
    if not filtered_groups: return 404 #group with submitted id was not found
    
    try:        
        api(filtered_groups[0].set_color_temp(color_temp))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Group ' + group_id + ' color set to: ' + str(color_temp), 200

@app.route('/group/<group_id>/level/<int:light_level>', methods=['PUT'])
def set_group_light_level(group_id, light_level):
    # Ensure light level value is within allowed range of (0, 254)
    if (light_level < 0): light_level = 0
    if (light_level > 254): light_level = 254  

    filtered_groups = list(filter(lambda group: str(group.raw.get(ATTR_ID)) == group_id, groups))
    if not filtered_groups: return 404 #group with submitted id was not found
    
    try:        
        api(filtered_groups[0].set_dimmer(light_level))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Group ' + group_id + ' light level set to: ' + str(light_level), 200


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
