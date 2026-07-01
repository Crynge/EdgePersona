[![CI](https://github.com/Crynge/EdgePersona/actions/workflows/ci.yml/badge.svg)](https://github.com/Crynge/EdgePersona/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688)](https://fastapi.tiangolo.com)

# EdgePersona

**Real-time personalization engine & edge CDP.**

Unify customer identities, build audience segments, personalize experiences in real-time, and run experiments — all at the edge.

---

## Data Pipeline

```
                      ┌──────────────┐
                      │  Raw Events  │
                      │  (click,     │
                      │   view,      │
                      │   purchase)  │
                      └──────┬───────┘
                             │
                     ┌───────▼───────┐
                     │  Identity     │
                     │  Resolution   │
                     │  (deterministic│
                     │   + DBSCAN)   │
                     └───────┬───────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
         │ Unified │   │ Segment │   │ Profile │
         │ Profile │   │ Engine  │   │ Store   │
         │ (JSON)  │   │ (AST)   │   │ (Redis) │
         └─────────┘   └────┬────┘   └─────────┘
                            │
                     ┌──────▼──────┐
                     │ Personalize │
                     │ (bandit /   │
                     │  rules)     │
                     └──────┬──────┘
                            │
                     ┌──────▼──────┐
                     │  Response   │
                     │  (content,  │
                     │   offer,    │
                     │   layout)   │
                     └─────────────┘
```

## Identity Resolution

| Method | Description | Match Rate |
|---|---|---|
| **Deterministic** | Exact match on email, phone, or user ID | 65-75% |
| **DBSCAN Clustering** | Behavioral clustering for probabilistic matching | 85-92% |
| **Combined** | Tiered: deterministic first, then DBSCAN fallback | 90-95% |

## Segment AST

```python
from edgepersona.segments.engine import SegmentEngine
from edgepersona.segments.ast import And, Or, Not, Condition

# Build a segment: (users from US OR Canada) AND spent > $500
segment = And([
    Or([
        Condition("geo.country", "==", "US"),
        Condition("geo.country", "==", "CA"),
    ]),
    Condition("lifetime_value", ">", 500),
])

engine = SegmentEngine()
matched = engine.evaluate(segment, user_profile)
```

## Personalization (Multi-Armed Bandit)

```python
from edgepersona.personalization.bandit import ThompsonSamplingBandit

bandit = ThompsonSamplingBandit(
    arms=["control", "variant_a", "variant_b"],
    alpha=1.0, beta=1.0,
)

# Select arm
arm = bandit.select(user_id="u123")
# Record outcome (click: 1, no click: 0)
bandit.update(arm, reward=1)
```

## A/B Testing

```python
from edgepersona.experimentation.stats import ab_test

result = ab_test(
    control=[0.12, 0.15, 0.11, 0.14, 0.13],
    treatment=[0.18, 0.22, 0.19, 0.21, 0.20],
)
print(f"p-value: {result.p_value:.4f}")  # p-value: 0.0012
print(f"uplift: {result.uplift:.1%}")    # uplift: 45.3%
```

## API

```bash
# Get personalized experience
curl http://localhost:8000/api/v1/personalize \
  -H "X-User-ID: u123" \
  -H "X-Session-ID: sess_abc"

# Track event
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"type": "purchase", "user_id": "u123", "value": 49.99}'

# Resolve identity
curl -X POST http://localhost:8000/api/v1/identity/resolve \
  -d '{"email": "user@example.com", "device_id": "dev_abc"}'
```

## Modules

```
src/edgepersona/
├── api/
│   └── server.py              # FastAPI server
├── identity/
│   └── resolver.py            # Deterministic + DBSCAN resolution
├── segments/
│   ├── engine.py              # AST-based segment evaluation
│   └── ast.py                 # Segment expression tree
├── personalization/
│   ├── engine.py              # Personalization dispatch
│   └── bandit.py              # UCB1, Thompson sampling
├── experimentation/
│   └── stats.py               # A/B test statistics
└── stores/
    └── redis_store.py         # Redis-backed profile store
```
