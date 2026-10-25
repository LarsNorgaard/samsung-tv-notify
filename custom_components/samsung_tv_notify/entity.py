"""Base entity for Samsung TV Notify."""

from __future__ import annotations

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TvNotifyCoordinator


class TvNotifyEntity(CoordinatorEntity[TvNotifyCoordinator]):
    """Shared device info and naming."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TvNotifyCoordinator, key: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_translation_key = key
        mac = entry.data.get("mac")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            connections={(CONNECTION_NETWORK_MAC, mac.lower())} if mac else set(),
            name=entry.title,
            manufacturer="Samsung",
            model=entry.data.get("model"),
        )
