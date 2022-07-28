import asyncio
import logging
from abc import ABC, abstractmethod
from io import BytesIO

import bleak

from .reader import Reader


_LOGGER = logging.getLogger(__name__)

DISCONNECTED = "DISCONNECTED"


class MACReader(Reader):

    CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

    def __init__(self, port, name):
        super().__init__(port, name)
        self._rx_queue = asyncio.Queue()
        self._client = None

    @classmethod
    async def discover(cls):
        """List BLE devices."""
        try:
            devices = await bleak.BleakScanner.discover()
            for d in devices:
                _LOGGER.info(f"Found BLE device {d.address} by {d.name}")
        except bleak.exc.BleakDBusError:
            pass

    async def start(self):
        await self._connect()
        await self._configure_ble()

    async def stop(self):
        if self._client:
            await self._client.disconnect()

    async def readln(self):
        line = BytesIO()
        while True:
            x = await self._rx_queue.get()
            if x == DISCONNECTED:
                self._connect()
                return b''
            line.write(x)
            if x.endswith(b'\n'):
                return line.getvalue()

    async def _connect(self):
        if self._client and self._client.is_connected:
            return
        self._client = bleak.BleakClient(self._port, disconnected_callback=self._disconnected)
        _LOGGER.debug(f"Connecting to {self._port}")
        await self._client.connect()
        await self._client.start_notify(self.CHAR_UUID, self._handle_rx)
        _LOGGER.info(f"Connected to {self._port}")

    async def _configure_ble(self):
        try:
            # check baudrate
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+BAUD?')
            r = await self._rx_queue.get()
            _LOGGER.debug(f"check baudrate: {r} vs {b'OK+Get:4'}")
            if r != b'OK+Get:4':
                # Note: HM-18 baudrate can only be changed from UART side, not BLE!
                _LOGGER.error("Set HM-18 BLE module baudrate to 19,200 baud!")
            # check name
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+NAME?')
            r = await self._rx_queue.get()
            _, n = r.decode().split(':')
            _LOGGER.debug(f"check name: {r} - {n} vs {self._name}")
            if n != self._name:
                await self._client.write_gatt_char(self.CHAR_UUID, f'AT+NAME{self._name}'.encode())
                _LOGGER.debug(f"Updated BLE module name: {await self._rx_queue.get()}")
        except:
            # no big deal if this does not work
            pass

    async def _handle_rx(self, _: int, data: bytearray):
        for s in data.splitlines(True):
            await self._rx_queue.put(s)

    def _disconnected(self, _: bleak.BleakClient):
        _LOGGER.info("BLE disconnected")
        # tell readln to reconnect!
        self._rx_queue.put_nowait(DISCONNECTED)
