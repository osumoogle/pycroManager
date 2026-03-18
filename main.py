import tkinter as tk
from ui import TimeTrackerApp


def main() -> None:
    root = tk.Tk()
    TimeTrackerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
