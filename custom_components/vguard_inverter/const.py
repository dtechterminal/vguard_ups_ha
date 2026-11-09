"""Constants for the V-Guard Smart integration."""
from datetime import timedelta

from . import protocol

DOMAIN = "vguard_inverter"  # Kept from when the integration covered inverters only
MANUFACTURER = "V-Guard"
MODELS = {protocol.INVERTER: "Smart Inverter", protocol.WATER_HEATER: "Smart Water Heater"}

CONF_SERIAL = "serial"
CONF_MODEL = "model"
CONF_CATEGORY = "category"  # protocol.INVERTER or protocol.WATER_HEATER
CONF_KEY = "key"  # Water heater AES key and IV, from the V-Guard app's account
CONF_IV = "iv"

# How long the config flow listens for devices. An inverter's last-will and latest
# telemetry are retained, so it shows up at once; a water heater only while it's on.
DISCOVERY_TIMEOUT = 5

# The inverter only streams telemetry for a while after `start`; ask again regularly
START_INTERVAL = timedelta(minutes=1)
# Without telemetry for this long the inverter's readings are stale and go unavailable
STALE_AFTER = timedelta(minutes=3)
