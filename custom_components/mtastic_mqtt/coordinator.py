from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.mqtt import client as mqtt_client
from homeassistant.util import json, dt
from homeassistant.helpers import storage

from meshtastic import mesh_pb2, mqtt_pb2, portnums_pb2, telemetry_pb2

from .constants import DOMAIN
from .proto import convert_envelope_to_json, try_encrypt_envelope

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
        self._entry_id = entry.entry_id


    async def _async_update(self):
        return self._platform.get_data(self._entry_id)

    async def _async_update_state(self, data: dict):
        self.async_set_updated_data({
            **self.data,
            **data,
        })
        await self._platform.async_put_data(self._entry_id, self.data)

    async def async_load(self):
        self._config = self._entry.as_dict()["options"]
        self._node_id = self._config["id"]
        self._id = int(self._node_id[1:], 16)
        _LOGGER.debug(f"async_load: {self._config}, {self.data}, {self._node_id}, {self._id}")
        self._data_subs = await mqtt_client.async_subscribe(self.hass, self._config.get("pb_topic"), self._async_on_pb_message, encoding=None)
        self._stat_subs = None
        if topic := self._config.get("stat_topic"):
            self._stat_subs = await mqtt_client.async_subscribe(self.hass, topic, self._async_on_stat_message)

    async def async_unload(self):
        _LOGGER.debug(f"async_unload:")
        self._data_subs()
        self._data_subs = None
        if self._stat_subs:
            self._stat_subs()
            self._stat_subs = None

    async def _async_process_message(self, obj):
        _LOGGER.debug(f"_async_process_message: JSON[{self._id}]: {obj}")
        if "type" in obj and "payload" in obj:
            if obj.get("from") != self._id:
                _LOGGER.debug(f"_async_process_message: ignoring relay message")
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

    async def _async_on_pb_message(self, message):
        _LOGGER.debug(f"_async_on_pb_message: {message}")
        try:
            env = mqtt_pb2.ServiceEnvelope()
            env.ParseFromString(message.payload)
            _LOGGER.debug(f"_async_on_pb_message(): parsed {env}")
            if env.packet.HasField("encrypted"):
                try_encrypt_envelope(env, self._config.get("key", "AQ=="))
                _LOGGER.debug(f"_async_on_pb_message(): decrypted {env.packet}")
            obj = convert_envelope_to_json(env)
            _LOGGER.debug(f"_async_on_pb_message(): JSON {obj}")
            await self._async_process_message(obj)
        except:
            _LOGGER.exception(f"Error parsing protobuf message")

    # async def _async_on_json_message(self, message):
    #     _LOGGER.debug(f"_async_on_json_message: {message}")
    #     try:
    #         obj = json.json_loads_object(message.payload)
    #         _LOGGER.debug(f"_async_on_json_message: JSON[{self._id}]: {obj}")
    #         await self._async_process_message(obj)

    #     except:
    #         _LOGGER.warn(f"Unexpected JSON: {message.payload}")

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
        self._attr_unique_id = f"mtastic_mqtt_{self.coordinator._entry_id}_{id}"
        self._attr_name = name
        return self

    @property
    def device_info(self):
        return {
            "identifiers": {
                ("entry_id", self.coordinator._entry_id), 
            },
            "name": self.coordinator._entry.title,
        }
