import os
from typing import NoReturn
from subsystems.bluetooth import BTClient, BTSubsystem
from command import CommandScheduler

async def run() -> NoReturn:
    bt = BTSubsystem(client=BTClient("PiServer"))
    await bt.start()

    while True:
        print(await bt.receive())

        CommandScheduler.get_instance().run()