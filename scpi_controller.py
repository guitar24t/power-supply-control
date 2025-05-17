from scpi import *
from serial import Serial

class PowerSupplyOutputController:
    def __init__(self, serial_connection : Serial):
        self.serial_connection = serial_connection

    def turn_on(self):
        write_command(self.serial_connection, OutputCmd, OutputCmd.set_on_subcommand)

    def turn_off(self):
        write_command(self.serial_connection, OutputCmd, OutputCmd.set_off_subcommand)


class RelayOutputController:
    def __init__(self, serial_connection : Serial):
        self.serial_connection = serial_connection

    def turn_on(self):
        self.serial_connection.write("AT+CH1=1".encode())

    def turn_off(self):
        self.serial_connection.write("AT+CH1=0".encode())
