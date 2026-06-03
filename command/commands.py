import time
from typing import TYPE_CHECKING, Callable, Optional
from .command import Command

if TYPE_CHECKING: from .subsystem import Subsystem

class InstantCommand(Command):
    """Runs a single action when initialized then finishes immediately"""

    def __init__(self,
                 action: Callable[[], None],
                 *requirements: Subsystem) -> None:
        super().__init__()
        self._action = action
        self.add_requirements(*requirements)

    def initialize(self) -> None:
        self._action()

    def is_finished(self) -> bool:
        return True

class RunCommand(Command):
    """Calls an action every tick. Runs until interrupted"""

    def __init__(self,
                 action: Callable[[], None],
                 *requirements: Subsystem) -> None:
        super().__init__()
        self._action = action
        self.add_requirements(*requirements)

    def execute(self) -> None:
        self._action()

    def is_finished(self) -> bool:
        return False

class StartEndCommand(Command):
    """Runs an action on start and one on end"""

    def __init__(self,
                 on_start: Callable[[], None],
                 on_end: Callable[[], None],
                 *requirements: Subsystem) -> None:
        super().__init__()
        self._on_start = on_start
        self._on_end = on_end
        self.add_requirements(*requirements)

    def initialize(self) -> None:
        self._on_start()

    def end(self, interrupted: bool) -> None:
        self._on_end()

    def is_finished(self) -> bool:
        return False

class WaitCommand(Command):
    """Finishes after a certain number of seconds"""

    def __init__(self, seconds: float) -> None:
        super().__init__()
        self._seconds = seconds
        self._start: Optional[float] = None

    def initialize(self) -> None:
        self._start = time.monotonic()

    def is_finished(self) -> bool:
        return self._start is not None and (time.monotonic() - self._start) >= self._seconds

    def runs_when_disabled() -> bool: return True

class WaitUntilCommand(Command):
    """Finishes as soon as a condition becomes True"""

    def __init__(self, condition: Callable[[], bool]) -> None:
        super().__init__()
        self._condition = condition

    def is_finished(self) -> bool:
        return self._condition()

    def runs_when_disabled() -> bool: return True

class PrintCommand(InstantCommand):
    """Prints a message then finishes immediately"""

    def __init__(self, message: str) -> None:
        super().__init__(lambda: print(message))