"""Chat client application controller shared by CLI and GUI adapters."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress

from client.commands import UserCommand, UserCommandKind
from client.events import ClientStatus, ViewEvent
from client.presenter import ChatPresenter
from client.session import ChatSession

ViewEventHandler = Callable[[ViewEvent], Awaitable[None]]
StatusHandler = Callable[[ClientStatus], Awaitable[None]]


async def noop_view_handler(event: ViewEvent) -> None:
    return None


async def noop_status_handler(status: ClientStatus) -> None:
    return None


class ChatClientController:
    """Coordinates session lifecycle and exposes UI-friendly operations."""

    def __init__(
        self,
        session: ChatSession,
        presenter: ChatPresenter | None = None,
        on_event: ViewEventHandler = noop_view_handler,
        on_status: StatusHandler = noop_status_handler,
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
        if command.kind is UserCommandKind.BROADCAST:
            await self._session.broadcast(command.text or "")
        elif command.kind is UserCommandKind.UNICAST:
            await self._session.unicast(command.to or "", command.text or "")
        elif command.kind is UserCommandKind.LEAVE:
            await self.stop(send_leave=True)

    async def stop(self, send_leave: bool = True) -> None:
        if send_leave and self._status is ClientStatus.CONNECTED:
            with suppress(Exception):
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
                    await self._on_event(event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            await self._on_event(self._presenter.disconnected(str(exc)))
        finally:
            await self._set_status(ClientStatus.DISCONNECTED)

    async def _set_status(self, status: ClientStatus) -> None:
        if self._status is status:
            return
        self._status = status
        await self._on_status(status)
