from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional, Set
from .command import Command, InterruptionBehaviour

if TYPE_CHECKING: from .subsystem import Subsystem

class CommandScheduler:
    _instance: Optional["CommandScheduler"] = None

    @classmethod
    def get_instance(cls) -> "CommandScheduler":
        if cls._instance is None: cls._instance = CommandScheduler()
        return cls._instance

    def __init__(self) -> None:
        self._scheduled: Set[Command] = set()
        self._requirements: Dict[Subsystem, Command] = {}
        self._subsystems: Set[Subsystem] = set()
        self._pending_schedule: List[Command] = []
        self._pending_cancel: List[Command] = []
        self._disabled: bool = False

    def register_subsystem(self, *subsystems: Subsystem) -> None:
        self._subsystems.update(subsystems)

    def schedule(self, *commands: Command) -> None:
        self._pending_schedule.extend(commands)

    def cancel(self, *commands: Command) -> None:
        self._pending_cancel.extend(commands)

    def cancel_all(self) -> None:
        for command in list(self._scheduled): self._cancel_now(command, interrupted=True)

    def _schedule_now(self, command: Command) -> None:
        if command in self._scheduled: return

        if self._disabled and not command.run_when_disabled(): return

        conflicting: Set[Command] = set()
        for req in command.requirements:
            current = self._requirements.get(req)
            if current is not None: conflicting.add(current)

        for existing in conflicting:
            if existing.interruption_behaviour is InterruptionBehaviour.CANCEL_INCOMING:
                return
            self._cancel_now(command, interrupted=True)

        command.initialize()
        self._scheduled.add(command)
        for req in command.requirements: self._requirements[req] = command

    def _cancel_now(self, command: Command, *, interrupted: bool) -> None:
        if command not in self._scheduled: return

        command.end(interrupted)
        self._scheduled.discard(command)
        for req in command.requirements:
            if self._requirements.get(req) is command:
                del self._requirements[req]

    def run(self) -> None:
        # 1. Subsystem periodics
        for subsystem in self._subsystems:
            subsystem.periodic()

        # 2. Execute all running commands and collect the finished ones
        finished: List[Command] = []
        for command in list(self._scheduled):
            command.execute()
            if command.is_finished(): finished.append(command)

        # 3. End finished commands
        for command in finished: self._cancel_now(command, interrupted=False)

        # 4. Schedule default commands for unoccupied subsystems
        for subsystem in self._subsystems:
            if subsystem.default_command is not None and subsystem not in self._requirements:
                self._schedule_now(subsystem.default_command)

        # 5. Flush pending cancels
        for command in self._pending_cancel:
            self._cancel_now(command, interrupted=True)
        self._pending_cancel.clear()

    def is_scheduled(self, *commands: Command) -> bool:
        return all(c in self._scheduled for c in commands)

    def requiring(self, subsystem: Subsystem) -> Optional[Command]:
        return self._requirements.get(subsystem)

    @property
    def scheduled_commands(self) -> FrozenSet[Command]:
        return frozenset(self._scheduled)

    @property
    def disabled(self) -> bool:
        return self._disabled

    @disabled.setter
    def disabled(self, value: bool) -> None:
        self._disabled = value