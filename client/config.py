"""Client runtime configuration."""

from __future__ import annotations

from dataclasses import dataclass
import os

DEFAULT_SERVER_URI = "ws://127.0.0.1:8765"


@dataclass(frozen=True)
class ClientConfig:
    server_uri: str = DEFAULT_SERVER_URI

    @classmethod
    def from_env(cls) -> "ClientConfig":
        return cls(server_uri=os.getenv("CHAT_SERVER_URI", DEFAULT_SERVER_URI))
