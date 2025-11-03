"""The V-Guard Inverter integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    MANUFACTURER,
    MODEL,
    TOPIC_TELEMETRY,
    TOPIC_CONTROL,
    TOPIC_LWT,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH, Platform.SELECT, Platform.NUMBER]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up V-Guard Inverter from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Get configuration
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    serial = entry.data[CONF_TOKEN]

    # Create device registry entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, serial)},
        manufacturer=MANUFACTURER,
        model=MODEL,
        name=f"V-Guard Inverter {serial[-6:]}",
        sw_version="2.2.2",
    )

    # Store configuration for platforms
    hass.data[DOMAIN][entry.entry_id] = {
        "host": host,
        "port": port,
        "serial": serial,
        "telemetry_topic": TOPIC_TELEMETRY.format(serial=serial),
        "control_topic": TOPIC_CONTROL.format(serial=serial),
        "lwt_topic": TOPIC_LWT.format(serial=serial),
    }

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Publish initial start command via MQTT
    try:
        await hass.components.mqtt.async_publish(
            hass,
            TOPIC_CONTROL.format(serial=serial),
            "start",
            qos=1,
        )
        _LOGGER.info("Published start command to V-Guard Inverter")
    except Exception as err:
        _LOGGER.error("Failed to publish start command: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
