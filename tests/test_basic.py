from urllib.parse import parse_qs
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.daikin_one_local.const import DOMAIN

BASE = "http://10.0.0.50:8081"
ROOT = {"api_ver": 1, "type": "residential", "model": "DTST-ONE-ADA-A", "brand": "Daikin", "firmware": "3.9.1"}
INFO = {"name": "West", "mode": 2, "availableModes": [0, 1, 2, 3, 4], "state": 1, "fan": 0, "fanState": 1,
        "tempUnits": 0, "spaceTemp": 25.3, "heatSetpoint": 20.0, "coolSetpoint": 25.0,
        "coolSetpointMax": 37.2, "coolSetpointMin": 15.6, "heatSetpointMax": 32.2, "heatSetpointMin": 4.4,
        "setpointDelta": 1.7, "spaceHum": 52}

def mock_dev(aioclient_mock, info=None):
    aioclient_mock.get(f"{BASE}/", json=ROOT)
    aioclient_mock.get(f"{BASE}/query/info", json=info or INFO)
    aioclient_mock.post(f"{BASE}/control", text="")

async def setup(hass, aioclient_mock, info=None):
    from homeassistant.util.unit_system import US_CUSTOMARY_SYSTEM
    hass.config.units = US_CUSTOMARY_SYSTEM
    mock_dev(aioclient_mock, info)
    e = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "10.0.0.50", CONF_PORT: 8081})
    e.add_to_hass(hass)
    assert await hass.config_entries.async_setup(e.entry_id)
    await hass.async_block_till_done()
    return e

async def test_user_flow(hass, aioclient_mock):
    mock_dev(aioclient_mock)
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {CONF_HOST: "10.0.0.50", CONF_PORT: 8081})
    assert r["type"] == "create_entry" and r["title"] == "West"

async def test_climate_state(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    ids = hass.states.async_entity_ids("climate"); assert len(ids) == 1
    s = hass.states.get(ids[0])
    print(s.state, s.attributes)
    assert s.state == "cool"
    assert s.attributes["temperature"] == 77
    assert s.attributes["hvac_action"] == "cooling"
    assert s.attributes["current_humidity"] == 52
    assert "heat_cool" in s.attributes["hvac_modes"]
    hum = [i for i in hass.states.async_entity_ids("sensor") if "humidity" in i]
    assert hass.states.get(hum[0]).state == "52"

async def test_set_temp_and_mode(hass, aioclient_mock):
    await setup(hass, aioclient_mock)
    eid = hass.states.async_entity_ids("climate")[0]
    await hass.services.async_call("climate", "set_temperature", {"entity_id": eid, "temperature": 78}, blocking=True)
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    body = posts[-1][2]
    print(body)
    assert body["coolSetpoint"] == "25.6"
    await hass.services.async_call("climate", "set_fan_mode", {"entity_id": eid, "fan_mode": "circulate"}, blocking=True)
    assert [c for c in aioclient_mock.mock_calls if c[0] == "POST"][-1][2]["fan"] == "2"
    await hass.services.async_call("climate", "set_hvac_mode", {"entity_id": eid, "hvac_mode": "heat_cool"}, blocking=True)
    assert [c for c in aioclient_mock.mock_calls if c[0] == "POST"][-1][2]["mode"] == "3"
