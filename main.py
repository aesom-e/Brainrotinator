import argparse
from dotenv import load_dotenv
import client
import server

def main() -> int | None:
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("-client", action="store_true")
    parser.add_argument("-server", action="store_true")
    args = parser.parse_args()

    if args.client: client.run()
    else:           server.run()

if __name__ == "__main__": exit(main())