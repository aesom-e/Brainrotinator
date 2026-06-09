from typing import Set, Callable

_CLEANUP_FUNCS: Set[Callable[[], None]] = set()

def register(func: Callable[[], None]): _CLEANUP_FUNCS.add(func)

def cleanup() -> None:
    for func in _CLEANUP_FUNCS: func()