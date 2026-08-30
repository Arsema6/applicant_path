from agents.form_integration import validate_evidence, resolve_followup_value


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
