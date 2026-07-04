"""Chat client application controller shared by CLI and GUI adapters."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress

from client.commands import UserCommand, CommandKind
from client.events import ClientStatus, ViewEvent
from client.presenter import ChatPresenter
from client.session import ChatSession

logger = logging.getLogger(__name__)

ViewEventHandler = Callable[[ViewEvent], Awaitable[None]]
StatusHandler = Callable[[ClientStatus], Awaitable[None]]


class ChatClientController:
    """Coordinates session lifecycle and exposes UI-friendly operations."""

    def __init__(
        self,
        session: ChatSession,
        presenter: ChatPresenter | None = None,
        on_event: ViewEventHandler | None = None,
        on_status: StatusHandler | None = None,
    ) -> None:
        self._session = session
        self._presenter = presenter or ChatPresenter()
        self._on_event = on_event
        self._on_status = on_status
        self._listen_task: asyncio.Task[None] | None = None
        self._status = ClientStatus.DISCONNECTED

    @property
    def status(self) -> ClientStatus:
        return self._status

    async def start(self, username: str) -> None:
        await self._set_status(ClientStatus.CONNECTING)

        try:
            await self._session.connect()
            await self._session.join(username)
        except Exception:
            await self._session.close()
            await self._set_status(ClientStatus.DISCONNECTED)
            raise

        await self._set_status(ClientStatus.CONNECTED)
        self._listen_task = asyncio.create_task(self._listen())

    async def submit(self, command: UserCommand) -> None:
        kind = command.kind

        if kind == CommandKind.BROADCAST:
            if command.text is None:
                return
            await self._session.broadcast(command.text)
            return

        if kind == CommandKind.UNICAST:
            if command.recipient is None or command.text is None:
                return
            await self._session.unicast(command.recipient, command.text)
            return

        if kind == CommandKind.LEAVE:
            await self.stop(send_leave=True)

    async def stop(self, send_leave: bool = True) -> None:
        if send_leave and self._status == ClientStatus.CONNECTED:
            with suppress(Exception):
                # Connection may already be closed during shutdown.
                await self._session.leave()

        if self._listen_task is not None:
            self._listen_task.cancel()

            with suppress(asyncio.CancelledError):
                await self._listen_task

            self._listen_task = None

        await self._session.close()
        await self._set_status(ClientStatus.DISCONNECTED)

    async def _listen(self) -> None:
        try:
            async for message in self._session.listen():
                for event in self._presenter.present(message):
                    await self._emit_event(event)

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            logger.exception("Error while listening for server messages")
            event = self._presenter.disconnected(f"Disconnected: {exc}")
            await self._emit_event(event)

        finally:
            await self._set_status(ClientStatus.DISCONNECTED)

    async def _set_status(self, status: ClientStatus) -> None:
        if self._status == status:
            return

        self._status = status
        await self._emit_status(status)

    async def _emit_event(self, event: ViewEvent) -> None:
        if self._on_event is not None:
            await self._on_event(event)

    async def _emit_status(self, status: ClientStatus) -> None:
        if self._on_status is not None:
            await self._on_status(status)