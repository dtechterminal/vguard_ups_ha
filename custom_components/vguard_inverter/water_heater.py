"""Water heater entity for V-Guard smart water heaters.

The entity is read-only. Power and temperature commands come back once they are confirmed
on a real heater.
"""
from __future__ import annotations

from homeassistant.components.water_heater import STATE_ELECTRIC, WaterHeaterEntity
from homeassistant.const import STATE_OFF, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .device import VGuardConfigEntry
from .entity import VGuardEntity

ON = "1"
HEATER = EntityDescription(key="water_heater", name=None)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the water heater."""
    async_add_entities([VGuardWaterHeater(
        entry.runtime_data, HEATER, protocol.CODE_HEATER_POWER, protocol.CODE_HEATER_STATUS,
        protocol.CODE_HEATER_TARGET,
    )])


class VGuardWaterHeater(VGuardEntity, WaterHeaterEntity):
    """Power and temperatures of a V-Guard water heater."""

    _attr_min_temp = protocol.HEATER_MIN_TEMP
    _attr_max_temp = protocol.HEATER_MAX_TEMP
    # HA 2026.11 renamed the temperature members to native_*; the old names remain
    # for older HA and are what it reads there
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def current_operation(self) -> str | None:
        if (power := self.raw) is None:
            return None
        return STATE_ELECTRIC if power == ON else STATE_OFF

    @property
    def native_current_temperature(self) -> float | None:
        return protocol.heater_current_temperature(self.device.values)

    @property
    def native_target_temperature(self) -> float | None:
        return protocol.heater_target_temperature(self.device.values)

    current_temperature = native_current_temperature
    target_temperature = native_target_temperature
