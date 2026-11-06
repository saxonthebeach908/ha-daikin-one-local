"""Polling coordinator for Daikin One Local."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DaikinOneLocalClient, DaikinOneLocalError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class DaikinOneLocalCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls /query/info."""

    def __init__(self, hass: HomeAssistant, client: DaikinOneLocalClient, root: dict[str, Any], scan_interval: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.root = root  # model, brand, firmware, api_ver, type

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.get_info()
        except DaikinOneLocalError as err:
            raise UpdateFailed(str(err)) from err
