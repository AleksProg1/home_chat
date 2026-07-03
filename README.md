# home_chat

Async Python websocket server and clients for a single-room chat. Users join with a unique username and can send broadcast messages to the room or unicast messages to one user.

## Install

```bash
pip install -r requirements.txt
```

## Run Server

```bash
python3 -m server.app
```

Default endpoint: `ws://127.0.0.1:8765`. Configure it with `CHAT_HOST` and `CHAT_PORT`.

## Run CLI Client

```bash
python3 -m client.cli
python3 -m client.cli --server ws://127.0.0.1:8765
```

CLI commands:

```text
login username: alice
hello room
[bob]: private hello
/logout
/quit
```

## Run GUI Client

```bash
python3 -m client.gui --server ws://127.0.0.1:8765
```

The GUI requires `PyQt5` from `requirements.txt`. It opens a login page first. After connecting, the chat page shows connected users in the left sidebar, messages in the main area, and a message input with a send button at the bottom. Select a user in the sidebar to send a private message; clear selection or select yourself to broadcast.

## Shared Protocol

The public client/server contract lives in `shared/protocol.py`. Clients import factories such as `client_join`, `client_broadcast`, `client_unicast`, `encode_message`, and `decode_server_message`. CLI and GUI do not build JSON manually and do not parse server JSON directly.

Client messages:

```json
{"action":"join","username":"alice"}
{"action":"broadcast","text":"Hello room"}
{"action":"unicast","to":"bob","text":"Hello Bob"}
{"action":"leave"}
```

Server messages:

```json
{"event":"welcome","username":"alice","users":["alice"]}
{"event":"user_joined","username":"bob","users":["alice","bob"]}
{"event":"message","scope":"broadcast","from":"alice","text":"Hello room"}
{"event":"message","scope":"unicast","from":"alice","to":"bob","text":"Hello Bob"}
{"event":"ack","message":"Message delivered to 'bob'"}
{"event":"error","code":"user_not_found","message":"User 'bob' is not connected"}
```

## Architecture

- `shared/` contains the stable JSON protocol and helper API shared by server and clients.
- `server/connection.py` owns the temporary in-memory `username -> connection` registry.
- `server/chat_service.py` contains server chat use cases and does not depend on websocket parsing.
- `server/ws_handler.py` adapts websocket frames to server service calls.
- `client/transport.py` contains the shared websocket transport for all clients.
- `client/session.py` owns client-side protocol serialization and deserialization.
- `client/controller.py` coordinates client lifecycle through UI-neutral commands and events.
- `client/presenter.py` maps server protocol messages to UI-neutral view events.
- `client/cli.py` and `client/gui.py` differ only by user interaction style.

## Tests

```bash
pytest
```
