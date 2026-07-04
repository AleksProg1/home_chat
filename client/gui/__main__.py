import argparse

from client.gui.app import run_gui
from client.config import ClientConfig

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyQt5 WebSocket chat client")
    parser.add_argument(
        "--server",
        default=ClientConfig.from_env().server_uri,
        help="WebSocket server URI, defaults to CHAT_SERVER_URI or ws://127.0.0.1:8765",
    )
    return parser


def main():
    args = build_parser().parse_args()
    run_gui(args.server)

if __name__ == "__main__":
    main()