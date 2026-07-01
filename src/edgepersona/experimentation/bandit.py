from __future__ import annotations
import math
import random
from typing import Any


class MultiArmedBandit:
    def __init__(
        self,
        arm_ids: list[str],
        algorithm: str = "ucb1",
        epsilon: float = 0.1,
    ) -> None:
        self.arm_ids = arm_ids
        self.algorithm = algorithm
        self.epsilon = epsilon
        self._counts: dict[str, int] = {a: 1 for a in arm_ids}
        self._rewards: dict[str, float] = {a: 0.0 for a in arm_ids}
        self._total_pulls = len(arm_ids)

    def select_arm(self, context: dict[str, Any] | None = None) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.arm_ids)
        if self.algorithm == "ucb1":
            return self._ucb1_select()
        if self.algorithm == "thompson":
            return self._thompson_select()
        return self._ucb1_select()

    def _ucb1_select(self) -> str:
        best_arm = self.arm_ids[0]
        best_score = -float("inf")
        for arm in self.arm_ids:
            c = self._counts[arm]
            avg = self._rewards[arm] / c
            bonus = math.sqrt(2 * math.log(self._total_pulls) / c)
            score = avg + bonus
            if score > best_score:
                best_score = score
                best_arm = arm
        return best_arm

    def _thompson_select(self) -> str:
        best_arm = self.arm_ids[0]
        best_sample = -float("inf")
        for arm in self.arm_ids:
            alpha = self._rewards[arm] + 1
            beta = self._counts[arm] - self._rewards[arm] + 1
            sample = random.betavariate(alpha, beta)
            if sample > best_sample:
                best_sample = sample
                best_arm = arm
        return best_arm

    def record_reward(self, arm: str, reward: float) -> None:
        if arm in self._counts:
            self._counts[arm] += 1
            self._rewards[arm] += reward
            self._total_pulls += 1
