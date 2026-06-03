import os
import argparse
from dotenv import load_dotenv
from connection import BTClient, BTServer

def main() -> int | None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("-client", action="store_true")
    parser.add_argument("-server", action="store_true")
    args = parser.parse_args()

    if args.client:
        mac = os.getenv("SERVER_MAC")
        bt = BTClient(mac)
    else:
        bt = BTServer()
        bt.start()

if __name__ == "__main__": exit(main())