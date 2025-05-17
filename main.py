from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
import sys
from serial import Serial
from controller import OutputController
from scpi import OutputCmd, query_command

#For Controlling:
#Abestop,AT6301,24171025,FV:V5.1.0
COM_PORT = "COM7"
TIMEOUT = 2
BAUDRATE = 115200
BYTESIZE = 8
PARITY = "N"
STOPBITS = 2

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Output Control")
        
        self.serial = Serial(
            port=COM_PORT,
            timeout=TIMEOUT,
            write_timeout=TIMEOUT,
            baudrate=BAUDRATE,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS
        )
        self.controller = OutputController(self.serial)

        self.init_ui()
        self.update_status()

    def init_ui(self):
        layout = QVBoxLayout()

        self.status_label = QLabel("Status: Unknown")
        layout.addWidget(self.status_label)

        self.on_button = QPushButton("On")
        self.off_button = QPushButton("Off")

        self.on_button.clicked.connect(self.turn_on)
        self.off_button.clicked.connect(self.turn_off)

        layout.addWidget(self.on_button)
        layout.addWidget(self.off_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_status(self):
        success, response = query_command(self.serial, OutputCmd)
        if success:
            self.status_label.setText(f"Status: {response}")
        else:
            self.status_label.setText("Status: Unknown")

    def turn_on(self):
        self.controller.turn_on()
        self.update_status()

    def turn_off(self):
        self.controller.turn_off()
        self.update_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())