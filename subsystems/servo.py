import time
from typing import Optional, override
from command import Command, Subsystem

class ServoSubsystem(Subsystem):
    def __init__(self, pin: int) -> None:
        super().__init__()
        self._pin: int = pin

        import pigpio
        pi = pigpio.pi()
        if pi.connected:
            self._pi: pigpio.pi = pi

    def set_pw(self, pw: int) -> None:
        self._pi.set_servo_pulsewidth(self._pin, pw)

class DoubleClickCommand(Command):
    _PRESS_SECS: float = 0.20
    _RETURN_SECS: float = 0.20
    _GAP_SECS: float = 0.11

    def __init__(self,
                 servo: ServoSubsystem,
                 neutral_us: int,
                 pressed_us: int) -> None:
        super().__init__()
        self.add_requirements(servo)
        self._servo: ServoSubsystem = servo
        self._neutral_us: int = neutral_us
        self._pressed_us: int = pressed_us
        self._phase: int = 0
        self._next_time: float = 0.

    @override
    def initialize(self) -> None:
        self._servo.set_pw(self._pressed_us)
        self._phase = 0
        self._next_time = time.monotonic() + self._pressed_us

    @override
    def execute(self) -> None:
        if time.monotonic() < self._next_time: return

        match self._phase:
            case 0:
                self._servo.set_pw(self._neutral_us)
                self._phase = 1
                self._next_time = time.monotonic() + self._RETURN_SECS
            case 1:
                self._phase = 2
                self._next_time = time.monotonic() + self._GAP_SECS
            case 2:
                self._servo.set_pw(self._pressed_us)
                self._phase = 3
                self._next_time = time.monotonic() + self._PRESS_SECS
            case 3:
                self._servo.set_pw(self._neutral_us)
                self._phase = 4
                self._next_time = time.monotonic() + self._RETURN_SECS
            case _: pass

    @override
    def is_finished(self) -> bool:
        return self._phase == 4

    @override
    def end(self, interrupted: bool) -> None:
        self._servo.set_pw(self._neutral_us)