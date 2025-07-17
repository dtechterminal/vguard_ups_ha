import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

class VGuardInverterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """V-Guard Inverter configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Validate user input
            try:
                # Additional validation if needed
                pass
            except Exception:
                errors["base"] = "invalid_input"
            else:
                return self.async_create_entry(title="V-Guard Inverter", data=user_input)

        data_schema = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.0.4"): cv.string,
            vol.Required(CONF_PORT, default=8883): cv.port,
            vol.Required(CONF_TOKEN, default="2303750156424940"): cv.string,  # SERIAL
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_import(self, import_data):
        """Import from config."""
        return self.async_create_entry(title="V-Guard Inverter (Imported)", data=import_data)
