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
    discovery_info: DiscoveryInfoType | None = None,
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
    reader = await Reader.create(port, name)
    # create reader task
    reader_task = asyncio.create_task(ve_reader(name, reader, async_add_entities))
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, reader_task.cancel)


async def ve_reader(name, reader, async_add_entities):
    entities = {}
    decoder = Decoder.init()
    while True:
        try:
            line = await reader.readln()
            _LOGGER.debug(f"Received {line}")
            label, v = line.decode('utf-8').strip().split('\t')
            value, spec = Decoder.decode(label, v)
            entity = entities.get(label)
            if entity == None:
                entity = GenericSensor(name, spec.name, spec.icon, spec.unit)
                async_add_entities([ entity ], True)
                entities[label] = entity
                _LOGGER.debug(f"Created entity {spec.name} [{spec.unit}]")
            _LOGGER.debug(f"Update {entity.name} = {value} [{spec.unit}]")
            entity.state = value
            entity.async_write_ha_state()
        except ValueError:
            # line.decode('utf-8') ...
            pass
        except TypeError:
            # Decoder.decode(...) == None
            pass
        except RuntimeError:
            # async_write_ha_state
            pass
        except asyncio.CancelledError:
            await reader.stop()
            break
        except Exception as exc:
            _LOGGER.exception(f"Unexpected error in VE.Direct Integration ({name}): {exc}.")
