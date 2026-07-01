from edgepersona.experimentation.ab_test import ABTestManager


def test_assign_consistent():
    manager = ABTestManager()
    manager.define_experiment("exp1", ["control", "variant_a"])
    v1 = manager.assign("user_123", "exp1")
    v2 = manager.assign("user_123", "exp1")
    assert v1 == v2


def test_assign_different_users():
    manager = ABTestManager()
    manager.define_experiment("exp2", ["control", "treatment"])
    v1 = manager.assign("user_a", "exp2")
    v2 = manager.assign("user_b", "exp2")
    assert v1 in ["control", "treatment"]
    assert v2 in ["control", "treatment"]


def test_record_impression():
    manager = ABTestManager()
    manager.define_experiment("exp3", ["a", "b"])
    manager.record_impression("exp3", "a")
    exp = manager._experiments["exp3"]
    assert exp.impressions["a"] == 1


def test_record_conversion():
    manager = ABTestManager()
    manager.define_experiment("exp4", ["x", "y"])
    manager.record_conversion("exp4", "x")
    exp = manager._experiments["exp4"]
    assert exp.conversions["x"] == 1


def test_chi_squared():
    manager = ABTestManager()
    manager.define_experiment("exp5", ["control", "variant"])
    for _ in range(100):
        manager.record_impression("exp5", "control")
        manager.record_impression("exp5", "variant")
    for _ in range(20):
        manager.record_conversion("exp5", "control")
    for _ in range(30):
        manager.record_conversion("exp5", "variant")
    result = manager.chi_squared_test("exp5")
    assert "p_value" in result
    assert "significant" in result


def test_ttest():
    manager = ABTestManager()
    manager.define_experiment("exp6", ["a", "b"])
    for _ in range(100):
        manager.record_impression("exp6", "a")
        manager.record_impression("exp6", "b")
    for _ in range(25):
        manager.record_conversion("exp6", "a")
    for _ in range(15):
        manager.record_conversion("exp6", "b")
    result = manager.t_test("exp6", "a", "b")
    assert "p_value" in result
    assert "significant" in result


def test_power_analysis():
    manager = ABTestManager()
    result = manager.power_analysis(
        effect_size=0.05, alpha=0.05, power=0.8
    )
    assert result["sample_size_per_variant"] > 0
    assert result["power"] >= 0.8
