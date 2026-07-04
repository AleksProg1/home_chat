from PyQt5 import QtCore, QtWidgets

from client.events import ClientStatus, ViewEvent, ViewEventKind
from client.gui.pages.login_page import LoginPage
from client.gui.pages.chat_page import ChatPage


class ChatWindow(QtWidgets.QMainWindow):
    connectRequested = QtCore.pyqtSignal(str)
    broadcastRequested = QtCore.pyqtSignal(str)
    unicastRequested = QtCore.pyqtSignal(str, str)
    leaveRequested = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._username = ""

        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        self.setWindowTitle("Home Chat")
        self.resize(860, 560)

        self.pages = QtWidgets.QStackedWidget()
        self.setCentralWidget(self.pages)

        self.login_page = LoginPage()
        self.chat_page = ChatPage()

        self.pages.addWidget(self.login_page)
        self.pages.addWidget(self.chat_page)
        self.pages.setCurrentWidget(self.login_page)

    def _connect_signals(self) -> None:
        self.login_page.connectRequested.connect(self._connect_requested)
        self.chat_page.sendRequested.connect(self._send_requested)
        self.chat_page.leaveRequested.connect(self.leaveRequested.emit)

    @QtCore.pyqtSlot(object)
    def apply_event(self, event: ViewEvent) -> None:
        if event.kind is ViewEventKind.USERS:
            self.chat_page.update_users(event.users)
            return

        if event.kind is ViewEventKind.ERROR:
            self.show_error(event.text)
            return

        self.chat_page.add_message(event.text)

    @QtCore.pyqtSlot(object)
    def apply_status(self, status: ClientStatus) -> None:
        self.login_page.set_status(status.value)
        self.chat_page.set_status(status.value)

        is_connecting = status is ClientStatus.CONNECTING
        is_connected = status is ClientStatus.CONNECTED

        self.login_page.set_connecting(is_connecting or is_connected)
        self.chat_page.set_connected(is_connected)

        if is_connected:
            self.pages.setCurrentWidget(self.chat_page)
        elif status is ClientStatus.DISCONNECTED:
            self.pages.setCurrentWidget(self.login_page)
            self.login_page.reset()

    @QtCore.pyqtSlot(str)
    def show_error(self, message: str) -> None:
        if self.pages.currentWidget() is self.login_page:
            self.login_page.show_error(message)
        else:
            self.chat_page.add_message(f"error: {message}")

    def _connect_requested(self, username: str) -> None:
        self._username = username
        self.chat_page.set_title(f"Chat as {username}")
        self.connectRequested.emit(username)

    def _send_requested(self, text: str) -> None:
        selected_user = self.chat_page.selected_user()

        if selected_user is None or selected_user == self._username:
            self.broadcastRequested.emit(text)
        else:
            self.unicastRequested.emit(selected_user, text)
