import argparse
import asyncio
import client
import server

def main() -> int | None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-client", action="store_true")
    parser.add_argument("-server", action="store_true")
    args = parser.parse_args()

    if args.client: asyncio.run(client.run())
    else:           asyncio.run(server.run())

if __name__ == "__main__": exit(main())