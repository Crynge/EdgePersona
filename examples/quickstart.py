"""EdgePersona Quickstart - demonstrates core functionality."""

from datetime import datetime, timezone

from edgepersona.identity import IdentityResolver
from edgepersona.identity.types import RawEvent
from edgepersona.segments import SegmentEngine
from edgepersona.personalization import PersonalizationEngine
from edgepersona.personalization.models import PersonalizationRule
from edgepersona.experimentation import MultiArmedBandit, ABTestManager


def main() -> None:
    # 1. Identity Resolution
    resolver = IdentityResolver()
    events = [
        RawEvent(
            user_id="alice",
            anonymous_id="anon_a1",
            event_type="page_view",
            properties={"page": "/pricing"},
            timestamp=datetime.now(timezone.utc),
        ),
        RawEvent(
            user_id="alice",
            anonymous_id="anon_a2",
            event_type="click",
            properties={"button": "signup"},
            timestamp=datetime.now(timezone.utc),
        ),
    ]
    profiles = resolver.resolve(events)
    print(f"Resolved {len(profiles)} profile(s)")
    for p in profiles:
        print(f"  Canonical ID: {p.canonical_id}")
        print(f"  Known IDs: {p.known_ids}")

    # 2. Segment Engine
    engine = SegmentEngine()
    engine.define("active_users", "event_count > 5")
    engine.define("new_users", "event_count <= 5")
    from edgepersona.identity.types import UnifiedProfile

    profile = UnifiedProfile(
        canonical_id="alice",
        traits={"event_count": 12, "tier": "premium"},
    )
    matched = engine.evaluate(profile)
    print(f"Matched segments: {matched}")

    # 3. Personalization
    p_engine = PersonalizationEngine()
    p_engine.add_rule(
        PersonalizationRule(
            condition="tier == premium",
            action={"banner": "premium_banner", "theme": "dark"},
            priority=10,
        )
    )
    p_engine.add_rule(
        PersonalizationRule(
            condition="",
            action={"banner": "default_banner", "theme": "light"},
            priority=0,
        )
    )
    result = p_engine.get_personalization("alice", {"tier": "premium"})
    print(f"Personalization: {result.content}")

    # 4. Multi-Armed Bandit
    bandit = MultiArmedBandit(
        arm_ids=["hero_a", "hero_b", "hero_c"],
        algorithm="ucb1",
        epsilon=0.1,
    )
    for _ in range(100):
        arm = bandit.select_arm({})
        reward = 1.0 if arm == "hero_a" else 0.5
        bandit.record_reward(arm, reward)
    print(f"Bandit arm counts: {dict(bandit._counts)}")

    # 5. A/B Testing
    ab = ABTestManager()
    ab.define_experiment("landing_page", ["control", "variant_a"])
    for user_id in [f"user_{i}" for i in range(100)]:
        variant = ab.assign(user_id, "landing_page")
        ab.record_impression("landing_page", variant)
        if hash(user_id) % 3 == 0:
            ab.record_conversion("landing_page", variant)
    chi = ab.chi_squared_test("landing_page")
    print(f"Chi-squared test: p={chi['p_value']:.4f}, significant={chi['significant']}")


if __name__ == "__main__":
    main()
