"""
Select platform for BrewPi ESP Control integration.
This file implements the SelectEntity for controlling BrewPi ESP devices via Home Assistant.
"""

# Import Home Assistant base classes and helpers
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
import logging
import traceback
import aiohttp
import asyncio

# Import all available controls for BrewPi ESP
from .control_consts import ALL_CONTROLS

# Domain constant for this integration
DOMAIN = "bewpi_esp_control"


# Set up the select entities for each control when the integration is added to Home Assistant
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    # Get the IP address from the config entry
    ip_address = entry.data.get("ip_address")
    entities = []
    # Only create BrewPiControlSelect entities for controls with type 'select'
    for control_key, control in ALL_CONTROLS.items():
        if control.get("type") != "select":
            continue
        options_dict = control.get("options", {})
        entities.append(BrewPiControlSelect(ip_address, control_key, control["name"], options_dict))
    # Add all entities to Home Assistant
    async_add_entities(entities)


# SelectEntity implementation for BrewPi ESP control options
class BrewPiControlSelect(SelectEntity):
    def __init__(self, ip_address: str, control_key: str, name: str, options_dict: dict):
        """
        Initialize the select entity for a specific BrewPi control.
        :param ip_address: IP address of the BrewPi ESP device
        :param control_key: Key for the control (e.g., mode)
        :param name: Human-readable name for the control
        :param options_dict: Mapping of control codes to display names
        """
        self._ip_address = ip_address
        self._control_key = control_key
        # Set entity name and unique ID
        self._attr_name = f"{name} ({ip_address})"
        self._attr_unique_id = f"{control_key}_{ip_address}"
        # List of options for the select entity
        self._attr_options = list(options_dict.values())
        # Mappings for code <-> name
        self._code_to_name = {k: v for k, v in options_dict.items()}
        self._name_to_code = {v: k for k, v in options_dict.items()}
        self._state = None
        # Entity registry and device info
        self._attr_entity_registry_enabled_default = True
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_device_info = {
            "identifiers": {(DOMAIN, ip_address)},
            "name": f"BrewPi ESP ({ip_address})",
            "manufacturer": "BrewPi",
            "model": "ESP Controller",
            "configuration_url": f"http://{ip_address}/"
        }
        # Logger for this entity
        self._logger = logging.getLogger(__name__)


    @property
    def current_option(self):
        """
        Return the currently selected option (display name).
        """
        return self._state


    async def async_update(self):
        """
        Fetch the current control state from the BrewPi ESP device via HTTP GET.
        Updates the entity's state with the current option.
        """
        self._logger.debug(f"Updating BrewPiControlSelect for IP: {self._ip_address}, control: {self._control_key}")
        if not self._ip_address:
            self._logger.warning("No IP address set for BrewPiControlSelect.")
            self._state = None
            return
        url = f"http://{self._ip_address}/api/all_temp_control/"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=20) as resp:
                    self._logger.debug(f"GET {url} status: {resp.status}")
                    text = await resp.text()
                    self._logger.debug(f"GET response body: {text}")
                    if resp.status == 200:
                        data = await resp.json()
                        self._logger.debug(f"Received data: {data}")
                        # Extract the mode code for this control from the response
                        mode_code = data.get("cs", {}).get(self._control_key)
                        self._logger.debug(f"Mode code from response: {mode_code}")
                        self._state = self._code_to_name.get(mode_code, None)
                    else:
                        self._logger.warning(f"Failed to fetch mode, status: {resp.status}, body: {text}")
                        self._state = None
        except asyncio.TimeoutError:
            self._logger.error(f"TimeoutError during async_update: GET {url} timed out.")
            self._state = None
        except asyncio.CancelledError:
            self._logger.error(f"CancelledError during async_update: GET {url} was cancelled.")
            self._state = None
        except Exception as e:
            self._logger.error(f"Exception during async_update: {e}\n{traceback.format_exc()}")
            self._state = None


    async def async_select_option(self, option: str):
        """
        Set the selected control option on the BrewPi ESP device via HTTP POST.
        :param option: The display name of the option to select
        If setting mode to 'b' (beer constant) or 'f' (fridge constant), include the current setpoint in the payload.
        """
        mode_code = self._name_to_code.get(option)
        if not mode_code:
            self._logger.warning(f"Invalid mode option selected: {option}")
            return
        url = f"http://{self._ip_address}/api/{self._control_key}/"
        payload = {self._control_key: mode_code}

        # If setting mode, include BeerSet or fridgeSet as appropriate
        if self._control_key == "mode" and mode_code in ("b", "f"):
            # Fetch current setpoints from the API
            setpoint_url = f"http://{self._ip_address}/api/all_temp_control/"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(setpoint_url, timeout=20) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            temp_data = data.get("temp", {})
                            if mode_code == "b":
                                if "BeerSet" in temp_data:
                                    payload["setpoint"] = temp_data["BeerSet"]
                            elif mode_code == "f":
                                if "FridgeSet" in temp_data:
                                    payload["setpoint"] = temp_data["FridgeSet"]
            except asyncio.TimeoutError:
                self._logger.error(f"TimeoutError fetching setpoints for payload: GET {setpoint_url} timed out.")
            except asyncio.CancelledError:
                self._logger.error(f"CancelledError fetching setpoints for payload: GET {setpoint_url} was cancelled.")
            except Exception as e:
                self._logger.error(f"Exception fetching setpoints for payload: {e}\n{traceback.format_exc()}")

        self._logger.debug(f"POST {url} with payload: {payload}")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=20) as resp:
                    self._logger.debug(f"POST status: {resp.status}")
                    text = await resp.text()
                    self._logger.debug(f"POST response body: {text}")
                    if resp.status == 200:
                        self._logger.info(f"Mode successfully set to {option} ({mode_code})")
                        self._state = option
                    else:
                        self._logger.warning(f"Failed to set mode, status: {resp.status}, body: {text}")
        except asyncio.TimeoutError:
            self._logger.error(f"TimeoutError during async_select_option: POST {url} timed out.")
        except asyncio.CancelledError:
            self._logger.error(f"CancelledError during async_select_option: POST {url} was cancelled.")
        except Exception as e:
            self._logger.error(f"Exception during async_select_option: {e}\n{traceback.format_exc()}")
