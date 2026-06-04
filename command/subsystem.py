from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING: from .command import Command

class Subsystem:
    def __init__(self) -> None:
        from .schdeuler import CommandScheduler
        CommandScheduler.get_instance().register_subsystem(self)
        self._default_command: Optional["Command"] = None

    def __repr__(self) -> str:
        return self.__class__.__name__

    def periodic(self) -> None:
        pass

    @property
    def default_command(self) -> Optional["Command"]:
        return self._default_command

    @default_command.setter
    def default_command(self, command: Optional["Command"]) -> None:
        if command is not None and self not in command.requirements:
            raise ValueError(
                f"{command} must require {self} to be its default command"
            )
        self._default_command = command

    @property
    def current_command(self) -> Optional["Command"]:
        from .schdeuler import CommandScheduler
        return CommandScheduler.get_instance().requiring(self)