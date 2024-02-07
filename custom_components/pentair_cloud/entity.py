"""Pentair entities."""
from __future__ import annotations

from typing import Any

from pypentair import PentairDevice

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PentairDataUpdateCoordinator


class PentairEntity(CoordinatorEntity[PentairDataUpdateCoordinator]):
    """Base class for Pentair entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PentairDataUpdateCoordinator,
        config_entry: ConfigEntry,
        description: EntityDescription,
        device_id: str,
    ) -> None:
        """Construct a PentairEntity."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self.entity_description = description
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}-{description.key}"

        device = self.get_device()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            manufacturer=device.maker,
            model=device.model,
            name=device.nickName,
            sw_version=device.softwareVersion,
        )

    def get_device(self) -> PentairDevice | None:
        """Get the device from the coordinator."""
        return self.coordinator.get_device(self._device_id)
