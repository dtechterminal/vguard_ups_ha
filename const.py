"""Constants for the V-Guard Inverter integration."""

DOMAIN = "vguard_inverter"

# Device information
MANUFACTURER = "V-Guard"
MODEL = "Smart Inverter"

# Configuration keys
CONF_SERIAL = "serial"

# Default values
DEFAULT_NAME = "V-Guard Inverter"

# MQTT topic patterns
TOPIC_TELEMETRY = "device/dups/CE01/{serial}"
TOPIC_CONTROL = "apps/dups/CE01/{serial}"
TOPIC_LWT = "device/dups/CE01/lwt/{serial}"

# Entity types
ENTITY_SENSOR = "sensor"
ENTITY_SWITCH = "switch"
ENTITY_SELECT = "select"
ENTITY_NUMBER = "number"
