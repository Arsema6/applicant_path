from agents.form_integration import validate_evidence, resolve_followup_value
from domain.contradictions import detect_contradictions
from domain.eligibility import evaluate_eligibility


def test_validate_evidence_flags_invalid_numeric_field():
    evidence = {
        "company_name": {"value": "Almaz Spice Mill", "status": "established"},
        "registration_number": {"value": "12345/2020", "status": "established"},
        "address": {"value": "Bekoji Tera", "status": "established"},
        "mobile_number": {"value": "+251911000000", "status": "established"},
        "email": {"value": "hello@example.com", "status": "established"},
        "business_organization": {"value": "Private Limited Company", "status": "established"},
        "years_in_operation": {"value": "-2", "status": "established"},
        "business_type": {"value": "Spice Milling", "status": "established"},
        "women_ownership_percent": {"value": "65", "status": "established"},
        "men_ownership_percent": {"value": "35", "status": "established"},
    }

    issues = validate_evidence(evidence)
    assert any("years_in_operation" in issue for issue in issues)


def test_resolve_followup_value_marks_conflict_as_contradictory():
    prior = {"value": "10", "status": "established", "source": "voice_note"}
    updated = resolve_followup_value(prior, "15", "follow_up")

    assert updated["status"] == "contradictory"
    assert "conflicts" in (updated.get("note") or "").lower()


def _established(value):
    return {"value": value, "status": "established"}


def test_detect_contradictions_flags_invalid_ownership_total():
    evidence = {
        "women_ownership_percent": _established(60),
        "men_ownership_percent": _established(30),
    }

    contradictions = detect_contradictions(evidence)

    assert [item.code for item in contradictions] == ["OWNERSHIP_TOTAL_NOT_100"]


def test_validate_evidence_includes_employee_contradictions():
    evidence = {
        "employees_current": _established(3),
        "female_employees_current": _established(4),
    }

    issues = validate_evidence(evidence)

    assert any("FEMALE_EMPLOYEES_CURRENT_EXCEEDS_TOTAL" in issue for issue in issues)


def test_eligibility_requires_established_identity_fields():
    result = evaluate_eligibility(
        {
            "company_name": _established("Almaz Spice Mill"),
            "registration_number": _established("12345/2020"),
            "address": _established("Bekoji Tera"),
            "business_type": {"value": "Spice milling", "status": "missing"},
        }
    )

    assert result.eligible is False
    assert result.issues[0].code == "MISSING_BUSINESS_TYPE"


def test_eligibility_blocks_contradictory_evidence():
    result = evaluate_eligibility(
        {
            "company_name": _established("Almaz Spice Mill"),
            "registration_number": _established("12345/2020"),
            "address": _established("Bekoji Tera"),
            "business_type": _established("Spice milling"),
            "years_in_operation": {
                "value": 5,
                "status": "contradictory",
            },
        }
    )

    assert result.eligible is False
    assert result.issues[0].code == "CONTRADICTORY_EVIDENCE"
