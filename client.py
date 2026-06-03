import os
from typing import NoReturn
from connection import BTClient

def run() -> NoReturn:
    bt = BTClient(os.getenv("SERVER_MAC"))

    while True:
        print(bt.receive())