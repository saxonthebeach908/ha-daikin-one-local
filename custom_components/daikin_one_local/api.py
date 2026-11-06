"""Minimal async client for the Daikin One Local API v1.0."""
from __future__ import annotations

import asyncio
import json
from typing import Any

import aiohttp


class DaikinOneLocalError(Exception):
    """Raised on communication or API errors."""


class DaikinOneLocalClient:
    """Talks to http://<host>:<port>/ on the thermostat."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        self._session = session
        self._base = f"http://{host}:{port}"
        # The thermostat is a small embedded server: never hit it concurrently.
        self._lock = asyncio.Lock()

    async def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        async with self._lock:
            try:
                async with self._session.request(
                    method,
                    f"{self._base}{path}",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    resp.raise_for_status()
                    text = await resp.text()
                # POST /control answers 200 with an empty body on success.
                payload = json.loads(text) if text.strip() else {}
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as err:
                raise DaikinOneLocalError(f"{method} {path} failed: {err}") from err
        if isinstance(payload, dict) and payload.get("error") is True:
            raise DaikinOneLocalError(payload.get("reason", "unknown error"))
        return payload

    async def get_root(self) -> dict[str, Any]:
        return await self._request("GET", "/")

    async def get_info(self) -> dict[str, Any]:
        return await self._request("GET", "/query/info")

    async def control(self, **params: Any) -> None:
        """mode, fan, heatSetpoint, coolSetpoint (setpoints in deg C)."""
        data = {k: _fmt(v) for k, v in params.items() if v is not None}
        if data:
            await self._request("POST", "/control", data)

    async def settings(self, **params: Any) -> None:
        """tempUnits, setpointDelta."""
        data = {k: _fmt(v) for k, v in params.items() if v is not None}
        if data:
            await self._request("POST", "/settings", data)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)
