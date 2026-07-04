from PyQt5 import QtCore, QtWidgets


class LoginPage(QtWidgets.QWidget):
    connectRequested = QtCore.pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(120, 80, 120, 80)
        layout.addStretch()

        title = QtWidgets.QLabel("Home Chat")
        title.setAlignment(QtCore.Qt.AlignCenter)

        font = title.font()
        font.setPointSize(24)
        font.setBold(True)
        title.setFont(font)

        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(36)

        self.connect_button = QtWidgets.QPushButton("Connect")
        self.connect_button.setMinimumHeight(36)

        self.status_label = QtWidgets.QLabel()
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)

        form = QtWidgets.QVBoxLayout()
        form.setSpacing(12)
        form.addWidget(title)
        form.addWidget(self.username_input)
        form.addWidget(self.connect_button)
        form.addWidget(self.status_label)

        layout.addLayout(form)
        layout.addStretch()

    def _connect_signals(self) -> None:
        self.connect_button.clicked.connect(self._connect_clicked)
        self.username_input.returnPressed.connect(self._connect_clicked)

    def _connect_clicked(self) -> None:
        username = self.username_input.text().strip()
        print("Debug login page. CONNECT CLICKED:", username, flush=True) #Debug

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

    def set_status(self, status: str) -> None:
        self.status_label.setText(status)

    def set_connecting(self, connecting: bool) -> None:
        self.username_input.setEnabled(not connecting)
        self.connect_button.setEnabled(not connecting)