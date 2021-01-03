#!/usr/bin/env python3

# -- Imports from base image --
# Hack to allow relative import above top level package
import sys
import os
folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa
from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json
from pytradfri.const import ATTR_ID, ATTR_NAME, ATTR_DEVICE_STATE, ATTR_LIGHT_DIMMER, ATTR_LIGHT_MIREDS

# -- Imports added here
from flask import Flask, abort
from flasgger import Swagger
import jsonpickle as jp
import traceback

app = Flask(__name__)
swagger = Swagger(app)

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
# separate handling of requirements.txt in this docker image

@app.route('/light', methods=['GET'])
def get_lights():
    """Retrieve a list of all registered lights.
    ---    
    responses:
      200:
        description: ok
        examples:
          {"id": "99999", "name": "Bulb1", "state": "1", "level": "254", "color": "330" }
    """
    lights_dict = list(map(lambda light: 
        {   "id": str(light.raw.get(ATTR_ID)), 
            "name": str(light.raw.get(ATTR_NAME)),
            "state": str(light.light_control.raw[0].get(ATTR_DEVICE_STATE)),
            "level": str(light.light_control.raw[0].get(ATTR_LIGHT_DIMMER)),
            "color": str(light.light_control.raw[0].get(ATTR_LIGHT_MIREDS)) 
        }, 
        lights))
    return jp.encode(lights_dict, unpicklable=False), 200, {'Content-Type': 'application/json'}

@app.route('/light/<light_id>/state/<state_on_off>', methods=['PUT'])
def set_light_state(light_id, state_on_off):
    """Turn specific light bulb on/off.
    ---
    parameters:
    - name: light_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /light' endpoint.
    - name: state_on_off
      in: path
      type: string
      required: true
      description: Parameter value must be either 'on' or 'off'.     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
    if (state_on_off.lower() != 'on' and state_on_off.lower() != 'off'): return 400

    state_boolean = True if (state_on_off.lower() == 'on') else False
    filtered_lights = list(filter(lambda light: str(light.raw.get(ATTR_ID)) == light_id, lights))
    if not filtered_lights: return 404 #light with submitted id was not found
    
    try:        
        api(filtered_lights[0].light_control.set_state(state_boolean))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Light ' + light_id + ', state set to: ' + state_on_off, 200


@app.route('/light/<light_id>/color/<int:color_temp>', methods=['PUT'])
def set_light_color(light_id, color_temp):
    """Set color temperature for specific light bulb.
    ---
    parameters:
    - name: light_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /light' endpoint.
    - name: color_temp
      in: path
      type: int
      required: true
      description: Parameter value must be within range (250, 454).     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
    # Ensure color temp value is within allowed range of (250, 454)
    if (color_temp < 250): color_temp = 250
    if (color_temp > 454): color_temp = 454  

    filtered_lights = list(filter(lambda light: str(light.raw.get(ATTR_ID)) == light_id, lights))
    if not filtered_lights: return 404 #light with submitted id was not found
    
    try:        
        api(filtered_lights[0].light_control.set_color_temp(color_temp))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Light ' + light_id + ', color set to: ' + str(color_temp), 200

@app.route('/light/<light_id>/level/<int:light_level>', methods=['PUT'])
def set_light_light_level(light_id, light_level):
    """Set light level for specific light bulb.
    ---
    parameters:
    - name: light_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /light' endpoint.
    - name: light_level
      in: path
      type: int
      required: true
      description: Parameter value must be within range (0, 254).     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
    # Ensure light level value is within allowed range of (0, 254)
    if (light_level < 0): light_level = 0
    if (light_level > 254): light_level = 254  

    filtered_lights = list(filter(lambda light: str(light.raw.get(ATTR_ID)) == light_id, lights))
    if not filtered_lights: return 404 #group with submitted id was not found
    
    try:        
        api(filtered_lights[0].light_control.set_dimmer(light_level))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Light ' + light_id + ', light level set to: ' + str(light_level), 200

@app.route('/group', methods=['GET'])
def get_groups():
    """Retrieve a list of all registered groups.
    ---    
    responses:
      200:
        description: ok
        examples:
          { "id": "99999", "name": "Group1", "state": "1", "level": "254", "color": "330" }
    """
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
    """Turn specific light group on/off.
    ---
    parameters:
    - name: group_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /group' endpoint.
    - name: state_on_off
      in: path
      type: string
      required: true
      description: Parameter value must be either 'on' or 'off'.     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
    if (state_on_off.lower() != 'on' and state_on_off.lower() != 'off'): return 400

    state_boolean = True if (state_on_off.lower() == 'on') else False
    filtered_groups = list(filter(lambda group: str(group.raw.get(ATTR_ID)) == group_id, groups))
    if not filtered_groups: return 404 #group with submitted id was not found
    
    try:        
        api(filtered_groups[0].set_state(state_boolean))    
    except Exception as e:
        app.logger.error(traceback.format_exc())
        abort(500)
    return 'Group ' + group_id + ', state set to: ' + state_on_off, 200

@app.route('/group/<group_id>/color/<int:color_temp>', methods=['PUT'])
def set_group_color(group_id, color_temp):
    """Set color temperature for specific light group.
    ---
    parameters:
    - name: group_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /group' endpoint.
    - name: color_temp
      in: path
      type: int
      required: true
      description: Parameter value must be within range (250, 454).     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
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
    return 'Group ' + group_id + ', color set to: ' + str(color_temp), 200

@app.route('/group/<group_id>/level/<int:light_level>', methods=['PUT'])
def set_group_light_level(group_id, light_level):
    """Set light level for specific light group.
    ---
    parameters:
    - name: group_id
      in: path
      type: string
      required: true
      description: Valid parameter values can be retrieved via 'GET /group' endpoint.
    - name: light_level
      in: path
      type: int
      required: true
      description: Parameter value must be within range (0, 254).     
    responses:
      200:
        description: ok
      400:
        description: Missing or invalid input
    """
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
    return 'Group ' + group_id + ', light level set to: ' + str(light_level), 200


# Initialization of server for retrieving lights/groups from IKEA Tradfri Gateway
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
