"""Water heater entity for V-Guard smart water heaters."""
from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    STATE_ELECTRIC,
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.const import ATTR_TEMPERATURE, STATE_OFF, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .device import VGuardConfigEntry
from .entity import VGuardEntity

ON, OFF = "1", "0"
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
    """Power and temperature of a V-Guard water heater."""

    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE
        | WaterHeaterEntityFeature.ON_OFF
        | WaterHeaterEntityFeature.OPERATION_MODE
    )
    _attr_operation_list = [STATE_OFF, STATE_ELECTRIC]
    _attr_min_temp = protocol.HEATER_MIN_TEMP
    _attr_max_temp = protocol.HEATER_MAX_TEMP
    _attr_target_temperature_step = 1
    # HA 2026.11 renamed the temperature members to native_*; the old names remain
    # for older HA and are what it reads there
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    @property
    def is_on(self) -> bool | None:
        if (power := self.raw) is None:
            return None
        return power == ON

    @property
    def current_operation(self) -> str | None:
        if (on := self.is_on) is None:
            return None
        return STATE_ELECTRIC if on else STATE_OFF

    @property
    def native_current_temperature(self) -> float | None:
        return protocol.heater_current_temperature(self.device.values)

    @property
    def native_target_temperature(self) -> float | None:
        return protocol.heater_target_temperature(self.device.values)

    current_temperature = native_current_temperature
    target_temperature = native_target_temperature

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.async_set(protocol.CODE_HEATER_POWER, ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.async_set(protocol.CODE_HEATER_POWER, OFF)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        await self.device.async_set(
            protocol.CODE_HEATER_POWER, OFF if operation_mode == STATE_OFF else ON)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.device.async_send(
            protocol.heater_temperature_command(temperature),
            **protocol.heater_expected_target(self.device.values, temperature))
