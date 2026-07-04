"""Maps protocol messages into UI-neutral view events."""

from __future__ import annotations

from client.events import ViewEvent, ViewEventKind
from shared.protocol import MessageScope, ServerEvent, ServerMessage


class ChatPresenter:
    """Keeps server-message interpretation out of CLI and GUI code."""

    def present(self, message: ServerMessage) -> list[ViewEvent]:
        if message.event == ServerEvent.WELCOME:
            return [
                ViewEvent(
                    kind=ViewEventKind.INFO,
                    text=f"Connected as {message.username}",
                    users=tuple(message.users or ()),
                ),
                self._users_event(message.users),
            ]

        if message.event == ServerEvent.USER_JOINED:
            return [
                ViewEvent(
                    kind=ViewEventKind.INFO,
                    text=f"{message.username} joined",
                    users=tuple(message.users or ()),
                ),
                self._users_event(message.users),
            ]

        if message.event == ServerEvent.USER_LEFT:
            return [
                ViewEvent(
                    kind=ViewEventKind.INFO,
                    text=f"{message.username} left",
                    users=tuple(message.users or ()),
                ),
                self._users_event(message.users),
            ]

        if message.event == ServerEvent.USER_LIST:
            return [self._users_event(message.users)]

        if message.event == ServerEvent.MESSAGE:
            return [self._message_event(message)]

        if message.event == ServerEvent.ACK:
            return [ViewEvent(kind=ViewEventKind.INFO, text=message.message or "OK")]

        if message.event == ServerEvent.ERROR:
            return [
                ViewEvent(
                    kind=ViewEventKind.ERROR,
                    text=message.message or "Server returned an error",
                )
            ]

        return [ViewEvent(kind=ViewEventKind.INFO, text=str(message.event))]

    def disconnected(self, reason: str = "Disconnected") -> ViewEvent:
        return ViewEvent(kind=ViewEventKind.DISCONNECTED, text=reason)

    def _message_event(self, message: ServerMessage) -> ViewEvent:
        sender = message.from_username or "unknown"
        text = message.text or ""
        is_private = message.scope is MessageScope.UNICAST
        prefix = f"[private] {sender}" if is_private else sender
        return ViewEvent(
            kind=ViewEventKind.MESSAGE,
            text=f"{prefix}: {text}",
            from_username=message.from_username,
            to=message.to,
            is_private=is_private,
        )

    def _users_event(self, users: list[str] | None) -> ViewEvent:
        resolved_users = tuple(users or ())
        return ViewEvent(
            kind=ViewEventKind.USERS,
            text=", ".join(resolved_users) if resolved_users else "No users online",
            users=resolved_users,
        )
