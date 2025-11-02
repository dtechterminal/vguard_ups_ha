"""Number platform for V-Guard Inverter."""
import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

# Number definitions: (vg_code, min_value, max_value, step, name, icon)
NUMBER_TYPES = {
    "performance_level": ("VG035", 1, 5, 1, "Performance Level", "mdi:speedometer"),
    "load_alarm_threshold": ("VG050", 50, 100, 10, "Load Alarm Threshold", "mdi:alert-circle-outline"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up V-Guard Inverter numbers from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data[CONF_TOKEN]
    telemetry_topic = config["telemetry_topic"]
    control_topic = config["control_topic"]

    entities = []
    for key, (vg_code, min_val, max_val, step, name, icon) in NUMBER_TYPES.items():
        entities.append(
            VGuardNumber(
                hass=hass,
                entry=entry,
                serial=serial,
                telemetry_topic=telemetry_topic,
                control_topic=control_topic,
                number_key=key,
                vg_code=vg_code,
                min_value=min_val,
                max_value=max_val,
                step=step,
                number_name=name,
                number_icon=icon,
            )
        )

    async_add_entities(entities)


class VGuardNumber(NumberEntity):
    """Representation of a V-Guard Inverter number."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        serial: str,
        telemetry_topic: str,
        control_topic: str,
        number_key: str,
        vg_code: str,
        min_value: float,
        max_value: float,
        step: float,
        number_name: str,
        number_icon: str,
    ) -> None:
        """Initialize the number."""
        self.hass = hass
        self._entry = entry
        self._serial = serial
        self._telemetry_topic = telemetry_topic
        self._control_topic = control_topic
        self._vg_code = vg_code
        self._attr_native_min_value = min_value
        self._attr_native_max_value = max_value
        self._attr_native_step = step
        self._attr_native_value = min_value
        self._attr_name = number_name
        self._attr_unique_id = f"{DOMAIN}_{serial}_{number_key}"
        self._attr_icon = number_icon
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

                # Update number value if key exists in payload
                if self._vg_code in payload:
                    value = payload[self._vg_code]
                    try:
                        float_value = float(value)
                        if self._attr_native_min_value <= float_value <= self._attr_native_max_value:
                            self._attr_native_value = float_value
                            self.async_write_ha_state()
                            _LOGGER.debug("Updated %s to %s", self._vg_code, float_value)
                        else:
                            _LOGGER.warning(
                                "Value %s for %s is out of range [%s, %s]",
                                float_value,
                                self._vg_code,
                                self._attr_native_min_value,
                                self._attr_native_max_value,
                            )
                    except (ValueError, TypeError) as err:
                        _LOGGER.warning(
                            "Failed to convert %s value '%s' to number: %s",
                            self._vg_code,
                            value,
                            err,
                        )

            except json.JSONDecodeError as err:
                _LOGGER.error("Failed to decode JSON: %s", err)
            except Exception as err:
                _LOGGER.error("Error processing message: %s", err)

        await mqtt.async_subscribe(self.hass, self._telemetry_topic, message_received, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        int_value = int(value)
        await mqtt.async_publish(
            self.hass,
            self._control_topic,
            f"{self._vg_code}:{int_value}",
            qos=1,
        )
        self._attr_native_value = int_value
        self.async_write_ha_state()
