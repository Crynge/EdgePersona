from __future__ import annotations
from typing import Any
from datetime import datetime, timedelta, timezone
import re


class Node:
    pass


class And(Node):
    def __init__(self, left: Node, right: Node) -> None:
        self.left = left
        self.right = right


class Or(Node):
    def __init__(self, left: Node, right: Node) -> None:
        self.left = left
        self.right = right


class Not(Node):
    def __init__(self, node: Node) -> None:
        self.node = node


class Comparison(Node):
    def __init__(self, lhs: str, op: str, rhs: Any) -> None:
        self.lhs = lhs
        self.op = op
        self.rhs = rhs


class In(Node):
    def __init__(self, lhs: str, values: list[Any]) -> None:
        self.lhs = lhs
        self.values = values


class Exists(Node):
    def __init__(self, field: str) -> None:
        self.field = field


class Function(Node):
    def __init__(self, name: str, args: list[Node]) -> None:
        self.name = name
        self.args = args


def _resolve_trait(traits: dict[str, Any], key: str) -> Any:
    parts = key.split(".")
    val: Any = traits
    for part in parts:
        if isinstance(val, dict):
            val = val.get(part, None)
        else:
            return None
    return val


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_duration(dur: str) -> timedelta:
    match = re.match(r"(\d+)\s*(s|m|h|d)", dur.strip())
    if not match:
        return timedelta()
    n = int(match.group(1))
    unit = match.group(2)
    mapping = {"s": "seconds", "m": "minutes", "h": "hours", "d": "days"}
    return timedelta(**{mapping[unit]: n})


def evaluate(node: Node, traits: dict[str, Any]) -> bool:
    if isinstance(node, And):
        return evaluate(node.left, traits) and evaluate(node.right, traits)
    if isinstance(node, Or):
        return evaluate(node.left, traits) or evaluate(node.right, traits)
    if isinstance(node, Not):
        return not evaluate(node.node, traits)
    if isinstance(node, Comparison):
        lhs_val = _resolve_trait(traits, node.lhs)
        rhs_val = node.rhs
        if isinstance(rhs_val, str) and rhs_val.startswith("now - "):
            rhs_val = _now() - _parse_duration(rhs_val[5:])
        if node.op == "==":
            return lhs_val == rhs_val
        if node.op == "!=":
            return lhs_val != rhs_val
        if node.op == ">":
            if lhs_val is None:
                return False
            return lhs_val > rhs_val
        if node.op == ">=":
            if lhs_val is None:
                return False
            return lhs_val >= rhs_val
        if node.op == "<":
            if lhs_val is None:
                return False
            return lhs_val < rhs_val
        if node.op == "<=":
            if lhs_val is None:
                return False
            return lhs_val <= rhs_val
        return False
    if isinstance(node, In):
        lhs_val = _resolve_trait(traits, node.lhs)
        return lhs_val in node.values
    if isinstance(node, Exists):
        return _resolve_trait(traits, node.field) is not None
    if isinstance(node, Function):
        if node.name == "count":
            val = _resolve_trait(traits, node.args[0].lhs) if node.args else None
            return isinstance(val, (int, float))
        return False
    return False
