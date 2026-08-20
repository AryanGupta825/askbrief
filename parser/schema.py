"""
Structured criteria schema.

Design notes (see NOTES.md for the full rationale):
- Every optional field defaults to None/empty rather than a guessed value.
- `confidence` tracks, per top-level field, whether the value was explicitly
  stated in the brief or inferred by the model. This is the mechanism that
  lets this parser behave like "Parser A" (complete) without lying like
  "Parser A" does about certainty -- and without going silent like
  "Parser B" on everything that isn't spelled out verbatim.
- Enums are used only where a controlled vocabulary genuinely helps matching
  (seniority, work_mode, role_family). Free text stays free text elsewhere
  (skills, exclusions) because forcing those into an enum would either
  hallucinate a taxonomy or lose information.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Seniority(str, Enum):
    junior = "junior"
    mid = "mid"
    senior = "senior"
    staff_plus = "staff+"


class WorkMode(str, Enum):
    onsite = "onsite"
    hybrid = "hybrid"
    remote = "remote"


class RoleFamily(str, Enum):
    backend = "backend"
    frontend = "frontend"
    fullstack = "fullstack"
    data = "data"
    devops = "devops"
    other = "other"


class Confidence(str, Enum):
    explicit = "explicit"   # stated in the brief in more or less these words
    inferred = "inferred"   # reasonably derived, not literally stated
    not_stated = "not_stated"  # field is null / empty, nothing to go on


class ExperienceRange(BaseModel):
    min_years: Optional[int] = None
    max_years: Optional[int] = None


class Location(BaseModel):
    cities: list[str] = Field(default_factory=list)
    work_mode: Optional[WorkMode] = None


class Compensation(BaseModel):
    min_lpa: Optional[float] = None
    max_lpa: Optional[float] = None
    currency: str = "INR"


class Criteria(BaseModel):
    role_title: Optional[str] = None
    role_family: Optional[RoleFamily] = None
    seniority: Optional[Seniority] = None
    experience: ExperienceRange = Field(default_factory=ExperienceRange)
    must_have_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    location: Location = Field(default_factory=Location)
    domain: Optional[str] = None
    compensation: Compensation = Field(default_factory=Compensation)
    headcount: Optional[int] = None
    exclusions: list[str] = Field(default_factory=list)

    # field_name -> Confidence, only for fields where the model made a call
    # (skills lists / exclusions are covered implicitly: an empty list means
    # nothing found, a populated list means it was found in text -- there's
    # no meaningful "inferred skill" case worth tracking separately)
    confidence: dict[str, Confidence] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
