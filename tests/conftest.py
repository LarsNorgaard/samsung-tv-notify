"""Shared pytest setup."""

from unittest.mock import patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.samsung_tv_notify.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

HOST = "192.0.2.10"
SERVICE = f"http://{HOST}:8099"
TV_API = f"http://{HOST}:8001/api/v2"
APP_URL = f"{TV_API}/applications/HAnotifyPC.HANotify"
TV_ID = "00000000-0000-4000-8000-000000000001"

DEVICE_INFO = {
    "id": f"uuid:{TV_ID}",
    "name": "55&quot; TV",
    "device": {
        "id": f"uuid:{TV_ID}",
        "name": "55&quot; TV",
        "modelName": "QE55Q80CATXXC",
        "wifiMac": "00:11:22:33:44:55",
    },
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let the test hass load custom_components/."""
    yield


@pytest.fixture(autouse=True)
def fast_sleep():
    """Don't really wait while polling for the service to start."""
    with patch("custom_components.samsung_tv_notify.api.asyncio.sleep", return_value=None):
        yield


def make_entry(options=None):
    return MockConfigEntry(
        domain=DOMAIN,
        title='55" TV',
        data={
            CONF_HOST: HOST,
            CONF_PORT: 8099,
            "model": "QE55Q80CATXXC",
            "mac": "00:11:22:33:44:55",
        },
        unique_id=TV_ID,
        options=options or {},
    )
