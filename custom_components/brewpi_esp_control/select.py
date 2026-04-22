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
from datetime import timedelta

from .control_consts import MODE_CONTROLS

DOMAIN = "bewpi_esp_control"


class BrewPiControlSelect(SelectEntity):
    def __init__(self, coordinator, control_key: str, name: str, options_dict: dict):
        self.coordinator = coordinator
        self._control_key = control_key
        self._attr_name = f"{name} ({coordinator.ip_address})"
        self._attr_unique_id = f"{control_key}_{coordinator.ip_address}"
        self._attr_options = list(options_dict.values())
        self._code_to_name = {k: v for k, v in options_dict.items()}
        self._name_to_code = {v: k for k, v in options_dict.items()}
        self._state = None
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.ip_address)},
            "name": f"BrewPi ESP ({coordinator.ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{coordinator.ip_address}/"
        }
        self._logger = logging.getLogger(__name__)
        self._attr_scan_interval = coordinator.update_interval

    @property
    def current_option(self):
        return self._state

    async def async_update(self):
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._logger.debug(f"Updating BrewPiControlSelect for IP: {getattr(self.coordinator, 'ip_address', 'unknown')}, control: {self._control_key}")
        # Use coordinator data, do not poll API directly
        try:
            await self.coordinator.async_request_refresh()
            data = self.coordinator.data
            if not data:
                self._state = None
                return
            mode_code = data.get("cs", {}).get(self._control_key)
            self._state = self._code_to_name.get(mode_code, None)
        except Exception as e:
            self._logger.warning(f"Exception during async_update: {e}")

    async def async_select_option(self, option: str):
        import asyncio
        mode_code = self._name_to_code.get(option)
        if not mode_code:
            self._logger.warning(f"Invalid mode option selected: {option}")
            return
        url = f"http://{self.coordinator.ip_address}/api/{self._control_key}/"
        set_point = 0
        if mode_code != "o":
            set_point = 10  # fallback default
            try:
                entity_id = f"number.beerset_{self.coordinator.ip_address.replace('.', '_')}"
                hass = getattr(self, 'hass', None)
                if hass is not None:
                    state = hass.states.get(entity_id)
                    if state is not None and state.state not in (None, "unknown", "unavailable"):
                        set_point = float(state.state)
                    else:
                        entity_id = f"number.fridgeset_{self.coordinator.ip_address.replace('.', '_')}"
                        state = hass.states.get(entity_id)
                        if state is not None and state.state not in (None, "unknown", "unavailable"):
                            set_point = float(state.state)
            except Exception as e:
                self._logger.warning(f"Could not get setpoint from number entity: {e}")
        payload = {"newMode": mode_code, "setPoint": set_point}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._logger.debug(f"PUT {url} with payload: {payload}, and headers: {headers}")
        try:
            import aiohttp
            import asyncio
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.put(url, json=payload, headers=headers) as resp:
                    self._logger.debug(f"PUT status: {resp.status}")
                    text = await resp.text()
                    self._logger.debug(f"PUT response body: {text}")
                    if resp.status == 200:
                        self._logger.info(f"Mode successfully set to {option} ({mode_code})")
                        self._state = option
                        self.async_write_ha_state()
                        await self.coordinator.async_request_refresh()
                    else:
                        self._logger.warning(f"Failed to set mode, status: {resp.status}, body: {text}")
        except (aiohttp.ClientError, asyncio.TimeoutError, asyncio.CancelledError) as e:
            self._logger.warning(f"Timeout or client error during async_select_option: {type(e).__name__}: {e}")
        except Exception as e:
            self._logger.error(f"Exception during async_select_option: {e}", exc_info=True)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    for control_key, control in MODE_CONTROLS.items():
        options_dict = control.get("options", {})
        entities.append(BrewPiControlSelect(coordinator, control_key, control["name"], options_dict))
    async_add_entities(entities)

    # (Removed duplicate class definition and methods)
