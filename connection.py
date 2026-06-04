from typing import Any, Optional
import asyncio
from bleak import BleakGATTCharacteristic, BleakClient, BleakScanner

# These are well-known constants
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_UUID      = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_UUID      = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class BTServer:
    def __init__(self, name="PiServer") -> None:
        self.name: str = name
        self._server: Optional["BlessServer"] = None
        self._rx_queue: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
        from bless import (
            BlessServer,
            GATTAttributePermissions,
            GATTCharacteristicProperties
        )

        self._server = BlessServer(name=self.name)
        self._server.read_request_func = self._read_request
        self._server.write_request_func = self._write_request

        await self._server.add_new_service(UART_SERVICE_UUID)
        await self._server.add_new_characteristic(
            UART_SERVICE_UUID,
            UART_TX_UUID,
            GATTCharacteristicProperties.notify,
            None,
            GATTAttributePermissions.readable
        )
        await self._server.add_new_characteristic(
            UART_SERVICE_UUID,
            UART_RX_UUID,
            GATTCharacteristicProperties.write | GATTCharacteristicProperties.write_without_response,
            None,
            GATTAttributePermissions.writeable
        )

        await self._server.start()
        print(f"Advertising as {self.name}")

    def _read_request(self, characteristic: Any, **kwargs) -> bytearray:
        return characteristic.value

    def _write_request(self, characteristic: Any, value: Any, **kwargs) -> None:
        if str(characteristic.uuid).lower() == UART_RX_UUID.lower():
            self._rx_queue.put_nowait(bytes(value).decode())

    async def send(self, message: str) -> None:
        char = self._server.get_characteristic(UART_TX_UUID)
        char.value = message.encode()
        self._server.update_value(UART_SERVICE_UUID, UART_TX_UUID)

    async def receive(self) -> str:
        return await self._rx_queue.get()

    async def close(self) -> None:
        if self._server is not None: await self._server.stop()
        self._server = None

class BTClient:
    def __init__(self, server_name: str) -> None:
        self.server_name = server_name
        self._client: Optional[BleakClient] = None
        self._rx_queue: asyncio.Queue = asyncio.Queue()

    async def connect(self) -> None:
        print(f"Scanning for '{self.server_name}'...")
        device = await BleakScanner.find_device_by_name(self.server_name)
        if device is None:
            raise RuntimeError(f"Could not find device '{self.server_name}'")

        self._client = BleakClient(device)
        await self._client.connect()
        await self._client.start_notify(UART_TX_UUID, self._notification_handler)
        print(f"Connected to {device.address}")

    def _notification_handler(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        self._rx_queue.put_nowait(data.decode())

    async def send(self, message: str) -> None:
        await self._client.write_gatt_char(UART_RX_UUID, message.encode())

    async def receive(self) -> str:
        return await self._rx_queue.get()

    async def close(self) -> None:
        if self._client is not None and self._client.is_connected:
            await self._client.disconnect()
        self._client = None