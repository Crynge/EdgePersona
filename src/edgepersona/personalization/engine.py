from __future__ import annotations
from dataclasses import dataclass, field
from string import Template
from typing import Any

from .models import FeatureStore, PersonalizationRule


@dataclass
class PersonalizationResult:
    content: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    ttl: int = 3600


class PersonalizationEngine:
    def __init__(self) -> None:
        self._rules: list[PersonalizationRule] = []
        self._feature_store = FeatureStore()

    def add_rule(self, rule: PersonalizationRule) -> None:
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)

    def get_personalization(
        self, profile_id: str, context: dict[str, Any] | None = None
    ) -> PersonalizationResult:
        ctx = context or {}
        matched = PersonalizationResult()
        for rule in self._rules:
            if self._evaluate_condition(rule.condition, ctx):
                rendered = self._render(rule.action, ctx)
                matched.content.update(rendered)
                matched.priority = rule.priority
                matched.ttl = rule.ttl
                break
        feature_content = self._feature_store.lookup("personalized", profile_id)
        if feature_content:
            matched.content.update(feature_content)
        return matched

    def _evaluate_condition(self, condition: str, ctx: dict[str, Any]) -> bool:
        if not condition:
            return True
        parts = condition.split()
        if len(parts) == 3:
            lhs = ctx.get(parts[0])
            op = parts[1]
            rhs = parts[2]
            if op == "==":
                return str(lhs) == str(rhs)
            if op == "!=":
                return str(lhs) != str(rhs)
            if op == ">":
                try:
                    return float(lhs or 0) > float(rhs)
                except (ValueError, TypeError):
                    return False
        return True

    def _render(
        self, action: dict[str, Any], ctx: dict[str, Any]
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, val in action.items():
            if isinstance(val, str):
                try:
                    t = Template(val)
                    result[key] = t.safe_substitute(ctx)
                except Exception:
                    result[key] = val
            else:
                result[key] = val
        return result
