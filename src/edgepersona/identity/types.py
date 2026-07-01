from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class RawEvent:
    anonymous_id: str | None = None
    user_id: str | None = None
    event_type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None
    ip: str = ""
    user_agent: str = ""


@dataclass
class UnifiedProfile:
    canonical_id: str = ""
    known_ids: set[str] = field(default_factory=set)
    traits: dict[str, Any] = field(default_factory=dict)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    segment_ids: list[str] = field(default_factory=list)


@dataclass
class IdentityCluster:
    profiles: list[UnifiedProfile] = field(default_factory=list)
    confidence: float = 0.0
