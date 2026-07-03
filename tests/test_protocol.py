import json

import pytest

from shared.protocol import (
    ClientAction,
    ErrorCode,
    MessageScope,
    ProtocolError,
    ServerEvent,
    client_broadcast,
    client_join,
    client_unicast,
    decode_client_message,
    decode_server_message,
    encode_message,
    server_error,
    server_message,
)


def test_client_message_factories_encode_to_public_json_contract():
    assert json.loads(encode_message(client_join("alice"))) == {
        "action": "join",
        "username": "alice",
    }
    assert json.loads(encode_message(client_broadcast("hello"))) == {
        "action": "broadcast",
        "text": "hello",
    }
    assert json.loads(encode_message(client_unicast("bob", "hi"))) == {
        "action": "unicast",
        "to": "bob",
        "text": "hi",
    }


def test_server_message_uses_from_field_instead_of_internal_name():
    payload = json.loads(
        encode_message(
            server_message(
                scope=MessageScope.UNICAST,
                from_username="alice",
                to="bob",
                text="secret",
            )
        )
    )

    assert payload == {
        "event": "message",
        "scope": "unicast",
        "from": "alice",
        "to": "bob",
        "text": "secret",
    }


def test_decode_client_message_validates_required_fields():
    with pytest.raises(ProtocolError) as error:
        decode_client_message('{"action":"unicast","to":"bob"}')

    assert error.value.code is ErrorCode.BAD_REQUEST
    assert "text" in error.value.message


def test_decode_server_message_round_trip():
    raw = encode_message(server_error(ErrorCode.USER_NOT_FOUND, "missing"))

    message = decode_server_message(raw)

    assert message.event is ServerEvent.ERROR
    assert message.code is ErrorCode.USER_NOT_FOUND
    assert message.message == "missing"


def test_decode_client_message_trims_user_input():
    message = decode_client_message('{"action":"join","username":" alice "}')

    assert message.action is ClientAction.JOIN
    assert message.username == "alice"
