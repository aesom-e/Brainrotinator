import asyncio
from typing import NoReturn
from subsystems.uart import UARTSubsystem, UARTMessageTrigger
from subsystems.servo import ServoSubsystem, DoubleClickCommand
from subsystems.uln2003 import ULN2003Subsystem, StepCommand
from triggers.button import ButtonDownTrigger, ButtonPull
from command import CommandScheduler, PrintCommand

async def run() -> NoReturn:
    uart = UARTSubsystem()
    await uart.start()
    await asyncio.sleep(1) # Wait for everything to be up

    servo = ServoSubsystem(13)
    double_click_command = DoubleClickCommand(servo, 700, 950)

    stepper = ULN2003Subsystem((21, 20, 16, 12))
    scroll_command = StepCommand(stepper, 1700, 0.001)

    button = ButtonDownTrigger(18, ButtonPull.PULL_UP)

    button.on_true(scroll_command)

    #UARTMessageTrigger(uart, "Works").on_true(PrintCommand("Works"))

    asyncio.create_task(command_scheduler_loop())

async def command_scheduler_loop() -> None:
    while True:
        CommandScheduler.get_instance().run()
        await asyncio.sleep(0)  # Yield to asyncio