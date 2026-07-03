"""Shared websocket transport for all chat clients."""

from __future__ import annotations

from types import TracebackType
from typing import AsyncIterator, Protocol

from websockets.asyncio.client import ClientConnection, connect


class ChatTransport(Protocol):
    async def connect(self) -> None:
        """Open the underlying network connection."""

    async def send(self, payload: str) -> None:
        """Send an already serialized protocol payload."""

    def incoming(self) -> AsyncIterator[str]:
        """Iterate over incoming text payloads."""

    async def close(self) -> None:
        """Close the underlying network connection."""


class WebSocketChatTransport:
    """WebSocket implementation hidden behind the transport port."""

    def __init__(self, uri: str) -> None:
        self._uri = uri
        self._connection_context = None
        self._connection: ClientConnection | None = None

    async def __aenter__(self) -> "WebSocketChatTransport":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def connect(self) -> None:
        if self._connection is not None:
            return

        connection_context = connect(self._uri)
        try:
            self._connection = await connection_context.__aenter__()
        except Exception:
            self._connection_context = None
            self._connection = None
            raise

        self._connection_context = connection_context

    async def send(self, payload: str) -> None:
        if self._connection is None:
            raise RuntimeError("Chat transport is not connected")
        await self._connection.send(payload)

    async def incoming(self) -> AsyncIterator[str]:
        if self._connection is None:
            raise RuntimeError("Chat transport is not connected")
        async for payload in self._connection:
            if isinstance(payload, str):
                yield payload

    async def close(self) -> None:
        if self._connection_context is None:
            self._connection = None
            return

        try:
            await self._connection_context.__aexit__(None, None, None)
        finally:
            self._connection_context = None
            self._connection = None
