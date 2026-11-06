"""Daikin One Local API integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DaikinOneLocalClient, DaikinOneLocalError
from .const import CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL
from .coordinator import DaikinOneLocalCoordinator

PLATFORMS = [Platform.CLIMATE, Platform.SENSOR]

type DaikinConfigEntry = ConfigEntry[DaikinOneLocalCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: DaikinConfigEntry) -> bool:
    client = DaikinOneLocalClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    try:
        root = await client.get_root()
    except DaikinOneLocalError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = DaikinOneLocalCoordinator(
        hass, client, root, entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_reload))
    return True


async def _reload(hass: HomeAssistant, entry: DaikinConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: DaikinConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
