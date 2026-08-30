from typing import Optional, List, Dict, Any
from pydantic import Field, create_model
from google.genai import types

from .gemini_extraction_agent import (
    client,
    MODEL,
    FIELD_DEFINITIONS,
    Evidence,
    SYSTEM_INSTRUCTION,
    validate_or_repair,
)


# =========================================================
# Critical fields
# =========================================================

CRITICAL_FIELDS = [
    "registration_number",
    "years_in_operation",
    "women_ownership_percent",
    "men_ownership_percent",
    "employees_current",
    "female_employees_current",
    "youth_employees_current",
    "sales_current",
    "business_type",
    "jobs_to_create",
    "requested_equipment",
]


# =========================================================
# Questions
# =========================================================

QUESTIONS = {

    "en": {

        "registration_number":
            "What is your business registration number?",

        "years_in_operation":
            "How many years has your business been operating?",

        "women_ownership_percent":
            "What percentage of your business is owned by women?",

        "men_ownership_percent":
            "What percentage of your business is owned by men?",

        "employees_current":
            "How many people currently work in your business?",

        "female_employees_current":
            "How many of your current employees are women?",

        "youth_employees_current":
            "How many of your current employees are between 15 and 29 years old?",

        "sales_current":
            "What are your most recent sales or revenue figures?",

        "business_type":
            "What type of business do you operate?",

        "jobs_to_create":
            "How many new jobs do you expect this support to create?",

        "requested_equipment":
            "What equipment do you need for your business?",
    },


    "am": {

        "registration_number":
            "የንግድዎ የምዝገባ ቁጥር ስንት ነው?",

        "years_in_operation":
            "ንግድዎን ስንት ዓመት ሲያካሂዱ ኖረዋል?",

        "women_ownership_percent":
            "ከንግድዎ ውስጥ ስንት በመቶ በሴቶች ባለቤትነት ላይ ነው?",

        "men_ownership_percent":
            "ከንግድዎ ውስጥ ስንት በመቶ በወንዶች ባለቤትነት ላይ ነው?",

        "employees_current":
            "በአሁኑ ጊዜ በንግድዎ ውስጥ ስንት ሰዎች ይሰራሉ?",

        "female_employees_current":
            "በአሁኑ ጊዜ ከሚሰሩት ሰራተኞች ውስጥ ስንቱ ሴቶች ናቸው?",

        "youth_employees_current":
            "በአሁኑ ጊዜ ከ15 እስከ 29 ዓመት ዕድሜ ያላቸው ስንት ሰራተኞች አሉ?",

        "sales_current":
            "በቅርብ ጊዜ ያለዎት የሽያጭ ወይም የገቢ መጠን ስንት ነው?",

        "business_type":
            "ምን ዓይነት ንግድ ነው የሚያካሂዱት?",

        "jobs_to_create":
            "ይህ ድጋፍ ስንት አዳዲስ የሥራ ዕድሎችን እንደሚፈጥር ይጠብቃሉ?",

        "requested_equipment":
            "ለንግድዎ ምን ዓይነት መሳሪያ ያስፈልግዎታል?",
    },


    "om": {

        "registration_number":
            "Lakkoofsi galmee daldala keessanii meeqa?",

        "years_in_operation":
            "Daldala keessan waggaa meeqaaf gaggeessaa jirtu?",

        "women_ownership_percent":
            "Daldala keessan keessaa dhibbeentaan meeqa dubartootaan kan qabamudha?",

        "men_ownership_percent":
            "Daldala keessan keessaa dhibbeentaan meeqa dhiironaan kan qabamudha?",

        "employees_current":
            "Yeroo ammaa daldala keessan keessatti namoonni meeqa hojjetu?",

        "female_employees_current":
            "Hojjettoota yeroo ammaa keessaa dubartoonni meeqa jiru?",

        "youth_employees_current":
            "Hojjettoota yeroo ammaa keessaa namoonni umurii 15 hanga 29 meeqa jiru?",

        "sales_current":
            "Gurgurtaa ykn galii keessan yeroo dhiyoo meeqa?",

        "business_type":
            "Daldala akkamii gaggeessaa jirtu?",

        "jobs_to_create":
            "Deeggarsi kun hojiiwwan haaraa meeqa akka uumu ni eegdu?",

        "requested_equipment":
            "Daldala keessaniif meeshaalee akkamii isin barbaachisu?",
    },
}


# =========================================================
# Gap detection
# =========================================================

def find_gaps(
    result: dict,
    only_fields: list[str] | None = None,
) -> list[dict]:
    """
    Local only — no model call.
    """

    fields = (
        only_fields
        if only_fields is not None
        else list(FIELD_DEFINITIONS.keys())
    )

    gaps = []

    for field in fields:

        entry = result.get(field)

        # Fixed: Handle both None and missing/status cases consistently
        if not entry or not isinstance(entry, dict):
            gaps.append({
                "field": field,
                "description": FIELD_DEFINITIONS.get(field, ""),
                "status": "missing",
                "value": None,
                "source": None,
                "confidence": 0.0,
                "note": "Field is missing.",
            })
            continue

        # Fixed: Check status properly
        status = entry.get("status", "missing")
        
        if status in {"missing", "unverified", "contradictory"}:
            gap_entry = {
                "field": field,
                "description": FIELD_DEFINITIONS.get(field, ""),
            }
            # Copy all fields from entry
            gap_entry.update(entry)
            gaps.append(gap_entry)

    return gaps


# =========================================================
# Question generation
# =========================================================

def generate_followup_question(
    gaps: list[dict],
    language: str = "en",
) -> str:
    """
    Zero Gemini calls.

    Exactly one field → exactly one question.
    """

    if not gaps:
        raise ValueError(
            "No gaps were provided."
        )

    field = gaps[0]["field"]

    language_questions = QUESTIONS.get(
        language,
        QUESTIONS["en"],
    )

    question = language_questions.get(
        field
    )

    if question:
        return question

    # Safe fallback
    fallbacks = {
        "en": f"Could you provide more information about {field.replace('_', ' ')}?",
        "am": "እባክዎ ስለዚህ መረጃ ተጨማሪ ዝርዝር ይስጡኝ።",
        "om": "Maaloo waa'ee odeeffannoo kanaa odeeffannoo dabalataa naaf kenni.",
    }
    
    return fallbacks.get(language, fallbacks["en"])


# =========================================================
# Merge follow-up answer
# =========================================================

def merge_followup_answer(
    existing_result: dict,
    followup_transcript: str,
    targeted_fields: list[str],
) -> dict:
    """
    Use ONE targeted extraction call.

    Only fields asked in the current question are extracted.
    """

    if not targeted_fields:
        return existing_result

    # Fixed: Ensure existing_result is a dict
    if not isinstance(existing_result, dict):
        existing_result = {}

    # Fixed: Build schema with proper field definitions
    field_defs = {}
    for field in targeted_fields:
        if field in FIELD_DEFINITIONS:
            field_defs[field] = (Evidence, Field(description=FIELD_DEFINITIONS[field]))
        else:
            field_defs[field] = (Evidence, Field(description=f"Field: {field}"))

    SubSchema = create_model(
        "FollowUpResult",
        **field_defs,
    )

    prompt = (
        "Extract ONLY the requested field(s) from this applicant "
        "follow-up answer.\n\n"

        "REQUESTED FIELDS:\n"

        + "\n".join(
            f"- {field}: {FIELD_DEFINITIONS.get(field, 'Unknown field')}"
            for field in targeted_fields
        )

        + "\n\nFOLLOW-UP ANSWER:\n"
        + followup_transcript

        + """

RULES:

- Use only information explicitly stated.
- Do not infer.
- Do not calculate.
- Preserve the applicant's original language.
- This answer came directly from the applicant.
- Return only the requested fields.
"""
    )

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            temperature=0,
        ),
    )

    new_partial = validate_or_repair(
        response.text,
        SubSchema,
        SYSTEM_INSTRUCTION,
        max_repairs=0,
    )

    merged = dict(existing_result)

    for field, new_entry in new_partial.items():

        if new_entry.get("status") == "missing":
            continue

        new_entry = dict(new_entry)

        # Applicant answered this question.
        new_entry["source"] = "voice_note"

        old_entry = merged.get(field)

        # -------------------------------------------------
        # Existing established value
        # -------------------------------------------------

        if (
            old_entry
            and old_entry.get("status") == "established"
        ):

            old_value = old_entry.get("value")
            new_value = new_entry.get("value")

            if (
                str(old_value).strip()
                == str(new_value).strip()
            ):

                new_entry["status"] = "established"

                new_entry["note"] = (
                    "Confirmed by the applicant's "
                    "follow-up answer."
                )

                merged[field] = new_entry

            else:

                merged[field] = {
                    "value": new_value,
                    "status": "contradictory",
                    "source": "voice_note",
                    "confidence": 0.5,
                    "note": (
                        f"Follow-up answer "
                        f"('{new_value}') conflicts with "
                        f"earlier evidence "
                        f"('{old_value}')."
                    ),
                }

        else:

            merged[field] = new_entry

    return merged