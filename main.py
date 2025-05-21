#!/usr/bin/env python3
# -*- coding: ascii -*-

from dataclasses import dataclass
from typing import Sequence
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QInputDialog, QDialog, QLineEdit, QComboBox
from PySide6.QtGui import QCloseEvent
from PySide6.QtCore import QRect, QPoint, Qt
import sys
from serial import Serial
import serial.tools.list_ports
import platform

@dataclass
class SerialParameters:
    timeout: int = 2
    write_timeout: int = 2
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = "N"
    stopbits: int = 1

#For Controlling:
#Abestop,AT6301,24171025,FV:V5.1.0
dc_supply_params = SerialParameters(
    timeout=2,
    write_timeout=2,
    baudrate=115200,
    bytesize=8,
    parity="N",
    stopbits=2
)

#For Controlling:
#DSD TECH SH-UR01A USB Relay Controller
relay_params = SerialParameters(
    timeout=2,
    write_timeout=2,
    baudrate=9600,
    bytesize=8,
    parity="N",
    stopbits=1
)

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
        self.setWindowTitle(f"Output Control: Select {port_type_text} Ports")

        self.inputs : list[QComboBox] = []
        layout = QVBoxLayout(self)

        counter = 0
        for label_text in labels:
            hbox = QHBoxLayout()
            label = QLabel(label_text)
            serial_port_select = QComboBox()
            serial_port_select.addItems(self.get_serial_ports())
            hbox.addWidget(label)
            hbox.addWidget(serial_port_select)
            layout.addLayout(hbox)
            self.inputs.append(serial_port_select)
            serial_port_select.setMinimumWidth(150)
            serial_port_select.setCurrentIndex(counter)
            serial_port_select.currentIndexChanged.connect(self.process_combo_box_values)
            counter += 1
            counter = min(counter, len(self.inputs))

        button_box = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        layout.addLayout(button_box)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        self.values = None

        self.process_combo_box_values()

        self.setFixedSize(layout.sizeHint())
        qr : QRect = self.frameGeometry()
        cp : QPoint = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def process_combo_box_values(self):
        selected_values = [cb.currentText() for cb in self.inputs]
        for idx, cb in enumerate(self.inputs):
            current_value = cb.currentText()
            cb.blockSignals(True)
            cb.clear()
            available_ports = [port for port in self.get_serial_ports() if port not in selected_values or port == current_value]
            cb.addItems(available_ports)
            if current_value in available_ports:
                cb.setCurrentText(current_value)
            cb.blockSignals(False)

    def get_serial_ports(self) -> Sequence[str]:
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
            sys.exit(0)


class MainWindow(QMainWindow):
    def __init__(self, serial_ports):

        if serial_ports is None or len(serial_ports) != 2:
            raise ValueError("Expected 2 serial ports for DC and Relay controllers")

        super().__init__()
        self.setWindowTitle("Output Control")

        try:
            self.dc_serial = Serial(
                port=serial_ports[0],
                timeout=dc_supply_params.timeout,
                write_timeout=dc_supply_params.write_timeout,
                baudrate=dc_supply_params.baudrate,
                bytesize=dc_supply_params.bytesize,
                parity=dc_supply_params.parity,
                stopbits=dc_supply_params.stopbits
            )
            self.dc_controller = PowerSupplyOutputController(self.dc_serial) 
        except Exception as e:
            self.dc_serial = None
            self.dc_controller = None
        
        try:
            self.relay_serial = Serial(
                port=serial_ports[1],
                timeout=relay_params.timeout,
                write_timeout=relay_params.write_timeout,
                baudrate=relay_params.baudrate,
                bytesize=relay_params.bytesize,
                parity=relay_params.parity,
                stopbits=relay_params.stopbits
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

    def init_ui(self):
        layout = QHBoxLayout()

        ps_layout = QVBoxLayout()

        self.dc_status_label = QLabel("Status: N/A")
        ps_layout.addWidget(self.dc_status_label)

        self.dc_on_button = QPushButton("On")
        self.dc_off_button = QPushButton("Off")

        self.dc_on_button.clicked.connect(self.turn_on_dc)
        self.dc_off_button.clicked.connect(self.turn_off_dc)

        ps_layout.addWidget(self.dc_on_button)
        ps_layout.addWidget(self.dc_off_button)
        
        layout.addLayout(ps_layout)


        relay_layout = QVBoxLayout()

        self.relay_status_label = QLabel("Status: N/A")
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

        self.setFixedSize(container.sizeHint())
        qr : QRect = self.frameGeometry()
        cp : QPoint = QApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

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
    serial_ports = [f"DC PS {port_type_text} Port:", f"Relay {port_type_text} Port:"]
    serial_port_values = SerialPortInputDialog.get_inputs(serial_ports)
    window = MainWindow(serial_port_values)
    window.show()
    sys.exit(app.exec())
