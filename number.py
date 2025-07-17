import asyncio
import logging
import paho.mqtt.client as mqtt
from homeassistant.components import number
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN

from .const import DOMAIN
from .sensor import schedule_entity_update

_LOGGER = logging.getLogger(__name__)

NUMBERS = {
    "performance_level": ("VG035", 1, 5, 1, "Performance Level"),
    "load_alarm_threshold": ("VG050", 50, 100, 10, "Load Alarm Threshold"),
}

# Icons for each number
NUMBER_ICONS = {
    "performance_level": "mdi:speedometer",
    "load_alarm_threshold": "mdi:alert-circle-outline",
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the V-Guard Inverter numbers."""
    # This function is kept for backwards compatibility
    # New installations will use async_setup_entry
    pass

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the V-Guard Inverter numbers based on config entry."""
    # Get the entry data
    entry_id = entry.entry_id
    domain_data = hass.data[DOMAIN][entry_id]
    
    # Wait for sensor platform to initialize if needed
    if 'mqtt_client' not in domain_data:
        _LOGGER.warning("MQTT client not found in domain data. Sensor platform may not be initialized yet.")
        # We'll create a minimal setup and return
        return False
    
    # Use the shared MQTT client and topics
    client = domain_data['mqtt_client']
    control_topic = domain_data['control_topic']
    
    _LOGGER.info("Using shared MQTT client for V-Guard Inverter numbers")
    
    entities = []
    for key, (vg_code, min_val, max_val, step, name) in NUMBERS.items():
        entities.append(VGuardNumber(hass, client, control_topic, vg_code, min_val, max_val, step, name, key))
    
    # Store entities in domain data for the message handler to access
    domain_data['number_entities'] = entities
    
    async_add_entities(entities)
    
    return True

class VGuardNumber(number.NumberEntity):
    """Representation of a V-Guard Inverter number."""

    def __init__(self, hass, client, topic, vg_code, min_val, max_val, step, name, unique_key):
        """Initialize the number."""
        self._hass = hass
        self._client = client
        self._topic = topic
        self._vg_code = vg_code
        self._attr_min_value = min_val
        self._attr_max_value = max_val
        self._attr_step = step
        self._attr_value = min_val
        self._attr_name = name
        self._attr_unique_id = f"vguard_number_{unique_key}"
        self._unique_key = unique_key
        self._attr_native_value = min_val

    @property
    def native_value(self) -> float | None:
        return self._attr_native_value


    @property
    def icon(self):
        """Return the icon of the number."""
        return NUMBER_ICONS.get(self._unique_key, "mdi:numeric")

    def set_value(self, value: float):
        """Set new value."""
        int_value = int(value)
        self._client.publish(self._topic, f"{self._vg_code}:{int_value}")
        self._attr_native_value = int_value  # update the authoritative attribute
        schedule_entity_update(self._hass, self)
