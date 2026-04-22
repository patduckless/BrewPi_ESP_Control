"""
Sensor platform for BrewPi ESP Control integration.
"""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

import aiohttp
import logging
import traceback
from datetime import timedelta


from .sensor_consts import SENSOR_TYPES, STATE_MAP
from .coordinator import BrewPiDataCoordinator

DOMAIN = "bewpi_esp_control"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = [
        BrewPiSensor(coordinator, key) for key in SENSOR_TYPES.keys()
    ]
    async_add_entities(entities)


class BrewPiSensor(SensorEntity):
    def __init__(self, coordinator: BrewPiDataCoordinator, key: str):
        self.coordinator = coordinator
        self._key = key
        sensor_info = SENSOR_TYPES[key]
        self._section = sensor_info.get("section", "temp")  # default to 'temp' if not specified
        self._attr_name = f"{sensor_info['name']} ({coordinator.ip_address})"
        self._attr_unique_id = f"brewpi_{key.lower()}_{coordinator.ip_address}"
        self._dynamic_unit = sensor_info.get("dynamic_unit", False)
        self._static_unit = sensor_info.get("unit")
        self._attr_unit_of_measurement = self._static_unit
        self._attr_device_class = sensor_info.get("device_class")
        self._attr_state_class = sensor_info.get("state_class")
        self._state = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.ip_address)},
            "name": f"BrewPi ESP ({coordinator.ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{coordinator.ip_address}/"
        }
        self._attr_scan_interval = coordinator.update_interval

    @property
    def state(self):
        # Special handling for State sensor
        if self._key == "State" and self._state is not None:
            # If controller mode is off (mode 'o' or code 9), return 'off'
            try:
                # _state may be int or str, handle both
                state_code = int(self._state)
                if state_code == 9:
                    return "off"
                return STATE_MAP.get(state_code, str(self._state))
            except Exception:
                # If _state is not int, check for string 'Control Off' or similar
                if str(self._state).lower() in ("control off", "off"):
                    return "off"
                return str(self._state)
        # Special handling for FridgeAnn and BeerAnn
        if self._key in ("FridgeAnn", "BeerAnn"):
            if self._state is None:
                return "not set"
        return self._state

    async def async_update(self):
        # Use coordinator data, do not poll API directly
        await self.coordinator.async_request_refresh()
        data = self.coordinator.data
        if not data:
            self._state = None
            return
        # If this is the Control State sensor, and mode is 'o', force state to 'off'
        if self._key == "State":
            mode = data.get("cs", {}).get("mode")
            if mode == "o":
                self._state = 9  # 9 is Control Off in STATE_MAP
                return
        # Dynamic unit logic for temperature unit
        if self._dynamic_unit:
            temp_format = data.get("cc", {}).get("tempFormat", "C").upper()
            if temp_format == "F":
                from homeassistant.const import UnitOfTemperature
                self._attr_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
            else:
                from homeassistant.const import UnitOfTemperature
                self._attr_unit_of_measurement = UnitOfTemperature.CELSIUS
        section = data.get(self._section, {})
        value = section.get(self._key)
        value_type = SENSOR_TYPES[self._key].get("type", str)
        if self._key in ("FridgeAnn", "BeerAnn"):
            # Show 'not set' if value is None or empty string
            if value is None or value == "":
                self._state = None
            else:
                self._state = value
        elif value == "" or value is None:
            self._state = None
        else:
            try:
                self._state = value_type(value)
            except Exception:
                self._state = value
