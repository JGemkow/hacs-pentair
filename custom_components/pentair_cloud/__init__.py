"""The Pentair integration."""
from __future__ import annotations

import logging

from pypentair import Pentair, PentairAuthenticationError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import CONF_ID_TOKEN, CONF_REFRESH_TOKEN, DOMAIN
from .entity import PentairDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SELECT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pentair from a config entry."""
    entry.add_update_listener(update_listener)

    client = Pentair(
        username=entry.data.get(CONF_USERNAME),
        access_token=entry.data.get(CONF_ACCESS_TOKEN),
        id_token=entry.data.get(CONF_ID_TOKEN),
        refresh_token=entry.data.get(CONF_REFRESH_TOKEN),
    )

    try:
        await hass.async_add_executor_job(client.get_auth)
    except PentairAuthenticationError as err:
        raise ConfigEntryAuthFailed(err) from err
    except Exception as ex:
        raise ConfigEntryNotReady(ex) from ex

    coordinator = PentairDataUpdateCoordinator(hass, client=client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    hass.data[DOMAIN].pop(entry.entry_id)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)
