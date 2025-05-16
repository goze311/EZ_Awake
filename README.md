# Screen Awake Application

The **Screen Awake Application** is a Python-based GUI tool that prevents your screen from going idle by simulating user activity. It periodically moves the mouse to keep the screen active.

## Features

- Selectable time intervals for mouse movement.
- Start, pause, resume, and stop functionality.
- Displays countdown to the next action.
- Tracks total running time.
- User-friendly interface built with `tkinter`.

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - `tkinter` (comes pre-installed with Python)
  - `pyautogui`
  - `traceback`

## Installation

1. Clone or download this repository.
2. Install the required Python packages using pip:
   ```bash
   pip install pyautogui
   ```

## Usage

1. Run the application:
   - If running from source:
     ```bash
     python main.py
     ```
   - If using the pre-built executable, navigate to the `dist` folder and run the `.exe` file.

2. Use the dropdown menu to select the interval for mouse movement.
3. Click the **Start** button to begin keeping the screen active.
4. Use the **Pause**, **Resume**, and **Stop** buttons to control the application.

## How It Works

- The application uses `pyautogui` to simulate mouse movements at regular intervals.
- The interval can be customized using the dropdown menu.
- The GUI provides real-time updates on the application's status and total running time.

## Notes

- Ensure that `pyautogui` is installed and functioning correctly.
- The application disables the `pyautogui.FAILSAFE` feature during operation to prevent interruptions. It is re-enabled when the application stops.

## Acknowledgments

- Built with Python and `tkinter`.
- Mouse movement functionality powered by `pyautogui`.
