from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from ..identity.types import RawEvent, UnifiedProfile


class ProfileStore(ABC):
    @abstractmethod
    def save(self, profile: UnifiedProfile) -> None: ...
    @abstractmethod
    def load(self, profile_id: str) -> UnifiedProfile | None: ...
    @abstractmethod
    def delete(self, profile_id: str) -> None: ...


class EventStore(ABC):
    @abstractmethod
    def append(self, event: RawEvent) -> None: ...
    @abstractmethod
    def query(
        self, profile_id: str, limit: int = 100
    ) -> list[RawEvent]: ...
    @abstractmethod
    def count(self, profile_id: str) -> int: ...


class SegmentStore(ABC):
    @abstractmethod
    def add_member(
        self, segment_id: str, profile_id: str
    ) -> None: ...
    @abstractmethod
    def remove_member(
        self, segment_id: str, profile_id: str
    ) -> None: ...
    @abstractmethod
    def get_members(
        self, segment_id: str
    ) -> set[str]: ...
    @abstractmethod
    def get_segments(
        self, profile_id: str
    ) -> set[str]: ...


class FeatureStore(ABC):
    @abstractmethod
    def set(
        self, feature_name: str, profile_id: str, value: Any
    ) -> None: ...
    @abstractmethod
    def lookup(
        self, feature_name: str, profile_id: str
    ) -> Any: ...
