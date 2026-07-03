"""Chat use cases for a single-room websocket server."""

from __future__ import annotations

import logging

from server.connection import (
    ConnectionRegistry,
    ConnectionSender,
    DuplicateUsernameError,
)
from shared.protocol import (
    ErrorCode,
    MessageScope,
    ServerMessage,
    server_ack,
    server_error,
    server_message,
    server_user_joined,
    server_user_left,
    server_welcome,
    encode_message,
)

logger = logging.getLogger(__name__)


class ChatService:
    """Coordinates chat actions without depending on websocket request parsing."""

    def __init__(self, registry: ConnectionRegistry) -> None:
        self._registry = registry

    async def join(self, username: str, connection: ConnectionSender) -> bool:
        try:
            self._registry.add(username, connection)
        except DuplicateUsernameError:
            await self._send(
                connection,
                server_error(ErrorCode.USERNAME_TAKEN, "Username is already connected"),
            )
            return False

        users = self._registry.usernames()
        await self._send(connection, server_welcome(username, users))
        await self._broadcast(
            server_user_joined(username, users),
            exclude={username},
        )
        return True

    async def leave(self, username: str) -> None:
        self._registry.remove(username)
        await self._broadcast(server_user_left(username, self._registry.usernames()))

    async def broadcast(self, from_username: str, text: str) -> None:
        await self._broadcast(
            server_message(
                scope=MessageScope.BROADCAST,
                from_username=from_username,
                text=text,
            )
        )

    async def unicast(self, from_username: str, to: str, text: str) -> None:
        recipient = self._registry.get(to)
        sender = self._registry.get(from_username)

        if recipient is None:
            if sender is not None:
                await self._send(
                    sender,
                    server_error(
                        ErrorCode.USER_NOT_FOUND, f"User '{to}' is not connected"
                    ),
                )
            return

        message = server_message(
            scope=MessageScope.UNICAST,
            from_username=from_username,
            to=to,
            text=text,
        )
        await self._send(recipient, message)

        if sender is not None and sender is not recipient:
            await self._send(sender, server_ack(f"Message delivered to '{to}'"))

    async def reject_unauthenticated(self, connection: ConnectionSender) -> None:
        await self._send(
            connection,
            server_error(
                ErrorCode.NOT_AUTHENTICATED, "Send 'join' before chat messages"
            ),
        )

    async def _broadcast(
        self,
        message: ServerMessage,
        exclude: set[str] | None = None,
    ) -> None:
        excluded_users = exclude or set()
        encoded = encode_message(message)
        for chat_connection in self._registry.all():
            if chat_connection.username in excluded_users:
                continue
            try:
                await chat_connection.sender.send(encoded)
            except Exception:
                logger.exception(
                    "Failed to send message to %s", chat_connection.username
                )

    async def _send(self, connection: ConnectionSender, message: ServerMessage) -> None:
        await connection.send(encode_message(message))
