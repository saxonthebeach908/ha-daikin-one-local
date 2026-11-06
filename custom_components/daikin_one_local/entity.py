"""Base entity for Daikin One Local."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DaikinOneLocalCoordinator


class DaikinOneLocalEntity(CoordinatorEntity[DaikinOneLocalCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: DaikinOneLocalCoordinator, entry_id: str, key: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        root = coordinator.root
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=coordinator.data.get("name") or "Daikin One",
            manufacturer=(root.get("brand") or "Daikin").title(),
            model=root.get("model"),
            sw_version=str(root.get("firmware")) if root.get("firmware") is not None else None,
        )
