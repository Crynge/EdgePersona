from edgepersona.segments.ast import (
    And,
    Comparison,
    Exists,
    In,
    Not,
    Or,
    evaluate,
)
from edgepersona.segments.engine import SegmentEngine, SegmentParser
from edgepersona.identity.types import UnifiedProfile


def test_parse_and_evaluate():
    parser = SegmentParser()
    node = parser.parse("event_count > 5")
    assert evaluate(node, {"event_count": 10}) is True
    assert evaluate(node, {"event_count": 3}) is False


def test_and_condition():
    node = And(
        Comparison("event_count", ">", 5),
        Comparison("tier", "==", "premium"),
    )
    assert evaluate(node, {"event_count": 10, "tier": "premium"}) is True
    assert evaluate(node, {"event_count": 10, "tier": "basic"}) is False
    assert evaluate(node, {"event_count": 1, "tier": "premium"}) is False


def test_or_condition():
    node = Or(
        Comparison("event_count", ">", 10),
        Comparison("tier", "==", "premium"),
    )
    assert evaluate(node, {"event_count": 5, "tier": "premium"}) is True
    assert evaluate(node, {"event_count": 15, "tier": "basic"}) is True
    assert evaluate(node, {"event_count": 1, "tier": "basic"}) is False


def test_not_condition():
    node = Not(Comparison("is_bot", "==", True))
    assert evaluate(node, {"is_bot": False}) is True
    assert evaluate(node, {"is_bot": True}) is False


def test_in_operator():
    node = In("country", ["US", "CA"])
    assert evaluate(node, {"country": "US"}) is True
    assert evaluate(node, {"country": "MX"}) is False


def test_exists_operator():
    node = Exists("email")
    assert evaluate(node, {"email": "a@b.com"}) is True
    assert evaluate(node, {}) is False


def test_segment_engine():
    engine = SegmentEngine()
    engine.define("active", "event_count > 5")
    engine.define("vip", "tier == premium")
    profile = UnifiedProfile(
        canonical_id="p1",
        traits={"event_count": 10, "tier": "premium"},
    )
    matched = engine.evaluate(profile)
    assert "active" in matched
    assert "vip" in matched


def test_membership_store():
    engine = SegmentEngine()
    engine.define("test_seg", "score > 50")
    profile = UnifiedProfile(
        canonical_id="p2", traits={"score": 100}
    )
    engine.evaluate(profile)
    membership = engine.get_membership("p2")
    assert "test_seg" in membership


def test_incremental_evaluation():
    engine = SegmentEngine()
    engine.define("high_score", "score > 50")
    p = UnifiedProfile(canonical_id="p3", traits={"score": 30})
    matched = engine.evaluate(p)
    assert "high_score" not in matched
    p.traits["score"] = 80
    matched = engine.evaluate(p)
    assert "high_score" in matched
