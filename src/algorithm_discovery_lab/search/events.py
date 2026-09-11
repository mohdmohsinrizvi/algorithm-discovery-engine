"""Search event model for structured logging and live UI updates."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any


class EventType(enum.Enum):
    SEARCH_STARTED = "search_started"
    GENERATION_COMPLETED = "generation_completed"
    CANDIDATE_GENERATED = "candidate_generated"
    CANDIDATE_VERIFIED = "candidate_verified"
    CANDIDATE_REJECTED = "candidate_rejected"
    NEW_BEST_FOUND = "new_best_found"
    BENCHMARK_COMPLETED = "benchmark_completed"
    DISCOVERY_CREATED = "discovery_created"
    SEARCH_FINISHED = "search_finished"
    ARCHIVE_UPDATED = "archive_updated"


@dataclass
class SearchEvent:
    event_type: EventType
    generation: int = 0
    candidate_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "generation": self.generation,
            "candidate_id": self.candidate_id,
            "data": self.data,
            "timestamp": self.timestamp,
        }
