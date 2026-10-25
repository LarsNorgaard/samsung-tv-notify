"""Tests for the notify, binary sensor and button entities."""

import aiohttp
import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from custom_components.samsung_tv_notify.const import CONF_AUTO_START, CONF_DISPLAY_TIME
from tests.conftest import APP_URL, SERVICE, TV_ID, make_entry

NOTIFY = "notify.55_tv"
SENSOR = "binary_sensor.55_tv_notification_service"
BUTTON = "button.55_tv_start_notification_service"


async def _setup(hass, options=None):
    entry = make_entry(options)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_entities_created(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    await _setup(hass)
    registry = er.async_get(hass)
    assert registry.async_get(NOTIFY).unique_id == f"{TV_ID}_notify"
    assert hass.states.get(SENSOR).state == "on"
    assert hass.states.get(BUTTON) is not None


async def test_sensor_off_when_service_down(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    await _setup(hass)
    assert hass.states.get(SENSOR).state == "off"


async def test_send_message(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    aioclient_mock.post(f"{SERVICE}/notify", json={"ok": True, "error": None})
    await _setup(hass, {CONF_DISPLAY_TIME: 15})
    await hass.services.async_call(
        "notify",
        "send_message",
        {"entity_id": NOTIFY, "title": "Door", "message": "Front door opened"},
        blocking=True,
    )
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert posts[-1][2] == {"title": "Door", "message": "Front door opened", "timeout": 15}


async def test_send_message_default_title(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    aioclient_mock.post(f"{SERVICE}/notify", json={"ok": True, "error": None})
    await _setup(hass)
    await hass.services.async_call(
        "notify", "send_message", {"entity_id": NOTIFY, "message": "Hi"}, blocking=True
    )
    posts = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert posts[-1][2]["title"] == "Home Assistant"
    assert posts[-1][2]["timeout"] == 10


async def test_send_message_auto_starts(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    aioclient_mock.post(APP_URL, text="true")
    aioclient_mock.post(f"{SERVICE}/notify", json={"ok": True, "error": None})
    await _setup(hass)
    # The service never comes up in this test, so auto-start must give up with an error.
    with pytest.raises(HomeAssistantError, match="did not start"):
        await hass.services.async_call(
            "notify", "send_message", {"entity_id": NOTIFY, "message": "Hi"}, blocking=True
        )
    assert any(str(c[1]) == APP_URL for c in aioclient_mock.mock_calls)


async def test_send_message_without_auto_start(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    aioclient_mock.post(f"{SERVICE}/notify", exc=aiohttp.ClientConnectionError())
    await _setup(hass, {CONF_AUTO_START: False})
    with pytest.raises(HomeAssistantError, match="Could not show"):
        await hass.services.async_call(
            "notify", "send_message", {"entity_id": NOTIFY, "message": "Hi"}, blocking=True
        )
    assert not any(str(c[1]) == APP_URL for c in aioclient_mock.mock_calls)


async def test_button_launches_app(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    aioclient_mock.post(APP_URL, status=404)
    await _setup(hass)
    with pytest.raises(HomeAssistantError, match="not installed"):
        await hass.services.async_call("button", "press", {"entity_id": BUTTON}, blocking=True)


async def test_unload(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    entry = await _setup(hass)
    assert await hass.config_entries.async_unload(entry.entry_id)
