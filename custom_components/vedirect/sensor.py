"""Read and decode output from Victron VE.Direct bus."""

# see https://github.com/home-assistant/core/blob/dev/homeassistant/components/serial/sensor.py
from __future__ import annotations

import asyncio
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .generic_sensor import GenericSensor
from .const import (CONF_NAME, CONF_PORT)

from .lib.reader import Reader
from .lib.decoder import Decoder


_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_PORT, default=''): cv.string,
    }
)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    _: DiscoveryInfoType | None = None,
) -> None:
    """Set up the VE.Direct sensor platform."""
    name = config.get(CONF_NAME)
    port = config.get(CONF_PORT)
    if port == '':
        # no port specified ... try to auto-detect
        port = await Reader.discover()
    if port == None:
        _LOGGER.error(f"No port (e.g. /dev/ttyUSB0) specified for {name}. Terminating.")
        return
    _LOGGER.info(f"VE.Direct: {name} @ {port}")
    # create reader task
    ve_sensor = VESensor(async_add_entities, port, name)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, ve_sensor.stop)
    async_add_entities([ ve_sensor ], True)


class VESensor(GenericSensor):

    def __init__(self, async_add_entities, port, device_name):
        super().__init__(device_name, "Product ID", "mdi:identifier")
        self._async_add_entities = async_add_entities
        self._port = port
        self._device_name = device_name
        self._loop_task = None

    async def async_added_to_hass(self):
        """Handle when an entity is about to be added to Home Assistant."""
        _LOGGER.debug("async_added_to_hass")
        self._loop_task = self.hass.loop.create_task(self._loop())

    async def _loop(self):
        """Read from VE.Direct interface"""
        entities = { 'PID': self }
        decoder = Decoder.init()
        reader = await Reader.create(self._port, self._device_name)
        await reader.start()
        while True:
            try:
                line = await reader.readln()
                # _LOGGER.debug(f"Received {line}")
                label, v = line.decode('utf-8').strip().split('\t')
                value, spec = Decoder.decode(label, v)
                entity = entities.get(label)
                if entity == None:
                    entity = GenericSensor(self._device_name, spec.name, spec.icon, spec.unit)
                    self._async_add_entities([ entity ], True)
                    entities[label] = entity
                    _LOGGER.debug(f"Created entity {spec.name} [{spec.unit}]")
                _LOGGER.debug(f"Update {entity.name} = {value} [{spec.unit}]")
                entity.state = value
                entity.async_write_ha_state()
            except (ValueError, TypeError, RuntimeError):
                pass
            except asyncio.CancelledError:
                await reader.stop()
                break
            except Exception as exc:
                _LOGGER.exception(f"Unexpected error in VE.Direct Integration ({self._device_name}): {exc}.")

    @callback
    def stop(self, _):
        """Close resources."""
        if self._loop_task:
            self._loop_task.cancel()
