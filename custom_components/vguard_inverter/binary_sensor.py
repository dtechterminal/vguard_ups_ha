"""Heating indicator for V-Guard water heaters."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .device import VGuardConfigEntry
from .entity import VGuardEntity

HEATING = BinarySensorEntityDescription(
    key="heating", translation_key="heating", device_class=BinarySensorDeviceClass.HEAT,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the heating indicator."""
    async_add_entities(
        [VGuardHeating(entry.runtime_data, HEATING, protocol.CODE_HEATER_HEATING)])


class VGuardHeating(VGuardEntity, BinarySensorEntity):
    """Whether the heating element is on."""

    @property
    def is_on(self) -> bool | None:
        if (heating := self.raw) is None:
            return None
        return heating == "1"
