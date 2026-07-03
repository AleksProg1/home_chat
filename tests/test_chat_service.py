import json

import pytest

from server.chat_service import ChatService
from server.connection import ConnectionRegistry
from shared.protocol import ErrorCode, ServerEvent


class FakeConnection:
    def __init__(self):
        self.sent = []

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))


@pytest.fixture
def chat_service():
    return ChatService(ConnectionRegistry())


@pytest.mark.asyncio
async def test_join_sends_welcome_and_notifies_existing_users(chat_service):
    alice = FakeConnection()
    bob = FakeConnection()

    assert await chat_service.join("alice", alice) is True
    assert await chat_service.join("bob", bob) is True

    assert alice.sent[0] == {
        "event": "welcome",
        "username": "alice",
        "users": ["alice"],
    }
    assert alice.sent[1] == {
        "event": "user_joined",
        "username": "bob",
        "users": ["alice", "bob"],
    }
    assert bob.sent[0] == {
        "event": "welcome",
        "username": "bob",
        "users": ["alice", "bob"],
    }


@pytest.mark.asyncio
async def test_duplicate_username_is_rejected(chat_service):
    first = FakeConnection()
    second = FakeConnection()

    assert await chat_service.join("alice", first) is True
    assert await chat_service.join("alice", second) is False

    assert second.sent == [
        {
            "event": "error",
            "code": ErrorCode.USERNAME_TAKEN,
            "message": "Username is already connected",
        }
    ]


@pytest.mark.asyncio
async def test_broadcast_delivers_message_to_room(chat_service):
    alice = FakeConnection()
    bob = FakeConnection()
    await chat_service.join("alice", alice)
    await chat_service.join("bob", bob)

    await chat_service.broadcast("alice", "hello")

    assert alice.sent[-1] == {
        "event": "message",
        "scope": "broadcast",
        "from": "alice",
        "text": "hello",
    }
    assert bob.sent[-1] == alice.sent[-1]


@pytest.mark.asyncio
async def test_unicast_delivers_to_recipient_and_acks_sender(chat_service):
    alice = FakeConnection()
    bob = FakeConnection()
    await chat_service.join("alice", alice)
    await chat_service.join("bob", bob)

    await chat_service.unicast("alice", "bob", "private")

    assert bob.sent[-1] == {
        "event": "message",
        "scope": "unicast",
        "from": "alice",
        "to": "bob",
        "text": "private",
    }
    assert alice.sent[-1] == {
        "event": "ack",
        "message": "Message delivered to 'bob'",
    }


@pytest.mark.asyncio
async def test_unicast_to_missing_user_reports_error_to_sender(chat_service):
    alice = FakeConnection()
    await chat_service.join("alice", alice)

    await chat_service.unicast("alice", "bob", "private")

    assert alice.sent[-1] == {
        "event": "error",
        "code": ErrorCode.USER_NOT_FOUND,
        "message": "User 'bob' is not connected",
    }


@pytest.mark.asyncio
async def test_reject_unauthenticated(chat_service):
    connection = FakeConnection()

    await chat_service.reject_unauthenticated(connection)

    assert connection.sent == [
        {
            "event": ServerEvent.ERROR,
            "code": ErrorCode.NOT_AUTHENTICATED,
            "message": "Send 'join' before chat messages",
        }
    ]
