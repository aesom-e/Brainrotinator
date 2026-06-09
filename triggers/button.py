from typing import override
from enum import Enum, auto
import RPi.GPIO as GPIO
from command import Trigger

class ButtonPull(Enum):
    INTERNAL = auto()
    PULL_UP = auto()
    PULL_DOWN = auto()

class ButtonDownTrigger(Trigger):
    def __init__(self, pin: int, pull: ButtonPull = ButtonPull.INTERNAL) -> None:
        super().__init__()
        GPIO.setmode(GPIO.BCM)
        if pull is ButtonPull.INTERNAL:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            self._pull: ButtonPull = ButtonPull.PULL_DOWN
        else:
            GPIO.setup(pin, GPIO.IN)
            self._pull: ButtonPull = pull
        self._pin: int = pin

    @override
    def get(self) -> bool:
        down_state: bool = self._pull is ButtonPull.PULL_DOWN
        return GPIO.input(self._pin) == down_state