from homeassistant.components import device_tracker
from homeassistant.helpers.entity import EntityCategory

from .coordinator import BaseEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = entry.runtime_data
    async_setup_entities([_Position(coordinator)])

class _Position(BaseEntity, device_tracker.TrackerEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"position_tracker", "Position")
        self._attr_entity_category = None

    @property
    def latitude(self) -> float | None:
        if pos := self.coordinator.data.get("position"):
            if value := pos.get("latitude_i"):
                return value / 10000000.0
        return None

    @property
    def longitude(self) -> float | None:
        if pos := self.coordinator.data.get("position"):
            if value := pos.get("longitude_i"):
                return value / 10000000.0
        return None

    @property
    def battery_level(self) -> int | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if (value := tel.get("battery_level")) > 0:
                return value
        return None

    @property
    def source_type(self) -> device_tracker.SourceType | str:
        return device_tracker.SourceType.GPS

    @property
    def extra_state_attributes(self):
        result = dict()
        if pos := self.coordinator.data.get("position"):
            for attr in ("altitude", "ground_speed", "sats_in_view"):
                if value := pos.get(attr):
                    result[attr] = value
        return result
