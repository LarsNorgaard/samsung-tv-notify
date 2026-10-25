"""Tests for the TV notification client."""

import aiohttp
import pytest

from custom_components.samsung_tv_notify.api import (
    TvNotifyClient,
    TvNotifyConnectionError,
    TvNotifyError,
)
from tests.conftest import APP_URL, DEVICE_INFO, HOST, SERVICE, TV_API, TV_ID


@pytest.fixture
async def client(hass, aioclient_mock):
    from homeassistant.helpers.aiohttp_client import async_get_clientsession

    return TvNotifyClient(async_get_clientsession(hass), HOST, 8099)


async def test_device_info_is_unescaped_and_stripped(client, aioclient_mock):
    aioclient_mock.get(f"{TV_API}/", json=DEVICE_INFO)
    info = await client.async_get_device_info()
    assert info == {
        "id": TV_ID,
        "name": '55" TV',
        "model": "QE55Q80CATXXC",
        "mac": "00:11:22:33:44:55",
    }


async def test_device_info_unreachable(client, aioclient_mock):
    aioclient_mock.get(f"{TV_API}/", exc=aiohttp.ClientConnectionError())
    with pytest.raises(TvNotifyConnectionError):
        await client.async_get_device_info()


async def test_service_running(client, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    assert await client.async_is_service_running() is True


async def test_service_down(client, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", exc=aiohttp.ClientConnectionError())
    assert await client.async_is_service_running() is False


async def test_send_posts_payload(client, aioclient_mock):
    aioclient_mock.post(f"{SERVICE}/notify", json={"ok": True, "error": None})
    await client.async_send("Door", "Front door opened", 12)
    assert aioclient_mock.mock_calls[-1][2] == {
        "title": "Door",
        "message": "Front door opened",
        "timeout": 12,
    }


async def test_send_rejected(client, aioclient_mock):
    aioclient_mock.post(f"{SERVICE}/notify", status=500, json={"ok": False, "error": "boom"})
    with pytest.raises(TvNotifyError, match="boom"):
        await client.async_send("t", "m", 10)


async def test_ensure_running_noop_when_up(client, aioclient_mock):
    aioclient_mock.get(f"{SERVICE}/health", json={"ok": True})
    await client.async_ensure_running()
    assert not any(call[0] == "POST" for call in aioclient_mock.mock_calls)


async def test_ensure_running_launches_app(client, aioclient_mock):
    # Down twice (initial check + check under the lock), then up after launch.
    responses = iter([False, False, True])
    aioclient_mock.post(APP_URL, text="true")

    async def fake_running():
        return next(responses)

    client.async_is_service_running = fake_running
    await client.async_ensure_running()
    assert [c[0] for c in aioclient_mock.mock_calls] == ["POST"]


async def test_ensure_running_times_out(client, aioclient_mock):
    aioclient_mock.post(APP_URL, text="true")

    async def never():
        return False

    client.async_is_service_running = never
    with pytest.raises(TvNotifyConnectionError, match="did not start"):
        await client.async_ensure_running(start_timeout=0.01)


async def test_launch_app_not_installed(client, aioclient_mock):
    aioclient_mock.post(APP_URL, status=404)
    with pytest.raises(TvNotifyError, match="not installed"):
        await client.async_launch_app()
