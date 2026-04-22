from homeassistant.const import UnitOfTemperature

SENSOR_TYPES = {
    "BeerTemp": {
        "name": "Beer Temperature",
        "dynamic_unit": True,
        "device_class": "temperature",
        "state_class": "measurement",
        "type": float,
    },
    "BeerSet": {
        "name": "Beer Setpoint",
        "dynamic_unit": True,
        "device_class": "temperature",
        "state_class": "measurement",
        "type": float,
    },
    "FridgeTemp": {
        "name": "Fridge Temperature",
        "dynamic_unit": True,
        "device_class": "temperature",
        "state_class": "measurement",
        "type": float,
    },
    "FridgeSet": {
        "name": "Fridge Setpoint",
        "dynamic_unit": True,
        "device_class": "temperature",
        "state_class": "measurement",
        "type": float,
    },
    "RoomTemp": {
        "name": "Room Temperature",
        "dynamic_unit": True,
        "device_class": "temperature",
        "state_class": "measurement",
        "type": float,
    },
    "BeerAnn": {
        "name": "Beer Annotation",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "type": str,
    },
    "FridgeAnn": {
        "name": "Fridge Annotation",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "type": str,
    },
    "State": {
        "name": "Control State",
        "unit": None,
        "device_class": None,
        "state_class": None,
        "type": str,
    },
}

STATE_MAP = {
    0: "Idle",
    1: "Waiting to cool",
    2: "Waiting to heat",
    3: "Waiting for peak",
    4: "Cooling",
    5: "Heating",
    6: "Cooling",
    7: "Heating",
    8: "Door open",
    9: "Control Off"
}