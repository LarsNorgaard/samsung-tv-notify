"""Samsung TV Notify: native notification banners on Samsung Tizen TVs."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TvNotifyClient
from .coordinator import TvNotifyCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.NOTIFY]


@dataclass
class TvNotifyData:
    """Runtime data for a config entry."""

    client: TvNotifyClient
    coordinator: TvNotifyCoordinator


type TvNotifyConfigEntry = ConfigEntry[TvNotifyData]


async def async_setup_entry(hass: HomeAssistant, entry: TvNotifyConfigEntry) -> bool:
    """Set up Samsung TV Notify from a config entry."""
    client = TvNotifyClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_PORT]
    )
    coordinator = TvNotifyCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = TvNotifyData(client, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: TvNotifyConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload(hass: HomeAssistant, entry: TvNotifyConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
