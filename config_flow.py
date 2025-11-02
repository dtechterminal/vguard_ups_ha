"""Config flow for V-Guard Inverter integration."""
import asyncio
import json
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import mqtt
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DISCOVERY_TIMEOUT = 30  # seconds


class VGuardInverterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for V-Guard Inverter."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_devices = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step - show menu."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["mqtt_discovery", "manual"],
        )

    async def async_step_mqtt_discovery(self, user_input=None):
        """Handle MQTT discovery step."""
        if user_input is not None:
            # User selected a device
            selected_device = user_input["device"]
            device_data = self.discovered_devices[selected_device]

            # Check if already configured
            await self.async_set_unique_id(device_data[CONF_TOKEN])
            self._abort_if_unique_id_configured()

            title = f"V-Guard Inverter {device_data[CONF_TOKEN][-6:]}"
            return self.async_create_entry(title=title, data=device_data)

        # Discover devices
        errors = {}
        discovered = await self._discover_devices()

        if not discovered:
            errors["base"] = "no_devices_found"

        if errors:
            return self.async_show_form(
                step_id="mqtt_discovery",
                errors=errors,
            )

        # Show device selection
        device_options = {
            serial: f"V-Guard Inverter {serial[-6:]}"
            for serial in discovered.keys()
        }

        data_schema = vol.Schema(
            {
                vol.Required("device"): vol.In(device_options),
            }
        )

        return self.async_show_form(
            step_id="mqtt_discovery",
            data_schema=data_schema,
            description_placeholders={"device_count": str(len(discovered))},
        )

    async def async_step_manual(self, user_input=None):
        """Handle manual configuration step."""
        errors = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(user_input[CONF_TOKEN])
            self._abort_if_unique_id_configured()

            try:
                title = f"V-Guard Inverter {user_input[CONF_TOKEN][-6:]}"
                return self.async_create_entry(title=title, data=user_input)
            except Exception as err:
                _LOGGER.exception("Unexpected exception: %s", err)
                errors["base"] = "unknown"

        # Show the manual configuration form
        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default="192.168.0.4"): cv.string,
                vol.Required(CONF_PORT, default=1883): cv.port,
                vol.Required(CONF_TOKEN): cv.string,
            }
        )

        return self.async_show_form(
            step_id="manual",
            data_schema=data_schema,
            errors=errors,
        )

    async def _discover_devices(self):
        """Discover V-Guard inverters via MQTT."""
        discovered = {}
        discovery_topic = "device/dups/CE01/+"

        @callback
        def message_received(msg):
            """Handle received MQTT message."""
            try:
                # Extract serial from topic: device/dups/CE01/{serial}
                topic_parts = msg.topic.split("/")
                if len(topic_parts) >= 4:
                    serial = topic_parts[3]

                    # Parse payload to get additional info if available
                    try:
                        payload = json.loads(msg.payload)
                        # Unwrap if nested
                        if len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
                            payload = next(iter(payload.values()))

                        # Extract host from payload if available (VG011 might contain this)
                        host = payload.get("host", "192.168.0.4")
                        port = payload.get("port", 1883)
                    except (json.JSONDecodeError, AttributeError):
                        # Default values if payload parsing fails
                        host = "192.168.0.4"
                        port = 1883

                    # Store discovered device
                    if serial not in discovered:
                        discovered[serial] = {
                            CONF_HOST: host,
                            CONF_PORT: port,
                            CONF_TOKEN: serial,
                        }
                        _LOGGER.debug("Discovered V-Guard inverter: %s", serial)

            except Exception as err:
                _LOGGER.debug("Error processing discovery message: %s", err)

        try:
            # Subscribe to discovery topic
            unsubscribe = await mqtt.async_subscribe(
                self.hass, discovery_topic, message_received, 1
            )

            # Wait for discovery timeout
            await asyncio.sleep(DISCOVERY_TIMEOUT)

            # Unsubscribe
            unsubscribe()

            self.discovered_devices = discovered
            _LOGGER.info("Discovery complete. Found %d device(s)", len(discovered))
            return discovered

        except Exception as err:
            _LOGGER.error("Discovery failed: %s", err)
            return {}

    async def async_step_import(self, import_data):
        """Handle import from configuration.yaml."""
        return await self.async_step_manual(import_data)
