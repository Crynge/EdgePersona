from __future__ import annotations
import re
from typing import Any
from threading import Lock

from .ast import (
    And,
    Comparison,
    Exists,
    In,
    Node,
    evaluate,
)
from ..identity.types import UnifiedProfile


class Segment:
    def __init__(self, name: str, condition: str) -> None:
        self.name = name
        self.condition = condition
        self._ast: Node | None = None

    def set_ast(self, ast_node: Node) -> None:
        self._ast = ast_node

    @property
    def ast(self) -> Node | None:
        return self._ast


_TT = re.compile(
    r"(\w+(?:\.\w+)*)\s*(==|!=|>=|<=|>|<|in|exists)\s*(.+?)(?:\s+(and|or)\s+|$)",
    re.IGNORECASE,
)


class SegmentParser:
    def parse(self, condition: str) -> Node:
        tokens = self._tokenize(condition)
        return self._build(tokens)

    def _tokenize(self, s: str) -> list[tuple[str, ...]]:
        s = s.strip()
        result: list[tuple[str, ...]] = []
        pattern = r"(\w+(?:\.\w+)*)\s*(==|!=|>=|<=|>|<|in|exists)\s*('[^']*'|\"[^\"]*\"|\w+(?:\s*-\s*\w+)*\s*[smhd]?|\d+)"
        pos = 0
        while pos < len(s):
            m = re.match(pattern, s[pos:])
            if not m:
                pos += 1
                continue
            lhs = m.group(1)
            op = m.group(2)
            raw = m.group(3).strip().strip("'\"")
            result.append((lhs, op, raw))
            pos += m.end()
        return result

    def _build(self, tokens: list[tuple[str, ...]]) -> Node:
        if not tokens:
            return Comparison("true", "==", True)
        node: Node = self._make_node(tokens[0])
        for t in tokens[1:]:
            node = And(node, self._make_node(t))
        return node

    def _make_node(self, tok: tuple[str, ...]) -> Node:
        lhs, op, raw = tok
        if op.lower() == "in":
            vals = [v.strip().strip("'\"") for v in raw.split(",")]
            return In(lhs, vals)
        if op.lower() == "exists":
            return Exists(lhs)
        rhs: Any = raw
        if raw.isdigit():
            rhs = int(raw)
        else:
            try:
                rhs = float(raw)
            except ValueError:
                rhs = raw
        return Comparison(lhs, op, rhs)


class MembershipStore:
    def __init__(self) -> None:
        self._membership: dict[str, set[str]] = {}
        self._lock = Lock()

    def add(self, profile_id: str, segment_id: str) -> None:
        with self._lock:
            self._membership.setdefault(profile_id, set()).add(segment_id)

    def remove(self, profile_id: str, segment_id: str) -> None:
        with self._lock:
            if profile_id in self._membership:
                self._membership[profile_id].discard(segment_id)

    def get(self, profile_id: str) -> set[str]:
        with self._lock:
            return set(self._membership.get(profile_id, set()))

    def get_all(self) -> dict[str, set[str]]:
        with self._lock:
            return {k: set(v) for k, v in self._membership.items()}


class SegmentEngine:
    def __init__(self) -> None:
        self._segments: dict[str, Segment] = {}
        self._membership = MembershipStore()
        self._parser = SegmentParser()

    def define(self, name: str, condition: str) -> Segment:
        seg = Segment(name, condition)
        ast_node = self._parser.parse(condition)
        seg.set_ast(ast_node)
        self._segments[name] = seg
        return seg

    def evaluate(self, profile: UnifiedProfile) -> set[str]:
        matched: set[str] = set()
        for seg_name, seg in self._segments.items():
            ast_node = seg.ast
            if ast_node and evaluate(ast_node, profile.traits):
                matched.add(seg_name)
                self._membership.add(profile.canonical_id, seg_name)
            else:
                self._membership.remove(profile.canonical_id, seg_name)
        return matched

    def get_membership(self, profile_id: str) -> set[str]:
        return self._membership.get(profile_id)

    def get_segment(self, name: str) -> Segment | None:
        return self._segments.get(name)
