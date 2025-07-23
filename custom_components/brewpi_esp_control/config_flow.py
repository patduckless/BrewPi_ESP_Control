"""
Config flow for BrewPi ESP Control integration.
"""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_IP_ADDRESS

DOMAIN = "bewpi_esp_control"

class BrewPiConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for BrewPi ESP Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            ip_address = user_input.get(CONF_IP_ADDRESS)
            if not ip_address:
                errors[CONF_IP_ADDRESS] = "required"
            if not errors:
                return self.async_create_entry(title=ip_address, data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_IP_ADDRESS): str}),
            errors=errors,
        )
