"""Support for Pentair sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from time import time
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfMass,
    UnitOfPower,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.dt import UTC

from .const import DOMAIN
from .entity import PentairDataUpdateCoordinator, PentairEntity


@dataclass
class RequiredKeysMixin:
    """Required keys mixin."""

    value_fn: Callable[[dict], Any]


@dataclass
class PentairSensorEntityDescription(SensorEntityDescription, RequiredKeysMixin):
    """Pentair sensor entity description."""


def convert_timestamp(_ts: float) -> datetime:
    """Convert a timestamp to a datetime."""
    return datetime.fromtimestamp(_ts / (1000 if _ts > time() else 1), UTC)


SENSOR_MAP: dict[str | None, tuple[PentairSensorEntityDescription, ...]] = {
    None: (
        PentairSensorEntityDescription(
            key="last_report",
            device_class=SensorDeviceClass.TIMESTAMP,
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key="last_report",
            value_fn=lambda device: device.lastReport,
        ),
    ),
    "PPA0": (
        PentairSensorEntityDescription(
            key="battery_level",
            device_class=SensorDeviceClass.BATTERY,
            entity_category=EntityCategory.DIAGNOSTIC,
            native_unit_of_measurement=PERCENTAGE,
            suggested_display_precision=1,
            translation_key="battery_level",
            value_fn=lambda device: device.batteryLevel,
        ),
    ),
    "SSS1": (
        PentairSensorEntityDescription(
            key="average_salt_usage_per_day",
            device_class=SensorDeviceClass.WEIGHT,
            native_unit_of_measurement=UnitOfMass.POUNDS,
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="average_salt_usage_per_day",
            value_fn=lambda device: device.averageSaltUsagePerDay,
        ),
        PentairSensorEntityDescription(
            key="battery_level",
            entity_category=EntityCategory.DIAGNOSTIC,
            icon="mdi:battery",
            translation_key="battery_level",
            value_fn=lambda device: device.batteryLevel,
        ),
        PentairSensorEntityDescription(
            key="salt_level",
            translation_key="salt_level",
            value_fn=lambda device: device.saltLevel,
        ),
    ),
    "IF31": (
        PentairSensorEntityDescription(
            key="active_program_number",
            entity_category=EntityCategory.DIAGNOSTIC,
            translation_key="active_program_number",
            value_fn=lambda device: device.activeProgramNumber
            if device.activeProgramNumber is not None
            else 0,
        ),
        PentairSensorEntityDescription(
            key="current_power_consumption",
            device_class=SensorDeviceClass.POWER,
            native_unit_of_measurement=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="current_power_consumption",
            value_fn=lambda device: device.currentPowerConsumption,
        ),
        PentairSensorEntityDescription(
            key="current_motor_speed",
            device_class=SensorDeviceClass.SPEED,
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="current_motor_speed",
            value_fn=lambda device: device.currentMotorSpeed,
        ),
        PentairSensorEntityDescription(
            key="current_estimated_flow",
            device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
            native_unit_of_measurement=UnitOfVolumeFlowRate.GALLONS_PER_MINUTE,
            state_class=SensorStateClass.MEASUREMENT,
            translation_key="current_estimated_flow",
            icon="mdi:water-sync",
            value_fn=lambda device: device.currentEstimatedFlow,
        ),
    ),
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair sensors using config entry."""
    coordinator: PentairDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PentairSensorEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=description,
            device_id=device.deviceId,
        )
        for device in coordinator.get_devices()
        for device_type, descriptions in SENSOR_MAP.items()
        for description in descriptions
        if device_type is None or device.deviceType == device_type
    ]

    if not entities:
        return

    async_add_entities(entities)


class PentairSensorEntity(PentairEntity, SensorEntity):
    """Pentair sensor entity."""

    entity_description: PentairSensorEntityDescription

    @property
    def native_value(self) -> str | int | datetime | None:
        """Return the value reported by the sensor."""
        return self.entity_description.value_fn(self.get_device())
