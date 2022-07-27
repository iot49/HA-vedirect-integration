from homeassistant.components.sensor import SensorEntity
import logging

_LOGGER = logging.getLogger(__name__)

"""Generic SensorEntity."""

class GenericSensor(SensorEntity):

    def __init__(self, device, name, icon, unit=None):
        self._device = device
        self._name = name
        self._icon = icon
        self._unit = unit
        self._state = self._attributes = None

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    @property
    def name(self) -> str:
        return f"{self._device} {self._name}"

    @property
    def icon(self) -> str:
        return self._icon

    @property
    def native_unit_of_measurement(self) -> str:
        return self._unit
        
    @property
    def native_value(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attributes

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def unique_id(self) -> str:
        return f"{self._device}_{self.name.replace(' ', '_').lower()}"
