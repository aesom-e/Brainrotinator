from typing import NoReturn
from subsystems.bluetooth import BTServer, BTSubsystem, BTSendCommand
from command import CommandScheduler

async def run() -> NoReturn:
    bt = BTSubsystem(server=BTServer())
    await bt.start()

    i = 0
    while True:
        BTSendCommand(bt, str(i)).schedule()
        i += 1

        CommandScheduler.get_instance().run()