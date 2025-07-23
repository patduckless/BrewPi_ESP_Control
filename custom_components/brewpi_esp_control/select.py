"""
Select platform for BrewPi ESP Control integration.
"""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
import aiohttp
import logging

from .control_consts import MODE_CONTROLS

DOMAIN = "bewpi_esp_control"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    ip_address = entry.data.get("ip_address")
    entities = []
    for control_key, control in MODE_CONTROLS.items():
        options_dict = control.get("options", {})
        entities.append(BrewPiControlSelect(ip_address, control_key, control["name"], options_dict))
    async_add_entities(entities)

class BrewPiControlSelect(SelectEntity):
    def __init__(self, ip_address: str, control_key: str, name: str, options_dict: dict):
        self._ip_address = ip_address
        self._control_key = control_key
        self._attr_name = f"{name} ({ip_address})"
        self._attr_unique_id = f"{control_key}_{ip_address}"
        self._attr_options = list(options_dict.values())
        self._code_to_name = {k: v for k, v in options_dict.items()}
        self._name_to_code = {v: k for k, v in options_dict.items()}
        self._state = None
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = {
            "identifiers": {(DOMAIN, ip_address)},
            "name": f"BrewPi ESP ({ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{ip_address}/"
        }
        self._logger = logging.getLogger(__name__)

    @property
    def current_option(self):
        return self._state

    async def async_update(self):
        self._logger.debug(f"Updating BrewPiControlSelect for IP: {self._ip_address}, control: {self._control_key}")
        if not self._ip_address:
            self._logger.warning("No IP address set for BrewPiControlSelect.")
            self._state = None
            return
        url = f"http://{self._ip_address}/api/all_temp_control/"
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    self._logger.debug(f"GET {url} status: {resp.status}")
                    text = await resp.text()
                    self._logger.debug(f"GET response body: {text}")
                    if resp.status == 200:
                        data = await resp.json()
                        self._logger.debug(f"Received data: {data}")
                        mode_code = data.get("cs", {}).get(self._control_key)
                        self._logger.debug(f"Mode code from response: {mode_code}")
                        self._state = self._code_to_name.get(mode_code, None)
                    else:
                        self._logger.warning(f"Failed to fetch mode, status: {resp.status}, body: {text}")
                        self._state = None
        except Exception as e:
            self._logger.error(f"Exception during async_update: {e}")
            self._state = None

    async def async_select_option(self, option: str):
        mode_code = self._name_to_code.get(option)
        if not mode_code:
            self._logger.warning(f"Invalid mode option selected: {option}")
            return
        url = f"http://{self._ip_address}/api/{self._control_key}/"
        payload = {self._control_key: mode_code}
        self._logger.debug(f"POST {url} with payload: {payload}")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as resp:
                    self._logger.debug(f"POST status: {resp.status}")
                    text = await resp.text()
                    self._logger.debug(f"POST response body: {text}")
                    if resp.status == 200:
                        self._logger.info(f"Mode successfully set to {option} ({mode_code})")
                        self._state = option
                    else:
                        self._logger.warning(f"Failed to set mode, status: {resp.status}, body: {text}")
        except Exception as e:
            self._logger.error(f"Exception during async_select_option: {e}")
