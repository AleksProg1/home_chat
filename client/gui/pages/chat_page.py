from PyQt5 import QtCore, QtGui, QtWidgets


class ChatPage(QtWidgets.QWidget):
    sendRequested = QtCore.pyqtSignal(str)
    leaveRequested = QtCore.pyqtSignal()

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._connect_signals()
        self._apply_styles()

    def _build_ui(self) -> None:
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        header = QtWidgets.QHBoxLayout()

        self.chat_title = QtWidgets.QLabel("Home Chat")
        self.chat_title.setObjectName("chatTitle")

        self.chat_status = QtWidgets.QLabel("disconnected")
        self.chat_status.setObjectName("chatStatus")

        self.leave_button = QtWidgets.QPushButton("Leave")
        self.leave_button.setObjectName("leaveButton")

        header.addWidget(self.chat_title)
        header.addStretch()
        header.addWidget(self.chat_status)
        header.addWidget(self.leave_button)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(14)

        self.sidebar_card = QtWidgets.QFrame()
        self.sidebar_card.setObjectName("card")
        sidebar = QtWidgets.QVBoxLayout(self.sidebar_card)
        sidebar.setContentsMargins(14, 14, 14, 14)
        sidebar.setSpacing(10)

        users_label = QtWidgets.QLabel("Users")
        users_label.setObjectName("sectionTitle")

        self.users = QtWidgets.QListWidget()
        self.users.setMinimumWidth(190)
        self.users.setMaximumWidth(240)
        self.users.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.clear_selection_button = QtWidgets.QPushButton("Broadcast")
        self.clear_selection_button.setObjectName("secondaryButton")

        sidebar.addWidget(users_label)
        sidebar.addWidget(self.users, 1)
        sidebar.addWidget(self.clear_selection_button)

        self.messages_card = QtWidgets.QFrame()
        self.messages_card.setObjectName("card")
        messages_layout = QtWidgets.QVBoxLayout(self.messages_card)
        messages_layout.setContentsMargins(14, 14, 14, 14)

        self.messages = QtWidgets.QTextEdit()
        self.messages.setReadOnly(True)

        messages_layout.addWidget(self.messages)

        content.addWidget(self.sidebar_card)
        content.addWidget(self.messages_card, 1)

        input_bar = QtWidgets.QHBoxLayout()
        input_bar.setSpacing(10)

        self.message_input = QtWidgets.QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setMinimumHeight(42)

        self.send_button = QtWidgets.QPushButton("Send")
        self.send_button.setMinimumHeight(42)
        self.send_button.setMinimumWidth(96)

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
        self.chat_status.setText(f"● {status}")

    def set_connected(self, connected: bool) -> None:
        self.message_input.setEnabled(connected)
        self.send_button.setEnabled(connected)
        self.leave_button.setEnabled(connected)

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            ChatPage {
                background-color: #111827;
            }

            QLabel#chatTitle {
                color: #F9FAFB;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#chatStatus {
                color: #22C55E;
                font-size: 14px;
            }

            QLabel#sectionTitle {
                color: #F9FAFB;
                font-size: 15px;
                font-weight: 700;
            }

            QFrame#card {
                background-color: #1F2937;
                border: 1px solid #374151;
                border-radius: 14px;
            }

            QListWidget {
                background-color: #111827;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 6px;
                outline: none;
            }

            QListWidget::item {
                padding: 8px;
                border-radius: 8px;
            }

            QListWidget::item:selected {
                background-color: #2563EB;
                color: white;
            }

            QTextEdit {
                background-color: #111827;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }

            QLineEdit {
                background-color: #1F2937;
                color: #F9FAFB;
                border: 1px solid #374151;
                border-radius: 10px;
                padding: 0 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #3B82F6;
            }

            QPushButton {
                background-color: #2563EB;
                color: white;
                border: none;
                border-radius: 10px;
                font-weight: 600;
                padding: 8px 14px;
            }

            QPushButton:hover {
                background-color: #3B82F6;
            }

            QPushButton:pressed {
                background-color: #1D4ED8;
            }

            QPushButton:disabled {
                background-color: #374151;
                color: #9CA3AF;
            }

            QPushButton#secondaryButton {
                background-color: #374151;
            }

            QPushButton#secondaryButton:hover {
                background-color: #4B5563;
            }

            QPushButton#leaveButton {
                background-color: #DC2626;
            }

            QPushButton#leaveButton:hover {
                background-color: #EF4444;
            }
        """)