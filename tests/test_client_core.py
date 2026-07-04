import asyncio
import json

import pytest

from client.commands import (
    CommandParseError,
    CommandKind,
    broadcast_command,
    parse_user_command,
)
from client.controller import ChatClientController
from client.events import ClientStatus, ViewEventKind
from client.presenter import ChatPresenter
from client.session import ChatSession
from shared.protocol import (
    MessageScope,
    ServerEvent,
    encode_message,
    server_message,
    server_welcome,
)


class FakeTransport:
    def __init__(self, incoming=None):
        self.connected = False
        self.closed = False
        self.sent = []
        self._incoming = list(incoming or [])

    async def connect(self):
        self.connected = True

    async def send(self, payload: str):
        self.sent.append(payload)

    async def incoming(self):
        for payload in self._incoming:
            yield payload

    async def close(self):
        self.closed = True


class FailingTransport(FakeTransport):
    async def connect(self):
        raise ConnectionRefusedError("connection refused")


@pytest.mark.asyncio
async def test_session_serializes_client_messages_with_shared_protocol():
    transport = FakeTransport()
    session = ChatSession(transport)

    await session.connect()
    await session.join("alice")
    await session.broadcast("hello")
    await session.unicast("bob", "private")
    await session.leave()

    assert transport.connected is True
    assert [json.loads(payload) for payload in transport.sent] == [
        {"action": "join", "username": "alice"},
        {"action": "broadcast", "text": "hello"},
        {"action": "unicast", "to": "bob", "text": "private"},
        {"action": "leave"},
    ]


@pytest.mark.asyncio
async def test_session_deserializes_server_messages_with_shared_protocol():
    raw_message = encode_message(
        server_message(
            scope=MessageScope.BROADCAST,
            from_username="alice",
            text="hello",
        )
    )
    session = ChatSession(FakeTransport(incoming=[raw_message]))

    messages = [message async for message in session.listen()]

    assert len(messages) == 1
    assert messages[0].event is ServerEvent.MESSAGE
    assert messages[0].from_username == "alice"
    assert messages[0].text == "hello"


def test_command_parser_supports_broadcast_unicast_and_leave():
    assert parse_user_command("hello").kind is CommandKind.BROADCAST

    private = parse_user_command("[bob]: hello")
    assert private.kind is CommandKind.UNICAST
    assert private.recipient == "bob"
    assert private.text == "hello"

    assert parse_user_command("/logout").kind is CommandKind.LEAVE


def test_command_parser_rejects_empty_input():
    with pytest.raises(CommandParseError):
        parse_user_command("   ")


def test_command_parser_rejects_invalid_private_messages():
    with pytest.raises(CommandParseError):
        parse_user_command("[bob] hello")

    with pytest.raises(CommandParseError):
        parse_user_command("[]: hello")

    with pytest.raises(CommandParseError):
        parse_user_command("[bob]:   ")


def test_presenter_maps_protocol_messages_to_ui_events():
    presenter = ChatPresenter()

    events = presenter.present(server_welcome("alice", ["alice", "bob"]))

    assert events[0].kind is ViewEventKind.INFO
    assert events[0].text == "Connected as alice"
    assert events[1].kind is ViewEventKind.USERS
    assert events[1].users == ("alice", "bob")


@pytest.mark.asyncio
async def test_chat_client_controller_uses_session_and_emits_presented_events():
    raw_message = encode_message(server_welcome("alice", ["alice"]))
    transport = FakeTransport(incoming=[raw_message])
    events = []
    statuses = []

    async def on_event(event):
        events.append(event)

    async def on_status(status):
        statuses.append(status)

    controller = ChatClientController(
        ChatSession(transport),
        on_event=on_event,
        on_status=on_status,
    )

    await controller.start("alice")
    await controller.submit(broadcast_command("hello"))
    await asyncio.sleep(0)
    await controller.stop(send_leave=False)

    assert statuses[:2] == [ClientStatus.CONNECTING, ClientStatus.CONNECTED]
    assert json.loads(transport.sent[0]) == {"action": "join", "username": "alice"}
    assert events[0].text == "Connected as alice"
    assert transport.closed is True


@pytest.mark.asyncio
async def test_chat_client_controller_returns_to_disconnected_when_start_fails():
    transport = FailingTransport()
    statuses = []

    async def on_status(status):
        statuses.append(status)

    controller = ChatClientController(
        ChatSession(transport),
        on_status=on_status,
    )

    with pytest.raises(ConnectionRefusedError):
        await controller.start("alice")

    assert controller.status is ClientStatus.DISCONNECTED
    assert transport.closed is True
    assert statuses == [ClientStatus.CONNECTING, ClientStatus.DISCONNECTED]
