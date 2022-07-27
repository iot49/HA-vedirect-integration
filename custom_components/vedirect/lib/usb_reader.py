from .reader import Reader

from serial.tools import list_ports
from serial import SerialException
import serial_asyncio
import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


class USBReader(Reader):

    @classmethod
    def discover(cls):
        candidate = None
        for port in list_ports.comports():
            # log all candidates to help user find correct port
            _LOGGER.info(f"Found device {port.vid:04x}:{port.pid:04x} by {port.manufacturer} @ {port.device}")
            # we found one that is known to be compatible with the integration
            # propose it as default in setup
            if port.vid == 0x0403 and port.pid == 0x6015 and "VictronEnergy" in port.manufacturer:
                candidate = port.device
        return candidate

    def __init__(self, port, name):
        super.__init__(port, name)
        self._reader = None
        
    async def readln(self):
        # https://stackoverflow.com/questions/28343941/python-serialexception-device-reports-readiness-to-read-but-returned-no-data-d
        while True:
            try:
                if self._reader == None:
                    self._reader, _ = await serial_asyncio.open_serial_connection(url=self._port, baudrate=19200)
                line = await self._reader.readline()
                return line
            except SerialException as exc:
                _LOGGER.exception(f"Error while reading {self._port}: {exc}")
                await asyncio.sleep(5)
