"""Config flow for Daikin One Local."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from .api import DaikinOneLocalClient, DaikinOneLocalError
from .const import CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN


class DaikinOneLocalConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host: str | None = None
        self._port: int = DEFAULT_PORT
        self._name: str | None = None

    async def _probe(self, host: str, port: int) -> dict[str, Any]:
        client = DaikinOneLocalClient(async_get_clientsession(self.hass), host, port)
        root = await client.get_root()
        info = await client.get_info()
        return {"root": root, "info": info}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host, port = user_input[CONF_HOST], user_input.get(CONF_PORT, DEFAULT_PORT)
            try:
                probe = await self._probe(host, port)
            except DaikinOneLocalError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"{host}")
                self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
                title = probe["info"].get("name") or probe["root"].get("model") or "Daikin One"
                return self.async_create_entry(title=title, data={CONF_HOST: host, CONF_PORT: port})
        schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_zeroconf(self, discovery_info: ZeroconfServiceInfo) -> ConfigFlowResult:
        props = discovery_info.properties
        mac = (props.get("mac") or "").replace(":", "").lower()
        self._host = str(discovery_info.ip_address)
        self._port = discovery_info.port or DEFAULT_PORT
        if mac:
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured(updates={CONF_HOST: self._host, CONF_PORT: self._port})
        try:
            probe = await self._probe(self._host, self._port)
        except DaikinOneLocalError:
            return self.async_abort(reason="cannot_connect")
        self._name = probe["info"].get("name") or props.get("model") or "Daikin One"
        self.context["title_placeholders"] = {"name": self._name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title=self._name, data={CONF_HOST: self._host, CONF_PORT: self._port})
        return self.async_show_form(step_id="confirm", description_placeholders={"name": self._name})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return DaikinOneLocalOptionsFlow()


class DaikinOneLocalOptionsFlow(OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        schema = vol.Schema({
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(int, vol.Range(min=5, max=300)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
