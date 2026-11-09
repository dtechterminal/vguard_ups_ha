"""Sensors for V-Guard inverters and water heaters.

VG codes were matched against a live inverter's telemetry and the V-Guard app.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import protocol
from .device import VGuardConfigEntry
from .entity import VGuardEntity

POWER_SOURCES = {"0": "mains", "1": "battery"}
BATTERY_STATES = {"0": "normal", "1": "charging", "2": "low"}


def _scaled(scale: float) -> Callable[[str], float | None]:
    return lambda value: protocol.number(value, scale)


@dataclass(frozen=True, kw_only=True)
class VGuardSensorDescription(SensorEntityDescription):
    """A sensor read from one VG code."""

    code: str
    convert: Callable[[str], float | str | None] = protocol.number


def _enum(key: str, code: str, states: dict[str, str]) -> VGuardSensorDescription:
    return VGuardSensorDescription(
        key=key, translation_key=key, code=code, convert=states.get,
        device_class=SensorDeviceClass.ENUM, options=list(states.values()),
    )


INVERTER_SENSORS = (
    VGuardSensorDescription(
        key="mains_voltage", translation_key="mains_voltage", code="VG014",
        device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    VGuardSensorDescription(
        key="output_voltage", translation_key="output_voltage", code="VG015",
        device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    VGuardSensorDescription(
        key="output_frequency", translation_key="output_frequency", code="VG019",
        device_class=SensorDeviceClass.FREQUENCY, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
    ),
    VGuardSensorDescription(
        key="load", translation_key="load", code="VG017", icon="mdi:gauge",
        state_class=SensorStateClass.MEASUREMENT, native_unit_of_measurement=PERCENTAGE,
    ),
    VGuardSensorDescription(
        key="battery_voltage", translation_key="battery_voltage", code="VG016",
        device_class=SensorDeviceClass.VOLTAGE, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    VGuardSensorDescription(
        key="charging_current", translation_key="charging_current", code="VG018",
        device_class=SensorDeviceClass.CURRENT, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    VGuardSensorDescription(
        key="backup_time", translation_key="backup_time", code="VG020",
        device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    VGuardSensorDescription(
        key="backup_energy", translation_key="backup_energy", code="VG211",
        device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
    ),
    _enum("power_source", "VG022", POWER_SOURCES),
    _enum("battery_status", "VG023", BATTERY_STATES),
    VGuardSensorDescription(
        key="battery_health", translation_key="battery_health", code="VG024",
        icon="mdi:battery-heart-variant", state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
    ),
    VGuardSensorDescription(
        # Reported in tenths of an amp-hour
        key="battery_capacity", translation_key="battery_capacity", code="VG025",
        convert=_scaled(10), icon="mdi:battery-high", native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VGuardSensorDescription(
        # Reported in hundredths of a volt
        key="low_battery_alarm_voltage", translation_key="low_battery_alarm_voltage",
        code="VG071", convert=_scaled(100), device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)

WIFI_SENSORS = (
    VGuardSensorDescription(
        key="wifi_signal", translation_key="wifi_signal", code="VG011",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH, state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        entity_category=EntityCategory.DIAGNOSTIC, entity_registry_enabled_default=False,
    ),
    VGuardSensorDescription(
        key="wifi_network", translation_key="wifi_network", code="VG136", convert=str,
        icon="mdi:wifi", entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VGuardConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the device's sensors."""
    device = entry.runtime_data
    descriptions = (INVERTER_SENSORS if device.is_inverter else ()) + WIFI_SENSORS
    async_add_entities(
        VGuardSensor(device, description, description.code) for description in descriptions
    )


class VGuardSensor(VGuardEntity, SensorEntity):
    """A reading the device reports."""

    entity_description: VGuardSensorDescription

    @property
    def native_value(self) -> float | str | None:
        if (raw := self.raw) is None:
            return None
        return self.entity_description.convert(raw)
