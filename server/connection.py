"""Connection registry abstractions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class DuplicateUsernameError(ValueError):
    """Raised when a user tries to join with an already connected username."""


class ConnectionSender(Protocol):
    async def send(self, message: str) -> None:
        """Send a serialized message through the connection."""


@dataclass(frozen=True, slots=True)
class ChatConnection:
    username: str
    sender: ConnectionSender


class ConnectionRegistry:
    """In-memory username -> connection storage."""

    def __init__(self) -> None:
        self._connections: dict[str, ConnectionSender] = {}

    def add(self, username: str, connection: ConnectionSender) -> None:
        if username in self._connections:
            raise DuplicateUsernameError(username)
        self._connections[username] = connection

    def remove(self, username: str) -> None:
        self._connections.pop(username, None)

    def get(self, username: str) -> ConnectionSender | None:
        return self._connections.get(username)

    def usernames(self) -> list[str]:
        return sorted(self._connections)

    def all(self) -> list[ChatConnection]:
        return [
            ChatConnection(username=username, sender=sender)
            for username, sender in self._connections.items()
        ]
