import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import winreg

from models import EventType, TimeEvent
from data import CSV_PATH, read_events, append_event, get_current_state, get_recent_sessions
from validation import validate_task_name, ValidationError
from settings import load_settings, save_settings

_DARK = {
    "bg": "#1e1e1e",
    "fg": "#d4d4d4",
    "entry_bg": "#2d2d2d",
    "entry_fg": "#d4d4d4",
    "select_bg": "#264f78",
    "tree_bg": "#252526",
    "tree_fg": "#d4d4d4",
    "heading_bg": "#333333",
    "button_bg": "#3a3a3a",
    "error": "#f44747",
}

_LIGHT = {
    "bg": "#f0f0f0",
    "fg": "#1e1e1e",
    "entry_bg": "#ffffff",
    "entry_fg": "#1e1e1e",
    "select_bg": "#0078d4",
    "tree_bg": "#ffffff",
    "tree_fg": "#1e1e1e",
    "heading_bg": "#e0e0e0",
    "button_bg": "#e1e1e1",
    "error": "#d32f2f",
}


def _is_dark_mode() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return value == 0
    except OSError:
        return False


def _resolve_dark(theme_pref: str) -> bool:
    if theme_pref == "dark":
        return True
    if theme_pref == "light":
        return False
    return _is_dark_mode()


def _apply_theme(root: tk.Tk, theme_pref: str = "system") -> dict:
    colors = _DARK if _resolve_dark(theme_pref) else _LIGHT
    style = ttk.Style(root)
    style.theme_use("clam")

    root.configure(bg=colors["bg"])

    style.configure(".", background=colors["bg"], foreground=colors["fg"])
    style.configure("TFrame", background=colors["bg"])
    style.configure("TLabel", background=colors["bg"], foreground=colors["fg"])
    style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
    style.configure("TButton", background=colors["button_bg"], foreground=colors["fg"])
    style.map("TButton",
              background=[("active", colors["select_bg"])],
              foreground=[("active", "#ffffff")])
    style.configure("TSeparator", background=colors["fg"])

    style.configure("Treeview",
                     background=colors["tree_bg"],
                     foreground=colors["tree_fg"],
                     fieldbackground=colors["tree_bg"],
                     rowheight=24)
    style.configure("Treeview.Heading",
                     background=colors["heading_bg"],
                     foreground=colors["fg"])
    style.map("Treeview",
              background=[("selected", colors["select_bg"])],
              foreground=[("selected", "#ffffff")])

    return colors


class TimeTrackerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Time Tracker")
        self.root.resizable(False, False)

        self._settings = load_settings()
        self._colors = _apply_theme(root, self._settings["theme"])
        self._timer_id: str | None = None
        self._events = read_events()
        self._state = get_current_state(self._events)

        self._build_ui()
        self._center_window()
        self._apply_state()

    def _center_window(self) -> None:
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(sticky="nsew")

        # Task entry
        ttk.Label(frame, text="Task / Project Name").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.task_var = tk.StringVar()
        self.task_entry = ttk.Entry(frame, textvariable=self.task_var, width=50)
        self.task_entry.grid(row=1, column=0, sticky="ew", pady=(0, 2))

        self.error_var = tk.StringVar()
        self.error_label = ttk.Label(frame, textvariable=self.error_var, foreground=self._colors["error"])
        self.error_label.grid(row=2, column=0, sticky="w", pady=(0, 8))

        # Clock buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 12))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)

        self.btn_text = tk.StringVar(value="Clock In")
        self.clock_btn = ttk.Button(btn_frame, textvariable=self.btn_text, command=self._toggle_clock)
        self.clock_btn.grid(row=0, column=0, sticky="ew", ipady=6)

        self.switch_btn = ttk.Button(btn_frame, text="Switch Task", command=self._switch_task)
        self.switch_btn.grid(row=0, column=1, sticky="ew", ipady=6, padx=(6, 0))

        # Status
        self.status_var = tk.StringVar(value="Status: Clocked out")
        ttk.Label(frame, textvariable=self.status_var).grid(row=4, column=0, sticky="w")

        self.elapsed_var = tk.StringVar(value="Current session: --")
        ttk.Label(frame, textvariable=self.elapsed_var).grid(row=5, column=0, sticky="w", pady=(0, 12))

        # Separator + table heading
        ttk.Separator(frame, orient="horizontal").grid(row=6, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(frame, text="Recent Tasks", font=("", 10, "bold")).grid(row=7, column=0, pady=(0, 4))

        # Treeview
        columns = ("task", "clock_in", "clock_out", "duration")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=10)
        self.tree.heading("task", text="Task")
        self.tree.heading("clock_in", text="Clock In")
        self.tree.heading("clock_out", text="Clock Out")
        self.tree.heading("duration", text="Duration")
        self.tree.column("task", width=160)
        self.tree.column("clock_in", width=80, anchor="center")
        self.tree.column("clock_out", width=80, anchor="center")
        self.tree.column("duration", width=80, anchor="center")
        self.tree.grid(row=8, column=0, sticky="ew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=8, column=1, sticky="ns")

        # Theme selector
        theme_frame = ttk.Frame(frame)
        theme_frame.grid(row=9, column=0, sticky="e", pady=(12, 0))
        ttk.Label(theme_frame, text="Theme:").pack(side="left", padx=(0, 6))
        self.theme_var = tk.StringVar(value=self._settings["theme"])
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["system", "light", "dark"],
            state="readonly",
            width=8,
        )
        theme_combo.pack(side="left")
        theme_combo.bind("<<ComboboxSelected>>", self._on_theme_change)

        self._refresh_table()

    def _on_theme_change(self, _event: tk.Event) -> None:
        choice = self.theme_var.get()
        self._settings["theme"] = choice
        save_settings(self._settings)
        self._colors = _apply_theme(self.root, choice)
        self.error_label.configure(foreground=self._colors["error"])

    def _apply_state(self) -> None:
        if self._state.is_clocked_in:
            self.btn_text.set("Clock Out")
            self.task_var.set("")
            self.task_entry.configure(state="normal")
            self.status_var.set(f"Status: Clocked in — {self._state.current_task}")
            self.switch_btn.grid()
            self._start_timer()
        else:
            self.btn_text.set("Clock In")
            self.task_entry.configure(state="normal")
            self.status_var.set("Status: Clocked out")
            self.elapsed_var.set("Current session: --")
            self.switch_btn.grid_remove()
            self._stop_timer()

    def _toggle_clock(self) -> None:
        self.error_var.set("")
        now = datetime.now()

        if not self._state.is_clocked_in:
            # Clock in
            try:
                task = validate_task_name(self.task_var.get())
            except ValidationError as e:
                self.error_var.set(str(e))
                return
            event = TimeEvent(timestamp=now, event_type=EventType.IN, task_name=task)
        else:
            # Clock out
            task = self._state.current_task or ""
            event = TimeEvent(timestamp=now, event_type=EventType.OUT, task_name=task)

        append_event(CSV_PATH, event)
        self._events = read_events()
        self._state = get_current_state(self._events)
        self._apply_state()
        self._refresh_table()

    def _switch_task(self) -> None:
        self.error_var.set("")
        if not self._state.is_clocked_in:
            return

        try:
            new_task = validate_task_name(self.task_var.get())
        except ValidationError as e:
            self.error_var.set(str(e))
            return

        now = datetime.now()
        old_task = self._state.current_task or ""
        out_event = TimeEvent(timestamp=now, event_type=EventType.OUT, task_name=old_task)
        in_event = TimeEvent(timestamp=now, event_type=EventType.IN, task_name=new_task)
        append_event(CSV_PATH, out_event)
        append_event(CSV_PATH, in_event)

        self._events = read_events()
        self._state = get_current_state(self._events)
        self._apply_state()
        self._refresh_table()

    def _start_timer(self) -> None:
        self._tick()

    def _tick(self) -> None:
        if self._state.clocked_in_since:
            elapsed = datetime.now() - self._state.clocked_in_since
            self.elapsed_var.set(f"Current session: {_format_duration(elapsed)}")
        self._timer_id = self.root.after(1000, self._tick)

    def _stop_timer(self) -> None:
        if self._timer_id is not None:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None

    def _refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        sessions = get_recent_sessions(self._events)
        for s in sessions:
            clock_in = s["clock_in"].strftime("%H:%M") if s["clock_in"] else ""
            clock_out = s["clock_out"].strftime("%H:%M") if s["clock_out"] else "—"
            duration = _format_duration(s["duration"]) if s["duration"] else "—"
            self.tree.insert("", "end", values=(s["task"], clock_in, clock_out, duration))


def _format_duration(td: timedelta) -> str:
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {seconds:02d}s"
    return f"{minutes}m {seconds:02d}s"
