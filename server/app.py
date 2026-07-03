"""Application factory and executable entrypoint."""

from __future__ import annotations

import asyncio
import logging

from websockets.asyncio.server import serve

from server.chat_service import ChatService
from server.config import ServerConfig
from server.connection import ConnectionRegistry
from server.ws_handler import ChatWebSocketHandler


def create_handler() -> ChatWebSocketHandler:
    registry = ConnectionRegistry()
    chat_service = ChatService(registry)
    return ChatWebSocketHandler(chat_service)


async def run_server(config: ServerConfig | None = None) -> None:
    resolved_config = config or ServerConfig.from_env()
    handler = create_handler()
    async with serve(handler, resolved_config.host, resolved_config.port):
        logging.info(
            "Chat server is listening on ws://%s:%s",
            resolved_config.host,
            resolved_config.port,
        )
        await asyncio.Future()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
