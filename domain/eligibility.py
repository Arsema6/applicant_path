"""Deterministic eligibility gates for funding applications."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class EligibilityIssue:
    code: str
    message: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    issues: tuple[EligibilityIssue, ...]


Rule = Callable[[dict[str, Any]], EligibilityIssue | None]


def _present_established(evidence: dict[str, Any], field: str) -> bool:
    entry = evidence.get(field)
    return (
        isinstance(entry, dict)
        and entry.get("status") == "established"
        and entry.get("value") not in (None, "")
    )


def require_established(field: str, label: str | None = None) -> Rule:
    """Build a rule requiring one field to have established evidence."""

    display_name = label or field.replace("_", " ")

    def rule(evidence: dict[str, Any]) -> EligibilityIssue | None:
        if _present_established(evidence, field):
            return None
        return EligibilityIssue(
            code=f"MISSING_{field.upper()}",
            message=f"{display_name.capitalize()} must be established before submission.",
            fields=(field,),
        )

    return rule


def _no_contradictory_fields(evidence: dict[str, Any]) -> EligibilityIssue | None:
    contradictory = [
        field
        for field, entry in evidence.items()
        if isinstance(entry, dict) and entry.get("status") == "contradictory"
    ]
    if not contradictory:
        return None
    return EligibilityIssue(
        code="CONTRADICTORY_EVIDENCE",
        message="Contradictory evidence must be resolved before submission.",
        fields=tuple(sorted(contradictory)),
    )


DEFAULT_RULES: tuple[Rule, ...] = (
    require_established("company_name", "company name"),
    require_established("registration_number", "registration or licence number"),
    require_established("address", "business address"),
    require_established("business_type", "business type"),
    _no_contradictory_fields,
)


def evaluate_eligibility(
    evidence: dict[str, Any],
    rules: tuple[Rule, ...] = DEFAULT_RULES,
) -> EligibilityResult:
    """Evaluate the deterministic gate without calling an AI model."""

    if not isinstance(evidence, dict):
        raise TypeError("evidence must be a dictionary")

    issues = tuple(issue for rule in rules if (issue := rule(evidence)) is not None)
    return EligibilityResult(eligible=not issues, issues=issues)
