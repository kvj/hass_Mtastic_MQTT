from __future__ import annotations
from .constants import DOMAIN, PLATFORMS
from .coordinator import Coordinator, Platform

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import service

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import logging

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
    }, extra=vol.ALLOW_EXTRA),
}, extra=vol.ALLOW_EXTRA)

async def _async_update_entry(hass, entry):
    _LOGGER.debug(f"_async_update_entry: {entry}")
    coordinator = entry.runtime_data
    await coordinator.async_unload()
    await coordinator.async_load()

async def async_setup_entry(hass: HomeAssistant, entry):
    platform = hass.data[DOMAIN]
    coordinator = Coordinator(platform, entry)
    entry.runtime_data = coordinator
    await coordinator.async_load()
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(_async_update_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    coordinator = entry.runtime_data

    await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await coordinator.async_unload()
    entry.runtime_data = None
    return True

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    platform = Platform(hass)
    await platform.async_load()
    hass.data[DOMAIN] = platform
    return True
