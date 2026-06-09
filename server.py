from typing import NoReturn
from subsystems.bluetooth import BTServer, BTSubsystem, BTSendCommand
from subsystems.mpu6050 import MPU6050, GyroReading
from command import CommandScheduler

async def run() -> NoReturn:
    #bt = BTSubsystem(server=BTServer())
    #await bt.start()

    gyro = MPU6050()

    i = 0
    while True:
        #BTSendCommand(bt, str(i)).schedule()
        i += 1

        print(gyro.read())

        CommandScheduler.get_instance().run()