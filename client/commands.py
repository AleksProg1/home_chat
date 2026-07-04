"""Common user command model and parser."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CommandKind(StrEnum):
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    LEAVE = "leave"


@dataclass(frozen=True)
class UserCommand:
    kind: CommandKind
    text: str | None = None
    recipient: str | None = None


def broadcast_command(text: str) -> UserCommand:
    return UserCommand(kind=CommandKind.BROADCAST, text=text)


def unicast_command(to: str, text: str) -> UserCommand:
    return UserCommand(kind=CommandKind.UNICAST, recipient=to, text=text)


def leave_command() -> UserCommand:
    return UserCommand(kind=CommandKind.LEAVE)


class CommandParseError(ValueError):
    """Raised when a user-facing command cannot be converted to a client action."""


def parse_user_command(raw_text: str) -> UserCommand:
    text = raw_text.strip()
    if not text:
        raise CommandParseError("Message cannot be empty")

    if text in {"/logout", "/leave"}:
        return leave_command()

    private_command = _parse_private_command(text)
    if private_command is not None:
        return private_command

    return broadcast_command(text)


def _parse_private_command(text: str) -> UserCommand | None:
    if not text.startswith("["):
        return None

    separator = text.find("]:")
    if separator == -1:
        raise CommandParseError("Use [username]: message for private messages")

    username = text[1:separator].strip()
    message = text[separator + 2 :].strip()

    if not username:
        raise CommandParseError("Private message username cannot be empty")
    if not message:
        raise CommandParseError("Private message text cannot be empty")

    return unicast_command(username, message)
