from __future__ import annotations
from threading import Lock
from typing import Any
from collections import defaultdict

from ..identity.types import RawEvent, UnifiedProfile
from .interfaces import EventStore, FeatureStore, ProfileStore, SegmentStore


class InMemoryProfileStore(ProfileStore):
    def __init__(self) -> None:
        self._data: dict[str, UnifiedProfile] = {}
        self._lock = Lock()

    def save(self, profile: UnifiedProfile) -> None:
        with self._lock:
            self._data[profile.canonical_id] = profile

    def load(self, profile_id: str) -> UnifiedProfile | None:
        with self._lock:
            return self._data.get(profile_id)

    def delete(self, profile_id: str) -> None:
        with self._lock:
            self._data.pop(profile_id, None)


class InMemoryEventStore(EventStore):
    def __init__(self) -> None:
        self._events: dict[str, list[RawEvent]] = defaultdict(list)
        self._lock = Lock()

    def append(self, event: RawEvent) -> None:
        with self._lock:
            key = event.user_id or event.anonymous_id or "unknown"
            self._events[key].append(event)

    def query(
        self, profile_id: str, limit: int = 100
    ) -> list[RawEvent]:
        with self._lock:
            events = self._events.get(profile_id, [])
            return events[-limit:]

    def count(self, profile_id: str) -> int:
        with self._lock:
            return len(self._events.get(profile_id, []))


class InMemorySegmentStore(SegmentStore):
    def __init__(self) -> None:
        self._segment_to_profiles: dict[str, set[str]] = defaultdict(set)
        self._profile_to_segments: dict[str, set[str]] = defaultdict(set)
        self._lock = Lock()

    def add_member(self, segment_id: str, profile_id: str) -> None:
        with self._lock:
            self._segment_to_profiles[segment_id].add(profile_id)
            self._profile_to_segments[profile_id].add(segment_id)

    def remove_member(self, segment_id: str, profile_id: str) -> None:
        with self._lock:
            self._segment_to_profiles.get(segment_id, set()).discard(
                profile_id
            )
            self._profile_to_segments.get(profile_id, set()).discard(
                segment_id
            )

    def get_members(self, segment_id: str) -> set[str]:
        with self._lock:
            return set(self._segment_to_profiles.get(segment_id, set()))

    def get_segments(self, profile_id: str) -> set[str]:
        with self._lock:
            return set(self._profile_to_segments.get(profile_id, set()))


class InMemoryFeatureStore(FeatureStore):
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def set(self, feature_name: str, profile_id: str, value: Any) -> None:
        with self._lock:
            self._data.setdefault(feature_name, {})[profile_id] = value

    def lookup(self, feature_name: str, profile_id: str) -> Any:
        with self._lock:
            return self._data.get(feature_name, {}).get(profile_id)
