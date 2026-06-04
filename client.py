import os
from typing import NoReturn
from connection import BTClient
from command import CommandScheduler

async def run() -> NoReturn:
    bt = BTClient("PiServer")

    while True:
        print(await bt.receive())

        CommandScheduler.get_instance().run()