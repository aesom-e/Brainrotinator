import os
from typing import NoReturn
from subsystems.bluetooth import BTClient, BTSubsystem
from subsystems.servo import ServoSubsystem, DoubleClickCommand
from subsystems.uln2003 import ULN2003Subsystem, StepCommand
from triggers.button import ButtonDownTrigger, ButtonPull
from command import CommandScheduler

async def run() -> NoReturn:
    #bt = BTSubsystem(client=BTClient("PiServer"))
    #await bt.start()

    servo = ServoSubsystem(13)
    double_click_command = DoubleClickCommand(servo, 700, 950)

    stepper = ULN2003Subsystem((21, 20, 16, 12))
    scroll_command = StepCommand(stepper, 1700, 0.001)

    button = ButtonDownTrigger(18, ButtonPull.PULL_UP)

    button.on_true(scroll_command)

    while True:

        #print(await bt.receive())

        CommandScheduler.get_instance().run()