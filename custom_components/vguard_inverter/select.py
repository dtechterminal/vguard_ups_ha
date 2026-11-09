"""Inverter mode select for V-Guard inverters."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .device import VGuardConfigEntry
from .entity import VGuardEntity

CODE_MODE = "VG021"
MODES = {"0": "normal", "1": "ups", "2": "equipment"}
MODE_VALUES = {option: value for value, option in MODES.items()}

MODE = SelectEntityDescription(
    key="inverter_mode", translation_key="inverter_mode", icon="mdi:home-lightning-bolt-outline",
    options=list(MODES.values()), entity_category=EntityCategory.CONFIG,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the inverter mode select."""
    async_add_entities([VGuardModeSelect(entry.runtime_data, MODE, CODE_MODE)])


class VGuardModeSelect(VGuardEntity, SelectEntity):
    """Normal, UPS or equipment mode."""

    @property
    def current_option(self) -> str | None:
        return MODES.get(self.raw)

    async def async_select_option(self, option: str) -> None:
        await self.device.async_set(self.code, MODE_VALUES[option])
