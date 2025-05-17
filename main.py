from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel
import sys
from serial import Serial
from scpi_controller import PowerSupplyOutputController, RelayOutputController
from scpi import OutputCmd, query_command

#For Controlling:
#Abestop,AT6301,24171025,FV:V5.1.0
DC_COM_PORT = "COM7"
DC_TIMEOUT = 2
DC_BAUDRATE = 115200
DC_BYTESIZE = 8
DC_PARITY = "N"
DC_STOPBITS = 2


RELAY_COM_PORT = "COM8"
RELAY_TIMEOUT = 2
RELAY_BAUDRATE = 9600
RELAY_BYTESIZE = 8
RELAY_PARITY = "N"
RELAY_STOPBITS = 1



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Output Control")
        
        try:
            self.dc_serial = Serial(
                port=DC_COM_PORT,
                timeout=DC_TIMEOUT,
                write_timeout=DC_TIMEOUT,
                baudrate=DC_BAUDRATE,
                bytesize=DC_BYTESIZE,
                parity=DC_PARITY,
                stopbits=DC_STOPBITS
            )
            self.dc_controller = PowerSupplyOutputController(self.dc_serial) 
        except Exception as e:
            self.dc_serial = None
            self.dc_controller = None
        
        try:
            self.relay_serial = Serial(
                port=RELAY_COM_PORT,
                timeout=RELAY_TIMEOUT,
                write_timeout=RELAY_TIMEOUT,
                baudrate=RELAY_BAUDRATE,
                bytesize=RELAY_BYTESIZE,
                parity=RELAY_PARITY,
                stopbits=RELAY_STOPBITS
            )
            self.relay_controller = RelayOutputController(self.relay_serial) 
        except Exception as e:
            self.relay_serial = None
            self.relay_controller = None


        self.init_ui()


    def init_ui(self):
        layout = QHBoxLayout()

        ps_layout = QVBoxLayout()

        self.dc_status_label = QLabel("Status: Unknown")
        ps_layout.addWidget(self.dc_status_label)

        self.dc_on_button = QPushButton("On")
        self.dc_off_button = QPushButton("Off")

        self.dc_on_button.clicked.connect(self.turn_on_dc)
        self.dc_off_button.clicked.connect(self.turn_off_dc)

        ps_layout.addWidget(self.dc_on_button)
        ps_layout.addWidget(self.dc_off_button)
        
        layout.addLayout(ps_layout)


        relay_layout = QVBoxLayout()

        self.relay_status_label = QLabel("Status: Unknown")
        relay_layout.addWidget(self.relay_status_label)

        self.relay_on_button = QPushButton("On")
        self.relay_off_button = QPushButton("Off")

        self.relay_on_button.clicked.connect(self.turn_on_relay)
        self.relay_off_button.clicked.connect(self.turn_off_relay)

        relay_layout.addWidget(self.relay_on_button)
        relay_layout.addWidget(self.relay_off_button)
        
        layout.addLayout(relay_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_dc_status(self):
        success, response = query_command(self.dc_serial, OutputCmd)
        if success:
            self.dc_status_label.setText(f"Status: {response}")
        else:
            self.dc_status_label.setText("Status: Unknown")
    
    def update_relay_status(self, status : str):
        self.relay_status_label.setText(f"Status: {status}")

    def turn_on_dc(self):
        self.dc_controller.turn_on()
        self.update_dc_status()

    def turn_off_dc(self):
        self.dc_controller.turn_off()
        self.update_dc_status()

    def turn_on_relay(self):
        self.relay_controller.turn_on()
        self.update_relay_status("ON")

    def turn_off_relay(self):
        self.relay_controller.turn_off()
        self.update_relay_status("OFF")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())