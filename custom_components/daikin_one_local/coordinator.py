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
            data = await self.client.get_info()
        except DaikinOneLocalError as err:
            raise UpdateFailed(str(err)) from err
        return _sanitize(data)


# Plausible ranges. Right after a reboot the thermostat reports 255 for
# sensors it has not read yet (seen 2026-11-08: spaceTemp 255, spaceHum 255).
_VALID_RANGES = {
    "spaceTemp": (-40.0, 60.0),  # deg C
    "spaceHum": (0.0, 100.0),  # %
}


def _sanitize(data: dict[str, Any]) -> dict[str, Any]:
    """Replace sentinel or out-of-range sensor values with None."""
    for key, (lo, hi) in _VALID_RANGES.items():
        value = data.get(key)
        if value is None:
            continue
        if not isinstance(value, (int, float)) or not lo <= value <= hi:
            _LOGGER.debug("Ignoring invalid %s=%r from thermostat", key, value)
            data[key] = None
    return data
