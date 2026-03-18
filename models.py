from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventType(Enum):
    IN = "IN"
    OUT = "OUT"


@dataclass(frozen=True)
class TimeEvent:
    timestamp: datetime
    event_type: EventType
    task_name: str


@dataclass(frozen=True)
class ClockState:
    is_clocked_in: bool
    current_task: str | None = None
    clocked_in_since: datetime | None = None
