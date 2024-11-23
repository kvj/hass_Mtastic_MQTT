from homeassistant.components import binary_sensor
from homeassistant.helpers.entity import EntityCategory

from .coordinator import BaseEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = entry.runtime_data
    if coordinator._stat_subs:
        async_setup_entities([_Online(coordinator)])

class _Online(BaseEntity, binary_sensor.BinarySensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"online", "Online")
        self._attr_device_class = binary_sensor.BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        if stat := self.coordinator.data.get("stat"):
            return stat == "online"
        return None
