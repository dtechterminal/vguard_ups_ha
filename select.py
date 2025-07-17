import asyncio
import logging
import paho.mqtt.client as mqtt
from homeassistant.components import select
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN

from .const import DOMAIN
from .sensor import schedule_entity_update

_LOGGER = logging.getLogger(__name__)

SELECTS = {
    "inverter_mode": ("VG021", ["Normal", "UPS", "Equipment"], ["0", "1", "2"], "Inverter Mode"),
}

# Icons for each select
SELECT_ICONS = {
    "inverter_mode": "mdi:home-lightning-bolt-outline",
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the V-Guard Inverter selects."""
    # This function is kept for backwards compatibility
    # New installations will use async_setup_entry
    pass

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the V-Guard Inverter selects based on config entry."""
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
    
    _LOGGER.info("Using shared MQTT client for V-Guard Inverter selects")
    
    entities = []
    for key, (vg_code, options, values, name) in SELECTS.items():
        entities.append(VGuardSelect(hass, client, control_topic, vg_code, options, values, name, key))
    
    # Store entities in domain data for the message handler to access
    domain_data['select_entities'] = entities
    
    async_add_entities(entities)
    
    return True

class VGuardSelect(select.SelectEntity):
    """Representation of a V-Guard Inverter select."""

    def __init__(self, hass, client, topic, vg_code, options, values, name, unique_key):
        """Initialize the select."""
        self._hass = hass
        self._client = client
        self._topic = topic
        self._vg_code = vg_code
        self._options = options
        self._values = values
        self._attr_options = options
        self._attr_current_option = options[0]
        self._attr_name = name
        self._attr_unique_id = f"vguard_select_{unique_key}"
        self._unique_key = unique_key
        
    @property
    def icon(self):
        """Return the icon of the select."""
        return SELECT_ICONS.get(self._unique_key, "mdi:format-list-bulleted")

    def select_option(self, option: str):
        """Change the selected option."""
        index = self._options.index(option)
        value = self._values[index]
        self._client.publish(self._topic, f"{self._vg_code}:{value}")
        self._attr_current_option = option
        # Use thread-safe method to update entity state
        schedule_entity_update(self._hass, self)