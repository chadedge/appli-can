"""Appli-CAN! — core package: the master schema and normalization helpers."""

from .schema import (
    SCHEMA_VERSION,
    Applicant,
    Application,
    Dataset,
    Screening,
    Skill,
    Source,
)

__all__ = [
    "SCHEMA_VERSION",
    "Applicant",
    "Application",
    "Dataset",
    "Screening",
    "Skill",
    "Source",
]
