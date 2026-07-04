import argparse
import asyncio

from client.config import ClientConfig
from client.cli.app import run_cli

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyQt5 WebSocket chat client")
    parser.add_argument(
        "--server",
        default=ClientConfig.from_env().server_uri,
        help="WebSocket server URI, defaults to CHAT_SERVER_URI or ws://127.0.0.1:8765",
    )
    return parser

def main() -> None:
    args = build_parser().parse_args()
    asyncio.run(run_cli(args.server))

if __name__ == "__main__":
    main()