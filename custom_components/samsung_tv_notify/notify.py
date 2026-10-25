"""Notify entity that shows a banner on the TV."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity, NotifyEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TvNotifyConfigEntry
from .api import TvNotifyError
from .const import (
    CONF_AUTO_START,
    CONF_DISPLAY_TIME,
    DEFAULT_AUTO_START,
    DEFAULT_DISPLAY_TIME,
    DOMAIN,
)
from .entity import TvNotifyEntity

DEFAULT_TITLE = "Home Assistant"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TvNotifyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([TvNotifyNotifyEntity(entry.runtime_data.coordinator)])


class TvNotifyNotifyEntity(TvNotifyEntity, NotifyEntity):
    """Send a text notification (title + message) to the TV."""

    _attr_supported_features = NotifyEntityFeature.TITLE
    _attr_name = None

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "notify")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        options = self.coordinator.config_entry.options
        client = self.coordinator.client
        try:
            if options.get(CONF_AUTO_START, DEFAULT_AUTO_START):
                await client.async_ensure_running()
            await client.async_send(
                title or DEFAULT_TITLE,
                message,
                options.get(CONF_DISPLAY_TIME, DEFAULT_DISPLAY_TIME),
            )
        except TvNotifyError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="send_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        finally:
            await self.coordinator.async_request_refresh()
