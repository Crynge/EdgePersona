from datetime import datetime, timezone

from edgepersona.identity.resolver import IdentityResolver
from edgepersona.identity.types import RawEvent, UnifiedProfile


def test_deterministic_resolution():
    resolver = IdentityResolver()
    events = [
        RawEvent(
            user_id="user_1",
            anonymous_id="anon_1",
            event_type="page_view",
            properties={"page": "/home"},
            timestamp=datetime.now(timezone.utc),
        ),
        RawEvent(
            user_id="user_1",
            anonymous_id="anon_2",
            event_type="click",
            properties={"button": "signup"},
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    profiles = resolver.resolve(events)
    assert len(profiles) == 1
    assert profiles[0].canonical_id == "deterministic:user_1"


def test_pure_anonymous_resolution():
    resolver = IdentityResolver()
    events = [
        RawEvent(
            anonymous_id="anon_x",
            event_type="page_view",
            properties={"page": "/pricing"},
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    profiles = resolver.resolve(events)
    assert len(profiles) == 1
    assert "anonymous:anon_x" in profiles[0].canonical_id


def test_merge_profiles():
    resolver = IdentityResolver()
    a = UnifiedProfile(
        canonical_id="user_a",
        known_ids={"user_a", "anon_a"},
        traits={"country": "US"},
        first_seen=datetime(2024, 1, 1, tzinfo=timezone.utc),
        last_seen=datetime(2024, 6, 1, tzinfo=timezone.utc),
        segment_ids=["active"],
    )
    b = UnifiedProfile(
        canonical_id="user_b",
        known_ids={"user_b", "anon_b"},
        traits={"tier": "premium"},
        first_seen=datetime(2024, 3, 1, tzinfo=timezone.utc),
        last_seen=datetime(2024, 9, 1, tzinfo=timezone.utc),
        segment_ids=["premium"],
    )
    merged = resolver.merge(a, b)
    assert "user_a" in merged.known_ids
    assert "user_b" in merged.known_ids
    assert merged.traits["country"] == "US"
    assert merged.traits["tier"] == "premium"
    assert merged.first_seen == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert merged.last_seen == datetime(2024, 9, 1, tzinfo=timezone.utc)
    assert "active" in merged.segment_ids
    assert "premium" in merged.segment_ids


def test_probabilistic_clustering():
    resolver = IdentityResolver()
    events = [
        RawEvent(
            anonymous_id="a1",
            event_type="view",
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        ),
        RawEvent(
            anonymous_id="a2",
            event_type="view",
            ip="192.168.1.1",
            user_agent="Mozilla/5.0",
        ),
    ]
    clusters = resolver.resolve_probabilistic(events)
    assert len(clusters) >= 1


def test_add_edge():
    resolver = IdentityResolver()
    resolver.add_edge("id_a", "id_b")
    resolver.add_edge("id_b", "id_c")
    ev = RawEvent(anonymous_id="id_a")
    result = resolver.resolve([ev])
    assert len(result) == 1
