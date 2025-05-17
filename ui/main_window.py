from PySide6.QtWidgets import QMainWindow, QPushButton, QVBoxLayout, QWidget
from controller import OutputController

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Output Control")
        self.setGeometry(100, 100, 300, 200)

        self.controller = OutputController()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.on_button = QPushButton("On")
        self.on_button.clicked.connect(self.turn_on)

        self.off_button = QPushButton("Off")
        self.off_button.clicked.connect(self.turn_off)

        layout.addWidget(self.on_button)
        layout.addWidget(self.off_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def turn_on(self):
        success, response = self.controller.turn_on()
        if success:
            print("Output turned on:", response)
        else:
            print("Failed to turn on:", response)

    def turn_off(self):
        success, response = self.controller.turn_off()
        if success:
            print("Output turned off:", response)
        else:
            print("Failed to turn off:", response)