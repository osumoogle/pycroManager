# pycroManager

Micro-manage your tasks and time with a lightweight Windows desktop app. Clock in and out of tasks, track elapsed time in real-time, and review recent session history — all stored locally in a simple CSV file.

## Features

- **Clock In / Out** — Toggle between tasks with a single button. Task names are validated and recorded with timestamps.
- **Live Session Timer** — See how long you've been working on the current task, updated every second.
- **Session History** — View your 20 most recent sessions in a table showing task name, clock-in/out times, and duration.
- **Theme Support** — Choose between light, dark, or system theme (auto-detects your Windows dark mode setting).
- **Local CSV Storage** — All timesheet data is saved to `timesheet.csv` in a human-readable format. No database or account required.

## Requirements

- Python 3.x with Tkinter (included in most Python installations)
- Windows (uses the Windows registry for system theme detection)

## Usage

```
python main.py
```

### Running with JetBrains Rider

A run configuration is included in `.run/pycroManager.run.xml`. To use it:

1. Install the **Python** plugin from the JetBrains marketplace (Settings > Plugins).
2. Open the project folder in Rider.
3. Ensure your Python interpreter is configured:
   - Go to **Settings > Languages & Frameworks > Python**.
   - Add or select your global Python installation (e.g. `C:\Python314\python.exe`).
4. The **pycroManager** run configuration should appear in the toolbar dropdown. Click the run button to launch the app.

If the configuration does not appear automatically, you can add it manually:
- Go to **Run > Edit Configurations > + > Python**.
- Set **Script** to `main.py` and **Working directory** to the project root.

## Project Structure

| File              | Purpose                                      |
| ----------------- | -------------------------------------------- |
| `main.py`         | Application entry point                      |
| `ui.py`           | Tkinter UI, theme system, and app controller |
| `models.py`       | Data models (TimeEvent, ClockState, etc.)    |
| `data.py`         | CSV read/write and session grouping          |
| `settings.py`     | JSON-based user settings (theme preference)  |
| `validation.py`   | Task name input validation                   |
| `timesheet.csv`   | Recorded time entries                        |
| `settings.json`   | Persisted user settings                      |

## License

[MIT](LICENSE)
