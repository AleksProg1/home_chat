"""Command-line chat client."""

from __future__ import annotations

import argparse
import asyncio
from contextlib import suppress

from client.commands import CommandParseError, parse_user_command
from client.config import ClientConfig
from client.controller import ChatClientController
from client.events import ClientStatus, ViewEvent, ViewEventKind
from client.session import ChatSession
from client.transport import WebSocketChatTransport

EXIT_COMMANDS = {"/quit", "/exit"}


class ConsoleView:
    async def show_event(self, event: ViewEvent) -> None:
        if event.kind is ViewEventKind.USERS:
            print(f"users: {event.text}")
        elif event.kind is ViewEventKind.ERROR:
            print(f"error: {event.text}")
        elif event.kind is ViewEventKind.DISCONNECTED:
            print(f"disconnected: {event.text}")
        else:
            print(event.text)

    async def show_status(self, status: ClientStatus) -> None:
        print(f"status: {status.value}")

    async def show_local_error(self, message: str) -> None:
        print(f"error: {message}")


async def run_cli(server_uri: str) -> None:
    view = ConsoleView()

    while True:
        username = await _prompt_username()
        if username is None:
            return

        should_exit = await _run_chat_session(server_uri, username, view)
        if should_exit:
            return


async def _prompt_username() -> str | None:
    while True:
        try:
            username = (await asyncio.to_thread(input, "Please enter your username: ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return None

        if username in EXIT_COMMANDS:
            return None
        if username:
            return username
        print("error: username is required")


async def _run_chat_session(server_uri: str, username: str, view: ConsoleView) -> bool:
    session = ChatSession(WebSocketChatTransport(server_uri))
    controller = ChatClientController(
        session=session,
        on_event=view.show_event,
        on_status=view.show_status,
    )

    try:
        try:
            await controller.start(username)
        except OSError as exc:
            await view.show_local_error(
                f"Cannot connect to {server_uri}: {exc}. Start the server first."
            )
            return False

        print(
            "Commands:\n"
            "[username]: message for unicast\n"
            "message for broadcast\n"
            "/logout to log out\n"
            "/quit or /exit to exit."
        )

        while controller.status is ClientStatus.CONNECTED:
            raw_command = await asyncio.to_thread(input, f"{username}> ")
            if raw_command.strip() in EXIT_COMMANDS:
                return True

            try:
                command = parse_user_command(raw_command)
            except CommandParseError as exc:
                await view.show_local_error(str(exc))
                continue

            await controller.submit(command)
            if controller.status is ClientStatus.DISCONNECTED:
                print("logged out")
                return False
    except (EOFError, KeyboardInterrupt):
        print()
        return True
    finally:
        with suppress(Exception):
            await controller.stop(
                send_leave=controller.status is ClientStatus.CONNECTED
            )

    return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WebSocket chat CLI client")
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
