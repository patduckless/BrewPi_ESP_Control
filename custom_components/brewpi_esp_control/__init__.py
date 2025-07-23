"""
BrewPi ESP Control integration init.
"""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType

DOMAIN = "bewpi_esp_control"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the BrewPi ESP Control integration from yaml (not used)."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up BrewPi ESP Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data
    _LOGGER.info(f"BrewPi ESP Control setup with IP: {entry.data.get('ip_address')}")
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor", "select"])
    )
    return True
