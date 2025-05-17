from serial import Serial

class SCPICommandBase():
    command = ""
    responses = []

class OutputCmd(SCPICommandBase):
    command = "OUTP"
    responses = ["OFF", "ON"]
    set_on_subcommand = "STATE ON"
    set_off_subcommand = "STATE OFF"

def validate_response(command: SCPICommandBase, response: str) -> bool:
    if command.responses is not None:
        return response in command.responses
    return True

def query_command(sc: Serial, command: SCPICommandBase) -> tuple[bool, str]:
    sc.write((command.command + "?\n").encode())
    response = sc.readline().decode().strip()
    return (validate_response(command, response), response)

def write_command(sc: Serial, command: SCPICommandBase, value: str):
    sc.write(f"{command.command}:{value}\n".encode())