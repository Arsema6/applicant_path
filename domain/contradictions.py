"""Deterministic consistency checks for evidence-backed applications."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Contradiction:
    code: str
    severity: str
    fields: tuple[str, ...]
    message: str
    resolution: str


def _numeric_value(evidence: dict[str, Any], field: str) -> float | None:
    entry = evidence.get(field)
    if not isinstance(entry, dict):
        return None

    value = entry.get("value")
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    try:
        cleaned = str(value).replace(",", "").strip()
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _has_established_value(evidence: dict[str, Any], field: str) -> bool:
    entry = evidence.get(field)
    return (
        isinstance(entry, dict)
        and entry.get("value") not in (None, "")
        and entry.get("status", "missing") == "established"
    )


def detect_contradictions(evidence: dict[str, Any]) -> list[Contradiction]:
    """Return only contradictions that can be proven from established values."""

    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a dictionary")

    contradictions: list[Contradiction] = []

    ownership_fields = ("women_ownership_percent", "men_ownership_percent")
    ownership_total = sum(
        _numeric_value(evidence, field) or 0
        for field in ownership_fields
        if _has_established_value(evidence, field)
    )
    if all(_has_established_value(evidence, field) for field in ownership_fields):
        if ownership_total != 100:
            contradictions.append(
                Contradiction(
                    code="OWNERSHIP_TOTAL_NOT_100",
                    severity="high",
                    fields=ownership_fields,
                    message=f"Ownership percentages total {ownership_total:g}%, not 100%.",
                    resolution="Confirm the ownership split with the applicant.",
                )
            )

    total_employees = _numeric_value(evidence, "employees_current")
    if total_employees is not None:
        for field, label in (
            ("female_employees_current", "female"),
            ("youth_employees_current", "youth"),
        ):
            count = _numeric_value(evidence, field)
            if count is not None and count > total_employees:
                contradictions.append(
                    Contradiction(
                        code=f"{field.upper()}_EXCEEDS_TOTAL",
                        severity="high",
                        fields=(field, "employees_current"),
                        message=(
                            f"{label.capitalize()} employees ({count:g}) exceed "
                            f"total employees ({total_employees:g})."
                        ),
                        resolution="Confirm the employee counts and their reporting period.",
                    )
                )

    for year in range(2022, 2027):
        total_field = f"employees_{year}"
        for subgroup in ("female", "youth"):
            subgroup_field = f"{subgroup}_employees_{year}"
            total = _numeric_value(evidence, total_field)
            count = _numeric_value(evidence, subgroup_field)
            if total is not None and count is not None and count > total:
                contradictions.append(
                    Contradiction(
                        code=f"{subgroup_field.upper()}_EXCEEDS_TOTAL",
                        severity="high",
                        fields=(subgroup_field, total_field),
                        message=(
                            f"{subgroup.capitalize()} employees in {year} ({count:g}) "
                            f"exceed total employees ({total:g})."
                        ),
                        resolution=f"Confirm the employee counts reported for {year}.",
                    )
                )

    return contradictions
