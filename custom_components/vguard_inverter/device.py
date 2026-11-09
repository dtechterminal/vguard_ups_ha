"""One V-Guard inverter: its MQTT subscriptions, latest readings and commands."""
from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import protocol
from .const import (
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    STALE_AFTER,
    START_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

type VGuardConfigEntry = ConfigEntry[VGuardInverter]
# Called with the VG codes whose values changed; an empty set means availability changed
type Listener = Callable[[set[str]], None]

CODE_FIRMWARE = "VG012"
CODE_MAC = "VG132"


class VGuardInverter:
    """Track one inverter."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.serial: str = entry.data[CONF_SERIAL]
        self.model: str = entry.data[CONF_MODEL]
        self.values: dict[str, str] = {}
        self._online: bool | None = None  # From the last-will topic; None until seen
        self._last_seen = None
        self._stale = True
        self._listeners: list[Listener] = []
        self._registry_synced = False
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, self.serial)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
            model_id=self.model,
            serial_number=self.serial,
        )

    @property
    def available(self) -> bool:
        """Whether the inverter is online and its readings are current."""
        return self._online is not False and not self._stale

    async def async_start(self) -> None:
        """Subscribe to the inverter and keep its telemetry flowing."""
        for topic, handler in (
            (protocol.lwt_topic(self.model, self.serial), self._async_lwt_received),
            (protocol.telemetry_topic(self.model, self.serial), self._async_telemetry_received),
        ):
            self.entry.async_on_unload(
                await mqtt.async_subscribe(self.hass, topic, handler, qos=1))
        self.entry.async_on_unload(
            async_track_time_interval(self.hass, self._async_tick, START_INTERVAL))
        await self.async_request_telemetry()

    @callback
    def async_add_listener(self, listener: Listener) -> CALLBACK_TYPE:
        """Call `listener` when readings or availability change."""
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)

    def _notify(self, codes: set[str]) -> None:
        for listener in list(self._listeners):
            listener(codes)

    @callback
    def _async_lwt_received(self, msg: mqtt.ReceiveMessage) -> None:
        if (online := protocol.parse_lwt(msg.payload)) is None or online == self._online:
            return
        was_available = self.available
        self._online = online
        _LOGGER.debug("%s is %s", self.serial, "online" if online else "offline")
        if online:
            # Back online after a restart: it waits for `start` before streaming again
            self.entry.async_create_background_task(
                self.hass, self.async_request_telemetry(), "vguard_inverter start")
        if self.available != was_available:
            self._notify(set())

    @callback
    def _async_telemetry_received(self, msg: mqtt.ReceiveMessage) -> None:
        if (values := protocol.parse_telemetry(msg.payload)) is None:
            _LOGGER.debug("%s: ignored message %r", self.serial, msg.payload)
            return
        changed = {code for code, value in values.items() if self.values.get(code) != value}
        self.values.update(values)
        self._last_seen = dt_util.utcnow()
        if self._stale:
            self._stale = False
            changed.update(self.values)
            if self._online is None:
                self._online = True
        if not self._registry_synced:
            self._sync_registry()
        if changed:
            self._notify(changed)

    def _sync_registry(self) -> None:
        """Record the firmware version and MAC address once the inverter reports them."""
        self._registry_synced = True
        extra: dict[str, Any] = {}
        if firmware := self.values.get(CODE_FIRMWARE):
            extra["sw_version"] = firmware
        if mac := protocol.mac_address(self.values.get(CODE_MAC)):
            extra["connections"] = {(CONNECTION_NETWORK_MAC, mac)}
        if extra:
            dr.async_get(self.hass).async_get_or_create(
                config_entry_id=self.entry.entry_id,
                identifiers={(DOMAIN, self.serial)},
                **extra,
            )

    async def _async_tick(self, _now: Any) -> None:
        if (not self._stale and self._last_seen is not None
                and dt_util.utcnow() - self._last_seen > STALE_AFTER):
            self._stale = True
            _LOGGER.debug("%s: no telemetry since %s", self.serial, self._last_seen)
            self._notify(set())
        await self.async_request_telemetry()

    async def _async_publish(self, payload: str) -> None:
        await mqtt.async_publish(
            self.hass, protocol.control_topic(self.model, self.serial), payload, qos=1)

    async def async_request_telemetry(self) -> None:
        """Ask the inverter to (keep) streaming telemetry."""
        await self._async_publish(protocol.COMMAND_START)

    async def async_set(self, code: str, value: str) -> None:
        """Change a setting; the next telemetry confirms it."""
        await self._async_publish(protocol.set_command(code, value))
        if self.values.get(code) != value:
            self.values[code] = value
            self._notify({code})
