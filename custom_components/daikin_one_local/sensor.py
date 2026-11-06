"""Sensors for Daikin One Local."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DaikinConfigEntry
from .const import STATE_NAMES
from .entity import DaikinOneLocalEntity


async def async_setup_entry(hass: HomeAssistant, entry: DaikinConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    c = entry.runtime_data
    ents = [
        TempSensor(c, entry.entry_id),
        EquipmentState(c, entry.entry_id),
    ]
    if c.data.get("spaceHum") is not None:
        ents.append(HumSensor(c, entry.entry_id))
    async_add_entities(ents)


class TempSensor(DaikinOneLocalEntity, SensorEntity):
    _attr_translation_key = "indoor_temperature"
    _attr_name = "Indoor temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_suggested_display_precision = 1

    def __init__(self, c, entry_id):
        super().__init__(c, entry_id, "space_temp")

    @property
    def native_value(self):
        return self.coordinator.data.get("spaceTemp")


class HumSensor(DaikinOneLocalEntity, SensorEntity):
    _attr_name = "Indoor humidity"
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(self, c, entry_id):
        super().__init__(c, entry_id, "space_hum")

    @property
    def native_value(self):
        return self.coordinator.data.get("spaceHum")


class EquipmentState(DaikinOneLocalEntity, SensorEntity):
    _attr_name = "Equipment state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(STATE_NAMES.values()) + ["unknown"]
    _attr_icon = "mdi:hvac"

    def __init__(self, c, entry_id):
        super().__init__(c, entry_id, "equipment_state")

    @property
    def native_value(self):
        return STATE_NAMES.get(self.coordinator.data.get("state"), "unknown")
