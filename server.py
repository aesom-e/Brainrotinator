from typing import NoReturn
from connection import BTServer

def run() -> NoReturn:
    bt = BTServer()

    i = 0
    while True:
        bt.send(str(i))
        i += 1