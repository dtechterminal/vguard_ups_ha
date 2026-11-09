"""V-Guard MQTT topics, commands and telemetry parsing.

This module has no Home Assistant imports so it can be tested on its own.

A V-Guard device's Wi-Fi module connects to the V-Guard broker (redirected to a local one).
It announces itself on a retained last-will topic and sends telemetry, a JSON object of
VG-coded string values. Topics are `device/<category>/<model>/<serial>`, with `dups` for
inverters and `smartewh` for water heaters.

Inverters stream telemetry every couple of seconds for about four minutes after `start`.
Water heaters are read-only: their readings follow the earlier V-Guard Smart draft, with
temperatures in the VG007 status field, and nothing is sent to them.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any

INVERTER = "dups"
WATER_HEATER = "smartewh"
CATEGORIES = (INVERTER, WATER_HEATER)
DEFAULT_MODELS = {INVERTER: "CE01", WATER_HEATER: "3013"}
DEFAULT_MODEL = DEFAULT_MODELS[INVERTER]

COMMAND_START = "start"
TELEMETRY_KEY = "VG029"
LWT_ONLINE = "online"
LWT_OFFLINE = "offline"

DISCOVERY_TOPICS = tuple(f"device/{category}/#" for category in CATEGORIES)

# Water heater codes
CODE_HEATER_STATUS = "VG007"  # 12 digits: current temperature, target, flags
CODE_HEATER_TARGET = "VG041"  # Target temperature in tenths of a degree
CODE_HEATER_POWER = "VG094"  # 1 on, 0 off
CODE_HEATER_HEATING = "VG190"  # 1 while the element is heating
HEATER_MIN_TEMP = 30  # The V-Guard app's range
HEATER_MAX_TEMP = 75

_SEGMENT = re.compile(r"^[A-Za-z0-9]+$")


def telemetry_topic(category: str, model: str, serial: str) -> str:
    """Return the topic a device sends telemetry on."""
    return f"device/{category}/{model}/{serial}"


def lwt_topic(category: str, model: str, serial: str) -> str:
    """Return the retained topic a device reports online/offline on."""
    return f"device/{category}/{model}/lwt/{serial}"


def control_topic(category: str, model: str, serial: str) -> str:
    """Return the topic commands are sent to."""
    return f"apps/{category}/{model}/{serial}"


@dataclass(frozen=True)
class TopicInfo:
    """What a device topic says about its sender."""

    category: str
    model: str
    serial: str
    lwt: bool


def parse_topic(topic: str) -> TopicInfo | None:
    """Return the category, model and serial of a telemetry or last-will topic."""
    parts = topic.split("/")
    if len(parts) < 4 or parts[0] != "device" or parts[1] not in CATEGORIES:
        return None
    if len(parts) == 4:
        model, serial, lwt = parts[2], parts[3], False
    elif len(parts) == 5 and parts[3] == "lwt":
        model, serial, lwt = parts[2], parts[4], True
    else:
        return None
    if not (_SEGMENT.match(model) and _SEGMENT.match(serial)) or len(serial) < 6:
        return None
    return TopicInfo(parts[1], model, serial, lwt)


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
    """Format a reported Wi-Fi MAC (`a1b2c3d4e5f6`) with colons."""
    if value is None or not re.fullmatch(r"[0-9A-Fa-f]{12}", value):
        return None
    return ":".join(value[i:i + 2] for i in range(0, 12, 2)).lower()


def _in_range(value: float | None) -> float | None:
    if value is None or not HEATER_MIN_TEMP <= value <= HEATER_MAX_TEMP:
        return None
    return value


def heater_current_temperature(values: dict[str, str]) -> float | None:
    """Return the water temperature, the first two digits of VG007 (`48...` is 48 °C)."""
    status = values.get(CODE_HEATER_STATUS, "")
    return number(status[:2]) if len(status) >= 2 and status[:2].isdigit() else None


def heater_target_temperature(values: dict[str, str]) -> float | None:
    """Return the target temperature.

    VG041 reports it in tenths of a degree. Without VG041, digits 3 and 4 of VG007 hold it
    with the digits reversed (`4805...` is 50 °C).
    """
    if (target := _in_range(number(values.get(CODE_HEATER_TARGET), 10))) is not None:
        return target
    status = values.get(CODE_HEATER_STATUS, "")
    if len(status) >= 4 and status[2:4].isdigit():
        return _in_range(number(status[3] + status[2]))
    return None
