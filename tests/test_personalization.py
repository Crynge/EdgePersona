from edgepersona.personalization.engine import (
    PersonalizationEngine,
    PersonalizationResult,
)
from edgepersona.personalization.models import FeatureStore, PersonalizationRule


def test_default_personalization():
    engine = PersonalizationEngine()
    engine.add_rule(
        PersonalizationRule(
            condition="",
            action={"banner": "default_banner"},
            priority=0,
        )
    )
    result = engine.get_personalization("p1", {})
    assert result.content["banner"] == "default_banner"


def test_condition_matching():
    engine = PersonalizationEngine()
    engine.add_rule(
        PersonalizationRule(
            condition="tier == premium",
            action={"banner": "premium_banner", "theme": "dark"},
            priority=10,
        )
    )
    engine.add_rule(
        PersonalizationRule(
            condition="",
            action={"banner": "default_banner", "theme": "light"},
            priority=0,
        )
    )
    result = engine.get_personalization(
        "p2", {"tier": "premium"}
    )
    assert result.content["banner"] == "premium_banner"
    assert result.content["theme"] == "dark"


def test_fallback_rule():
    engine = PersonalizationEngine()
    engine.add_rule(
        PersonalizationRule(
            condition="tier == premium",
            action={"banner": "premium"},
            priority=10,
        )
    )
    engine.add_rule(
        PersonalizationRule(
            condition="",
            action={"banner": "fallback"},
            priority=0,
        )
    )
    result = engine.get_personalization("p3", {"tier": "basic"})
    assert result.content["banner"] == "fallback"


def test_template_rendering():
    engine = PersonalizationEngine()
    engine.add_rule(
        PersonalizationRule(
            condition="",
            action={"message": "Hello $name"},
            priority=0,
        )
    )
    result = engine.get_personalization("p4", {"name": "Alice"})
    assert result.content["message"] == "Hello Alice"


def test_feature_store():
    store = FeatureStore()
    store.set("price_elasticity", "u1", 0.75)
    val = store.lookup("price_elasticity", "u1")
    assert val == 0.75
    val = store.lookup("price_elasticity", "u2")
    assert val is None


def test_feature_store_thread_safety():
    import threading

    store = FeatureStore()
    results = []

    def worker(i: int) -> None:
        store.set("f", f"u{i}", i)
        results.append(store.lookup("f", f"u{i}"))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(results) == 10
