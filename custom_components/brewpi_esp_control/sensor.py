"""
Sensor platform for BrewPi ESP Control integration.
"""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import aiohttp

from .sensor_consts import SENSOR_TYPES, STATE_MAP

DOMAIN = "bewpi_esp_control"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    ip_address = entry.data.get("ip_address")
    entities = [
        BrewPiSensor(ip_address, key, config_entry=entry) for key in SENSOR_TYPES.keys()
    ]
    async_add_entities(entities)

class BrewPiSensor(SensorEntity):
    def __init__(self, ip_address: str, key: str, config_entry=None):
        self._ip_address = ip_address
        self._key = key
        sensor_info = SENSOR_TYPES[key]
        self._attr_name = f"{sensor_info['name']} ({ip_address})"
        self._attr_unique_id = f"brewpi_{key.lower()}_{ip_address}"
        self._attr_unit_of_measurement = sensor_info["unit"]
        self._attr_device_class = sensor_info["device_class"]
        self._attr_state_class = sensor_info["state_class"]
        self._state = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, ip_address)},
            "name": f"BrewPi ESP ({ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{ip_address}/"
        }
        self._config_entry = config_entry

    @property
    def state(self):
        if self._key == "State" and self._state is not None:
            try:
                return STATE_MAP.get(int(self._state), str(self._state))
            except Exception:
                return str(self._state)
        return self._state

    async def async_update(self):
        if not self._ip_address:
            self._state = None
            return
        url = f"http://{self._ip_address}/api/all_temp_control/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if self._key == "State":
                            value = data.get("temp", {}).get("State")
                            if value == "" or value is None:
                                self._state = None
                            else:
                                try:
                                    self._state = int(value)
                                except Exception:
                                    self._state = value
                        else:
                            value = data.get("temp", {}).get(self._key)
                            value_type = SENSOR_TYPES[self._key]["type"]
                            if value == "" or value is None:
                                self._state = None
                            else:
                                try:
                                    self._state = value_type(value)
                                except Exception:
                                    self._state = value
                    else:
                        self._state = None
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error updating BrewPiSensor {self._key}: {e}")
            self._state = None
