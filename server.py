from typing import NoReturn
from subsystems.bluetooth import BTServer, BTSubsystem, BTSendCommand
from subsystems.mpu6050 import MPU6050, GyroReading, Extreme, GyroExtremeTrigger
from command import CommandScheduler, PrintCommand

async def run() -> NoReturn:
    #bt = BTSubsystem(server=BTServer())
    #await bt.start()

    gyro = MPU6050()
    scroll_trigger = GyroExtremeTrigger(gyro, ('x', Extreme.RightExtreme))
    like_trigger = GyroExtremeTrigger(gyro, ('y', Extreme.RightExtreme))

    i = 0
    while True:
        #BTSendCommand(bt, str(i)).schedule()
        i += 1
        #print_reading(gyro.read(), gyro.extremes)
        scroll_trigger.on_true(PrintCommand("Scroll"))
        like_trigger.on_true(PrintCommand("Like"))

        CommandScheduler.get_instance().run()

# THESE ARE FOR TESTING

def make_bar(value: float) -> str:
    ratio = (value + 180.) / 360.
    filled = int(ratio * 40)
    filled = max(0, min(40, filled))
    bar = '#' * filled + '.' * (40 - filled)
    return f"[{bar}] {value:.1f}"

def print_reading(reading: GyroReading, extremes) -> None:
    lines = []
    for name, val in zip("xyz", reading):
        line = f"{name}: {make_bar(val)}"
        if extremes[ord(name) - ord('x')] is Extreme.LeftExtreme: line += " [Left Extreme]"
        if extremes[ord(name) - ord('x')] is Extreme.RightExtreme: line += " [Right Extreme]"
        lines.append(line)

    print("\033[3A", end="")
    for line in lines: print(f"\033[2K{line}")