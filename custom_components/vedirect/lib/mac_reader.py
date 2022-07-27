import asyncio
import logging
from abc import ABC, abstractmethod
from io import BytesIO

from bleak import BleakScanner, BleakClient
from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

from .reader import Reader


_LOGGER = logging.getLogger(__name__)


class MACReader(Reader):

    CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"

    def __init__(self, port, name):
        super().__init__(port, name)
        self._rx_queue = asyncio.Queue()
        self._client = None

    @classmethod
    async def discover(cls):
        """List BLE devices."""
        devices = await BleakScanner.discover()
        for d in devices:
            _LOGGER.info(f"Found BLE device {d.address} by {d.name}")

    async def stop(self):
        await self._client.disconnect()
        self._connect_task.cancel()
        
    async def readln(self):
        await self._connect()
        line = BytesIO()
        while True:
            s = await self._rx_queue.get()
            line.write(c)
            if s.endswith(b'\n'):
                return line.getvalue()

    async def _connect(self):
        if self._client and self._client.is_connected:
            return
        client = BleakClient(self._port, disconnected_callback=self._disconnected)
        _LOGGER.debug(f"Connecting to {self._port}")
        await self._client.connect()
        await self._client.start_notify(self.CHAR_UUID, self._handle_rx)
        if self._client == None:
            # run this only the first time we are connecting
            self._connect_task = asyncio.create_task(self._connection_monitor())
            await self._configure_ble()
        self._client = client
        _LOGGER.info(f"Connected to {self._port}")

    async def _connection_monitor(self):
        # reconnect if connection is lost
        # Note: can't do this in _disconnected as it's not async
        while True:
            await self._connect()
            await asyncio.sleep(5)

    async def _configure_ble(self):
        try:
            # check baudrate
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+BAUD?')
            r = await self._rx_queue.get()
            _LOGGER.debug(f"check baudrate: {r}")
            if r != b'OK+Get:4':
                # Note: baudrate can only be changed from UART side, not BLE!
                _LOGGER.error("Set HM-18 BLE module baudrate to 19,200 baud!")
            # check name
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+NAME?')
            r = await self._rx_queue.get()
            _LOGGER.debug(f"check name: {r}")            
            _, n = r.decode().split(':')
            if n != self._name:
                await self._client.write_gatt_char(self.CHAR_UUID, f'AT+NAME{self._name}'.encode())
                _LOGGER.debug(f"Updated BLE module name: {await self._rx_queue.get()}")
        except:
            # no big deal if this does not work
            pass

    async def _configure_ble(self):
        try:
            # check baudrate
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+BAUD?')
            r = await self._rx_queue.get()
            print(f"check baudrate: {r}")
            if r != b'OK+Get:4':
                _LOGGER.error("HM-18 BLE module is not configured for 19,200 baud!")
            # check name
            await self._client.write_gatt_char(self.CHAR_UUID, b'AT+NAME?')
            r = await self._rx_queue.get()
            print(f"check name: {r}")
            _, n = r.decode().split(':')
            if n != self._name:
                await self._client.write_gatt_char(self.CHAR_UUID, f'AT+NAME{self._name}'.encode())
                print(f"Updated BLE module name: {await self._rx_queue.get()}")
        except:
            pass

    async def _handle_rx(self, _: int, data: bytearray):
        for s in data.splitline(True):
            await self._rx_queue.put(s)

    def _disconnected(self, _: BleakClient):
        _LOGGER.info("BLE disconnected")
        

