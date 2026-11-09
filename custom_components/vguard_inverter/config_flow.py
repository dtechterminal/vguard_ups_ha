"""Config flow for V-Guard Inverter."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback

from . import protocol
from .const import CONF_MODEL, CONF_SERIAL, DISCOVERY_TIMEOUT, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _title(serial: str) -> str:
    return f"V-Guard Inverter {serial[-4:]}"


class VGuardInverterConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a V-Guard inverter."""

    VERSION = 2

    def __init__(self) -> None:
        self._discovered: dict[str, str] = {}  # serial -> model
        self._discovery_task: asyncio.Task[None] | None = None
        self._manual_errors: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose discovery or manual setup."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_ready")
        return self.async_show_menu(step_id="user", menu_options=["mqtt_discovery", "manual"])

    async def async_step_mqtt_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Listen for inverters on the MQTT broker."""
        if self._discovery_task is None:
            self._discovery_task = self.hass.async_create_task(self._async_discover())
        if not self._discovery_task.done():
            return self.async_show_progress(
                step_id="mqtt_discovery",
                progress_action="discovering",
                progress_task=self._discovery_task,
            )
        self._discovery_task = None
        if not self._discovered:
            self._manual_errors = {"base": "no_devices_found"}
            return self.async_show_progress_done(next_step_id="manual")
        return self.async_show_progress_done(next_step_id="pick_device")

    async def _async_discover(self) -> None:
        configured = self._async_current_ids(include_ignore=False)
        self._discovered = {}

        @callback
        def message(msg: mqtt.ReceiveMessage) -> None:
            if (info := protocol.parse_topic(msg.topic)) and info.serial not in configured:
                self._discovered[info.serial] = info.model

        unsubscribe = await mqtt.async_subscribe(self.hass, protocol.DISCOVERY_TOPIC, message)
        try:
            await asyncio.sleep(DISCOVERY_TIMEOUT)
        finally:
            unsubscribe()
        _LOGGER.debug("Discovery found %d new inverter(s)", len(self._discovered))

    async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose one of the discovered inverters."""
        # Reached from the progress step, HA may pass that step's input on
        if user_input and (serial := user_input.get(CONF_SERIAL)) in self._discovered:
            return await self._async_create(serial, self._discovered[serial])
        options = {serial: f"{_title(serial)} ({serial})" for serial in self._discovered}
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_SERIAL): vol.In(options)}),
            description_placeholders={"device_count": str(len(options))},
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Enter the inverter's serial number by hand."""
        errors: dict[str, str] = {}
        # Reached from the progress step, HA may pass that step's input on
        if user_input and CONF_SERIAL in user_input:
            serial = user_input[CONF_SERIAL].strip()
            model = user_input.get(CONF_MODEL, protocol.DEFAULT_MODEL).strip()
            if protocol.parse_topic(protocol.telemetry_topic(model, serial)) is None:
                errors["base"] = "invalid_serial"
            else:
                return await self._async_create(serial, model)
        else:
            errors, self._manual_errors = self._manual_errors, {}
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_SERIAL): str,
                vol.Required(CONF_MODEL, default=protocol.DEFAULT_MODEL): str,
            }),
            errors=errors,
        )

    async def _async_create(self, serial: str, model: str) -> ConfigFlowResult:
        await self.async_set_unique_id(serial)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=_title(serial), data={CONF_SERIAL: serial, CONF_MODEL: model})
