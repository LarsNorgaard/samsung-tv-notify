"""Client for the HA Notify app on a Samsung Tizen TV."""

from __future__ import annotations

import asyncio
import html
import logging
from typing import Any

import aiohttp

from .const import APP_ID, START_TIMEOUT, TV_API_PORT

_LOGGER = logging.getLogger(__name__)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=5)


class TvNotifyError(Exception):
    """Base error for the TV notification client."""


class TvNotifyConnectionError(TvNotifyError):
    """The TV or its notification service could not be reached."""


class TvNotifyClient:
    """Talks to the HA Notify service (:8099) and Samsung's REST API (:8001)."""

    def __init__(self, session: aiohttp.ClientSession, host: str, port: int) -> None:
        self._session = session
        self.host = host
        self.port = port
        self._start_lock = asyncio.Lock()

    @property
    def _service_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def _tv_url(self) -> str:
        return f"http://{self.host}:{TV_API_PORT}/api/v2"

    async def async_get_device_info(self) -> dict[str, Any]:
        """Return the TV's device info (id, name, model) from the REST API."""
        try:
            async with self._session.get(f"{self._tv_url}/", timeout=REQUEST_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise TvNotifyConnectionError(f"TV not reachable: {err}") from err
        device = data.get("device") or {}
        tv_id = device.get("id") or data.get("id") or ""
        return {
            "id": tv_id.removeprefix("uuid:"),
            "name": html.unescape(device.get("name") or data.get("name") or "Samsung TV"),
            "model": device.get("modelName"),
            "mac": device.get("wifiMac"),
        }

    async def async_is_service_running(self) -> bool:
        """Return True if the notification service answers on its port."""
        try:
            async with self._session.get(
                f"{self._service_url}/health", timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status != 200:
                    return False
                data = await resp.json(content_type=None)
        except aiohttp.ClientError, TimeoutError, ValueError:
            return False
        return bool(data.get("ok"))

    async def async_launch_app(self) -> None:
        """Launch the HA Notify app, which starts the service and closes itself."""
        try:
            async with self._session.post(
                f"{self._tv_url}/applications/{APP_ID}", timeout=REQUEST_TIMEOUT
            ) as resp:
                if resp.status == 404:
                    raise TvNotifyError(f"The {APP_ID} app is not installed on the TV")
                resp.raise_for_status()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise TvNotifyConnectionError(f"Could not launch the TV app: {err}") from err

    async def async_ensure_running(self, start_timeout: float = START_TIMEOUT) -> None:
        """Start the service if needed and wait until it answers."""
        if await self.async_is_service_running():
            return
        async with self._start_lock:
            if await self.async_is_service_running():
                return
            _LOGGER.debug("Notification service on %s is down, launching %s", self.host, APP_ID)
            await self.async_launch_app()
            loop = asyncio.get_running_loop()
            deadline = loop.time() + start_timeout
            while loop.time() < deadline:
                await asyncio.sleep(1)
                if await self.async_is_service_running():
                    return
        raise TvNotifyConnectionError("The notification service did not start in time")

    async def async_send(self, title: str, message: str, display_time: int) -> None:
        """Show a notification banner on the TV."""
        payload = {"title": title, "message": message, "timeout": display_time}
        try:
            async with self._session.post(
                f"{self._service_url}/notify", json=payload, timeout=REQUEST_TIMEOUT
            ) as resp:
                data = await resp.json(content_type=None)
                if resp.status != 200 or not data.get("ok"):
                    raise TvNotifyError(f"The TV rejected the notification: {data.get('error')}")
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            raise TvNotifyConnectionError(f"Could not send the notification: {err}") from err
