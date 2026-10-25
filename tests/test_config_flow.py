"""Tests for the config and options flow."""

import aiohttp
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResultType

from custom_components.samsung_tv_notify.const import (
    CONF_AUTO_START,
    CONF_DISPLAY_TIME,
    DOMAIN,
)
from tests.conftest import APP_URL, DEVICE_INFO, HOST, SERVICE, TV_API, TV_ID, make_entry


async def _start(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow_creates_entry(hass, aioclient_mock):
    aioclient_mock.get(f"{TV_API}/", json=DEVICE_INFO)
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: 8099}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == '55" TV'
    assert result["result"].unique_id == TV_ID
    assert result["data"] == {
        CONF_HOST: HOST,
        CONF_PORT: 8099,
        "model": "QE55Q80CATXXC",
        "mac": "00:11:22:33:44:55",
    }


async def test_user_flow_cannot_connect(hass, aioclient_mock):
    aioclient_mock.get(f"{TV_API}/", exc=aiohttp.ClientConnectionError())
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: 8099}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_app_missing(hass, aioclient_mock):
    aioclient_mock.get(f"{TV_API}/", json=DEVICE_INFO)
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    aioclient_mock.post(APP_URL, status=404)
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: 8099}
    )
    assert result["errors"] == {"base": "app_not_installed"}


async def test_user_flow_already_configured(hass, aioclient_mock):
    make_entry().add_to_hass(hass)
    aioclient_mock.get(f"{TV_API}/", json=DEVICE_INFO)
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: HOST, CONF_PORT: 8099}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_AUTO_START: False, CONF_DISPLAY_TIME: 20}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_AUTO_START: False, CONF_DISPLAY_TIME: 20}
