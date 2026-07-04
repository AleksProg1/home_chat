from PyQt5 import QtCore, QtWidgets


class LoginPage(QtWidgets.QWidget):
    connectRequested = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._connect_signals()
        self._apply_styles()

    def _build_ui(self) -> None:
        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setAlignment(QtCore.Qt.AlignCenter)

        self.card = QtWidgets.QFrame()
        self.card.setObjectName("loginCard")
        self.card.setFixedWidth(360)

        card_layout = QtWidgets.QVBoxLayout(self.card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(14)

        title = QtWidgets.QLabel("Home Chat")
        title.setObjectName("titleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Connect to the chat server")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(42)

        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setMinimumHeight(42)
        self.connect_button.setCursor(QtCore.Qt.PointingHandCursor)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setWordWrap(True)

        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addSpacing(12)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.connect_button)
        card_layout.addWidget(self.status_label)

        root_layout.addWidget(self.card)

    def _connect_signals(self) -> None:
        self.connect_button.clicked.connect(self._connect_clicked)
        self.username_input.returnPressed.connect(self._connect_clicked)

    def _connect_clicked(self) -> None:
        username = self.username_input.text().strip()
        print("Debug login page. CONNECT CLICKED:", username, flush=True)

        if not username:
            self.show_error("Username is required")
            return

        self.connectRequested.emit(username)

    def reset(self) -> None:
        self.username_input.clear()
        self.status_label.clear()

        self.username_input.setEnabled(True)
        self.connect_button.setEnabled(True)

        self.username_input.setFocus()

    def show_error(self, message: str) -> None:
        self.status_label.setText(message)
        self.status_label.setProperty("state", "error")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)
        self.status_label.setProperty("state", "normal")
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def set_connecting(self, connecting: bool) -> None:
        self.username_input.setEnabled(not connecting)
        self.connect_button.setEnabled(not connecting)

        if connecting:
            self.connect_button.setText("Connecting...")
        else:
            self.connect_button.setText("Connect")

    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            LoginPage {
                background-color: #101418;
            }

            QFrame#loginCard {
                background-color: #171c22;
                border: 1px solid #2b333d;
                border-radius: 16px;
            }

            QLabel#titleLabel {
                color: #f5f7fa;
                font-size: 28px;
                font-weight: 700;
            }

            QLabel#subtitleLabel {
                color: #8f9ba8;
                font-size: 14px;
            }

            QLineEdit {
                background-color: #0f1318;
                color: #f5f7fa;
                border: 1px solid #303946;
                border-radius: 10px;
                padding: 0 12px;
                font-size: 14px;
            }

            QLineEdit:focus {
                border: 1px solid #4f8cff;
            }

            QPushButton {
                background-color: #4f8cff;
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #6aa0ff;
            }

            QPushButton:pressed {
                background-color: #3d76dc;
            }

            QPushButton:disabled {
                background-color: #2c3644;
                color: #8792a0;
            }

            QLabel#statusLabel {
                color: #8f9ba8;
                min-height: 20px;
            }

            QLabel#statusLabel[state="error"] {
                color: #ff6b6b;
            }
        """)