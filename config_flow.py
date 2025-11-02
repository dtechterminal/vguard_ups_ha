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
        discovery_topic = "device/dups/CE01/#"  # Changed from + to # to catch all subtopics

        _LOGGER.info("Starting MQTT discovery on topic: %s", discovery_topic)

        @callback
        def message_received(msg):
            """Handle received MQTT message."""
            try:
                _LOGGER.debug("Received discovery message on topic: %s", msg.topic)

                # Extract serial from topic: device/dups/CE01/{serial} or device/dups/CE01/lwt/{serial}
                topic_parts = msg.topic.split("/")

                # Handle both telemetry and LWT topics
                if "lwt" in topic_parts:
                    # LWT topic: device/dups/CE01/lwt/{serial}
                    if len(topic_parts) >= 5:
                        serial = topic_parts[4]
                        _LOGGER.debug("Found serial from LWT topic: %s", serial)
                elif len(topic_parts) >= 4:
                    # Telemetry topic: device/dups/CE01/{serial}
                    serial = topic_parts[3]
                    _LOGGER.debug("Found serial from telemetry topic: %s", serial)
                else:
                    _LOGGER.debug("Topic format not recognized: %s", msg.topic)
                    return

                # Don't add duplicates and validate serial number
                if serial and serial not in discovered and len(serial) > 5:
                    # Get MQTT broker config from Home Assistant's MQTT integration
                    mqtt_data = self.hass.data.get("mqtt")
                    if mqtt_data:
                        # Try to get broker from MQTT config
                        host = "192.168.0.4"  # Default fallback
                        port = 1883
                    else:
                        host = "192.168.0.4"
                        port = 1883

                    discovered[serial] = {
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_TOKEN: serial,
                    }
                    _LOGGER.info("✓ Discovered V-Guard inverter: %s", serial)

            except Exception as err:
                _LOGGER.error("Error processing discovery message: %s", err, exc_info=True)

        try:
            # Check if MQTT is available
            if "mqtt" not in self.hass.data:
                _LOGGER.error("MQTT integration is not set up in Home Assistant")
                return {}

            # Subscribe to discovery topic
            _LOGGER.info("Subscribing to MQTT topic for discovery...")
            unsubscribe = await mqtt.async_subscribe(
                self.hass, discovery_topic, message_received, 1
            )

            # Wait for discovery timeout with progress logging
            _LOGGER.info("Listening for devices (30 seconds)...")
            for i in range(6):
                await asyncio.sleep(5)
                _LOGGER.debug("Discovery progress: %d/%d seconds, found %d device(s)",
                            (i+1)*5, DISCOVERY_TIMEOUT, len(discovered))

            # Unsubscribe
            unsubscribe()

            self.discovered_devices = discovered
            _LOGGER.info("Discovery complete. Found %d device(s): %s",
                        len(discovered), list(discovered.keys()))
            return discovered

        except Exception as err:
            _LOGGER.error("Discovery failed: %s", err, exc_info=True)
            return {}

    async def async_step_import(self, import_data):
        """Handle import from configuration.yaml."""
        return await self.async_step_manual(import_data)
