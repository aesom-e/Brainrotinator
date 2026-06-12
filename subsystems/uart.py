from typing import Optional, override
import asyncio
import serial_asyncio
from command import Subsystem, InstantCommand, Trigger

class UARTSubsystem(Subsystem):
    def __init__(self, port: str = "/dev/serial0", baud_rate: int = 115200) -> None:
        self.port: str = port
        self.baud_rate: int = baud_rate
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._rx_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        self._reader, self._writer = await serial_asyncio.open_serial_connection(
            url=self.port, baudrate=self.baud_rate
        )
        self._reader_task = asyncio.get_event_loop().create_task(self._read_loop())
        print(f"UART open on {self.port} at {self.baud_rate} baud")

    async def _read_loop(self) -> None:
        while True:
            line = await self._reader.readline()
            self._rx_queue.put_nowait(line.decode().rstrip("\n"))

    async def send(self, message: str) -> None:
        self._writer.write((message + "\n").encode())
        await self._writer.drain()

    async def receive(self) -> str:
        return await self._rx_queue.get()

    def receive_nowait(self) -> Optional[str]:
        if self._rx_queue.empty(): return None
        return self._rx_queue.get_nowait()

    async def close(self) -> None:
        if self._reader_task is not None:
            self._reader_task.cancel()
            self._reader_task = None

        if self._writer is not None:
            self._writer.close()
            await self._writer.wait_closed()
            self._writer = None

        self._reader = None

class UARTSendCommand(InstantCommand):
    def __init__(self,
                 uart: UARTSubsystem,
                 message: str) -> None:
        self._uart: UARTSubsystem = uart
        self._message: str = message
        super().__init__(self._send_message, uart)

    def _send_message(self) -> None:
        asyncio.get_event_loop().create_task(self._uart.send(self._message))

class UARTMessageTrigger(Trigger):
    def __init__(self,
                 uart: UARTSubsystem,
                 message: str) -> None:
        super().__init__()

        self._uart: UARTSubsystem = uart
        self._message: str = message

    @override
    def get(self) -> bool:
        msg = self._uart.receive_nowait()
        if msg is None: return False
        return msg == self._message