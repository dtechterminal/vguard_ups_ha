"""Config flow for V-Guard Inverter integration."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class VGuardInverterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for V-Guard Inverter."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_TOKEN])
            self._abort_if_unique_id_configured()

            try:
                # You could add connection validation here if needed
                # For now, we'll just accept the input
                title = f"V-Guard Inverter {user_input[CONF_TOKEN][-6:]}"
                return self.async_create_entry(title=title, data=user_input)
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # Show the form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.0.4"): cv.string,
                vol.Required(CONF_PORT, default=8883): cv.port,
                vol.Required(CONF_TOKEN): cv.string,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_import(self, import_data):
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)
