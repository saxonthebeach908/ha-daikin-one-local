"""Climate entity for Daikin One Local.

The Local API speaks Celsius for every temperature. The thermostat itself
works in whole degrees F when set to Fahrenheit, so when tempUnits == 0 we
present the entity in Fahrenheit and round setpoints to whole degrees before
converting, to avoid 77 F turning into 76.9 F on the thermostat.
"""
from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    FAN_AUTO,
    FAN_ON,
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaikinConfigEntry
from .api import DaikinOneLocalError
from .const import (
    FAN_AUTO as API_FAN_AUTO,
    FAN_ON as API_FAN_ON,
    FAN_SCHEDULED,
    MODE_AUTO,
    MODE_COOL,
    MODE_DRY,
    MODE_EMERGENCY_HEAT,
    MODE_FAN,
    MODE_HEAT,
    MODE_OFF,
)
from .entity import DaikinOneLocalEntity

FAN_CIRCULATE = "circulate"
PRESET_EMERGENCY = "emergency_heat"
PRESET_NONE = "none"

API_TO_HVAC = {
    MODE_OFF: HVACMode.OFF,
    MODE_HEAT: HVACMode.HEAT,
    MODE_COOL: HVACMode.COOL,
    MODE_AUTO: HVACMode.HEAT_COOL,
    MODE_EMERGENCY_HEAT: HVACMode.HEAT,
    MODE_FAN: HVACMode.FAN_ONLY,
    MODE_DRY: HVACMode.DRY,
}
HVAC_TO_API = {
    HVACMode.OFF: MODE_OFF,
    HVACMode.HEAT: MODE_HEAT,
    HVACMode.COOL: MODE_COOL,
    HVACMode.HEAT_COOL: MODE_AUTO,
    HVACMode.FAN_ONLY: MODE_FAN,
    HVACMode.DRY: MODE_DRY,
}
API_FAN = {API_FAN_AUTO: FAN_AUTO, API_FAN_ON: FAN_ON, FAN_SCHEDULED: FAN_CIRCULATE}
FAN_API = {v: k for k, v in API_FAN.items()}

STATE_TO_ACTION = {
    1: HVACAction.COOLING,
    2: HVACAction.DRYING,
    3: HVACAction.HEATING,
    4: HVACAction.FAN,
    5: HVACAction.IDLE,
    6: HVACAction.IDLE,
    7: HVACAction.IDLE,
    8: HVACAction.HEATING,
}


def _c_to_f(c: float | None) -> float | None:
    return None if c is None else c * 9 / 5 + 32


def _f_to_c(f: float) -> float:
    return (f - 32) * 5 / 9


async def async_setup_entry(hass: HomeAssistant, entry: DaikinConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([DaikinOneLocalClimate(entry.runtime_data, entry.entry_id)])


class DaikinOneLocalClimate(DaikinOneLocalEntity, ClimateEntity):
    _attr_name = None
    _attr_fan_modes = [FAN_AUTO, FAN_ON, FAN_CIRCULATE]
    _enable_turn_on_off_backwards_compatibility = False

    def __init__(self, coordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "climate")
        self._last_on_mode = HVACMode.COOL

    # ---- units -------------------------------------------------------
    @property
    def _fahrenheit(self) -> bool:
        return self.coordinator.data.get("tempUnits", 0) == 0

    @property
    def temperature_unit(self) -> str:
        return UnitOfTemperature.FAHRENHEIT if self._fahrenheit else UnitOfTemperature.CELSIUS

    @property
    def target_temperature_step(self) -> float:
        return 1.0 if self._fahrenheit else 0.5

    def _out(self, c: float | None) -> float | None:
        """API (C) -> entity unit."""
        if c is None:
            return None
        return round(_c_to_f(c)) if self._fahrenheit else round(c * 2) / 2

    def _in(self, v: float) -> float:
        """Entity unit -> API (C)."""
        return round(_f_to_c(round(v)), 1) if self._fahrenheit else round(v * 2) / 2

    # ---- state -------------------------------------------------------
    @property
    def _d(self) -> dict[str, Any]:
        return self.coordinator.data

    @property
    def hvac_modes(self) -> list[HVACMode]:
        modes = []
        for m in self._d.get("availableModes", [MODE_OFF, MODE_HEAT, MODE_COOL, MODE_AUTO]):
            hm = API_TO_HVAC.get(m)
            if hm and hm not in modes:
                modes.append(hm)
        if HVACMode.OFF not in modes:
            modes.insert(0, HVACMode.OFF)
        return modes

    @property
    def hvac_mode(self) -> HVACMode | None:
        return API_TO_HVAC.get(self._d.get("mode"))

    @property
    def preset_modes(self) -> list[str] | None:
        if MODE_EMERGENCY_HEAT in self._d.get("availableModes", []):
            return [PRESET_NONE, PRESET_EMERGENCY]
        return None

    @property
    def preset_mode(self) -> str | None:
        if self.preset_modes is None:
            return None
        return PRESET_EMERGENCY if self._d.get("mode") == MODE_EMERGENCY_HEAT else PRESET_NONE

    @property
    def supported_features(self) -> ClimateEntityFeature:
        f = ClimateEntityFeature.FAN_MODE | ClimateEntityFeature.TURN_ON | ClimateEntityFeature.TURN_OFF
        if self.hvac_mode == HVACMode.HEAT_COOL:
            f |= ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        elif self.hvac_mode in (HVACMode.HEAT, HVACMode.COOL):
            f |= ClimateEntityFeature.TARGET_TEMPERATURE
        if self.preset_modes:
            f |= ClimateEntityFeature.PRESET_MODE
        return f

    @property
    def hvac_action(self) -> HVACAction | None:
        if self._d.get("mode") == MODE_OFF:
            return HVACAction.OFF
        return STATE_TO_ACTION.get(self._d.get("state"))

    @property
    def current_temperature(self) -> float | None:
        c = self._d.get("spaceTemp")
        if c is None:
            return None
        return round(_c_to_f(c), 1) if self._fahrenheit else c

    @property
    def current_humidity(self) -> float | None:
        return self._d.get("spaceHum")

    @property
    def target_temperature(self) -> float | None:
        mode = self._d.get("mode")
        if mode == MODE_COOL:
            return self._out(self._d.get("coolSetpoint"))
        if mode in (MODE_HEAT, MODE_EMERGENCY_HEAT):
            return self._out(self._d.get("heatSetpoint"))
        return None

    @property
    def target_temperature_high(self) -> float | None:
        return self._out(self._d.get("coolSetpoint")) if self._d.get("mode") == MODE_AUTO else None

    @property
    def target_temperature_low(self) -> float | None:
        return self._out(self._d.get("heatSetpoint")) if self._d.get("mode") == MODE_AUTO else None

    @property
    def min_temp(self) -> float:
        lo = min(x for x in (self._d.get("heatSetpointMin"), self._d.get("coolSetpointMin")) if x is not None) if any(
            self._d.get(k) is not None for k in ("heatSetpointMin", "coolSetpointMin")) else 10.0
        return self._out(lo)

    @property
    def max_temp(self) -> float:
        hi = max(x for x in (self._d.get("heatSetpointMax"), self._d.get("coolSetpointMax")) if x is not None) if any(
            self._d.get(k) is not None for k in ("heatSetpointMax", "coolSetpointMax")) else 32.0
        return self._out(hi)

    @property
    def fan_mode(self) -> str | None:
        return API_FAN.get(self._d.get("fan"))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "equipment_state": self._d.get("state"),
            # Reads 0 while actively cooling on firmware 4.1.6, so this is not
            # "blower running"; exposed raw until its meaning is confirmed.
            "fan_state": self._d.get("fanState"),
            "setpoint_delta_c": self._d.get("setpointDelta"),
        }

    # ---- commands ----------------------------------------------------
    async def _send(self, **params: Any) -> None:
        try:
            await self.coordinator.client.control(**params)
        except DaikinOneLocalError as err:
            raise HomeAssistantError(str(err)) from err
        # Optimistic local update, then confirm from the thermostat.
        self.coordinator.data.update({k: v for k, v in params.items() if v is not None})
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode != HVACMode.OFF:
            self._last_on_mode = hvac_mode
        await self._send(mode=HVAC_TO_API[hvac_mode])

    async def async_turn_on(self) -> None:
        await self.async_set_hvac_mode(self._last_on_mode)

    async def async_turn_off(self) -> None:
        await self.async_set_hvac_mode(HVACMode.OFF)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        await self._send(mode=MODE_EMERGENCY_HEAT if preset_mode == PRESET_EMERGENCY else MODE_HEAT)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        await self._send(fan=FAN_API[fan_mode])

    async def async_set_temperature(self, **kwargs: Any) -> None:
        params: dict[str, Any] = {}
        if (hm := kwargs.get(ATTR_HVAC_MODE)) is not None:
            params["mode"] = HVAC_TO_API[hm]
        mode = params.get("mode", self._d.get("mode"))
        if (t := kwargs.get(ATTR_TEMPERATURE)) is not None:
            if mode in (MODE_HEAT, MODE_EMERGENCY_HEAT):
                params["heatSetpoint"] = self._in(t)
            else:
                params["coolSetpoint"] = self._in(t)
        if (lo := kwargs.get(ATTR_TARGET_TEMP_LOW)) is not None:
            params["heatSetpoint"] = self._in(lo)
        if (hi := kwargs.get(ATTR_TARGET_TEMP_HIGH)) is not None:
            params["coolSetpoint"] = self._in(hi)
        await self._send(**params)

    @callback
    def _handle_coordinator_update(self) -> None:
        if self.hvac_mode not in (None, HVACMode.OFF):
            self._last_on_mode = self.hvac_mode
        super()._handle_coordinator_update()

