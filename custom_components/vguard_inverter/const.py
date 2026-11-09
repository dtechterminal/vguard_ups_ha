"""Constants for the V-Guard Inverter integration."""
from datetime import timedelta

DOMAIN = "vguard_inverter"
MANUFACTURER = "V-Guard"
MODEL = "Smart Inverter"

CONF_SERIAL = "serial"
CONF_MODEL = "model"

# How long the config flow listens for inverters. Their last-will and latest telemetry
# are retained, so known inverters show up at once.
DISCOVERY_TIMEOUT = 5

# The inverter only streams telemetry for a while after `start`; ask again regularly
START_INTERVAL = timedelta(minutes=1)
# Without telemetry for this long the readings are stale and entities go unavailable
STALE_AFTER = timedelta(minutes=3)
