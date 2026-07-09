"""The Appli-CAN! master schema.

One normalized structure that every vendor's ATS dump gets mapped onto, so that
mismatched exports (Workday, Greenhouse, generic CSV, flattened PDF, ...) can be
compared and reported on together.

Design contract:
  * Canonical fields are NORMALIZED (dates -> ISO date, scores -> 0-100,
    stages/outcomes -> canonical vocab from data/mappings.yml, fit tier -> a
    0.0-1.0 fit_quality).
  * The verbatim vendor value is preserved alongside every normalized field
    (the ``*_raw`` companions) so nothing is silently reinterpreted.
  * Anything we do NOT recognize is preserved in an ``extra`` bag rather than
    dropped. Models use ``extra="forbid"`` so unmapped keys can't leak in by
    accident — the normalizer must route them into ``extra`` deliberately.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = "0.1.0"

_STRICT = ConfigDict(extra="forbid")


class Skill(BaseModel):
    """A single parsed/matched skill. ``name`` is lowercased on normalization."""

    model_config = _STRICT

    name: str
    confidence: Optional[float] = Field(None, ge=0, le=1)
    baseline_match: Optional[bool] = None


class Screening(BaseModel):
    """Automated screening telemetry — the black-box output we're after."""

    model_config = _STRICT

    match_score: Optional[float] = Field(
        None, ge=0, le=100, description="Normalized to a 0-100 scale."
    )
    match_score_raw: Optional[Any] = Field(
        None, description="Value exactly as the vendor gave it (0.63, '59 / 100', 68%...)."
    )
    fit_tier_raw: Optional[str] = Field(None, description="Vendor tier verbatim (A, Gold, ...).")
    fit_quality: Optional[float] = Field(
        None, ge=0, le=1, description="Cross-vendor tier quality; our mapping, not the vendor's."
    )
    parsed_skills: list[Skill] = Field(default_factory=list)
    auto_screened: Optional[bool] = None
    keyword_hits: Optional[int] = Field(None, ge=0)
    keyword_misses: Optional[int] = Field(None, ge=0)


class Application(BaseModel):
    """One role you applied to at one company — the core record."""

    model_config = _STRICT

    # Identity
    company: str
    role_title: str = Field(description="Kept verbatim; job titles don't safely merge.")
    requisition_id: Optional[str] = None

    # Dates — normalized to ISO date, raw string preserved
    applied_date: Optional[date] = None
    applied_date_raw: Optional[str] = None
    dispositioned_date: Optional[date] = None
    dispositioned_date_raw: Optional[str] = None

    # Funnel
    stage_reached: Optional[str] = Field(None, description="Canonical stage from mappings.yml.")
    stage_reached_raw: Optional[str] = None

    # Outcome
    outcome: Optional[str] = Field(None, description="Canonical outcome from mappings.yml.")
    disposition_raw: Optional[str] = None

    # Automated telemetry
    screening: Screening = Field(default_factory=Screening)
    inferences: dict[str, Any] = Field(
        default_factory=dict, description="Freeform automated inferences (seniority, gaps, ...)."
    )

    # Provenance
    source_vendor: Optional[str] = None
    source_file: Optional[str] = None

    # Extension mechanism — unmapped vendor fields, preserved verbatim
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _require_some_applied_date(self) -> "Application":
        if self.applied_date is None and not self.applied_date_raw:
            raise ValueError(
                "an application needs at least applied_date or applied_date_raw "
                "(use 'unknown' if the dump truly omitted it)"
            )
        return self


class Applicant(BaseModel):
    """You — recorded once per dataset."""

    model_config = _STRICT

    full_name: Optional[str] = None
    emails: list[str] = Field(default_factory=list)
    phone: Optional[str] = None
    location: Optional[str] = None
    ca_resident: Optional[bool] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Source(BaseModel):
    """Provenance for one company's dump; ties back to tracker.md."""

    model_config = _STRICT

    company: str
    ats_vendor: Optional[str] = None
    source_files: list[str] = Field(default_factory=list)
    request_date: Optional[date] = None
    received_date: Optional[date] = None
    withholding_noted: Optional[bool] = Field(
        None, description="Did the response admit to withholding data under trade-secret claims?"
    )
    extra: dict[str, Any] = Field(default_factory=dict)


class Dataset(BaseModel):
    """The whole normalized picture: you, your requests, and every application."""

    model_config = _STRICT

    schema_version: str = SCHEMA_VERSION
    applicant: Applicant
    sources: list[Source] = Field(default_factory=list)
    applications: list[Application] = Field(default_factory=list)
