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
    from .coordinator import BrewPiDataCoordinator
    hass.data.setdefault(DOMAIN, {})
    ip_address = entry.data.get("ip_address")
    scan_interval = entry.data.get("scan_interval", 30)
    coordinator = BrewPiDataCoordinator(hass, ip_address, scan_interval)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "config": entry.data,
    }
    _LOGGER.info(f"BrewPi ESP Control setup with IP: {ip_address}")
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, ["sensor", "select", "number"])
    )
    return True
