from PyQt5 import QtCore, QtGui, QtWidgets

from client.gui.chat_window import ChatWindow
from client.gui.client_worker import ClientWorker

def run_gui(server_uri: str) -> int:
    app = QtWidgets.QApplication([])

    worker = ClientWorker(server_uri)
    worker.run_loop()

    window = ChatWindow()

    window.connectRequested.connect(worker.connect_to_server)
    window.broadcastRequested.connect(worker.send_broadcast)
    window.unicastRequested.connect(worker.send_unicast)
    window.leaveRequested.connect(worker.leave)

    worker.eventReceived.connect(window.apply_event)
    worker.statusChanged.connect(window.apply_status)
    worker.errorOccurred.connect(window.show_error)

    app.aboutToQuit.connect(worker.stop)

    window.show()
    return app.exec_()