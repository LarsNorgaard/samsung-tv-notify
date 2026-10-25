"""Button that starts the notification service on the TV."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TvNotifyConfigEntry
from .api import TvNotifyError
from .const import DOMAIN
from .entity import TvNotifyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TvNotifyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([TvNotifyStartButton(entry.runtime_data.coordinator)])


class TvNotifyStartButton(TvNotifyEntity, ButtonEntity):
    """Launch the HA Notify app so its service starts (briefly takes over the screen)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "start_service")

    async def async_press(self) -> None:
        try:
            await self.coordinator.client.async_ensure_running()
        except TvNotifyError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="start_failed",
                translation_placeholders={"error": str(err)},
            ) from err
        finally:
            await self.coordinator.async_request_refresh()
