"""Polls whether the TV's notification service is running."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import TvNotifyClient
from .const import DOMAIN, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class TvNotifyCoordinator(DataUpdateCoordinator[bool]):
    """Data is True when the notification service answers.

    A stopped service (TV off or in standby) is a normal state, not an update
    failure, so entities stay available and simply report it.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: TvNotifyClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client

    async def _async_update_data(self) -> bool:
        return await self.client.async_is_service_running()
