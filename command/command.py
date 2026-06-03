from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Set

if TYPE_CHECKING: from .subsystem import Subsystem

class InterruptionBehaviour(Enum):
    CANCEL_SELF = auto()
    CANCEL_INCOMING = auto()

class Command(ABC):
    def __init__(self) -> None:
        self._requirements: Set[Subsystem] = set()

    def __repr__(self) -> str:
        return self.__class__.__name__

    def initialize(self) -> None: pass
    def execute(self) -> None: pass
    def end(self, interrupted: bool) -> None: pass

    @abstractmethod
    def is_finished(self) -> bool: ...

    @property
    def requirements(self) -> Set[Subsystem]: return self._requirements

    def add_requirements(self, *subsystems: Subsystem) -> None:
        self._requirements.update(subsystems)

    @property
    def interruption_behaviour(self) -> InterruptionBehaviour:
        return InterruptionBehaviour.CANCEL_SELF

    @staticmethod
    def runs_when_disabled() -> bool: return False