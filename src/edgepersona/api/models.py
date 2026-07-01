from __future__ import annotations
from typing import Any
from datetime import datetime

from pydantic import BaseModel


class RawEventRequest(BaseModel):
    anonymous_id: str | None = None
    user_id: str | None = None
    event_type: str = ""
    properties: dict[str, Any] = {}
    timestamp: datetime | None = None
    ip: str = ""
    user_agent: str = ""


class IngestRequest(BaseModel):
    events: list[RawEventRequest]


class IdentifyRequest(BaseModel):
    events: list[RawEventRequest]


class ProfileResponse(BaseModel):
    canonical_id: str
    known_ids: list[str]
    traits: dict[str, Any]
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    segment_ids: list[str] = []


class PersonalizeResponse(BaseModel):
    content: dict[str, Any]
    priority: int = 0
    ttl: int = 3600


class ExperimentAssignRequest(BaseModel):
    user_id: str
    experiment_name: str


class ExperimentAssignResponse(BaseModel):
    user_id: str
    experiment_name: str
    variant: str


class ExperimentRecordRequest(BaseModel):
    experiment_name: str
    variant: str
    event_type: str


class ExperimentRecordResponse(BaseModel):
    status: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
