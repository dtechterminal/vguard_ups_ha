"""Sensor platform for V-Guard Inverter."""
import json
import logging
import datetime
from typing import Any

from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)

# Sensor definitions: (key, name, icon, device_class, state_class, transform_fn)
SENSOR_TYPES = {
    "VG011": ("Wi-Fi Signal", "mdi:wifi", SensorDeviceClass.SIGNAL_STRENGTH, SensorStateClass.MEASUREMENT, lambda v: f"{v} dBm"),
    "VG012": ("Wi-Fi Firmware Version", "mdi:cellphone-wireless", None, None, None),
    "VG132": ("Wi-Fi MAC ID", "mdi:access-point-network", None, None, lambda v: ':'.join(v[i:i+2] for i in range(0, len(v), 2)) if v else v),
    "VG136": ("Router SSID", "mdi:router-wireless", None, None, None),
    "VG304": ("Timezone Offset", "mdi:clock-time-four-outline", None, None, None),
    "VG042": ("System Uptime", "mdi:timer-outline", None, None, lambda v: str(datetime.timedelta(seconds=int(v)))),
    "VG144": ("Temperature", "mdi:thermometer", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT, lambda v: f"{v}°C"),
    "VG146": ("Total Energy", "mdi:lightning-bolt", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, lambda v: f"{int(v)/1000:.2f} kWh"),
    "VG211": ("Energy Usage", "mdi:power-plug", SensorDeviceClass.ENERGY, SensorStateClass.TOTAL_INCREASING, lambda v: f"{int(v)/1000:.2f} kWh"),
    "VG033": ("Charging Mode", "mdi:battery-charging", None, None, None),
    "VG095": ("Battery Capacity", "mdi:battery", None, None, None),
    "VG003": ("Device Status Code", "mdi:information-outline", None, None, None),
    "VG013": ("Device Model Parameter", "mdi:tag-outline", None, None, None),
    "VG109": ("Last Update Time", "mdi:clock-outline", None, None, None),
    "VG041": ("Power Mode", "mdi:power", None, None, lambda v: "normal mode" if v == "0" else "unknown"),
    "VG094": ("System Mode", "mdi:cog-outline", None, None, lambda v: "normal operation" if v == "1" else "unknown"),
    "VG014": ("Input Voltage", "mdi:flash", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, lambda v: f"{v} V"),
    "VG015": ("Output Voltage", "mdi:flash-outline", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, lambda v: f"{v} V"),
    "VG016": ("Battery Voltage", "mdi:battery-outline", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT, lambda v: f"{v} V"),
    "VG017": ("Battery Percentage", "mdi:battery-charging-outline", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT, lambda v: f"{v}%"),
    "VG018": ("Charging Current", "mdi:current-ac", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT, lambda v: f"{v} A"),
    "VG019": ("Load Percentage", "mdi:gauge", None, SensorStateClass.MEASUREMENT, lambda v: f"{v}%"),
    "VG020": ("Backup Time", "mdi:clock", None, None, lambda v: f"{int(int(v)/60)}h{int(int(v)%60)}m"),
    "VG022": ("Inverter Status", "mdi:power-socket", None, None, None),
    "VG023": ("Battery Status", "mdi:battery-alert", None, None, None),
    "VG024": ("Battery Health", "mdi:heart-pulse", None, None, lambda v: f"{v}%"),
    "VG025": ("Battery Capacity in Ah", "mdi:battery-high", None, None, lambda v: f"{int(v)/10} Ah"),
    "VG026": ("Total Runtime", "mdi:timer", None, None, lambda v: str(datetime.timedelta(seconds=int(v)))),
    "VG098": ("Total Runtime Mirror", "mdi:timer-sand", None, None, lambda v: str(datetime.timedelta(seconds=int(v)))),
    "VG037": ("Forced Power Cut Duration", "mdi:timer-off-outline", None, None, lambda v: f"{v} min"),
    "VG038": ("Forced Power Cut Status", "mdi:power-off", None, None, lambda v: "ON" if v == "1" else "OFF"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up V-Guard Inverter sensors from config entry."""
    config = hass.data[DOMAIN][entry.entry_id]
    serial = entry.data[CONF_TOKEN]
    telemetry_topic = config["telemetry_topic"]

    entities = []
    for key, (name, icon, device_class, state_class, transform) in SENSOR_TYPES.items():
        entities.append(
            VGuardSensor(
                hass=hass,
                entry=entry,
                serial=serial,
                telemetry_topic=telemetry_topic,
                sensor_key=key,
                sensor_name=name,
                sensor_icon=icon,
                device_class=device_class,
                state_class=state_class,
                transform=transform,
            )
        )

    async_add_entities(entities)


class VGuardSensor(SensorEntity):
    """Representation of a V-Guard Inverter sensor."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        serial: str,
        telemetry_topic: str,
        sensor_key: str,
        sensor_name: str,
        sensor_icon: str,
        device_class: SensorDeviceClass | None,
        state_class: SensorStateClass | None,
        transform: callable | None,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._entry = entry
        self._serial = serial
        self._telemetry_topic = telemetry_topic
        self._key = sensor_key
        self._transform = transform
        self._attr_name = sensor_name
        self._attr_unique_id = f"{DOMAIN}_{serial}_{sensor_key}"
        self._attr_icon = sensor_icon
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_native_value = None
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

                # Update sensor value if key exists in payload
                if self._key in payload:
                    value = payload[self._key]
                    if self._transform:
                        try:
                            self._attr_native_value = self._transform(value)
                        except Exception as err:
                            _LOGGER.warning("Transform failed for %s: %s", self._key, err)
                            self._attr_native_value = value
                    else:
                        self._attr_native_value = value

                    self.async_write_ha_state()
                    _LOGGER.debug("Updated %s to %s", self._key, self._attr_native_value)

            except json.JSONDecodeError as err:
                _LOGGER.error("Failed to decode JSON: %s", err)
            except Exception as err:
                _LOGGER.error("Error processing message: %s", err)

        await mqtt.async_subscribe(self.hass, self._telemetry_topic, message_received, 1)
