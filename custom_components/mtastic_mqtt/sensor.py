from homeassistant.components import sensor
from homeassistant.helpers.entity import EntityCategory

from .coordinator import BaseEntity
from .constants import DOMAIN

import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_setup_entities):
    coordinator = hass.data[DOMAIN]["devices"][entry.entry_id]
    async_setup_entities([
        _LastUpdate(coordinator),
        _TelemetryBattery(coordinator), 
        _TelemetryVoltage(coordinator),
        _TelemetryAirtimelUtil(coordinator),
        _TelemetryChannelUtil(coordinator),
        _Neighbors(coordinator),
    ])

class _TelemetryBattery(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"tel_battery_level", "Battery")
        self._attr_device_class = sensor.SensorDeviceClass.BATTERY
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "%"
        self._attr_entity_registry_enabled_default = False
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if (value := tel.get("battery_level")) > 0:
                return value
        return None

class _TelemetryVoltage(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"tel_voltage", "Voltage")
        self._attr_device_class = sensor.SensorDeviceClass.VOLTAGE
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "V"
        self._attr_suggested_display_precision = 1
        self._attr_entity_registry_enabled_default = False
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if (value := tel.get("voltage")) > 0:
                return value
        return None

class _TelemetryAirtimelUtil(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"tel_air_util_tx", "Tx Airtime Utilization")
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "%"
        self._attr_suggested_display_precision = 1
        self._attr_entity_registry_enabled_default = False
        self._attr_icon = "mdi:cloud-percent"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if value := tel.get("air_util_tx"):
                return value
        return None

class _TelemetryChannelUtil(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"tel_channel_utilization", "Channel Utilization")
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "%"
        self._attr_suggested_display_precision = 1
        self._attr_entity_registry_enabled_default = False
        self._attr_icon = "mdi:gauge"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if value := tel.get("channel_utilization"):
                return value
        return None

class _TelemetryChannelUtil(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"tel_channel_utilization", "Channel Utilization")
        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "%"
        self._attr_suggested_display_precision = 1
        self._attr_entity_registry_enabled_default = False
        self._attr_icon = "mdi:gauge"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if tel := self.coordinator.data.get("device_metrics"):
            if value := tel.get("channel_utilization"):
                return value
        return None

class _LastUpdate(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"last_update", "Last Update")

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_class = sensor.SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        return self.coordinator.last_update

    @property
    def extra_state_attributes(self):
        result = dict()
        if pos := self.coordinator.data.get("nodeinfo"):
            for attr in ("id", "longname", "shortname"):
                if value := pos.get(attr):
                    result[attr] = value
        return result

class _Neighbors(BaseEntity, sensor.SensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.with_name(f"nn_neighbors", "Neighbors Count")
        self._attr_state_class = "measurement"
        self._attr_suggested_display_precision = 0
        self._attr_entity_registry_enabled_default = False
        self._attr_icon = "mdi:map-marker-multiple-outline"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> float | None:
        if nn := self.coordinator.data.get("neighborinfo"):
            if (value := nn.get("neighbors_count")) >= 0:
                return value
        return None

