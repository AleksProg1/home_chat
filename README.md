# home_chat

Async Python websocket server for a single-room chat. Users join with a unique username and can send broadcast messages to the room or unicast messages to one user.

## Run

```bash
pip install -r requirements.txt
python3 -m server.app
```

Default endpoint: `ws://127.0.0.1:8765`. Configure it with `CHAT_HOST` and `CHAT_PORT`.

## Shared Protocol

The public client/server contract lives in `shared/protocol.py`. A future Python client can import factories such as `client_join`, `client_broadcast`, `client_unicast`, `encode_message`, and `decode_server_message`.

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

## Design

- `shared/` contains the stable JSON protocol and helper API for clients.
- `server/connection.py` owns the temporary in-memory `username -> connection` registry.
- `server/chat_service.py` contains chat use cases and does not depend on websocket parsing.
- `server/ws_handler.py` adapts websocket frames to service calls.
- `server/app.py` wires dependencies and starts the websocket server.

## Tests

```bash
pytest
```
