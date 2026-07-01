from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .. import __version__
from ..identity import IdentityResolver
from ..identity.types import RawEvent, UnifiedProfile
from ..segments import SegmentEngine
from ..personalization import PersonalizationEngine, PersonalizationResult
from ..personalization.models import PersonalizationRule
from ..experimentation import ABTestManager
from .models import (
    ExperimentAssignRequest,
    ExperimentAssignResponse,
    ExperimentRecordRequest,
    ExperimentRecordResponse,
    HealthResponse,
    IdentifyRequest,
    IngestRequest,
    PersonalizeResponse,
    ProfileResponse,
)

app = FastAPI(title="EdgePersona", version=__version__)

_identity = IdentityResolver()
_segments = SegmentEngine()
_personalization = PersonalizationEngine()
_ab_test = ABTestManager()


@app.on_event("startup")
async def _startup() -> None:
    _segments.define("active_users", "event_count > 5")
    _segments.define("new_users", "event_count <= 5")
    _personalization.add_rule(
        PersonalizationRule(
            condition="segment == premium",
            action={"banner": "premium_banner", "theme": "dark"},
            priority=10,
        )
    )
    _personalization.add_rule(
        PersonalizationRule(
            condition="",
            action={"banner": "default_banner", "theme": "light"},
            priority=0,
        )
    )
    _ab_test.define_experiment(
        "homepage_redesign", ["control", "variant_a", "variant_b"]
    )


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", version=__version__)


@app.post("/ingest", status_code=201)
async def ingest(req: IngestRequest) -> dict:
    events = [
        RawEvent(
            anonymous_id=e.anonymous_id,
            user_id=e.user_id,
            event_type=e.event_type,
            properties=e.properties,
            timestamp=e.timestamp,
            ip=e.ip,
            user_agent=e.user_agent,
        )
        for e in req.events
    ]
    _identity.resolve(events)
    return {"ingested": len(events), "status": "ok"}


@app.post("/identify")
async def identify(req: IdentifyRequest) -> list[ProfileResponse]:
    events = [
        RawEvent(
            anonymous_id=e.anonymous_id,
            user_id=e.user_id,
            event_type=e.event_type,
            properties=e.properties,
            timestamp=e.timestamp,
            ip=e.ip,
            user_agent=e.user_agent,
        )
        for e in req.events
    ]
    profiles = _identity.resolve(events)
    return [
        ProfileResponse(
            canonical_id=p.canonical_id,
            known_ids=list(p.known_ids),
            traits=p.traits,
            first_seen=p.first_seen,
            last_seen=p.last_seen,
            segment_ids=p.segment_ids,
        )
        for p in profiles
    ]


@app.get("/profile/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str) -> ProfileResponse:
    segments = _segments.get_membership(profile_id)
    return ProfileResponse(
        canonical_id=profile_id,
        known_ids=[profile_id],
        traits={},
        segment_ids=list(segments) if segments else [],
    )


@app.get("/personalize/{profile_id}", response_model=PersonalizeResponse)
async def personalize(profile_id: str) -> PersonalizeResponse:
    segments = _segments.get_membership(profile_id) or set()
    context: dict = {"profile_id": profile_id, "segment": ""}
    if "premium" in segments:
        context["segment"] = "premium"
    result = _personalization.get_personalization(profile_id, context)
    return PersonalizeResponse(
        content=result.content,
        priority=result.priority,
        ttl=result.ttl,
    )


@app.post(
    "/experiment/assign",
    response_model=ExperimentAssignResponse,
)
async def experiment_assign(
    req: ExperimentAssignRequest,
) -> ExperimentAssignResponse:
    variant = _ab_test.assign(req.user_id, req.experiment_name)
    return ExperimentAssignResponse(
        user_id=req.user_id,
        experiment_name=req.experiment_name,
        variant=variant,
    )


@app.post("/experiment/record", response_model=ExperimentRecordResponse)
async def experiment_record(
    req: ExperimentRecordRequest,
) -> ExperimentRecordResponse:
    if req.event_type == "impression":
        _ab_test.record_impression(req.experiment_name, req.variant)
    elif req.event_type == "conversion":
        _ab_test.record_conversion(req.experiment_name, req.variant)
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown event_type: {req.event_type}",
        )
    return ExperimentRecordResponse(status="ok")
