"""Runtime configuration for the websocket chat server."""

from __future__ import annotations

from dataclasses import dataclass
import os

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


@dataclass(frozen=True, slots=True)
class ServerConfig:
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT

    @classmethod
    def from_env(cls) -> "ServerConfig":
        return cls(
            host=os.getenv("CHAT_HOST", DEFAULT_HOST),
            port=int(os.getenv("CHAT_PORT", str(DEFAULT_PORT))),
        )
