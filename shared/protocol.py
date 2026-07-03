"""JSON protocol shared by the chat server and future clients.

Client -> server messages:
    {"action": "join", "username": "alice"}
    {"action": "broadcast", "text": "Hello everyone"}
    {"action": "unicast", "to": "bob", "text": "Hi Bob"}
    {"action": "leave"}

Server -> client messages:
    {"event": "welcome", "username": "alice", "users": ["alice"]}
    {"event": "message", "scope": "broadcast", "from": "alice", "text": "..."}
    {"event": "message", "scope": "unicast", "from": "alice", "to": "bob", "text": "..."}
    {"event": "error", "code": "bad_request", "message": "..."}
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
import json
from typing import Any


class ProtocolError(ValueError):
    """Raised when a websocket payload does not match the chat protocol."""

    def __init__(self, message: str, code: "ErrorCode" = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or ErrorCode.BAD_REQUEST


class ClientAction(StrEnum):
    JOIN = "join"
    BROADCAST = "broadcast"
    UNICAST = "unicast"
    LEAVE = "leave"


class ServerEvent(StrEnum):
    ACK = "ack"
    WELCOME = "welcome"
    MESSAGE = "message"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_LIST = "user_list"
    ERROR = "error"


class MessageScope(StrEnum):
    BROADCAST = "broadcast"
    UNICAST = "unicast"


class ErrorCode(StrEnum):
    BAD_REQUEST = "bad_request"
    NOT_AUTHENTICATED = "not_authenticated"
    USERNAME_TAKEN = "username_taken"
    USER_NOT_FOUND = "user_not_found"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True, slots=True)
class ClientMessage:
    action: ClientAction
    username: str | None = None
    to: str | None = None
    text: str | None = None


@dataclass(frozen=True, slots=True)
class ServerMessage:
    event: ServerEvent
    code: ErrorCode | None = None
    message: str | None = None
    scope: MessageScope | None = None
    username: str | None = None
    users: list[str] | None = None
    from_username: str | None = None
    to: str | None = None
    text: str | None = None


def client_join(username: str) -> ClientMessage:
    return ClientMessage(action=ClientAction.JOIN, username=username)


def client_broadcast(text: str) -> ClientMessage:
    return ClientMessage(action=ClientAction.BROADCAST, text=text)


def client_unicast(to: str, text: str) -> ClientMessage:
    return ClientMessage(action=ClientAction.UNICAST, to=to, text=text)


def client_leave() -> ClientMessage:
    return ClientMessage(action=ClientAction.LEAVE)


def server_ack(message: str) -> ServerMessage:
    return ServerMessage(event=ServerEvent.ACK, message=message)


def server_welcome(username: str, users: list[str]) -> ServerMessage:
    return ServerMessage(event=ServerEvent.WELCOME, username=username, users=users)


def server_message(
    *,
    scope: MessageScope,
    from_username: str,
    text: str,
    to: str | None = None,
) -> ServerMessage:
    return ServerMessage(
        event=ServerEvent.MESSAGE,
        scope=scope,
        from_username=from_username,
        to=to,
        text=text,
    )


def server_user_joined(username: str, users: list[str]) -> ServerMessage:
    return ServerMessage(
        event=ServerEvent.USER_JOINED,
        username=username,
        users=users,
    )


def server_user_left(username: str, users: list[str]) -> ServerMessage:
    return ServerMessage(
        event=ServerEvent.USER_LEFT,
        username=username,
        users=users,
    )


def server_user_list(users: list[str]) -> ServerMessage:
    return ServerMessage(event=ServerEvent.USER_LIST, users=users)


def server_error(code: ErrorCode, message: str) -> ServerMessage:
    return ServerMessage(event=ServerEvent.ERROR, code=code, message=message)


def encode_message(message: ClientMessage | ServerMessage) -> str:
    payload = _drop_empty(asdict(message))
    if isinstance(message, ServerMessage) and message.from_username is not None:
        payload["from"] = payload.pop("from_username")
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def decode_client_message(raw_message: str) -> ClientMessage:
    payload = _decode_json_object(raw_message)
    action = _parse_enum(payload.get("action"), ClientAction, "action")

    if action is ClientAction.JOIN:
        return ClientMessage(
            action=action, username=_required_text(payload, "username")
        )
    if action is ClientAction.BROADCAST:
        return ClientMessage(action=action, text=_required_text(payload, "text"))
    if action is ClientAction.UNICAST:
        return ClientMessage(
            action=action,
            to=_required_text(payload, "to"),
            text=_required_text(payload, "text"),
        )
    if action is ClientAction.LEAVE:
        return ClientMessage(action=action)

    raise ProtocolError("Unsupported client action")


def decode_server_message(raw_message: str) -> ServerMessage:
    payload = _decode_json_object(raw_message)
    event = _parse_enum(payload.get("event"), ServerEvent, "event")
    code = _optional_enum(payload.get("code"), ErrorCode, "code")
    scope = _optional_enum(payload.get("scope"), MessageScope, "scope")
    return ServerMessage(
        event=event,
        code=code,
        message=_optional_text(payload, "message"),
        scope=scope,
        username=_optional_text(payload, "username"),
        users=_optional_string_list(payload, "users"),
        from_username=_optional_text(payload, "from"),
        to=_optional_text(payload, "to"),
        text=_optional_text(payload, "text"),
    )


def _decode_json_object(raw_message: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError as exc:
        raise ProtocolError("Payload must be valid JSON") from exc

    if not isinstance(payload, dict):
        raise ProtocolError("Payload must be a JSON object")
    return payload


def _parse_enum(value: Any, enum_type: type[StrEnum], field_name: str) -> StrEnum:
    if not isinstance(value, str):
        raise ProtocolError(f"Field '{field_name}' is required")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise ProtocolError(f"Field '{field_name}' has unsupported value") from exc


def _optional_enum(
    value: Any,
    enum_type: type[StrEnum],
    field_name: str,
) -> StrEnum | None:
    if value is None:
        return None
    return _parse_enum(value, enum_type, field_name)


def _required_text(payload: dict[str, Any], field_name: str) -> str:
    value = _optional_text(payload, field_name)
    if value is None:
        raise ProtocolError(f"Field '{field_name}' is required")
    if not value.strip():
        raise ProtocolError(f"Field '{field_name}' cannot be empty")
    return value.strip()


def _optional_text(payload: dict[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ProtocolError(f"Field '{field_name}' must be a string")
    return value


def _optional_string_list(payload: dict[str, Any], field_name: str) -> list[str] | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ProtocolError(f"Field '{field_name}' must be a list of strings")
    return value


def _drop_empty(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value is not None}
