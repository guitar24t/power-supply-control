from scpi import *

class OutputController:
    def __init__(self, serial_connection):
        self.serial_connection = serial_connection

    def turn_on(self):
        write_command(self.serial_connection, OutputCmd, OutputCmd.set_on_subcommand)

    def turn_off(self):
        write_command(self.serial_connection, OutputCmd, OutputCmd.set_off_subcommand)
