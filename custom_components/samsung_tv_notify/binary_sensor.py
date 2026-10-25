"""Binary sensor showing whether the TV's notification service is running."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import TvNotifyConfigEntry
from .entity import TvNotifyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TvNotifyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([TvNotifyServiceSensor(entry.runtime_data.coordinator)])


class TvNotifyServiceSensor(TvNotifyEntity, BinarySensorEntity):
    """On while the HA Notify service on the TV answers."""

    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "service_running")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data)
