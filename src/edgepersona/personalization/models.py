from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from threading import Lock


@dataclass
class PersonalizationRule:
    condition: str = ""
    action: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    ttl: int = 3600


class FeatureStore:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def set(self, feature_name: str, profile_id: str, value: Any) -> None:
        with self._lock:
            self._store.setdefault(feature_name, {})[profile_id] = value

    def lookup(self, feature_name: str, profile_id: str) -> Any:
        with self._lock:
            features = self._store.get(feature_name, {})
            return features.get(profile_id, None)
