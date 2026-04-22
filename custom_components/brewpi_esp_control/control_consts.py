MODE_CONTROLS = {
    "mode": {
        "name": "Controller Mode",
        "options": {
            "o": "Off",
            "b": "Beer constant mode",
            "f": "Fridge constant mode",
        }
    }
}

SETPOINT_CONTROLS = {
    "setPoint": {
        "name": "Setpoint",
        "dynamic_unit": True,
        "min": 0.0,
        "max": 30.0,
        "step": 0.1,
    },
}
