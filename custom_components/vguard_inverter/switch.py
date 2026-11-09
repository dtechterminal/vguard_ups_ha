"""Switches for V-Guard inverter settings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .device import VGuardConfigEntry
from .entity import VGuardEntity


@dataclass(frozen=True, kw_only=True)
class VGuardSwitchDescription(SwitchEntityDescription):
    """A setting the inverter reports and accepts as one VG code."""

    code: str
    on: str = "1"
    off: str = "0"
    entity_category: EntityCategory | None = EntityCategory.CONFIG


SWITCHES = (
    VGuardSwitchDescription(
        key="turbo_charging", translation_key="turbo_charging", code="VG099",
        icon="mdi:battery-charging-high",
    ),
    VGuardSwitchDescription(
        # The buzzer is the odd one out: 0 is on, 2 is off
        key="changeover_buzzer", translation_key="changeover_buzzer", code="VG034",
        on="0", off="2", icon="mdi:volume-high",
    ),
    VGuardSwitchDescription(
        key="appliance_mode", translation_key="appliance_mode", code="VG036",
        icon="mdi:power-plug-outline",
    ),
    VGuardSwitchDescription(
        key="daytime_load_usage", translation_key="daytime_load_usage", code="VG185",
        icon="mdi:weather-sunny",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter's switches."""
    async_add_entities(
        VGuardSwitch(entry.runtime_data, description, description.code)
        for description in SWITCHES
    )


class VGuardSwitch(VGuardEntity, SwitchEntity):
    """An on/off inverter setting."""

    entity_description: VGuardSwitchDescription

    @property
    def is_on(self) -> bool | None:
        raw = self.raw
        if raw == self.entity_description.on:
            return True
        if raw == self.entity_description.off:
            return False
        return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.async_set(self.code, self.entity_description.on)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.async_set(self.code, self.entity_description.off)
