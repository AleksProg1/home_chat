import asyncio
import threading
from concurrent.futures import Future
from typing import Coroutine, Any

from PyQt5 import QtCore

from client.commands import broadcast_command, leave_command, unicast_command
from client.controller import ChatClientController
from client.events import ClientStatus, ViewEvent
from client.session import ChatSession
from client.transport import WebSocketChatTransport


class ClientWorker(QtCore.QObject):
    eventReceived = QtCore.pyqtSignal(object)
    statusChanged = QtCore.pyqtSignal(object)
    errorOccurred = QtCore.pyqtSignal(str)

    def __init__(self, server_uri: str) -> None:
        super().__init__()
        self._server_uri = server_uri
        self._loop: asyncio.AbstractEventLoop | None = None
        self._controller: ChatClientController | None = None
        self._loop_thread: threading.Thread | None = None

    def run_loop(self) -> None:
        if self._loop is not None:
            return

        self._loop = asyncio.new_event_loop()

        def runner() -> None:
            assert self._loop is not None
            asyncio.set_event_loop(self._loop)
            print("ASYNC LOOP STARTED", flush=True)
            self._loop.run_forever()
            self._loop.close()

        self._loop_thread = threading.Thread(
            target=runner,
            daemon=True,
        )
        self._loop_thread.start()

    @QtCore.pyqtSlot(str)
    def connect_to_server(self, username: str) -> None:
        print("WORKER connect_to_server:", username, flush=True)
        self._submit(self._start(username))

    @QtCore.pyqtSlot(str)
    def send_broadcast(self, text: str) -> None:
        self._submit_controller_command(broadcast_command(text))

    @QtCore.pyqtSlot(str, str)
    def send_unicast(self, to: str, text: str) -> None:
        self._submit_controller_command(unicast_command(to, text))

    @QtCore.pyqtSlot()
    def leave(self) -> None:
        self._submit_controller_command(leave_command())

    @QtCore.pyqtSlot()
    def stop(self) -> None:
        if self._controller is not None:
            self._submit(self._controller.stop())

        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._loop.stop)

    async def _start(self, username: str) -> None:
        session = ChatSession(WebSocketChatTransport(self._server_uri))

        self._controller = ChatClientController(
            session=session,
            on_event=self._emit_event,
            on_status=self._emit_status,
        )

        await self._controller.start(username)

    async def _emit_event(self, event: ViewEvent) -> None:
        self.eventReceived.emit(event)

    async def _emit_status(self, status: ClientStatus) -> None:
        self.statusChanged.emit(status)

    def _submit_controller_command(self, command: object) -> None:
        if self._controller is None:
            self.errorOccurred.emit("Connect before sending messages")
            return

        self._submit(self._controller.submit(command))

    def _submit(self, coroutine: Coroutine[Any, Any, Any]) -> None:
        if self._loop is None:
            self.errorOccurred.emit("Worker event loop is not ready")
            return

        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        future.add_done_callback(self._report_failure)

    def _report_failure(self, future: Future[Any]) -> None:
        try:
            future.result()
        except Exception as exc:
            print("ASYNC ERROR:", repr(exc), flush=True)
            self.errorOccurred.emit(str(exc))