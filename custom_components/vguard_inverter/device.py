"""One V-Guard device: its MQTT subscriptions, latest readings and commands."""
from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

from . import protocol
from .const import (
    CONF_CATEGORY,
    CONF_IV,
    CONF_KEY,
    CONF_MODEL,
    CONF_SERIAL,
    DOMAIN,
    MANUFACTURER,
    MODELS,
    STALE_AFTER,
    START_INTERVAL,
)
from .crypto import VGuardCipher

_LOGGER = logging.getLogger(__name__)

type VGuardConfigEntry = ConfigEntry[VGuardDevice]
# Called with the VG codes whose values changed; an empty set means availability changed
type Listener = Callable[[set[str]], None]

CODE_MAC = "VG132"
# Inverters report their Wi-Fi firmware in VG012; water heaters their firmware in VG010 and
# hardware revision in VG012
FIRMWARE_CODES = {protocol.INVERTER: "VG012", protocol.WATER_HEATER: "VG010"}
CODE_HEATER_HARDWARE = "VG012"


class VGuardDevice:
    """Track one inverter or water heater."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        data = entry.data
        self.serial: str = data[CONF_SERIAL]
        self.model: str = data[CONF_MODEL]
        # Entries from 3.0 are all inverters
        self.category: str = data.get(CONF_CATEGORY, protocol.INVERTER)
        # Water heaters may encrypt their messages with a per-device key
        self.cipher = (VGuardCipher(data[CONF_KEY], data[CONF_IV])
                       if data.get(CONF_KEY) and self.category == protocol.WATER_HEATER else None)
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
            model=MODELS.get(self.category),
            model_id=self.model,
            serial_number=self.serial,
        )

    @property
    def is_inverter(self) -> bool:
        return self.category == protocol.INVERTER

    @property
    def available(self) -> bool:
        """Whether the device is online and its readings are current."""
        return self._online is not False and not self._stale

    def _topic(self, topic: Callable[[str, str, str], str]) -> str:
        return topic(self.category, self.model, self.serial)

    async def async_start(self) -> None:
        """Subscribe to the device; keep an inverter's telemetry flowing."""
        for topic, handler in (
            (self._topic(protocol.lwt_topic), self._async_lwt_received),
            (self._topic(protocol.telemetry_topic), self._async_telemetry_received),
        ):
            self.entry.async_on_unload(
                await mqtt.async_subscribe(self.hass, topic, handler, qos=1, encoding=None))
        if self.is_inverter:
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
        if online and self.is_inverter:
            # Back online after a restart: it waits for `start` before streaming again
            self.entry.async_create_background_task(
                self.hass, self.async_request_telemetry(), "vguard start")
        if self.available != was_available:
            self._notify(set())

    def _parse(self, payload: str | bytes) -> dict[str, str] | None:
        if (values := protocol.parse_telemetry(payload)) is None and self.cipher:
            if (text := self.cipher.decrypt(payload)) is not None:
                values = protocol.parse_telemetry(text)
        return values

    @callback
    def _async_telemetry_received(self, msg: mqtt.ReceiveMessage) -> None:
        if (values := self._parse(msg.payload)) is None:
            _LOGGER.debug("%s: ignored message %r", self.serial, msg.payload)
            return
        _LOGGER.debug("%s: %s", self.serial, values)
        changed = {code for code, value in values.items() if self.values.get(code) != value}
        self.values.update(values)
        self._last_seen = dt_util.utcnow()
        if self._stale or self._online is None:
            changed.update(self.values)
            self._stale = False
            self._online = True
        if not self._registry_synced:
            self._sync_registry()
        if changed:
            self._notify(changed)

    def _sync_registry(self) -> None:
        """Record the firmware version and MAC address once the device reports them."""
        self._registry_synced = True
        extra: dict[str, Any] = {}
        if firmware := self.values.get(FIRMWARE_CODES[self.category]):
            extra["sw_version"] = firmware
        if not self.is_inverter and (hardware := self.values.get(CODE_HEATER_HARDWARE)):
            extra["hw_version"] = hardware
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

    async def async_request_telemetry(self) -> None:
        """Ask an inverter to (keep) streaming telemetry."""
        await mqtt.async_publish(
            self.hass, self._topic(protocol.control_topic), protocol.COMMAND_START, qos=1)

    async def async_send(self, command: str, **expected: str) -> None:
        """Send an inverter a command and show the values it should lead to until
        telemetry confirms."""
        if not self.is_inverter:
            raise HomeAssistantError("V-Guard water heaters are read-only")
        await mqtt.async_publish(self.hass, self._topic(protocol.control_topic), command, qos=1)
        if changed := {code for code, value in expected.items() if self.values.get(code) != value}:
            self.values.update(expected)
            self._notify(changed)

    async def async_set(self, code: str, value: str) -> None:
        """Change a setting; the next telemetry confirms it."""
        await self.async_send(protocol.set_command(code, value), **{code: value})
