"""Websocket endpoint implementation."""

from __future__ import annotations

import logging

from websockets.asyncio.server import ServerConnection
from websockets.exceptions import ConnectionClosed

from server.chat_service import ChatService
from shared.protocol import (
    ClientAction,
    ErrorCode,
    ProtocolError,
    decode_client_message,
    encode_message,
    server_error,
)

logger = logging.getLogger(__name__)


class ChatWebSocketHandler:
    """Translates websocket frames into chat service calls."""

    def __init__(self, chat_service: ChatService) -> None:
        self._chat_service = chat_service

    async def __call__(self, connection: ServerConnection) -> None:
        username: str | None = None

        try:
            async for raw_message in connection:
                if not isinstance(raw_message, str):
                    await connection.send(
                        encode_message(
                            server_error(
                                ErrorCode.BAD_REQUEST, "Payload must be a text frame"
                            )
                        )
                    )
                    continue

                try:
                    message = decode_client_message(raw_message)
                except ProtocolError as exc:
                    await connection.send(
                        encode_message(server_error(exc.code, exc.message))
                    )
                    continue

                if message.action is ClientAction.JOIN:
                    if username is not None:
                        await connection.send(
                            encode_message(
                                server_error(ErrorCode.BAD_REQUEST, "Already joined")
                            )
                        )
                        continue
                    joined = await self._chat_service.join(
                        message.username or "", connection
                    )
                    if joined:
                        username = message.username
                    continue

                if username is None:
                    await self._chat_service.reject_unauthenticated(connection)
                    continue

                if message.action is ClientAction.BROADCAST:
                    await self._chat_service.broadcast(username, message.text or "")
                elif message.action is ClientAction.UNICAST:
                    await self._chat_service.unicast(
                        username, message.to or "", message.text or ""
                    )
                elif message.action is ClientAction.LEAVE:
                    break
        except ConnectionClosed:
            logger.debug("Websocket connection closed")
        finally:
            if username is not None:
                await self._chat_service.leave(username)
