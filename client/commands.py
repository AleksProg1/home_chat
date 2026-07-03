"""Common user command model and parser."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class UserCommandKind(StrEnum):
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    LEAVE = "leave"


@dataclass(frozen=True, slots=True)
class UserCommand:
    kind: UserCommandKind
    text: str | None = None
    to: str | None = None


def broadcast_command(text: str) -> UserCommand:
    return UserCommand(kind=UserCommandKind.BROADCAST, text=text)


def unicast_command(to: str, text: str) -> UserCommand:
    return UserCommand(kind=UserCommandKind.UNICAST, to=to, text=text)


def leave_command() -> UserCommand:
    return UserCommand(kind=UserCommandKind.LEAVE)


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

    closing_bracket_index = text.find("]:")
    if closing_bracket_index == -1:
        raise CommandParseError("Use [username]: message for private messages")

    username = text[1:closing_bracket_index].strip()
    message = text[closing_bracket_index + 2 :].strip()

    if not username:
        raise CommandParseError("Private message username cannot be empty")
    if not message:
        raise CommandParseError("Private message text cannot be empty")

    return unicast_command(username, message)
