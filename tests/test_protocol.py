"""Tests for topics, commands and telemetry parsing.

The telemetry shape was captured from a real inverter; the serial number is synthetic.
"""
import json

import pytest

from vguard import protocol

SERIAL = "2300000000001234"

# One telemetry message as the inverter sends it, trimmed to the codes the integration reads
TELEMETRY = json.dumps({"VG029": {
    "VG003": "1234", "VG011": "-59", "VG012": "1.6", "VG014": "253.40", "VG015": "247.80",
    "VG016": "13.13", "VG017": "0", "VG018": "0.20", "VG019": "50.50", "VG020": "1808",
    "VG021": "1", "VG022": "0", "VG023": "0", "VG024": "100", "VG025": "2500", "VG034": "2",
    "VG035": "0", "VG036": "0", "VG050": "63", "VG071": "1100", "VG099": "0",
    "VG109": "Mon Nov  9 23:48:04", "VG132": "a1b2c3d4e5f6", "VG136": "Home Wi-Fi",
    "VG185": "0", "VG195": ",NA", "VG211": "6634", "VG304": "UTC-05:30",
}})


def test_topics():
    assert protocol.telemetry_topic("CE01", SERIAL) == f"device/dups/CE01/{SERIAL}"
    assert protocol.lwt_topic("CE01", SERIAL) == f"device/dups/CE01/lwt/{SERIAL}"
    assert protocol.control_topic("CE01", SERIAL) == f"apps/dups/CE01/{SERIAL}"


@pytest.mark.parametrize(("topic", "lwt"), [
    (f"device/dups/CE01/{SERIAL}", False),
    (f"device/dups/CE01/lwt/{SERIAL}", True),
])
def test_parse_topic(topic, lwt):
    assert protocol.parse_topic(topic) == protocol.TopicInfo("CE01", SERIAL, lwt)


@pytest.mark.parametrize("topic", [
    f"apps/dups/CE01/{SERIAL}",  # Our own commands
    f"device/smartewh/3013/{SERIAL}",  # A water heater
    f"device/dups/CE01/x/{SERIAL}",
    "device/dups/CE01/123",  # Too short for a serial
    "device/dups/CE01/lwt",
    "device/dups/CE01/12345$",
])
def test_parse_topic_rejects_others(topic):
    assert protocol.parse_topic(topic) is None


def test_discovery_topic_covers_both():
    assert protocol.DISCOVERY_TOPIC == "device/dups/#"


def test_parse_telemetry():
    values = protocol.parse_telemetry(TELEMETRY.encode())
    assert values["VG014"] == "253.40"
    assert values["VG136"] == "Home Wi-Fi"
    assert all(isinstance(value, str) for value in values.values())


def test_parse_telemetry_stringifies_and_drops_nulls():
    values = protocol.parse_telemetry('{"VG029": {"VG014": 230.5, "VG015": null}}')
    assert values == {"VG014": "230.5"}


@pytest.mark.parametrize("payload", [
    "start",
    '{"VG029":{"VG011":"-59","VG012":"1.6",',  # Cut off mid-message
    '{"other": {}}',
    '{"VG029": "x"}',
    "[]",
])
def test_parse_telemetry_rejects(payload):
    assert protocol.parse_telemetry(payload) is None


@pytest.mark.parametrize(("payload", "online"), [
    ("online", True), (b"offline", False), (" Online\n", True), ("", None), ("{}", None),
])
def test_parse_lwt(payload, online):
    assert protocol.parse_lwt(payload) is online


def test_set_command():
    assert protocol.set_command("VG099", "1") == "VG099:1"
    assert protocol.COMMAND_START == "start"


@pytest.mark.parametrize(("value", "scale", "expected"), [
    ("253.40", 1, 253.4),
    ("2500", 10, 250.0),  # Battery capacity in tenths of Ah
    ("1100", 100, 11.0),  # Low battery alarm in hundredths of a volt
    ("-59", 1, -59.0),
    ("NA", 1, None),
    ("nan", 1, None),
    (None, 1, None),
])
def test_number(value, scale, expected):
    assert protocol.number(value, scale) == expected


@pytest.mark.parametrize(("value", "expected"), [
    ("a1b2c3d4e5f6", "a1:b2:c3:d4:e5:f6"),
    ("A1B2C3D4E5F6", "a1:b2:c3:d4:e5:f6"),
    ("a1b2c3d4e5", None),
    (None, None),
])
def test_mac_address(value, expected):
    assert protocol.mac_address(value) == expected
