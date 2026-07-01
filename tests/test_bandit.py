from edgepersona.experimentation.bandit import MultiArmedBandit


def test_ucb1_select():
    bandit = MultiArmedBandit(
        arm_ids=["A", "B", "C"], algorithm="ucb1", epsilon=0
    )
    arm = bandit.select_arm(context={})
    assert arm in ["A", "B", "C"]


def test_thompson_select():
    bandit = MultiArmedBandit(
        arm_ids=["X", "Y"], algorithm="thompson", epsilon=0
    )
    arm = bandit.select_arm(context={})
    assert arm in ["X", "Y"]


def test_record_reward():
    bandit = MultiArmedBandit(
        arm_ids=["arm1", "arm2"], algorithm="ucb1", epsilon=0
    )
    for _ in range(10):
        arm = bandit.select_arm(context={})
        bandit.record_reward(arm, 1.0)
    assert bandit._counts["arm1"] > 0
    assert bandit._counts["arm2"] > 0
    assert bandit._rewards["arm1"] > 0


def test_epsilon_greedy():
    bandit = MultiArmedBandit(
        arm_ids=["a", "b"], algorithm="ucb1", epsilon=1.0
    )
    selected = set()
    for _ in range(100):
        selected.add(bandit.select_arm(context={}))
    assert len(selected) == 2


def test_bandit_convergence():
    bandit = MultiArmedBandit(
        arm_ids=["good", "bad"], algorithm="ucb1", epsilon=0.05
    )
    for _ in range(500):
        arm = bandit.select_arm(context={})
        reward = 1.0 if arm == "good" else 0.1
        bandit.record_reward(arm, reward)
    good_avg = bandit._rewards["good"] / bandit._counts["good"]
    bad_avg = bandit._rewards["bad"] / bandit._counts["bad"]
    assert good_avg > bad_avg
