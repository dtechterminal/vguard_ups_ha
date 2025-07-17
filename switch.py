import asyncio
import logging
import paho.mqtt.client as mqtt
from homeassistant.components import switch
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.helpers.entity import ToggleEntity

from .const import DOMAIN
from .sensor import schedule_entity_update

_LOGGER = logging.getLogger(__name__)

SWITCHES = {
    "turbo_charging": ("VG099", "1", "0", "Turbo Charging"),
    "advance_low_battery_alarm": ("VG071", "1", "0", "Advance Low Battery Alarm"),
    "mains_changeover_buzzer": ("VG034", "0", "2", "Mains Changeover Buzzer"),  # 0=on, 2=off
    "appliance_mode": ("VG036", "1", "0", "Appliance Mode"),
    "daytime_load_usage": ("VG185", "1", "0", "Daytime Load Usage"),
    "battery_type_lock": ("VG105", "0", "1", "Battery Type Lock"),  # Inverted: on=locked (0), off=unlocked (1)
}

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the V-Guard Inverter switches."""
    entry_id = list(hass.data[DOMAIN].keys())[0]
    domain_data = hass.data[DOMAIN][entry_id]
    
    # Wait for sensor platform to initialize if needed
    if 'mqtt_client' not in domain_data:
        _LOGGER.warning("MQTT client not found in domain data. Sensor platform may not be initialized yet.")
        # We'll create a minimal setup and return
        return
    
    # Use the shared MQTT client and topics
    client = domain_data['mqtt_client']
    control_topic = domain_data['control_topic']
    
    _LOGGER.info("Using shared MQTT client for V-Guard Inverter switches")
    
    entities = []
    for key, (vg_code, on_value, off_value, name) in SWITCHES.items():
        entities.append(VGuardSwitch(hass, client, control_topic, vg_code, on_value, off_value, name, key))
    
    add_entities(entities)

class VGuardSwitch(ToggleEntity):
    """Representation of a V-Guard Inverter switch."""

    def __init__(self, hass, client, topic, vg_code, on_value, off_value, name, unique_key):
        """Initialize the switch."""
        self._hass = hass
        self._client = client
        self._topic = topic
        self._vg_code = vg_code
        self._on_value = on_value
        self._off_value = off_value
        self._state = False
        self._attr_name = name
        self._attr_unique_id = f"vguard_switch_{unique_key}"

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._client.publish(self._topic, f"{self._vg_code}:{self._on_value}")
        self._state = True
        # Use thread-safe method to update entity state
        schedule_entity_update(self._hass, self)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._client.publish(self._topic, f"{self._vg_code}:{self._off_value}")
        self._state = False
        # Use thread-safe method to update entity state
        schedule_entity_update(self._hass, self)