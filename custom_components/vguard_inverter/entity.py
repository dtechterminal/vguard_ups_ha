"""Base entity for V-Guard devices."""
from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.entity import Entity, EntityDescription

from .device import VGuardDevice


class VGuardEntity(Entity):
    """An entity that follows the VG codes its device reports."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self, device: VGuardDevice, description: EntityDescription, *codes: str
    ) -> None:
        self.device = device
        self.entity_description = description
        self.code = codes[0]
        self.codes = frozenset(codes)
        self._attr_unique_id = f"{device.serial}_{description.key}"
        self._attr_device_info = device.device_info

    @property
    def available(self) -> bool:
        return self.device.available and not self.codes.isdisjoint(self.device.values)

    @property
    def raw(self) -> str | None:
        """The latest value the device reported for this entity's first code."""
        return self.device.values.get(self.code)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.device.async_add_listener(self._async_device_updated))

    @callback
    def _async_device_updated(self, codes: set[str]) -> None:
        if not codes or not self.codes.isdisjoint(codes):
            self.async_write_ha_state()
