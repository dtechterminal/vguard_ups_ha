"""Switch platform for V-Guard Inverter."""
import json
import logging

from homeassistant.components import mqtt
from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

# Switch definitions: (vg_code, on_value, off_value, name, icon)
SWITCH_TYPES = {
    "turbo_charging": ("VG099", "1", "0", "Turbo Charging", "mdi:battery-charging-high"),
    "advance_low_battery_alarm": ("VG071", "1", "0", "Advance Low Battery Alarm", "mdi:battery-alert"),
    "mains_changeover_buzzer": ("VG034", "0", "2", "Mains Changeover Buzzer", "mdi:volume-high"),
    "appliance_mode": ("VG036", "1", "0", "Appliance Mode", "mdi:power-standby"),
    "daytime_load_usage": ("VG185", "1", "0", "Daytime Load Usage", "mdi:weather-sunny"),
    "battery_type_unlock": ("VG105", "1", "0", "Battery Type Unlock", "mdi:lock-open-variant"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up V-Guard Inverter switches from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data[CONF_TOKEN]
    telemetry_topic = config["telemetry_topic"]
    control_topic = config["control_topic"]

    entities = []
    for key, (vg_code, on_value, off_value, name, icon) in SWITCH_TYPES.items():
        entities.append(
            VGuardSwitch(
                hass=hass,
                entry=entry,
                serial=serial,
                telemetry_topic=telemetry_topic,
                control_topic=control_topic,
                switch_key=key,
                vg_code=vg_code,
                on_value=on_value,
                off_value=off_value,
                switch_name=name,
                switch_icon=icon,
            )
        )

    async_add_entities(entities)


class VGuardSwitch(SwitchEntity):
    """Representation of a V-Guard Inverter switch."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        serial: str,
        telemetry_topic: str,
        control_topic: str,
        switch_key: str,
        vg_code: str,
        on_value: str,
        off_value: str,
        switch_name: str,
        switch_icon: str,
    ) -> None:
        """Initialize the switch."""
        self.hass = hass
        self._entry = entry
        self._serial = serial
        self._telemetry_topic = telemetry_topic
        self._control_topic = control_topic
        self._vg_code = vg_code
        self._on_value = on_value
        self._off_value = off_value
        self._attr_name = switch_name
        self._attr_unique_id = f"{DOMAIN}_{serial}_{switch_key}"
        self._attr_icon = switch_icon
        self._attr_is_on = False
        self._attr_available = False  # Will be True once we receive data
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

                # Update switch state if key exists in payload
                if self._vg_code in payload:
                    value = payload[self._vg_code]
                    if value == self._on_value:
                        self._attr_is_on = True
                    elif value == self._off_value:
                        self._attr_is_on = False
                    else:
                        _LOGGER.warning(
                            "Unexpected value '%s' for switch %s", value, self._vg_code
                        )
                        return

                    self._attr_available = True  # Mark as available once we have data
                    self.async_write_ha_state()
                    _LOGGER.debug("Updated %s to %s", self._vg_code, self._attr_is_on)

            except json.JSONDecodeError as err:
                _LOGGER.error("Failed to decode JSON: %s", err)
            except Exception as err:
                _LOGGER.error("Error processing message: %s", err)

        await mqtt.async_subscribe(self.hass, self._telemetry_topic, message_received, 1)

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await mqtt.async_publish(
            self.hass,
            self._control_topic,
            f"{self._vg_code}:{self._on_value}",
            qos=1,
        )
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await mqtt.async_publish(
            self.hass,
            self._control_topic,
            f"{self._vg_code}:{self._off_value}",
            qos=1,
        )
        self._attr_is_on = False
        self.async_write_ha_state()
