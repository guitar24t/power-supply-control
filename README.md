# pyside6-output-control

This project is a PySide6 GUI application designed to control an SCPI-compatible device's output state. It provides a simple interface with "On" and "Off" buttons to manage the device's output.

## Project Structure

```
pyside6-output-control
├── src
│   └── main.py          # Entry point of the application
├── requirements.txt      # Lists project dependencies
└── README.md             # Documentation for the project
```


1. **Install dependencies:**
   It is recommended to use a virtual environment. You can create one using:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
   Then install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

To run the application, execute the following command:
```
python3 main.py
```

Once the application is running, you will see a window with "On" and "Off" buttons. Clicking these buttons will send the corresponding commands to the SCPI/Relay device to control its output state.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.