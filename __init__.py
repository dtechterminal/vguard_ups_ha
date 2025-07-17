import logging
import voluptuous as vol
import json
import paho.mqtt.client as mqtt
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_TOKEN): cv.string,  # Using CONF_TOKEN for SERIAL
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass, config):
    """Set up the V-Guard Inverter component."""
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=conf,
        )
    )
    return True

async def async_setup_entry(hass, entry):
    """Set up V-Guard Inverter from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Store entry data
    conf = entry.data
    broker = conf[CONF_HOST]
    port = conf[CONF_PORT]
    serial = conf[CONF_TOKEN]
    
    # Create shared MQTT client
    client = mqtt.Client()
    client.connect(broker, port)
    client.loop_start()
    
    # Define topics
    telemetry_topic = f"device/dups/CE01/{serial}"
    control_topic = f"apps/dups/CE01/{serial}"
    lwt_topic = f"device/dups/CE01/lwt/{serial}"
    
    # Send initial 'start' command
    client.publish(control_topic, "start")
    
    # Store shared data
    hass.data[DOMAIN][entry.entry_id] = {
        "config": conf,
        "mqtt_client": client,
        "telemetry_topic": telemetry_topic,
        "control_topic": control_topic,
        "lwt_topic": lwt_topic,
        "latest_data": {},  # Store latest telemetry data
    }
    
    # Set up MQTT message handler
    def on_message(client, userdata, msg):
        if msg.topic == telemetry_topic:
            try:
                data = json.loads(msg.payload.decode())
                # Unwrap if nested
                if len(data) == 1 and isinstance(next(iter(data.values())), dict):
                    data = next(iter(data.values()))
                
                # Store latest data
                hass.data[DOMAIN][entry.entry_id]["latest_data"] = data
                
                # Signal data update to all platforms
                hass.helpers.dispatcher.async_dispatcher_send(f"{DOMAIN}_data_update", data)
            except Exception as e:
                _LOGGER.error(f"Error processing telemetry: {e}")
    
    # Subscribe to telemetry topic
    client.on_message = on_message
    client.subscribe(telemetry_topic)
    
    # Forward the setup to the sensor and switch platforms
    discovery.load_platform(hass, "sensor", DOMAIN, {}, entry)
    discovery.load_platform(hass, "switch", DOMAIN, {}, entry)
    discovery.load_platform(hass, "mode_select", DOMAIN, {}, entry)
    discovery.load_platform(hass, "number", DOMAIN, {}, entry)

    return True
