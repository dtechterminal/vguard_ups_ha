import json
import logging
import datetime
import paho.mqtt.client as mqtt
from homeassistant.components import sensor
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    CONF_HOST, CONF_PORT, CONF_TOKEN, STATE_UNKNOWN
)
from homeassistant.helpers.entity import Entity
import asyncio
from functools import partial

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Derived from the script's mappings (unchanged from previous versions)
DESCRIPTIONS = {
    "VG011": "Wi-Fi Signal",
    "VG012": "Wi-Fi Firmware version",
    "VG132": "Wi-Fi Mac ID",
    "VG136": "Router SSID",
    "VG304": "Timezone offset",
    "VG042": "System Uptime",
    "VG144": "Temperature",
    "VG146": "Total Energy",
    "VG211": "Energy Usage",
    "VG033": "Charging Mode",
    "VG095": "Battery Capacity",
    "VG195": ",NA",
    "VG135": "1",
    "VG003": "Device Status Code - Indicates the operational status of the device",
    "VG010": "Unknown tag (value)",
    "VG013": "Device Model Parameter",
    "VG109": "Last Update Time",
    "VG041": "Power Mode",
    "VG094": "System Mode",
    "VG206": "Unknown numeric flag",
    "VG014": "Input Voltage",
    "VG015": "Output Voltage",
    "VG016": "Battery Voltage",
    "VG017": "Battery Percentage",
    "VG018": "Charging Current",
    "VG019": "Load Percentage",
    "VG020": "Backup Time",
    "VG022": "Inverter Status",
    "VG023": "Battery Status",
    "VG024": "Battery Health",
    "VG025": "Battery Capacity in Ah",
    "VG026": "Total Runtime",
    "VG098": "Total Runtime Mirror",
    "VG037": "Forced power cut duration (minutes)",
    "VG038": "Forced power cut status",
    # Removed duplicate sensors that are already implemented as switches:
    # "VG099": "Turbo Charging",
    # "VG071": "Advance low battery alarm",
    # "VG034": "Mains changeover buzzer (0=on, 2=off)",
    # "VG036": "Appliance Mode (0=off,1=on)",
    # "VG185": "Daytime Load Usage",
    # "VG105": "Battery type switch lock/unlock (1=unlocked,0=locked)",
    # Removed duplicate sensor that is already implemented as a select:
    # "VG021": "Inverter mode (0=Normal,1=UPS,2=Equipment)",
    # Removed duplicate sensor that is already implemented as a number:
    # "VG035": "Performance Level (1-7)",
    # "VG050": "Alarm if load exceeds",
}

TRANSFORMS = {
    "VG011": lambda v: f"{v} dBm",
    "VG042": lambda v: str(datetime.timedelta(seconds=int(v))),
    "VG041": lambda v: "normal mode" if v == "0" else "unknown",
    "VG094": lambda v: "normal operation" if v == "1" else "unknown",
    "VG144": lambda v: f"{v}°C",
    "VG146": lambda v: f"{int(v)/1000:.2f} kWh",
    "VG211": lambda v: f"{int(v)/1000:.2f} kWh",
    "VG014": lambda v: f"{v} V",
    "VG015": lambda v: f"{v} V",
    "VG016": lambda v: f"{v} V",
    "VG017": lambda v: f"{v}%",
    "VG018": lambda v: f"{v} A",
    "VG020": lambda v: f"{int(int(v)/60)}h{int(int(v)%60)}m",
    "VG024": lambda v: f"{v}%",
    "VG025": lambda v: f"{int(v)/10} Ah",
    "VG026": lambda v: str(datetime.timedelta(seconds=int(v))),
    "VG098": lambda v: str(datetime.timedelta(seconds=int(v))),
    "VG104": lambda v: str(datetime.timedelta(seconds=int(v))),
    "VG036": lambda v: "ON" if v == "1" else "OFF",
    "VG037": lambda v: f"{v} min",
    "VG038": lambda v: "ON" if v == "1" else "OFF",
    "VG035": lambda v: f"Level {v}",
    "VG185": lambda v: "ON" if v == "1" else "OFF",
    "VG050": lambda v: f"{v}%",
    "VG071": lambda v: "ON" if v == "1" else "OFF",
    "VG034": lambda v: "ON" if v == "0" else ("OFF" if v == "2" else v),
    "VG021": lambda v: "Normal" if v == "0" else ("UPS" if v == "1" else ("Equipment" if v == "2" else v)),
    "VG105": lambda v: "Unlocked" if v == "1" else ("Locked" if v == "0" else v),
    "VG099": lambda v: "ON" if v == "1" else "OFF",
    "VG132": lambda v: ':'.join(v[i:i+2] for i in range(0, len(v), 2)) if v else v,  # Format MAC address with colons
}

# Icons for each sensor type
ICONS = {
    "VG011": "mdi:wifi",  # Wi-Fi Signal
    "VG012": "mdi:cellphone-wireless",  # Wi-Fi Firmware version
    "VG132": "mdi:access-point-network",  # Wi-Fi Mac ID
    "VG136": "mdi:router-wireless",  # Router SSID
    "VG304": "mdi:clock-time-four-outline",  # Timezone offset
    "VG042": "mdi:timer-outline",  # System Uptime
    "VG144": "mdi:thermometer",  # Temperature
    "VG146": "mdi:lightning-bolt",  # Total Energy
    "VG211": "mdi:power-plug",  # Energy Usage
    "VG033": "mdi:battery-charging",  # Charging Mode
    "VG095": "mdi:battery",  # Battery Capacity
    "VG003": "mdi:information-outline",  # Device Status Code
    "VG010": "mdi:help-circle-outline",  # Unknown tag
    "VG013": "mdi:tag-outline",  # Device Model Parameter
    "VG109": "mdi:clock-outline",  # Last Update Time
    "VG041": "mdi:power",  # Power Mode
    "VG094": "mdi:cog-outline",  # System Mode
    "VG206": "mdi:flag-outline",  # Unknown numeric flag
    "VG014": "mdi:flash",  # Input Voltage
    "VG015": "mdi:flash-outline",  # Output Voltage
    "VG016": "mdi:battery-outline",  # Battery Voltage
    "VG017": "mdi:battery-charging-outline",  # Battery Percentage
    "VG018": "mdi:current-ac",  # Charging Current
    "VG019": "mdi:gauge",  # Load Percentage
    "VG020": "mdi:clock",  # Backup Time
    "VG021": "mdi:home-lightning-bolt-outline",  # Inverter mode
    "VG022": "mdi:power-socket",  # Inverter Status
    "VG023": "mdi:battery-alert",  # Battery Status
    "VG024": "mdi:heart-pulse",  # Battery Health
    "VG025": "mdi:battery-high",  # Battery Capacity in Ah
    "VG026": "mdi:timer",  # Total Runtime
    "VG098": "mdi:timer-sand",  # Total Runtime Mirror
    "VG099": "mdi:battery-charging-high",  # Turbo Charging
    "VG037": "mdi:timer-off-outline",  # Forced power cut duration
    "VG038": "mdi:power-off",  # Forced power cut status
    "VG035": "mdi:speedometer",  # Performance Level
    "VG185": "mdi:weather-sunny",  # Daytime Load Usage
    "VG071": "mdi:alarm-light-outline",  # Advance low battery alarm
    "VG034": "mdi:volume-high",  # Mains changeover buzzer
    "VG050": "mdi:alert-circle-outline",  # Alarm if load exceeds
    "VG105": "mdi:lock-outline",  # Battery type switch lock/unlock
    "VG036": "mdi:power-standby",  # Appliance Mode
}

def calculate_battery_percentage(vg_data):
    try:
        battery_voltage = float(vg_data.get('VG014', '0'))
        charging_current = float(vg_data.get('VG015', '0'))
        max_battery_voltage = float(vg_data.get('VG016', '0'))
        is_charging = int(vg_data.get('VG071', '0')) == 1100
        is_discharging = not is_charging

        if is_charging:
            total = battery_voltage + charging_current
            if total > 0:
                percentage = (battery_voltage / total) * 100
                return max(0, min(100, int(percentage)))
            return 0
        else:
            if max_battery_voltage > 0:
                percentage = (battery_voltage / max_battery_voltage) * 100
                return max(0, min(100, int(percentage)))
            return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

# Helper function for thread-safe entity state updates
def schedule_entity_update(hass, entity):
    """Schedule entity state update on the event loop in a thread-safe way."""
    def _update_entity_state():
        """Update entity state on the event loop."""
        entity.async_schedule_update_ha_state()
    
    # Use call_soon_threadsafe to schedule the update on the event loop
    hass.loop.call_soon_threadsafe(_update_entity_state)

# Define the MQTT message handler outside the setup function
def on_message_handler(hass, entities, telemetry_topic):
    """Handle MQTT messages for V-Guard Inverter."""
    def on_message(client, userdata, msg):
        if msg.topic == telemetry_topic:
            try:
                _LOGGER.debug(f"Received message on {msg.topic}: {msg.payload.decode()}")
                data = json.loads(msg.payload.decode())
                
                # Log the original data structure for debugging
                _LOGGER.debug(f"Original data structure: {data}")
                
                # Handle different data formats
                # If data is a dictionary with a single key and that value is a dictionary, unwrap it
                if len(data) == 1 and isinstance(next(iter(data.values())), dict):
                    data = next(iter(data.values()))
                    _LOGGER.debug(f"Unwrapped data structure: {data}")
                
                # If data is a list, try to convert it to a dictionary
                if isinstance(data, list):
                    _LOGGER.debug(f"Data is a list, attempting to convert to dictionary")
                    try:
                        # Try to convert list to dictionary if it contains key-value pairs
                        dict_data = {}
                        for item in data:
                            if isinstance(item, dict) and len(item) == 1:
                                key = next(iter(item.keys()))
                                dict_data[key] = item[key]
                        if dict_data:
                            data = dict_data
                            _LOGGER.debug(f"Converted list to dictionary: {data}")
                    except Exception as list_err:
                        _LOGGER.warning(f"Failed to convert list to dictionary: {list_err}")
                
                # Calculate battery percentage
                if "VG019" in DESCRIPTIONS:
                    data["VG019"] = str(calculate_battery_percentage(data))
                
                # Log the keys found in the data
                _LOGGER.debug(f"Keys found in data: {list(data.keys())}")
                
                # Count how many entities will be updated
                update_count = sum(1 for entity in entities if entity.key in data)
                _LOGGER.debug(f"Entities to update: {update_count} out of {len(entities)}")
                
                # Update all sensors on the event loop
                for entity in entities:
                    if entity.key in data:
                        value = data[entity.key]
                        transform = TRANSFORMS.get(entity.key)
                        try:
                            new_state = transform(value) if transform else value
                            _LOGGER.debug(f"Updating {entity.key} with value {value}, transformed to {new_state}")
                        except Exception as transform_err:
                            _LOGGER.warning(f"Transformation failed for {entity.key}: {transform_err}")
                            new_state = value
                        entity._state = new_state
                        # Use thread-safe method to update entity state
                        schedule_entity_update(hass, entity)
                    else:
                        # Log which entities are not being updated
                        _LOGGER.debug(f"Entity {entity.key} not found in data")
                
                # Update number entities if they exist in domain data
                if DOMAIN in hass.data:
                    for entry_id in hass.data[DOMAIN]:
                        domain_data = hass.data[DOMAIN][entry_id]
                        
                        # Update number entities
                        if 'number_entities' in domain_data:
                            for number_entity in domain_data['number_entities']:
                                vg_code = number_entity._vg_code
                                if vg_code in data:
                                    value = data[vg_code]
                                    try:
                                        # Convert to float and ensure it's within the allowed range
                                        float_value = float(value)
                                        if number_entity._attr_min_value <= float_value <= number_entity._attr_max_value:
                                            number_entity._attr_value = float_value
                                            _LOGGER.debug(f"Updating number entity {vg_code} with value {float_value}")
                                            # Use thread-safe method to update entity state
                                            schedule_entity_update(hass, number_entity)
                                    except (ValueError, TypeError):
                                        _LOGGER.warning(f"Failed to convert {vg_code} value '{value}' to number")
                        
                        # Update select entities
                        if 'select_entities' in domain_data:
                            for select_entity in domain_data['select_entities']:
                                vg_code = select_entity._vg_code
                                if vg_code in data:
                                    value = data[vg_code]
                                    try:
                                        # Find the corresponding option for this value
                                        if value in select_entity._values:
                                            index = select_entity._values.index(value)
                                            option = select_entity._options[index]
                                            select_entity._attr_current_option = option
                                            _LOGGER.debug(f"Updating select entity {vg_code} with option {option} for value {value}")
                                            # Use thread-safe method to update entity state
                                            schedule_entity_update(hass, select_entity)
                                    except (ValueError, IndexError):
                                        _LOGGER.warning(f"Failed to find option for {vg_code} value '{value}'")
                        
                        # Update switch entities
                        if 'switch_entities' in domain_data:
                            for switch_entity in domain_data['switch_entities']:
                                vg_code = switch_entity._vg_code
                                if vg_code in data:
                                    value = data[vg_code]
                                    try:
                                        # Determine if the switch should be on or off based on the value
                                        if value == switch_entity._on_value:
                                            new_state = True
                                        elif value == switch_entity._off_value:
                                            new_state = False
                                        else:
                                            # If the value doesn't match either on or off value, log a warning
                                            _LOGGER.warning(f"Received unexpected value '{value}' for switch {vg_code}")
                                            continue
                                            
                                        # Only update if the state has changed
                                        if switch_entity._state != new_state:
                                            switch_entity._state = new_state
                                            _LOGGER.debug(f"Updating switch entity {vg_code} with state {new_state}")
                                            # Use thread-safe method to update entity state
                                            schedule_entity_update(hass, switch_entity)
                                    except Exception as switch_err:
                                        _LOGGER.warning(f"Failed to update switch {vg_code}: {switch_err}")
                
                # If only VG011 (Wi-Fi Signal) is being updated, log a warning
                if "VG011" in data and update_count == 1:
                    _LOGGER.warning("Only Wi-Fi Signal (VG011) is being updated. This may indicate an issue with the data format.")
            except Exception as e:
                _LOGGER.error(f"Error processing telemetry: {e}", exc_info=True)
    
    return on_message

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the V-Guard Inverter sensors."""
    # This function is kept for backwards compatibility
    # New installations will use async_setup_entry
    pass

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the V-Guard Inverter sensors based on config entry."""
    # Get the entry data
    entry_id = entry.entry_id
    conf = hass.data[DOMAIN][entry_id]
    
    # Check if we already have a shared MQTT client
    if 'mqtt_client' not in hass.data[DOMAIN][entry_id]:
        _LOGGER.info("Creating shared MQTT client for V-Guard Inverter integration")
        broker = conf[CONF_HOST]
        port = conf[CONF_PORT]
        serial = conf[CONF_TOKEN]

        telemetry_topic = f"device/dups/CE01/{serial}"
        control_topic = f"apps/dups/CE01/{serial}"
        lwt_topic = f"device/dups/CE01/lwt/{serial}"

        # Create a shared MQTT client for the integration
        client = mqtt.Client()
        client.connect(broker, port)
        client.loop_start()

        # Send initial 'start' command
        client.publish(control_topic, "start")
        
        # Store the client and topics in hass.data for other platforms to use
        hass.data[DOMAIN][entry_id]['mqtt_client'] = client
        hass.data[DOMAIN][entry_id]['telemetry_topic'] = telemetry_topic
        hass.data[DOMAIN][entry_id]['control_topic'] = control_topic
        hass.data[DOMAIN][entry_id]['lwt_topic'] = lwt_topic
        
        # Also store entities list for message handler
        hass.data[DOMAIN][entry_id]['sensor_entities'] = []
    else:
        _LOGGER.info("Using existing shared MQTT client for V-Guard Inverter integration")
        client = hass.data[DOMAIN][entry_id]['mqtt_client']
        telemetry_topic = hass.data[DOMAIN][entry_id]['telemetry_topic']
        control_topic = hass.data[DOMAIN][entry_id]['control_topic']
        
    entities = []
    for key in DESCRIPTIONS:
        entities.append(VGuardSensor(hass, client, telemetry_topic, key))

    # Store entities for message handler
    hass.data[DOMAIN][entry_id]['sensor_entities'] = entities
    
    # Set up the message handler
    message_handler = on_message_handler(hass, entities, telemetry_topic)
    client.on_message = message_handler
    client.subscribe(telemetry_topic)
    
    async_add_entities(entities)
    
    return True

class VGuardSensor(Entity):
    """Representation of a V-Guard Inverter sensor."""

    def __init__(self, hass, client, topic, key):
        """Initialize the sensor."""
        self._hass = hass
        self._client = client
        self._topic = topic
        self.key = key
        self._state = STATE_UNKNOWN
        self._attr_name = DESCRIPTIONS.get(key, key)
        self._attr_unique_id = f"vguard_{key.lower()}"
        self._attr_device_class = None
        self._attr_state_class = None
        
        # Set device_class and state_class for voltage sensors
        if key in ["VG014", "VG015", "VG016"]:  # Input, Output, Battery Voltage
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            
        # Set device_class and state_class for current sensors
        elif key == "VG018":  # Charging Current
            self._attr_device_class = SensorDeviceClass.CURRENT
            self._attr_state_class = SensorStateClass.MEASUREMENT
            
        # Set device_class and state_class for WiFi signal
        elif key == "VG011":  # WiFi Signal
            self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
            self._attr_state_class = SensorStateClass.MEASUREMENT
            
        # Set device_class for temperature
        elif key == "VG144":  # Temperature
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            
        # Set device_class for energy sensors
        elif key in ["VG146", "VG211"]:  # Total Energy, Energy Usage
            self._attr_device_class = SensorDeviceClass.ENERGY
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            
        # Set device_class for battery percentage
        elif key == "VG017":  # Battery Percentage
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICONS.get(self.key, "mdi:help-circle")

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state != STATE_UNKNOWN
