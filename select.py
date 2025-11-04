"""Select platform for V-Guard Inverter."""
import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

# Select definitions: (vg_code, options, values, name, icon)
SELECT_TYPES = {
    "inverter_mode": ("VG021", ["Normal", "UPS", "Equipment"], ["0", "1", "2"], "Inverter Mode", "mdi:home-lightning-bolt-outline"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up V-Guard Inverter selects from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data[CONF_TOKEN]
    telemetry_topic = config["telemetry_topic"]
    control_topic = config["control_topic"]

    entities = []
    for key, (vg_code, options, values, name, icon) in SELECT_TYPES.items():
        entities.append(
            VGuardSelect(
                hass=hass,
                entry=entry,
                serial=serial,
                telemetry_topic=telemetry_topic,
                control_topic=control_topic,
                select_key=key,
                vg_code=vg_code,
                options=options,
                values=values,
                select_name=name,
                select_icon=icon,
            )
        )

    async_add_entities(entities)


class VGuardSelect(SelectEntity):
    """Representation of a V-Guard Inverter select."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        serial: str,
        telemetry_topic: str,
        control_topic: str,
        select_key: str,
        vg_code: str,
        options: list[str],
        values: list[str],
        select_name: str,
        select_icon: str,
    ) -> None:
        """Initialize the select."""
        self.hass = hass
        self._entry = entry
        self._serial = serial
        self._telemetry_topic = telemetry_topic
        self._control_topic = control_topic
        self._vg_code = vg_code
        self._options = options
        self._values = values
        self._attr_options = options
        self._attr_current_option = options[0]
        self._attr_name = select_name
        self._attr_unique_id = f"{DOMAIN}_{serial}_{select_key}"
        self._attr_icon = select_icon
        self._attr_available = False  # Will be True once we receive any MQTT message
        self._has_received_message = False
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, serial)},
            name=f"V-Guard Inverter {serial[-6:]}",
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def async_added_to_hass(self) -> None:
        """Subscribe to MQTT topic."""

        @callback
        def message_received(msg):
            """Handle new MQTT messages."""
            try:
                payload = json.loads(msg.payload)
                _LOGGER.debug("Received MQTT message: %s", payload)

                # Unwrap nested data if needed
                if len(payload) == 1 and isinstance(next(iter(payload.values())), dict):
                    payload = next(iter(payload.values()))

                # Mark entity as available after receiving first message
                if not self._has_received_message:
                    self._has_received_message = True
                    self._attr_available = True
                    _LOGGER.debug("Entity %s is now available", self._vg_code)

                # Update select state if key exists in payload
                if self._vg_code in payload:
                    value = payload[self._vg_code]
                    try:
                        # Find the corresponding option for this value
                        if value in self._values:
                            index = self._values.index(value)
                            self._attr_current_option = self._options[index]
                            self.async_write_ha_state()
                            _LOGGER.debug(
                                "Updated %s to %s", self._vg_code, self._attr_current_option
                            )
                    except (ValueError, IndexError) as err:
                        _LOGGER.warning(
                            "Failed to find option for %s value '%s': %s",
                            self._vg_code,
                            value,
                            err,
                        )
                        # Still write state to show entity is available
                        self.async_write_ha_state()
                elif self._has_received_message:
                    # Entity is available but value not in this message
                    # Still write state to ensure availability is reflected
                    self.async_write_ha_state()

            except json.JSONDecodeError as err:
                _LOGGER.error("Failed to decode JSON: %s", err)
            except Exception as err:
                _LOGGER.error("Error processing message: %s", err)

        await mqtt.async_subscribe(self.hass, self._telemetry_topic, message_received, 1)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        try:
            index = self._options.index(option)
            value = self._values[index]
            await mqtt.async_publish(
                self.hass,
                self._control_topic,
                f"{self._vg_code}:{value}",
                qos=1,
            )
            self._attr_current_option = option
            self.async_write_ha_state()
        except ValueError as err:
            _LOGGER.error("Invalid option '%s': %s", option, err)
