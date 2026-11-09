"""Config flow for V-Guard Smart."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import mqtt
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from . import protocol
from .const import (
    CONF_CATEGORY,
    CONF_IV,
    CONF_KEY,
    CONF_MODEL,
    CONF_SERIAL,
    DISCOVERY_TIMEOUT,
    DOMAIN,
)
from .crypto import KEY_LENGTH

_LOGGER = logging.getLogger(__name__)

NAMES = {protocol.INVERTER: "V-Guard Inverter", protocol.WATER_HEATER: "V-Guard Water Heater"}


def _title(category: str, serial: str) -> str:
    return f"{NAMES[category]} {serial[-4:]}"


KEY_SCHEMA = vol.Schema({vol.Optional(CONF_KEY): str, vol.Optional(CONF_IV): str})


def _key_errors(user_input: dict[str, Any]) -> dict[str, str]:
    """Check that the water heater key and IV are both given or both left out."""
    key, iv = user_input.get(CONF_KEY, ""), user_input.get(CONF_IV, "")
    if not key and not iv:
        return {}
    if len(key.encode()) != KEY_LENGTH or len(iv.encode()) != KEY_LENGTH:
        return {"base": "invalid_key"}
    return {}


class VGuardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a V-Guard inverter or water heater."""

    VERSION = 2

    def __init__(self) -> None:
        self._discovered: dict[str, protocol.TopicInfo] = {}
        self._discovery_task: asyncio.Task[None] | None = None
        self._manual_errors: dict[str, str] = {}
        self._pending: dict[str, str] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Choose discovery or manual setup."""
        if not await mqtt.async_wait_for_mqtt_client(self.hass):
            return self.async_abort(reason="mqtt_not_ready")
        return self.async_show_menu(step_id="user", menu_options=["mqtt_discovery", "manual"])

    async def async_step_mqtt_discovery(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Listen for devices on the MQTT broker."""
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
                self._discovered[info.serial] = info

        unsubscribes = [
            await mqtt.async_subscribe(self.hass, topic, message)
            for topic in protocol.DISCOVERY_TOPICS
        ]
        try:
            await asyncio.sleep(DISCOVERY_TIMEOUT)
        finally:
            for unsubscribe in unsubscribes:
                unsubscribe()
        _LOGGER.debug("Discovery found %d new device(s)", len(self._discovered))

    async def async_step_pick_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose one of the discovered devices."""
        # Reached from the progress step, HA may pass that step's input on
        if user_input and (info := self._discovered.get(user_input.get(CONF_SERIAL, ""))):
            self._pending = {
                CONF_SERIAL: info.serial, CONF_MODEL: info.model, CONF_CATEGORY: info.category}
            if info.category == protocol.WATER_HEATER:
                return await self.async_step_key()
            return await self._async_create(self._pending)
        options = {
            serial: f"{_title(info.category, serial)} ({serial})"
            for serial, info in self._discovered.items()
        }
        return self.async_show_form(
            step_id="pick_device",
            data_schema=vol.Schema({vol.Required(CONF_SERIAL): vol.In(options)}),
            description_placeholders={"device_count": str(len(options))},
        )

    async def async_step_key(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Ask for a discovered water heater's key and IV."""
        errors: dict[str, str] = {}
        if user_input is not None and not (errors := _key_errors(user_input)):
            return await self._async_create({**self._pending, **user_input})
        return self.async_show_form(step_id="key", data_schema=KEY_SCHEMA, errors=errors)

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Enter a device's details by hand."""
        errors: dict[str, str] = {}
        # Reached from the progress step, HA may pass that step's input on
        if user_input and CONF_SERIAL in user_input:
            category = user_input.get(CONF_CATEGORY, protocol.INVERTER)
            data = {
                CONF_SERIAL: user_input[CONF_SERIAL].strip(),
                CONF_CATEGORY: category,
                CONF_MODEL: (user_input.get(CONF_MODEL) or "").strip()
                or protocol.DEFAULT_MODELS[category],
            }
            if category == protocol.WATER_HEATER:
                data |= {k: user_input[k] for k in (CONF_KEY, CONF_IV) if user_input.get(k)}
            topic = protocol.telemetry_topic(category, data[CONF_MODEL], data[CONF_SERIAL])
            if protocol.parse_topic(topic) is None:
                errors["base"] = "invalid_serial"
            elif not (errors := _key_errors(data)):
                return await self._async_create(data)
        else:
            errors, self._manual_errors = self._manual_errors, {}
        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required(CONF_CATEGORY, default=protocol.INVERTER): SelectSelector(
                    SelectSelectorConfig(
                        options=list(protocol.CATEGORIES), translation_key="category",
                        mode=SelectSelectorMode.LIST,
                    )),
                vol.Required(CONF_SERIAL): str,
                vol.Optional(CONF_MODEL): str,
            }).extend(KEY_SCHEMA.schema),
            errors=errors,
        )

    async def _async_create(self, data: dict[str, str]) -> ConfigFlowResult:
        await self.async_set_unique_id(data[CONF_SERIAL])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=_title(data[CONF_CATEGORY], data[CONF_SERIAL]), data=data)
