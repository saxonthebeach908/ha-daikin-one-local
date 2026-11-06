"""Fixtures captured from the West One+ (firmware 4.1.6) on 2026-11-05."""
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.daikin_one_local.const import DOMAIN, DEFAULT_PORT

HOST = "192.168.1.60"
BASE = f"http://{HOST}"
ROOT = {"api_ver": 1, "type": "residential", "model": "ONETOUCH", "brand": "DK", "firmware": "4.1.6"}
INFO = {"name": "Main Room", "mode": 3, "availableModes": [0, 1, 2, 3], "state": 1, "fan": 0, "fanState": 0,
        "tempUnits": 0, "spaceTemp": 23.2, "heatSetpoint": 20, "coolSetpoint": 22.8, "coolSetpointMax": 32.2,
        "coolSetpointMin": 12, "heatSetpointMax": 30.2, "heatSetpointMin": 10, "setpointDelta": 2, "spaceHum": 48}


async def _setup(hass, aioclient_mock):
    hass.config.units = US_CUSTOMARY_SYSTEM
    aioclient_mock.get(f"{BASE}/", json=ROOT)
    aioclient_mock.get(f"{BASE}/query/info", json=INFO)
    aioclient_mock.post(f"{BASE}/control", text="")  # real device: 200, empty body
    e = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: HOST, CONF_PORT: DEFAULT_PORT})
    e.add_to_hass(hass)
    assert await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    return hass.states.async_entity_ids("climate")[0]


async def test_real_auto_state(hass, aioclient_mock):
    eid = await _setup(hass, aioclient_mock)
    s = hass.states.get(eid)
    assert DEFAULT_PORT == 80
    assert s.state == "heat_cool"
    assert s.attributes["target_temp_low"] == 68
    assert s.attributes["target_temp_high"] == 73
    assert s.attributes["current_temperature"] == 74
    assert s.attributes["current_humidity"] == 48
    assert s.attributes["hvac_action"] == "cooling"
    assert set(s.attributes["hvac_modes"]) == {"off", "heat", "cool", "heat_cool"}
    assert "preset_modes" not in s.attributes  # no emergency heat on this unit


async def test_real_range_write_empty_body(hass, aioclient_mock):
    eid = await _setup(hass, aioclient_mock)
    await hass.services.async_call("climate", "set_temperature",
        {"entity_id": eid, "target_temp_low": 68, "target_temp_high": 75}, blocking=True)
    body = [c for c in aioclient_mock.mock_calls if c[0] == "POST"][-1][2]
    assert body == {"heatSetpoint": "20.0", "coolSetpoint": "23.9"}
