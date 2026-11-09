"""Number settings for V-Guard inverters."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .device import VGuardConfigEntry
from .entity import VGuardEntity


@dataclass(frozen=True, kw_only=True)
class VGuardNumberDescription(NumberEntityDescription):
    """A numeric setting the inverter reports and accepts as one VG code."""

    code: str
    mode: NumberMode = NumberMode.BOX
    entity_category: EntityCategory | None = EntityCategory.CONFIG


NUMBERS = (
    VGuardNumberDescription(
        # 0 when the inverter chooses the level itself
        key="performance_level", translation_key="performance_level", code="VG035",
        native_min_value=0, native_max_value=5, native_step=1, icon="mdi:speedometer",
    ),
    VGuardNumberDescription(
        key="load_alarm_threshold", translation_key="load_alarm_threshold", code="VG050",
        native_min_value=50, native_max_value=100, native_step=1,
        native_unit_of_measurement=PERCENTAGE, icon="mdi:alert-circle-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter's numeric settings."""
    async_add_entities(
        VGuardNumber(entry.runtime_data, description, description.code)
        for description in NUMBERS
    )


class VGuardNumber(VGuardEntity, NumberEntity):
    """A numeric inverter setting."""

    @property
    def native_value(self) -> float | None:
        return protocol.number(self.raw)

    async def async_set_native_value(self, value: float) -> None:
        await self.device.async_set(self.code, str(int(value)))
