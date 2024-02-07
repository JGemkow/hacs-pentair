"""Pentair coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, List

from deepdiff import DeepDiff
from pypentair import Pentair, PentairDevice

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = 30


class PentairDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, client: Pentair) -> None:
        """Initialize."""
        self.api = client
        self.devices: List(PentairDevice) = []

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL),
        )

    def get_device(self, device_id: str) -> PentairDevice | None:
        """Get device by id."""
        return next(
            (device for device in self.devices if device.deviceId == device_id),
            None,
        )

    def get_devices(self, device_type: str | None = None) -> List(PentairDevice):
        """Get devices by device type, if provided."""
        return [
            device
            for device in self.devices
            if device_type is None or device.deviceType == device_type
        ]

    async def _async_update_data(self):
        """Update data via library, refresh token if necessary."""
        try:
            if devices := await self.hass.async_add_executor_job(self.api.get_devices):
                enrichedDevices = []

                for device in devices:
                    enrichedDevices.append(
                        await self.hass.async_add_executor_job(
                            self.api.get_device, device.deviceId
                        )
                    )

                diff = DeepDiff(
                    self.devices,
                    enrichedDevices,
                    ignore_order=True,
                    report_repetition=True,
                    verbose_level=2,
                )
                _LOGGER.debug("Devices updated: %s", diff if diff else "no changes")
                self.devices = enrichedDevices
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error(
                "Unknown exception while updating Pentair data: %s", err, exc_info=1
            )
            raise UpdateFailed(err) from err
        return self.devices
