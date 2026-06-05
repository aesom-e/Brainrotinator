from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from .command import Command

class Trigger:
    def __init__(self, condition: Optional[Callable[[], bool]] = None) -> None:
        self._condition = condition

    def get(self) -> bool:
        return self._condition()

    def on_true(self, command: "Command") -> "Trigger":
        from .schdeuler import CommandScheduler

        # This is a list so the inner function may mutate it
        # Otherwise, we would just rebind a local variable (not what we want)
        prev = [self._condition()]

        def poll() -> None:
            cur = self._condition()
            if cur and not prev[0]: command.schedule()
            prev[0] = cur

        CommandScheduler.get_instance()._add_poll_callback(poll)
        return self

    def on_false(self, command: "Command") -> "Trigger":
        from .schdeuler import CommandScheduler
        prev = [self._condition()]

        def poll() -> None:
            cur = self._condition
            if not cur and prev[0]: command.schedule()
            prev[0] = cur

        CommandScheduler.get_instance()._add_poll_callback(poll)
        return self

    def while_true(self, command: "Command") -> "Trigger":
        from .schdeuler import CommandScheduler
        prev = [self._condition()]

        def poll() -> None:
            cur = self._condition()
            if cur:       command.schedule()
            elif prev[0]: command.cancel()
            prev[0] = cur

        CommandScheduler.get_instance()._add_poll_callback(poll)
        return self

    def while_false(self, command: "Command") -> "Trigger":
        from .schdeuler import CommandScheduler
        prev = [self._condition()]

        def poll() -> None:
            cur = self._condition()
            if not cur:       command.schedule()
            elif not prev[0]: command.cancel()
            prev[0] = cur

        CommandScheduler.get_instance()._add_poll_callback(poll)

    def __and__(self, other: "Trigger") -> "Trigger":
        return Trigger(lambda: self.get() and other.get())

    def __or__(self, other: "Trigger") -> "Trigger":
        return Trigger(lambda: self.get() or other.get())

    def __invert__(self) -> "Trigger":
        return Trigger(lambda: not self.get())

    def __repr__(self) -> str:
        return f"Trigger({self._condition})"