import hashlib
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

import numpy as np
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

from .types import IdentityCluster, RawEvent, UnifiedProfile


def _fingerprint_hash(ip: str, ua: str) -> str:
    raw = f"{ip}|{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _ip_ua_vector(ip: str, ua: str) -> list[float]:
    ip_seed = int(hashlib.md5(ip.encode()).hexdigest()[:8], 16)
    ua_seed = int(hashlib.md5(ua.encode()).hexdigest()[:8], 16)
    return [float(ip_seed % 1000) / 1000.0, float(ua_seed % 1000) / 1000.0]


class IdentityResolver:
    def __init__(self) -> None:
        self._graph: dict[str, set[str]] = defaultdict(set)
        self._profiles: dict[str, UnifiedProfile] = {}
        self._lock: Any = None

    def resolve(self, events: list[RawEvent]) -> list[UnifiedProfile]:
        profiles: dict[str, UnifiedProfile] = {}
        for ev in events:
            cid = self._resolve_single(ev)
            if cid not in profiles:
                profiles[cid] = UnifiedProfile(
                    canonical_id=cid,
                    known_ids=set(),
                    traits={},
                    first_seen=ev.timestamp or datetime.now(timezone.utc),
                    last_seen=ev.timestamp or datetime.now(timezone.utc),
                )
            p = profiles[cid]
            if ev.user_id:
                p.known_ids.add(ev.user_id)
            if ev.anonymous_id:
                p.known_ids.add(ev.anonymous_id)
            p.traits.update(ev.properties)
            if ev.timestamp:
                if p.first_seen is None or ev.timestamp < p.first_seen:
                    p.first_seen = ev.timestamp
                if p.last_seen is None or ev.timestamp > p.last_seen:
                    p.last_seen = ev.timestamp
        return list(profiles.values())

    def _resolve_single(self, ev: RawEvent) -> str:
        if ev.user_id:
            return f"deterministic:{ev.user_id}"
        if ev.anonymous_id:
            candidates = self._graph.get(ev.anonymous_id, set())
            if candidates:
                return next(iter(candidates))
            return f"anonymous:{ev.anonymous_id}"
        fp = _fingerprint_hash(ev.ip, ev.user_agent)
        return f"probabilistic:{fp}"

    def resolve_probabilistic(
        self, events: list[RawEvent]
    ) -> list[IdentityCluster]:
        if len(events) < 2:
            return [
                IdentityCluster(
                    profiles=self.resolve(events), confidence=1.0
                )
            ]
        vectors = []
        for ev in events:
            vectors.append(_ip_ua_vector(ev.ip, ev.user_agent))
        X = np.array(vectors)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        clustering = DBSCAN(eps=0.5, min_samples=1)
        labels = clustering.fit_predict(X_scaled)
        clusters_map: dict[int, list[RawEvent]] = defaultdict(list)
        for ev, label in zip(events, labels):
            clusters_map[int(label)].append(ev)
        clusters: list[IdentityCluster] = []
        for evs in clusters_map.values():
            resolved = self.resolve(evs)
            size = len(evs)
            confidence = min(1.0, size / 10.0)
            clusters.append(IdentityCluster(profiles=resolved, confidence=confidence))
        return clusters

    def merge(
        self, profile_a: UnifiedProfile, profile_b: UnifiedProfile
    ) -> UnifiedProfile:
        merged = UnifiedProfile(
            canonical_id=profile_a.canonical_id,
            known_ids=profile_a.known_ids | profile_b.known_ids,
            traits={**profile_a.traits, **profile_b.traits},
            first_seen=(
                profile_a.first_seen
                if profile_a.first_seen and profile_b.first_seen
                and profile_a.first_seen <= profile_b.first_seen
                else profile_b.first_seen
            ),
            last_seen=(
                profile_a.last_seen
                if profile_a.last_seen and profile_b.last_seen
                and profile_a.last_seen >= profile_b.last_seen
                else profile_b.last_seen
            ),
            segment_ids=list(
                set(profile_a.segment_ids) | set(profile_b.segment_ids)
            ),
        )
        return merged

    def add_edge(self, id_a: str, id_b: str) -> None:
        self._graph[id_a].add(id_b)
        self._graph[id_b].add(id_a)
