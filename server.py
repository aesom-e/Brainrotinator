from typing import NoReturn
import cleanup
from subsystems.bluetooth import BTServer, BTSubsystem, BTSendCommand
from subsystems.mpu6050 import MPU6050, GyroReading
from command import CommandScheduler

async def run() -> NoReturn:
    #bt = BTSubsystem(server=BTServer())
    #await bt.start()

    gyro = MPU6050()
    cleanup.register(lambda: gyro.close())

    i = 0
    while True:
        #BTSendCommand(bt, str(i)).schedule()
        i += 1

        CommandScheduler.get_instance().run()

# THESE ARE FOR TESTING

def make_bar(value: float) -> str:
    ratio = (value + 180.) / 360.
    filled = int(ratio * 40)
    filled = max(0, min(40, filled))
    bar = '#' * filled + '.' * (40 - filled)
    return f"[{bar}] {value:.1f}"

def print_reading(reading: GyroReading) -> None:
    lines = []
    for name, val in zip("xyz", reading):
        lines.append(f"{name}: {make_bar(val)}")

    print("\033[3A", end="")
    for line in lines: print(f"\033[2K{line}")