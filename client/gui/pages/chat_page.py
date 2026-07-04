from PyQt5 import QtCore, QtGui, QtWidgets


class ChatPage(QtWidgets.QWidget):
    sendRequested = QtCore.pyqtSignal(str)
    leaveRequested = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
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

    def _connect_signals(self) -> None:
        self.send_button.clicked.connect(self._send_clicked)
        self.message_input.returnPressed.connect(self._send_clicked)
        self.clear_selection_button.clicked.connect(self.users.clearSelection)
        self.leave_button.clicked.connect(self.leaveRequested.emit)

    def _send_clicked(self) -> None:
        text = self.message_input.text().strip()

        if not text:
            return

        self.sendRequested.emit(text)
        self.message_input.clear()

    def selected_user(self) -> str | None:
        selected_items = self.users.selectedItems()

        if not selected_items:
            return None

        return selected_items[0].text()

    def update_users(self, users: tuple[str, ...]) -> None:
        selected_user = self.selected_user()

        self.users.clear()
        self.users.addItems(list(users))

        if selected_user is None:
            return

        matches = self.users.findItems(
            selected_user,
            QtCore.Qt.MatchFlag.MatchExactly,
        )

        if matches:
            self.users.setCurrentItem(matches[0])

    def add_message(self, text: str) -> None:
        self.messages.append(text)

    def set_title(self, title: str) -> None:
        self.chat_title.setText(title)

    def set_status(self, status: str) -> None:
        self.chat_status.setText(status)

    def set_connected(self, connected: bool) -> None:
        self.message_input.setEnabled(connected)
        self.send_button.setEnabled(connected)
        self.leave_button.setEnabled(connected)