import csv
from datetime import datetime
from pathlib import Path

from models import ClockState, EventType, TimeEvent

CSV_PATH = Path(__file__).parent / "timesheet.csv"
_HEADER = ["timestamp", "event_type", "task_name"]


def read_events(path: Path = CSV_PATH) -> list[TimeEvent]:
    if not path.exists():
        return []
    events: list[TimeEvent] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                events.append(TimeEvent(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    event_type=EventType(row["event_type"]),
                    task_name=row["task_name"],
                ))
            except (KeyError, ValueError):
                continue
    return events


def append_event(path: Path, event: TimeEvent) -> None:
    write_header = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_HEADER)
        if write_header:
            writer.writeheader()
        writer.writerow({
            "timestamp": event.timestamp.isoformat(timespec="seconds"),
            "event_type": event.event_type.value,
            "task_name": event.task_name,
        })


def get_current_state(events: list[TimeEvent]) -> ClockState:
    if not events:
        return ClockState(is_clocked_in=False)
    last = events[-1]
    if last.event_type == EventType.IN:
        return ClockState(
            is_clocked_in=True,
            current_task=last.task_name,
            clocked_in_since=last.timestamp,
        )
    return ClockState(is_clocked_in=False)


def get_recent_sessions(events: list[TimeEvent], limit: int = 20) -> list[dict]:
    sessions: list[dict] = []
    i = 0
    while i < len(events):
        ev = events[i]
        if ev.event_type == EventType.IN:
            session: dict = {
                "task": ev.task_name,
                "clock_in": ev.timestamp,
                "clock_out": None,
                "duration": None,
            }
            if i + 1 < len(events) and events[i + 1].event_type == EventType.OUT:
                out_ev = events[i + 1]
                session["clock_out"] = out_ev.timestamp
                session["duration"] = out_ev.timestamp - ev.timestamp
                i += 2
            else:
                i += 1
            sessions.append(session)
        else:
            i += 1
    sessions.reverse()
    return sessions[:limit]
