from typing import NoReturn
from connection import BTServer
from command import CommandScheduler

async def run() -> NoReturn:
    bt = BTServer()
    await bt.start()

    i = 0
    while True:
        await bt.send(str(i))
        i += 1

        CommandScheduler.get_instance().run()