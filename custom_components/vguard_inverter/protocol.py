"""V-Guard inverter MQTT topics, commands and telemetry parsing.

This module has no Home Assistant imports so it can be tested on its own.

The inverter's Wi-Fi module connects to the V-Guard broker (redirected to a local one). It
announces itself on a retained last-will topic and streams telemetry, a JSON object of
VG-coded string values, every couple of seconds after it receives `start`.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any

CATEGORY = "dups"  # V-Guard's product category for inverters
DEFAULT_MODEL = "CE01"
COMMAND_START = "start"
TELEMETRY_KEY = "VG029"
LWT_ONLINE = "online"
LWT_OFFLINE = "offline"

DISCOVERY_TOPIC = f"device/{CATEGORY}/#"

_SEGMENT = re.compile(r"^[A-Za-z0-9]+$")


def telemetry_topic(model: str, serial: str) -> str:
    """Return the topic an inverter streams telemetry on."""
    return f"device/{CATEGORY}/{model}/{serial}"


def lwt_topic(model: str, serial: str) -> str:
    """Return the retained topic an inverter reports online/offline on."""
    return f"device/{CATEGORY}/{model}/lwt/{serial}"


def control_topic(model: str, serial: str) -> str:
    """Return the topic commands are sent to."""
    return f"apps/{CATEGORY}/{model}/{serial}"


@dataclass(frozen=True)
class TopicInfo:
    """What a device topic says about its sender."""

    model: str
    serial: str
    lwt: bool


def parse_topic(topic: str) -> TopicInfo | None:
    """Return the model and serial of a telemetry or last-will topic."""
    parts = topic.split("/")
    if len(parts) == 4 and parts[:2] == ["device", CATEGORY]:
        model, serial, lwt = parts[2], parts[3], False
    elif len(parts) == 5 and parts[:2] == ["device", CATEGORY] and parts[3] == "lwt":
        model, serial, lwt = parts[2], parts[4], True
    else:
        return None
    if not (_SEGMENT.match(model) and _SEGMENT.match(serial)) or len(serial) < 6:
        return None
    return TopicInfo(model, serial, lwt)


def _text(payload: str | bytes) -> str:
    if isinstance(payload, bytes):
        return payload.decode("utf-8", "replace")
    return payload


def parse_telemetry(payload: str | bytes) -> dict[str, str] | None:
    """Return the VG-coded values of a telemetry message, all as strings."""
    try:
        data = json.loads(_text(payload))
    except ValueError:
        return None
    if not isinstance(data, dict) or not isinstance(values := data.get(TELEMETRY_KEY), dict):
        return None
    return {str(code): str(value) for code, value in values.items() if value is not None}


def parse_lwt(payload: str | bytes) -> bool | None:
    """Return True for online, False for offline, None for anything else."""
    state = _text(payload).strip().lower()
    if state == LWT_ONLINE:
        return True
    if state == LWT_OFFLINE:
        return False
    return None


def set_command(code: str, value: Any) -> str:
    """Return the command that sets one VG code."""
    return f"{code}:{value}"


def number(value: str | None, scale: float = 1) -> float | None:
    """Return a reported value as a number, or None when it isn't one."""
    if value is None:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return round(number / scale, 3) if math.isfinite(number) else None


def mac_address(value: str | None) -> str | None:
    """Format the reported Wi-Fi MAC (`a1b2c3d4e5f6`) with colons."""
    if value is None or not re.fullmatch(r"[0-9A-Fa-f]{12}", value):
        return None
    return ":".join(value[i:i + 2] for i in range(0, 12, 2)).lower()
