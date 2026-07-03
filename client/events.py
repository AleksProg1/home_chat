"""UI-neutral events produced from server protocol messages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ViewEventKind(StrEnum):
    INFO = "info"
    ERROR = "error"
    MESSAGE = "message"
    USERS = "users"
    DISCONNECTED = "disconnected"


class ClientStatus(StrEnum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"


@dataclass(frozen=True, slots=True)
class ViewEvent:
    kind: ViewEventKind
    text: str
    users: tuple[str, ...] = ()
    from_username: str | None = None
    to: str | None = None
    is_private: bool = False
