from __future__ import annotations
import hashlib
import math
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from scipy import stats


@dataclass
class Experiment:
    name: str
    variants: list[str] = field(default_factory=list)
    impressions: dict[str, int] = field(default_factory=dict)
    conversions: dict[str, int] = field(default_factory=dict)


class ABTestManager:
    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._assignments: dict[str, dict[str, str]] = {}
        self._lock = Lock()

    def define_experiment(
        self, name: str, variants: list[str]
    ) -> Experiment:
        exp = Experiment(
            name=name,
            variants=variants,
            impressions={v: 0 for v in variants},
            conversions={v: 0 for v in variants},
        )
        with self._lock:
            self._experiments[name] = exp
        return exp

    def assign(self, user_id: str, experiment_name: str) -> str:
        with self._lock:
            if (
                user_id in self._assignments
                and experiment_name in self._assignments[user_id]
            ):
                return self._assignments[user_id][experiment_name]
        exp = self._experiments.get(experiment_name)
        if not exp or not exp.variants:
            return "control"
        hash_val = hashlib.sha256(
            f"{user_id}:{experiment_name}".encode()
        ).hexdigest()
        idx = int(hash_val[:8], 16) % len(exp.variants)
        variant = exp.variants[idx]
        with self._lock:
            self._assignments.setdefault(user_id, {})[experiment_name] = variant
        return variant

    def record_impression(
        self, experiment_name: str, variant: str
    ) -> None:
        with self._lock:
            exp = self._experiments.get(experiment_name)
            if exp and variant in exp.impressions:
                exp.impressions[variant] += 1

    def record_conversion(
        self, experiment_name: str, variant: str
    ) -> None:
        with self._lock:
            exp = self._experiments.get(experiment_name)
            if exp and variant in exp.conversions:
                exp.conversions[variant] += 1

    def chi_squared_test(
        self, experiment_name: str
    ) -> dict[str, Any]:
        exp = self._experiments.get(experiment_name)
        if not exp:
            return {"p_value": 1.0, "significant": False}
        observed: list[int] = []
        for v in exp.variants:
            imps = exp.impressions.get(v, 0)
            convs = exp.conversions.get(v, 0)
            observed.append(convs)
            observed.append(imps - convs)
        if len(exp.variants) < 2:
            return {"p_value": 1.0, "significant": False}
        dof = len(exp.variants) - 1
        total_per_variant = [
            exp.impressions.get(v, 0) for v in exp.variants
        ]
        total_conversions = sum(
            exp.conversions.get(v, 0) for v in exp.variants
        )
        total_impressions = sum(total_per_variant)
        if total_impressions == 0:
            return {"p_value": 1.0, "significant": False}
        expected: list[float] = []
        for i, v in enumerate(exp.variants):
            expected_per_variant = (
                total_per_variant[i] * total_conversions / total_impressions
            )
            expected.append(expected_per_variant)
            expected.append(total_per_variant[i] - expected_per_variant)
        chi2 = 0.0
        for o, e in zip(observed, expected):
            if e > 0:
                chi2 += (o - e) ** 2 / e
        p = 1.0 - stats.chi2.cdf(chi2, dof)
        return {"chi_squared": chi2, "p_value": p, "significant": p < 0.05}

    def t_test(
        self, experiment_name: str, variant_a: str, variant_b: str
    ) -> dict[str, Any]:
        exp = self._experiments.get(experiment_name)
        if not exp:
            return {"p_value": 1.0, "significant": False}
        n_a = exp.impressions.get(variant_a, 0)
        n_b = exp.impressions.get(variant_b, 0)
        c_a = exp.conversions.get(variant_a, 0)
        c_b = exp.conversions.get(variant_b, 0)
        if n_a < 2 or n_b < 2:
            return {"p_value": 1.0, "significant": False}
        rate_a = c_a / n_a
        rate_b = c_b / n_b
        pooled = (c_a + c_b) / (n_a + n_b)
        se = math.sqrt(
            pooled * (1 - pooled) * (1 / n_a + 1 / n_b)
        )
        if se == 0:
            return {"p_value": 1.0, "significant": False}
        t = (rate_a - rate_b) / se
        dof = n_a + n_b - 2
        p = 2 * (1 - stats.t.cdf(abs(t), dof))
        return {"t_statistic": t, "p_value": p, "significant": p < 0.05}

    def power_analysis(
        self,
        effect_size: float = 0.05,
        alpha: float = 0.05,
        power: float = 0.8,
    ) -> dict[str, Any]:
        n = 1
        while True:
            dof = 2 * n - 2
            t_crit = stats.t.ppf(1 - alpha / 2, dof)
            ncp = effect_size / math.sqrt(2 / n)
            p = 1 - stats.nct.cdf(t_crit, dof, ncp) + stats.nct.cdf(
                -t_crit, dof, ncp
            )
            if p >= power:
                return {
                    "sample_size_per_variant": n,
                    "effect_size": effect_size,
                    "alpha": alpha,
                    "power": power,
                }
            n += 1
            if n > 1000000:
                return {
                    "sample_size_per_variant": n,
                    "effect_size": effect_size,
                    "alpha": alpha,
                    "power": p,
                }
