from typing import Any, Optional, override
import asyncio
from bleak import BleakGATTCharacteristic, BleakClient, BleakScanner
from bless import BlessServer, GATTAttributePermissions, GATTCharacteristicProperties
from command import InstantCommand, Subsystem, Trigger

# These are well-known constants
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_UUID      = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_UUID      = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class BTServer:
    def __init__(self, name="PiServer") -> None:
        self.name: str = name
        self._server: Optional[BlessServer] = None
        self._rx_queue: asyncio.Queue = asyncio.Queue()

    async def start(self) -> None:
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

    @staticmethod
    def _read_request(characteristic: Any, **kwargs) -> bytearray:
        return characteristic.value

    def _write_request(self, characteristic: Any, value: Any, **kwargs) -> None:
        if str(characteristic.uuid).lower() == UART_RX_UUID.lower():
            self._rx_queue.put_nowait(bytes(value).decode())

    async def send(self, message: str) -> None:
        char = self._server.get_characteristic(UART_TX_UUID)
        char.value = message.encode()
        self._server.update_value(UART_SERVICE_UUID, UART_TX_UUID)

    async def wait_for_connection(self) -> None:
        while len(self._server._subscribed_clients) == 0:
            await asyncio.sleep(0.1)

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

# A tagged enum would be great here
class BTSubsystem(Subsystem):
    def __init__(self, *,
                 server: Optional[BTServer] = None,
                 client: Optional[BTClient] = None) -> None:
        super().__init__()

        if server is None and client is None:
            raise ValueError("One of server or client must not be None")

        if server is not None:
            self._server: BTServer = server
            self._is_server: bool = True
        else:
            self._client: BTClient = client
            self._is_server: bool = False

        self._message_queue: asyncio.Queue[str] = asyncio.Queue()
        self._update_queue_task: asyncio.Task = asyncio.get_event_loop().create_task(self._update_queue())

    async def _update_queue(self) -> None:
        if self._is_server:
            while True: await self._message_queue.put(await self._server.receive())
        while True: await self._message_queue.put(await self._client.receive())

    @property
    def is_server(self) -> bool: return self._is_server

    async def start(self) -> None:
        if self._is_server: await self._server.start()
        else:               await self._client.connect()

    async def send(self, message: str) -> None:
        if self._is_server: await self._server.send(message)
        else:               await self._client.send(message)

    async def receive(self) -> str:
        if not self._message_queue.empty(): return self._message_queue.get_nowait()

        else: return await self._message_queue.get()

    def receive_nowait(self) -> Optional[str]:
        if self._message_queue.empty(): return None
        return self._message_queue.get_nowait()

    async def close(self) -> None:
        if self._update_queue_task: self._update_queue_task.cancel()

        if self._is_server: await self._server.close()
        else:               await self._client.close()

class BTSendCommand(InstantCommand):
    def __init__(self, bt: BTSubsystem, message: str) -> None:
        self._bt: BTSubsystem = bt
        self._message: str = message

        super().__init__(self._send_message, bt)

    def _send_message(self) -> None:
        asyncio.get_event_loop().create_task(self._bt.send(self._message))

class BTMessageTrigger(Trigger):
    def __init__(self, bt: BTSubsystem, message: str) -> None:
        super().__init__()

        self._bt: BTSubsystem = bt
        self._message: str = message

    @override
    def get(self) -> bool:
        # Currently, this drains the receive queue
        # This is bad practice, but I'm under time crunch right now
        # so this will have to do
        msg = self._bt.receive_nowait()
        if msg is None: return False
        return msg == self._message