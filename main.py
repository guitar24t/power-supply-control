#!/usr/bin/env python3

from dataclasses import dataclass
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog, QDialog, QLineEdit, QComboBox
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import QRect, QPoint, Qt
import sys
from serial import Serial
import serial.tools.list_ports
import serial.tools.list_ports_common
import platform

#For Controlling:
#Abestop,AT6301,24171025,FV:V5.1.0
DC_COM_PORT = "COM3" if platform.system() == "Windows" else "/dev/ttyUSB0"
DC_TIMEOUT = 2
DC_BAUDRATE = 115200
DC_BYTESIZE = 8
DC_PARITY = "N"
DC_STOPBITS = 2

#For Controlling:
#DSD TECH SH-UR01A USB Relay Controller
RELAY_COM_PORT = "COM4" if platform.system() == "Windows" else "/dev/ttyUSB1"
RELAY_TIMEOUT = 2
RELAY_BAUDRATE = 9600
RELAY_BYTESIZE = 8
RELAY_PARITY = "N"
RELAY_STOPBITS = 1

port_type_text = "COM" if platform.system() == "Windows" else "Serial"

class SCPICommandBase():
    command = ""
    responses = []

class OutputCmd(SCPICommandBase):
    command = "OUTP"
    responses = ["OFF", "ON"]
    set_on_subcommand = "STATE ON"
    set_off_subcommand = "STATE OFF"

class SCPI:
    @classmethod
    def validate_response(cls, command: SCPICommandBase, response: str) -> bool:
        if command.responses is not None:
            return response in command.responses
        return True

    @classmethod
    def query_command(cls, sc: Serial, command: SCPICommandBase) -> tuple[bool, str]:
        sc.write((command.command + "?\n").encode())
        response = sc.readline().decode().strip()
        return (cls.validate_response(command, response), response)

    @classmethod
    def write_command(cls, sc: Serial, command: SCPICommandBase, value: str):
        sc.write(f"{command.command}:{value}\n".encode())


class PowerSupplyOutputController:
    def __init__(self, serial_connection : Serial):
        self.serial_connection = serial_connection

    def turn_on(self):
        SCPI.write_command(self.serial_connection, OutputCmd(), OutputCmd.set_on_subcommand)

    def turn_off(self):
        SCPI.write_command(self.serial_connection, OutputCmd(), OutputCmd.set_off_subcommand)


class RelayOutputController:
    def __init__(self, serial_connection : Serial):
        self.serial_connection = serial_connection

    def turn_on(self):
        self.serial_connection.write('AT+CH1=1'.encode())

    def turn_off(self):
        self.serial_connection.write('AT+CH1=0'.encode())


class SerialPortInputDialog(QDialog):
    def __init__(self, labels, parent=None):
        super().__init__(parent)

        self.inputs : list[QComboBox] = []
        layout = QVBoxLayout(self)

        for label_text in labels:
            hbox = QHBoxLayout()
            label = QLabel(label_text)
            serial_port_select = QComboBox()
            serial_port_select.addItems(self.get_serial_ports())
            hbox.addWidget(label)
            hbox.addWidget(serial_port_select)
            layout.addLayout(hbox)
            self.inputs.append(serial_port_select)

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        self.values = None

    def get_serial_ports(self) -> list[serial.tools.list_ports_common.ListPortInfo]:
        port_list = serial.tools.list_ports.comports()
        port_list[:] = [p for p in port_list if not p.device.startswith("/dev/ttyS")] # Exclude /dev/ttyS* ports
        if not port_list:
            print("No serial ports found. Exiting.")
            sys.exit(1)
        return [port.device for port in port_list]

    def get_values(self):
      return self.values

    def accept(self):
        self.values = [input.currentText() for input in self.inputs]
        super().accept()

    @staticmethod
    def get_inputs(labels, parent=None):
        dialog = SerialPortInputDialog(labels, parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.get_values()
        else:
            return None


class MainWindow(QMainWindow):
    def __init__(self, serial_ports):
        super().__init__()
        self.setWindowTitle("Output Control")
        self.setGeometry(100, 100, 200, 200)

        qr : QRect = self.frameGeometry()
        cp : QPoint = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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

    def closeEvent(self, event: QCloseEvent):
        try:
            if self.dc_serial is not None:
                self.dc_serial.close()
        except Exception as e:
            print(f"Error closing DC serial port: {e}")
        
        try:
            if self.relay_serial is not None:   
                self.relay_serial.close()
        except Exception as e:
            print(f"Error closing Relay serial port: {e}")

        event.accept()


    from typing import Optional

    def select_com_port(self, title, ports : list[serial.tools.list_ports_common.ListPortInfo]) -> Optional[str]:
        port_list = [f"{p.device}" for p in ports]
        if not port_list:
            return None
        port, ok = QInputDialog.getItem(self, title, f"Select {port_type_text} Port:", port_list, 0, False)
        if ok and port:
            return port
        return None

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
        if self.dc_serial is not None:
            try:
                success, response = SCPI.query_command(self.dc_serial, OutputCmd())
                if success:
                    self.dc_status_label.setText(f"Status: {response}")
                else:
                    self.dc_status_label.setText("Status: Unknown")
            except:
                self.dc_status_label.setText("DC not available")
        else:
            self.dc_status_label.setText("DC not available")
    
    def update_relay_status(self, status : str):
        self.relay_status_label.setText(f"Status: {status}")

    def turn_on_dc(self):
        if self.dc_controller is None:
            self.dc_status_label.setText("DC not available")
            return
        try:
            self.dc_controller.turn_on()
            self.update_dc_status()
        except:
            self.dc_status_label.setText("DC not available")
            return

    def turn_off_dc(self):
        if self.dc_controller is None:
            self.dc_status_label.setText("DC not available")
            return
        try:
            self.dc_controller.turn_off()
            self.update_dc_status()
        except:
            self.dc_status_label.setText("DC not available")
            return

    def turn_on_relay(self):
        if self.relay_controller is None:
            self.relay_status_label.setText("Relay not available")
            return
        try:
            self.relay_controller.turn_on()
            self.update_relay_status("ON")
        except:
            self.relay_status_label.setText("Relay not available")
            return

    def turn_off_relay(self):
        if self.relay_controller is None:
            self.relay_status_label.setText("Relay not available")
            return
        try:
            self.relay_controller.turn_off()
            self.update_relay_status("OFF")
        except:
            self.relay_status_label.setText("Relay not available")
            return

if __name__ == "__main__":
    app = QApplication(sys.argv)
    serial_ports = [f"DC PS {port_type_text} Port", f"Relay {port_type_text} Port"]
    values = SerialPortInputDialog.get_inputs(serial_ports)
    window = MainWindow(serial_ports)
    window.show()
    sys.exit(app.exec())
