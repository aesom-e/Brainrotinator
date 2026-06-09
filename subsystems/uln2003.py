import time
from enum import Enum, auto
from typing import Tuple, List, Dict, override
import RPi.GPIO as GPIO
from command import Command, InstantCommand, Subsystem

class StepMode(Enum):
    HALF = auto()
    FULL = auto()
    WAVE = auto()

_SEQUENCES: Dict[StepMode, List[List[int]]] = {
    StepMode.HALF: [
        [1, 0, 0, 0],
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
        [1, 0, 0, 1],
    ],
    StepMode.FULL: [
        [1, 1, 0, 0],
        [0, 1, 1, 0],
        [0, 0, 1, 1],
        [1, 0, 0, 1],
    ],
    StepMode.WAVE: [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1],
    ]
}

_DEFAULT_STEPS_PER_REV: int = 2048

class ULN2003Subsystem(Subsystem):
    _INIT: bool = False

    def __init__(self,
                 pins: Tuple[int, int, int, int],
                 *,
                 mode: StepMode = StepMode.HALF,
                 steps_per_rev: int = _DEFAULT_STEPS_PER_REV) -> None:
        super().__init__()
        self._pins: List[int] = list(pins)
        self._mode: StepMode = mode
        self._sequence: List[List[int]] = _SEQUENCES[mode]
        self._seq_len: int = len(self._sequence)
        self._steps_per_rev: int = steps_per_rev
        self._seq_index: int = 0
        self._position: int = 0

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        for pin in self._pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Horrible but it should work
        if not self._INIT:
            self._INIT = True
            import subprocess
            subprocess.run(["sudo", "pigpiod"], capture_output=True)
            time.sleep(1)

    def _apply_step(self) -> None:
        row = self._sequence[self._seq_index]
        for pin, val in zip(self._pins, row): GPIO.output(pin, val)

    def _deenergise(self) -> None:
        for pin in self._pins: GPIO.output(pin, 0)

    @property
    def position(self) -> int:
        return self._position

    @property
    def angle(self) -> float:
        steps = self._position % self._steps_per_rev
        return (steps / self._steps_per_rev) * 360.

    def step_once(self, forward: bool = True) -> None:
        if forward:
            self._seq_index = (self._seq_index + 1) % self._seq_len
            self._position += 1
        else:
            self._seq_index = (self._seq_index - 1) % self._seq_len
            self._position -= 1
        self._apply_step()

    def stop(self) -> None: self._deenergise()

class StepCommand(Command):
    def __init__(self,
                 motor: ULN2003Subsystem,
                 steps: int,
                 step_delay: float = 0.001) -> None:
        super().__init__()
        self.add_requirements(motor)
        self._motor: ULN2003Subsystem = motor
        self._total: int = abs(steps)
        self._forward: bool = steps >= 0
        self._delay: float = step_delay
        self._done: int = 0
        self._next_step_time: float = 0.
        print("StepCommand")

    @override
    def initialize(self) -> None:
        self._done = 0
        self._next_step_time = time.monotonic()

    @override
    def execute(self) -> None:
        now = time.monotonic()
        if now < self._next_step_time: return
        self._motor.step_once(self._forward)
        self._done += 1
        self._next_step_time = now + self._delay

    @override
    def is_finished(self) -> bool: return self._done >= self._total

    @override
    def end(self, interrupted: bool) -> None: self._motor.stop()