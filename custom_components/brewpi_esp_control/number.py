"""
Number platform for BrewPi ESP Control integration.
"""
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
import logging
import traceback
from datetime import timedelta


from .control_consts import SETPOINT_CONTROLS
from .coordinator import BrewPiDataCoordinator

DOMAIN = "bewpi_esp_control"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    entities = []
    for setpoint_key, setpoint in SETPOINT_CONTROLS.items():
        entities.append(BrewPiSetpointNumber(coordinator, setpoint_key, setpoint))
    async_add_entities(entities)


class BrewPiSetpointNumber(NumberEntity):
    def __init__(self, coordinator: BrewPiDataCoordinator, setpoint_key: str, setpoint: dict):
        self.coordinator = coordinator
        self._setpoint_key = setpoint_key
        self._dynamic_unit = setpoint.get("dynamic_unit", False)
        self._static_unit = setpoint.get("unit")
        self._attr_name = f"{setpoint['name']} ({coordinator.ip_address})"
        self._attr_unique_id = f"{setpoint_key}_{coordinator.ip_address}"
        self._attr_native_unit_of_measurement = self._static_unit
        self._attr_native_min_value = setpoint.get("min")
        self._attr_native_max_value = setpoint.get("max")
        self._attr_native_step = setpoint.get("step")
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.ip_address)},
            "name": f"BrewPi ESP ({coordinator.ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{coordinator.ip_address}/"
        }
        self._logger = logging.getLogger(__name__)
        self._value = setpoint.get("min", 0.0)
        self._attr_scan_interval = coordinator.update_interval

    @property
    def native_value(self):
        return self._value

    async def async_update(self):

        try:
            await self.coordinator.async_request_refresh()
            data = self.coordinator.data
            if not data:
                return
            # Dynamic unit logic for temperature unit
            if self._dynamic_unit:
                temp_format = data.get("cc", {}).get("tempFormat", "C").upper()
                if temp_format == "F":
                    from homeassistant.const import UnitOfTemperature
                    self._attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
                else:
                    from homeassistant.const import UnitOfTemperature
                    self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
            # Try cs first, then temp
            value = data.get("cs", {}).get(self._setpoint_key)
            if value is None:
                value = data.get("temp", {}).get(self._setpoint_key)
            if value is not None:
                self._value = float(value)
        except Exception as e:
            self._logger.warning(f"Exception during async_update: {e}")

    async def async_set_native_value(self, value: float):
        # Get current mode from Home Assistant state, then coordinator data, then fallback to 'o'
        mode_code = None
        try:
            hass = self.hass if hasattr(self, 'hass') else None
            if hass is not None:
                entity_id = f"select.mode_{self.coordinator.ip_address.replace('.', '_')}"
                state = hass.states.get(entity_id)
                if state is not None and state.state not in (None, "unknown", "unavailable"):
                    # Map state name to code using MODE_CONTROLS
                    from .control_consts import MODE_CONTROLS
                    options = MODE_CONTROLS["mode"]["options"]
                    name_to_code = {v: k for k, v in options.items()}
                    mode_code = name_to_code.get(state.state)
        except Exception as e:
            self._logger.warning(f"Could not get current mode from select entity: {e}")

        # If not found in HA state, try coordinator data
        if not mode_code:
            try:
                data = self.coordinator.data
                if data and "cs" in data and "mode" in data["cs"]:
                    mode_code = data["cs"]["mode"]
            except Exception as e:
                self._logger.warning(f"Could not get current mode from coordinator data: {e}")

        # Fallback to 'o' only if all else fails
        if not mode_code:
            mode_code = "o"

        url = f"http://{self.coordinator.ip_address}/api/mode/"
        payload = {"newMode": mode_code, "setPoint": value}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        self._logger.debug(f"PUT {url} with payload: {payload}")
        import asyncio
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, timeout=10, headers=headers) as resp:
                    if resp.status == 200:
                        self._value = value
                        self.async_write_ha_state()
                        await self.coordinator.async_request_refresh()
                    else:
                        text = await resp.text()
                        self._logger.warning(f"Failed to set setpoint, status: {resp.status}, body: {text}")
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            self._logger.warning(f"Timeout or cancellation during async_set_native_value: {e}")
        except Exception as e:
            self._logger.error(f"Exception during async_set_native_value: {e}", exc_info=True)
