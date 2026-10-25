"""Config and options flow for Samsung TV Notify."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TvNotifyClient, TvNotifyConnectionError, TvNotifyError
from .const import (
    CONF_AUTO_START,
    CONF_DISPLAY_TIME,
    DEFAULT_AUTO_START,
    DEFAULT_DISPLAY_TIME,
    DEFAULT_PORT,
    DOMAIN,
)

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
    }
)


class TvNotifyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up a TV running the HA Notify app."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = TvNotifyClient(
                async_get_clientsession(self.hass), user_input[CONF_HOST], user_input[CONF_PORT]
            )
            try:
                info = await client.async_get_device_info()
                # Starting the service also proves the app is installed.
                await client.async_ensure_running()
            except TvNotifyConnectionError:
                errors["base"] = "cannot_connect"
            except TvNotifyError:
                errors["base"] = "app_not_installed"
            else:
                await self.async_set_unique_id(info["id"] or user_input[CONF_HOST])
                self._abort_if_unique_id_configured(updates={CONF_HOST: user_input[CONF_HOST]})
                return self.async_create_entry(
                    title=info["name"],
                    data={**user_input, "model": info["model"], "mac": info["mac"]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry) -> OptionsFlow:
        return TvNotifyOptionsFlow()


class TvNotifyOptionsFlow(OptionsFlow):
    """Auto-start and banner display time."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_AUTO_START, default=options.get(CONF_AUTO_START, DEFAULT_AUTO_START)
                ): bool,
                vol.Required(
                    CONF_DISPLAY_TIME,
                    default=options.get(CONF_DISPLAY_TIME, DEFAULT_DISPLAY_TIME),
                ): vol.All(int, vol.Range(min=3, max=60)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
