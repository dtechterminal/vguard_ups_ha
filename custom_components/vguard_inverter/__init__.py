"""The V-Guard Smart integration."""
from __future__ import annotations

import logging

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from . import protocol
from .const import CONF_MODEL, CONF_SERIAL
from .device import VGuardConfigEntry, VGuardDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = {
    protocol.INVERTER: [Platform.NUMBER, Platform.SELECT, Platform.SENSOR, Platform.SWITCH],
    protocol.WATER_HEATER: [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.WATER_HEATER],
}


async def async_setup_entry(hass: HomeAssistant, entry: VGuardConfigEntry) -> bool:
    """Set up a device from a config entry."""
    if not await mqtt.async_wait_for_mqtt_client(hass):
        raise ConfigEntryNotReady("MQTT is not available")
    device = VGuardDevice(hass, entry)
    entry.runtime_data = device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS[device.category])
    await device.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: VGuardConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS[entry.runtime_data.category])


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Move 2.x entries (serial stored as `token`, unused broker host/port) to version 2."""
    if entry.version == 1:
        hass.config_entries.async_update_entry(
            entry,
            data={CONF_SERIAL: entry.data["token"], CONF_MODEL: protocol.DEFAULT_MODEL},
            version=2,
        )
        _LOGGER.debug("Migrated %s to version 2", entry.title)
    return entry.version == 2
