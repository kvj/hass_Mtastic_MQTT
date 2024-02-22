from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.util import json, dt
from homeassistant.helpers import storage

from .constants import DOMAIN

import logging
from datetime import datetime

_LOGGER = logging.getLogger(__name__)

class Platform():

    def __init__(self, hass):
        self.hass = hass
        self._storage = storage.Store(hass, 1, DOMAIN)

    async def async_load(self):
        data_ = await self._storage.async_load()
        _LOGGER.debug(f"async_load(): Loaded stored data: {data_}")
        self._storage_data = data_ if data_ else {}

    def get_data(self, key: str, def_={}):
        if key in self._storage_data:
            return self._storage_data[key]
        return def_

    async def async_put_data(self, key: str, data):
        if data:
            self._storage_data = {
                **self._storage_data,
                key: data,
            }
        else:
            if key in self._storage_data:
                del self._storage_data[key]
        await self._storage.async_save(self._storage_data)


class Coordinator(DataUpdateCoordinator):

    def __init__(self, platform, entry):
        super().__init__(
            platform.hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._async_update,
        )
        self._platform = platform
        self._entry = entry
        self._config = entry.as_dict()["options"]
        self._node_id = entry.as_dict()["data"]["id"]
        self._id = int(self._node_id[1:], 16)

    async def _async_update(self):
        return self._platform.get_data(self._node_id)

    async def _async_update_state(self, data: dict):
        self.async_set_updated_data({
            **self.data,
            **data,
        })
        await self._platform.async_put_data(self._node_id, self.data)

    async def async_load(self):
        _LOGGER.debug(f"async_load: {self._config}, {self.data}, {self._node_id}, {self._id}")
        self._json_subs = await mqtt_client.async_subscribe(self.hass, self._config["json_topic"], self._async_on_json_message)
        self._stat_subs = None
        if topic := self._config.get("stat_topic"):
            self._stat_subs = await mqtt_client.async_subscribe(self.hass, topic, self._async_on_stat_message)

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        self._json_subs()
        if self._stat_subs:
            self._stat_subs()

    async def _async_on_json_message(self, message):
        _LOGGER.debug(f"_async_on_json_message: {message}")
        try:
            obj = json.json_loads_object(message.payload)
            _LOGGER.debug(f"_async_on_json_message: JSON[{self._id}]: {obj}")
            if "type" in obj and "payload" in obj:
                if obj.get("from") != self._id:
                    return
                type_ = obj["type"]
                payload = {
                    **self.data.get(type_, {}),
                    **obj["payload"],
                }
                if type_ == "nodeinfo" and obj.get("sender") != payload.get("id"):
                    return # nodeinfo about other node - ignoring for now
                dt_now = dt.now()
                await self._async_update_state({
                    type_: payload,
                    "last_update": dt_now.timestamp(),
                })

        except:
            _LOGGER.warn(f"Unexpected JSON: {message.payload}")

    async def _async_on_stat_message(self, message):
        _LOGGER.debug(f"_async_on_stat_message: {message}")
        await self._async_update_state({
            "stat": message.payload,
        })

    @property
    def last_update(self):
        return datetime.fromtimestamp(self.data["last_update"], tz=dt.DEFAULT_TIME_ZONE) if "last_update" in self.data else None

class BaseEntity(CoordinatorEntity):

    def __init__(self, coordinator: Coordinator):
        super().__init__(coordinator)

    def with_name(self, id: str, name: str):
        self._attr_has_entity_name = True
        self._attr_unique_id = f"mtastic_mqtt_{self.coordinator._id}_{id}"
        self._attr_name = name
        return self

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("entry_id", self.coordinator._entry.entry_id), 
            },
            "name": self.coordinator._node_id,
        }
