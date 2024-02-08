"""Select platform for Pentair IF3 Pool Pumps."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from pypentair import PentairIF3Pump

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PentairDataUpdateCoordinator
from .entity import PentairEntity


@dataclass(frozen=True, kw_only=True)
class PentairSelectEntityDescription(
    SelectEntityDescription,
):
    """Description of a Pentair select entity."""

    current_option_fn: Callable[[PentairIF3Pump], str]
    select_option_fn: Callable[
        [PentairDataUpdateCoordinator, str], Coroutine[Any, Any, bool]
    ]
    options_fn: Callable[[PentairIF3Pump], list[str]]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator: PentairDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = [
        PentairSelectEntity(
            coordinator=coordinator,
            config_entry=config_entry,
            description=PentairSelectEntityDescription(
                key="active_program_name",
                icon="mdi:pump",
                translation_key="active_program_name",
                options_fn=lambda device: ["Stopped"]
                + [program.name for program in device.enabledPrograms],
                select_option_fn=lambda coordinator,
                option,
                device: coordinator.change_active_pump_program(device, option),
                current_option_fn=lambda device: device.activeProgramName
                if device.activeProgramName is not None
                else "Stopped",
            ),
            device_id=device.deviceId,
        )
        for device in coordinator.get_devices()
        if device.deviceType in ["IF31"]
    ]

    if not entities:
        return

    async_add_entities(entities)


class PentairSelectEntity(PentairEntity, SelectEntity):
    """Pentair select entity."""

    entity_description: PentairSelectEntityDescription

    @property
    def options(self) -> list[str]:
        """Return a set of selectable options."""
        return self.entity_description.options_fn(self.get_device())

    @property
    def current_option(self) -> str:
        """Return the current selected option."""
        return str(self.entity_description.current_option_fn(self.get_device()))

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_option_fn(
            self.coordinator, option, self.get_device()
        )
        self.async_write_ha_state()
