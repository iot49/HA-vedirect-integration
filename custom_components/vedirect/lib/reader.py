from abc import ABC, abstractmethod
import re

class Reader(ABC):

    @classmethod
    async def create(cls, port: str, name: str):
        # Reader "factory"
        from .usb_reader import USBReader
        from .mac_reader import MACReader
        is_ble = re.match('([a-fA-F0-9]{2}[:|\-]?){6}', port)
        reader = MACReader(port, name) if is_ble else USBReader(port, name)
        await reader._start()
        return reader

    @classmethod
    async def discover(cls):
        """Log connected VEDirect devices. Return port if a compatible device is found."""
        from .usb_reader import USBReader
        from .mac_reader import MACReader
        await MACReader.discover()
        return await USBReader.discover()

    @abstractmethod
    async def readln(self) -> str:
        """Read one line"""
        pass

    async def stop(self):
        # clean shutdown (e.g. disconnect from ble)
        pass

    async def start(self):
        pass

    def __init__(self, port, name):
        self._port = port
        self._name = name
