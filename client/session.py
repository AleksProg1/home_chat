"""Protocol-aware chat session shared by CLI and GUI."""

from __future__ import annotations

from typing import AsyncIterator

from client.transport import ChatTransport
from shared.protocol import (
    ServerMessage,
    client_broadcast,
    client_join,
    client_leave,
    client_unicast,
    decode_server_message,
    encode_message,
)


class ChatSession:
    """High-level client API that owns protocol serialization boundaries."""

    def __init__(self, transport: ChatTransport) -> None:
        self._transport = transport

    async def connect(self) -> None:
        await self._transport.connect()

    async def join(self, username: str) -> None:
        await self._send_protocol_message(client_join(username))

    async def broadcast(self, text: str) -> None:
        await self._send_protocol_message(client_broadcast(text))

    async def unicast(self, to: str, text: str) -> None:
        await self._send_protocol_message(client_unicast(to, text))

    async def leave(self) -> None:
        await self._send_protocol_message(client_leave())

    async def listen(self) -> AsyncIterator[ServerMessage]:
        async for raw_message in self._transport.incoming():
            yield decode_server_message(raw_message)

    async def close(self) -> None:
        await self._transport.close()

    async def _send_protocol_message(self, message: object) -> None:
        await self._transport.send(encode_message(message))
