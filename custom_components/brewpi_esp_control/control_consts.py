ALL_CONTROLS = {
    "mode": {
        "name": "Controller Mode",
        "type": "select",
        "options": {
            "o": "Off",
            "b": "Beer constant mode",
            "f": "Fridge constant mode",
        }
    },
    "beerSet": {
        "name": "Beer Setpoint",
        "type": "number",
        "unit": "°C",
        "min": 0.0,
        "max": 30.0,
        "step": 0.1,
    },
    "fridgeSet": {
        "name": "Fridge Setpoint",
        "type": "number",
        "unit": "°C",
        "min": 0.0,
        "max": 30.0,
        "step": 0.1,
    },
}
