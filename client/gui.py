"""PyQt5 chat client using the shared client core."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from typing import Any

from client.commands import broadcast_command, leave_command, unicast_command
from client.config import ClientConfig
from client.chat_client_controller import ChatClientController
from client.events import ClientStatus, ViewEvent, ViewEventKind
from client.session import ChatSession
from client.transport import WebSocketChatTransport


@dataclass(frozen=True, slots=True)
class GuiOptions:
    server_uri: str


def _load_pyqt5() -> tuple[Any, Any, Any]:
    try:
        from PyQt5 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise RuntimeError(
            "PyQt5 is required for GUI client. Install requirements.txt"
        ) from exc
    return QtCore, QtGui, QtWidgets


def run_gui(options: GuiOptions) -> int:
    QtCore, QtGui, QtWidgets = _load_pyqt5()

    class ClientWorker(QtCore.QObject):
        eventReceived = QtCore.pyqtSignal(object)
        statusChanged = QtCore.pyqtSignal(object)
        errorOccurred = QtCore.pyqtSignal(str)

        def __init__(self, server_uri: str) -> None:
            super().__init__()
            self._server_uri = server_uri
            self._loop: asyncio.AbstractEventLoop | None = None
            self._controller: ChatClientController | None = None

        @QtCore.pyqtSlot(str)
        def connect_to_server(self, username: str) -> None:
            self._ensure_loop()
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

        def run_loop(self) -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_forever()
            self._loop.close()

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

        def _submit(self, coroutine: object) -> None:
            self._ensure_loop()
            assert self._loop is not None
            future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
            future.add_done_callback(self._report_failure)

        def _ensure_loop(self) -> None:
            if self._loop is None:
                raise RuntimeError("Worker event loop is not ready")

        def _report_failure(self, future: object) -> None:
            try:
                future.result()
            except Exception as exc:
                self.errorOccurred.emit(str(exc))

    class ChatWindow(QtWidgets.QMainWindow):
        connectRequested = QtCore.pyqtSignal(str)
        broadcastRequested = QtCore.pyqtSignal(str)
        unicastRequested = QtCore.pyqtSignal(str, str)
        leaveRequested = QtCore.pyqtSignal()

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Home Chat")
            self.resize(860, 560)
            self._username = ""

            self.pages = QtWidgets.QStackedWidget()
            self.setCentralWidget(self.pages)

            self.login_page = self._build_login_page()
            self.chat_page = self._build_chat_page()
            self.pages.addWidget(self.login_page)
            self.pages.addWidget(self.chat_page)
            self.pages.setCurrentWidget(self.login_page)

        def _build_login_page(self) -> QtWidgets.QWidget:
            page = QtWidgets.QWidget()
            outer = QtWidgets.QVBoxLayout(page)
            outer.setContentsMargins(120, 80, 120, 80)
            outer.addStretch()

            title = QtWidgets.QLabel("Home Chat")
            title.setAlignment(QtCore.Qt.AlignCenter)
            title_font = title.font()
            title_font.setPointSize(24)
            title_font.setBold(True)
            title.setFont(title_font)

            self.login_status = QtWidgets.QLabel("disconnected")
            self.login_status.setAlignment(QtCore.Qt.AlignCenter)

            self.username_input = QtWidgets.QLineEdit()
            self.username_input.setPlaceholderText("username")
            self.username_input.setMinimumHeight(36)

            self.connect_button = QtWidgets.QPushButton("Connect")
            self.connect_button.setMinimumHeight(36)

            form = QtWidgets.QVBoxLayout()
            form.setSpacing(12)
            form.addWidget(title)
            form.addWidget(self.username_input)
            form.addWidget(self.connect_button)
            form.addWidget(self.login_status)

            outer.addLayout(form)
            outer.addStretch()

            self.connect_button.clicked.connect(self._connect_clicked)
            self.username_input.returnPressed.connect(self._connect_clicked)
            return page

        def _build_chat_page(self) -> QtWidgets.QWidget:
            page = QtWidgets.QWidget()
            root = QtWidgets.QVBoxLayout(page)
            root.setContentsMargins(12, 12, 12, 12)
            root.setSpacing(10)

            header = QtWidgets.QHBoxLayout()
            self.chat_title = QtWidgets.QLabel("Chat")
            title_font = self.chat_title.font()
            title_font.setPointSize(16)
            title_font.setBold(True)
            self.chat_title.setFont(title_font)

            self.chat_status = QtWidgets.QLabel("disconnected")
            self.leave_button = QtWidgets.QPushButton("Leave")
            header.addWidget(self.chat_title)
            header.addStretch()
            header.addWidget(self.chat_status)
            header.addWidget(self.leave_button)

            content = QtWidgets.QHBoxLayout()
            content.setSpacing(12)

            sidebar = QtWidgets.QVBoxLayout()
            users_label = QtWidgets.QLabel("Users")
            users_label_font = users_label.font()
            users_label_font.setBold(True)
            users_label.setFont(users_label_font)

            self.users = QtWidgets.QListWidget()
            self.users.setMinimumWidth(180)
            self.users.setMaximumWidth(240)
            self.users.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

            self.clear_selection_button = QtWidgets.QPushButton("Broadcast")
            sidebar.addWidget(users_label)
            sidebar.addWidget(self.users, 1)
            sidebar.addWidget(self.clear_selection_button)

            self.messages = QtWidgets.QTextEdit()
            self.messages.setReadOnly(True)
            self.messages.setFont(
                QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
            )

            content.addLayout(sidebar)
            content.addWidget(self.messages, 1)

            input_bar = QtWidgets.QHBoxLayout()
            self.message_input = QtWidgets.QLineEdit()
            self.message_input.setPlaceholderText("message")
            self.message_input.setMinimumHeight(34)
            self.send_button = QtWidgets.QPushButton("Send")
            self.send_button.setMinimumHeight(34)
            input_bar.addWidget(self.message_input, 1)
            input_bar.addWidget(self.send_button)

            root.addLayout(header)
            root.addLayout(content, 1)
            root.addLayout(input_bar)

            self.send_button.clicked.connect(self._send_clicked)
            self.message_input.returnPressed.connect(self._send_clicked)
            self.clear_selection_button.clicked.connect(self.users.clearSelection)
            self.leave_button.clicked.connect(self.leaveRequested.emit)
            return page

        @QtCore.pyqtSlot(object)
        def apply_event(self, event: ViewEvent) -> None:
            if event.kind is ViewEventKind.USERS:
                self._apply_users(event.users)
                return

            self.messages.append(event.text)
            if event.kind is ViewEventKind.ERROR:
                self.login_status.setText(event.text)

        @QtCore.pyqtSlot(object)
        def apply_status(self, status: ClientStatus) -> None:
            self.login_status.setText(status.value)
            self.chat_status.setText(status.value)

            is_connecting = status is ClientStatus.CONNECTING
            is_connected = status is ClientStatus.CONNECTED

            self.connect_button.setEnabled(not is_connecting and not is_connected)
            self.username_input.setEnabled(not is_connecting and not is_connected)
            self.message_input.setEnabled(is_connected)
            self.send_button.setEnabled(is_connected)
            self.leave_button.setEnabled(is_connected)

            if is_connected:
                self.pages.setCurrentWidget(self.chat_page)
            elif status is ClientStatus.DISCONNECTED:
                self.pages.setCurrentWidget(self.login_page)

        @QtCore.pyqtSlot(str)
        def show_error(self, message: str) -> None:
            if self.pages.currentWidget() is self.login_page:
                self.login_status.setText(message)
            else:
                self.messages.append(f"error: {message}")

        def _connect_clicked(self) -> None:
            username = self.username_input.text().strip()
            if not username:
                self.login_status.setText("username is required")
                return

            self._username = username
            self.chat_title.setText(f"Chat as {username}")
            self.connectRequested.emit(username)

        def _send_clicked(self) -> None:
            text = self.message_input.text().strip()
            if not text:
                return

            selected_user = self._selected_user()
            if selected_user is None:
                self.broadcastRequested.emit(text)
            else:
                self.unicastRequested.emit(selected_user, text)
            self.message_input.clear()

        def _selected_user(self) -> str | None:
            selected_items = self.users.selectedItems()
            if not selected_items:
                return None

            selected_user = selected_items[0].text()
            if selected_user == self._username:
                return None
            return selected_user

        def _apply_users(self, users: tuple[str, ...]) -> None:
            selected_user = self._selected_user()
            self.users.clear()
            self.users.addItems(list(users))

            if selected_user is None:
                return

            matches = self.users.findItems(selected_user, QtCore.Qt.MatchExactly)
            if matches:
                self.users.setCurrentItem(matches[0])

    app = QtWidgets.QApplication([])
    thread = QtCore.QThread()
    worker = ClientWorker(options.server_uri)
    window = ChatWindow()

    worker.moveToThread(thread)
    thread.started.connect(worker.run_loop)
    window.connectRequested.connect(worker.connect_to_server)
    window.broadcastRequested.connect(worker.send_broadcast)
    window.unicastRequested.connect(worker.send_unicast)
    window.leaveRequested.connect(worker.leave)
    worker.eventReceived.connect(window.apply_event)
    worker.statusChanged.connect(window.apply_status)
    worker.errorOccurred.connect(window.show_error)
    app.aboutToQuit.connect(worker.stop)
    app.aboutToQuit.connect(thread.quit)

    thread.start()
    window.show()
    exit_code = app.exec_()
    thread.wait(1000)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PyQt5 WebSocket chat client")
    parser.add_argument(
        "--server",
        default=ClientConfig.from_env().server_uri,
        help="WebSocket server URI, defaults to CHAT_SERVER_URI or ws://127.0.0.1:8765",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    raise SystemExit(run_gui(GuiOptions(server_uri=args.server)))


if __name__ == "__main__":
    main()
