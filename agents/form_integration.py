import os
import re
import math
import requests
from typing import Dict, Any
from dotenv import load_dotenv

from agents.ai_agents import FIELD_DEFINITIONS

# Load variables from .env
load_dotenv()


# ============================================================
# JOTFORM CONFIGURATION
# ============================================================

JOTFORM_API_KEY = os.getenv("JOTFORM_API_KEY")
JOTFORM_FORM_ID = os.getenv(
    "JOTFORM_FORM_ID",
    "251212903767052"
)

JOTFORM_API_URL = "https://api.jotform.com"


# ============================================================
# HELPERS
# ============================================================

def _check_api_key():
    """Make sure the Jotform API key exists."""

    if not JOTFORM_API_KEY:
        raise RuntimeError(
            "JOTFORM_API_KEY is missing. "
            "Add it to your .env file."
        )


def _value(evidence: dict, field: str):
    """
    Get a value from the evidence structure.

    Expected structure:

    {
        "company_name": {
            "value": "ABC",
            "status": "established"
        }
    }
    """

    entry = evidence.get(field) or {}

    value = entry.get("value")

    if value in (None, ""):
        return None

    return value


# ============================================================
# GET FORM QUESTIONS
# ============================================================

def get_form_questions() -> Dict[str, Any]:
    """
    Retrieve the actual questions/QIDs from Jotform.

    This is useful for discovering the real Jotform
    field structure.
    """

    _check_api_key()

    url = (
        f"{JOTFORM_API_URL}"
        f"/form/{JOTFORM_FORM_ID}"
        f"/questions"
    )

    response = requests.get(
        url,
        headers={
            "APIKEY": JOTFORM_API_KEY
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if data.get("responseCode") != 200:
        raise RuntimeError(
            f"Jotform returned an error: {data}"
        )

    return data.get("content", {})


# ============================================================
# PRINT FORM SCHEMA
# ============================================================

def print_form_questions():
    """
    Print all Jotform questions and their QIDs.

    Run:

        python agents/form_integration.py

    to inspect the form.
    """

    questions = get_form_questions()

    print("\n========== JOTFORM QUESTIONS ==========\n")

    for qid, question in questions.items():

        if not isinstance(question, dict):
            continue

        print(f"QID: {qid}")
        print(f"Type: {question.get('type')}")
        print(f"Name: {question.get('name')}")
        print(f"Text: {question.get('text')}")
        print(f"Order: {question.get('order')}")

        # Print additional information when available.
        if question.get("subFields"):
            print(
                f"Subfields: "
                f"{question.get('subFields')}"
            )

        if question.get("options"):
            print(
                f"Options: "
                f"{question.get('options')}"
            )

        print("-" * 60)


# ============================================================
# KNOWN JOTFORM FIELD MAPPING
# ============================================================

# These mappings are currently known from your form.
#
# IMPORTANT:
# The QIDs marked as "verified later" should eventually be
# checked against get_form_questions().
#
# Do NOT assume an internal AI field name is the same as
# the Jotform QID.

KNOWN_FIELD_MAP = {

    # --------------------------------------------------------
    # COMPANY PROFILE
    # --------------------------------------------------------

    "company_name": {
        "name": "q3_nameOf",
        "qid": "3",
    },

    "registration_number": {
        "name": "q4_businessRegistration",
        "qid": "4",
    },

    "address": {
        "name": "q5_address",
        "qid": "5",
    },

    "mobile_number": {
        "name": "q6_mobileNumber",
        "qid": "6",
    },

    "email": {
        "name": "q7_email",
        "qid": "7",
    },

    "business_organization": {
        "name": "q8_formOf",
        "qid": "8",
    },

    "years_in_operation": {
        "name": "q9_numberOf",
        "qid": "9",
    },

    "business_type": {
        "name": "q10_typeOf",
        "qid": "10",
    },

    # --------------------------------------------------------
    # COMPANY OVERVIEW
    # --------------------------------------------------------

    "company_overview": {
        "name": "q12_companyOverview",
        "qid": "12",
    },

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    "market_overview": {
        "name": "q17_market",
        "qid": "17",
    },

    # --------------------------------------------------------
    # REQUESTED INTERVENTION
    # --------------------------------------------------------

    "problems_to_address": {
        "name": "q30_problems",
        "qid": "30",
    },

    "social_environmental_impact": {
        "name": "q40_social",
        "qid": "40",
    },

    "occupational_safety_health": {
        "name": "q41_osh",
        "qid": "41",
    },
}


# ============================================================
# COMPOSED APPLICATION FIELDS
# ============================================================

def build_composed_answers(
    evidence: dict
) -> Dict[str, str]:
    """
    Combine multiple internal AI fields when the real
    Jotform question represents them as one question.
    """

    answers = {}

    # --------------------------------------------------------
    # MOTIVATION + PERSONAL INVOLVEMENT
    # --------------------------------------------------------

    motivation = []

    value = _value(
        evidence,
        "motivation_to_apply"
    )

    if value:
        motivation.append(
            f"Motivation: {value}"
        )

    value = _value(
        evidence,
        "personal_involvement"
    )

    if value:
        motivation.append(
            f"Personal involvement: {value}"
        )

    if motivation:

        answers[
            "motivation_to_apply"
        ] = "\n".join(motivation)


    # --------------------------------------------------------
    # SHORT-TERM + LONG-TERM GOALS
    # --------------------------------------------------------

    goals = []

    value = _value(
        evidence,
        "short_term_goals"
    )

    if value:
        goals.append(
            f"Short-term goals: {value}"
        )

    value = _value(
        evidence,
        "long_term_goals"
    )

    if value:
        goals.append(
            f"Long-term goals: {value}"
        )

    if goals:

        answers["goals"] = "\n".join(goals)


    # --------------------------------------------------------
    # MARKET INFORMATION
    # --------------------------------------------------------

    market = []

    fields = [
        (
            "Market overview",
            "market_overview"
        ),
        (
            "Target customers",
            "target_customers"
        ),
        (
            "Geographies served",
            "geographies_served"
        ),
        (
            "Competitive advantage",
            "competitive_advantage"
        ),
        (
            "Market challenges",
            "market_challenges"
        ),
    ]

    for label, field in fields:

        value = _value(
            evidence,
            field
        )

        if value:

            market.append(
                f"{label}: {value}"
            )

    if market:

        answers[
            "market_overview"
        ] = "\n".join(market)


    return answers


# ============================================================
# BUILD SIMPLE SUBMISSION DATA
# ============================================================

def build_submission_data(
    evidence: dict
) -> Dict[str, Any]:
    """
    Convert internal AI evidence into Jotform QID/value data.

    Example:

        {
            "3": "ABC Manufacturing",
            "4": "12345/2020",
            "5": "Bole, Addis Ababa"
        }
    """

    submission = {}

    # --------------------------------------------------------
    # SIMPLE FIELDS
    # --------------------------------------------------------

    for field, config in KNOWN_FIELD_MAP.items():

        value = _value(
            evidence,
            field
        )

        if value is None:
            continue

        qid = config["qid"]

        submission[qid] = value


    # --------------------------------------------------------
    # COMPOSED FIELDS
    # --------------------------------------------------------

    composed = build_composed_answers(
        evidence
    )


    # --------------------------------------------------------
    # MOTIVATION
    # --------------------------------------------------------

    if "motivation_to_apply" in composed:

        # Current assumed QID.
        #
        # Change this after confirming the actual
        # Jotform question.
        submission["13"] = (
            composed["motivation_to_apply"]
        )


    # --------------------------------------------------------
    # GOALS
    # --------------------------------------------------------

    if "goals" in composed:

        # Current assumed QID.
        #
        # Change this after confirming the actual
        # Jotform question.
        submission["14"] = (
            composed["goals"]
        )


    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    if "market_overview" in composed:

        submission["17"] = (
            composed["market_overview"]
        )


    return submission


# ============================================================
# EVIDENCE VALIDATION
# ============================================================

def _clean_value(value: Any) -> str | None:
    """Normalize field values to stripped strings."""
    if value is None:
        return None

    if isinstance(value, str):
        cleaned = value.strip()
        return cleaned or None

    cleaned = str(value).strip()
    return cleaned or None


def _extract_numeric_value(value: Any) -> float | None:
    """Extract a numeric value from common text formats such as 1.5M or 1,500."""
    cleaned = _clean_value(value)
    if cleaned is None:
        return None

    match = re.search(r"[-+]?\d[\d,]*\.?\d*(?:[eE][-+]?\d+)?", cleaned)
    if not match:
        return None

    try:
        number = float(match.group(0).replace(",", ""))
        if math.isnan(number) or math.isinf(number):
            return None
        return number
    except ValueError:
        return None


def validate_evidence(evidence: dict) -> list[str]:
    """Validate the extracted evidence before final submission."""
    if not isinstance(evidence, dict):
        return ["evidence: application state is invalid"]

    issues: list[str] = []

    for field in FIELD_DEFINITIONS:
        entry = evidence.get(field) or {}
        status = entry.get("status", "missing")
        value = _clean_value(entry.get("value"))

        if value is None or status in {"missing", "unverified", "contradictory"}:
            if field in {
                "company_name",
                "registration_number",
                "address",
                "mobile_number",
                "email",
                "business_organization",
                "years_in_operation",
                "business_type",
                "company_overview",
                "market_overview",
                "motivation_to_apply",
                "personal_involvement",
                "short_term_goals",
                "long_term_goals",
                "products_services",
                "problems_to_address",
                "social_environmental_impact",
                "occupational_safety_health",
            }:
                issues.append(f"{field}: required field is missing or incomplete")
            continue

        if field in {"mobile_number"}:
            digits = re.sub(r"\D", "", value)
            if len(digits) < 7:
                issues.append(f"{field}: mobile number looks invalid")

        if field == "email":
            if not re.fullmatch(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
                issues.append(f"{field}: email format is invalid")

        if field in {"years_in_operation"}:
            numeric = _extract_numeric_value(value)
            if numeric is None or numeric < 0:
                issues.append(f"{field}: years in operation must be a non-negative number")

        if field.endswith("_percent"):
            numeric = _extract_numeric_value(value)
            if numeric is None or numeric < 0 or numeric > 100:
                issues.append(f"{field}: percent value must be between 0 and 100")

        if field.startswith(("sales_", "employees_", "female_employees_", "youth_employees_")) or field in {
            "sales_current",
            "employees_current",
            "female_employees_current",
            "youth_employees_current",
            "jobs_to_create",
            "local_raw_material_percentage",
        }:
            numeric = _extract_numeric_value(value)
            if numeric is None or numeric < 0:
                issues.append(f"{field}: value must be a non-negative number")

    return issues


def resolve_followup_value(previous_entry: dict | None, new_value: Any, source: str = "follow_up") -> dict:
    """Resolve a new follow-up answer and surface contradictions without overwriting good evidence silently."""
    cleaned_new = _clean_value(new_value)
    if cleaned_new is None:
        return {
            "value": None,
            "status": "missing",
            "source": source,
            "confidence": 0.0,
            "note": "No answer was provided.",
        }

    if not isinstance(previous_entry, dict):
        return {
            "value": cleaned_new,
            "status": "established",
            "source": source,
            "confidence": 0.95,
            "note": "Confirmed by follow-up answer.",
        }

    previous_value = _clean_value(previous_entry.get("value"))
    previous_status = previous_entry.get("status")

    if previous_status == "established" and previous_value is not None and previous_value != cleaned_new:
        return {
            "value": cleaned_new,
            "status": "contradictory",
            "source": source,
            "confidence": 0.55,
            "note": f"Follow-up answer ('{cleaned_new}') conflicts with earlier evidence ('{previous_value}').",
        }

    return {
        "value": cleaned_new,
        "status": "established",
        "source": source,
        "confidence": 0.95,
        "note": "Confirmed by follow-up answer.",
    }


# ============================================================
# VALIDATE SUBMISSION
# ============================================================

def validate_submission_data(
    submission_data: Dict[str, Any]
):
    """
    Validate the data before sending it to Jotform.
    """

    if not submission_data:

        raise ValueError(
            "There is no application information "
            "available for submission."
        )


    cleaned = {}

    for qid, value in submission_data.items():

        if value in (None, ""):
            continue

        if isinstance(value, list):

            if not value:
                continue

            cleaned[qid] = value

        elif isinstance(value, dict):

            if not value:
                continue

            cleaned[qid] = value

        else:

            text = str(value).strip()

            if not text:
                continue

            cleaned[qid] = text


    if not cleaned:

        raise ValueError(
            "All submission fields are empty."
        )


    return cleaned


# ============================================================
# SUBMIT APPLICATION
# ============================================================

def submit_application(
    evidence: dict
) -> Dict[str, Any]:
    """
    Submit the completed application directly to Jotform.

    Flow:

        Streamlit
            ↓
        evidence
            ↓
        build_submission_data()
            ↓
        validate_submission_data()
            ↓
        Jotform API
            ↓
        submission response
    """

    _check_api_key()


    # --------------------------------------------------------
    # BUILD DATA
    # --------------------------------------------------------

    submission_data = (
        build_submission_data(
            evidence
        )
    )


    # --------------------------------------------------------
    # VALIDATE DATA
    # --------------------------------------------------------

    submission_data = (
        validate_submission_data(
            submission_data
        )
    )


    # --------------------------------------------------------
    # CONVERT TO JOTFORM PAYLOAD
    # --------------------------------------------------------

    payload = {}

    for qid, value in submission_data.items():

        # Simple values
        if not isinstance(
            value,
            (list, dict)
        ):

            payload[
                f"submission[{qid}]"
            ] = str(value)

            continue


        # ----------------------------------------------------
        # Lists
        #
        # Used by some Jotform checkbox/multiple-value fields.
        # ----------------------------------------------------

        if isinstance(value, list):

            for index, item in enumerate(value):

                payload[
                    f"submission[{qid}][{index}]"
                ] = str(item)


        # ----------------------------------------------------
        # Dictionaries
        #
        # Used by some structured/table fields.
        # ----------------------------------------------------

        elif isinstance(value, dict):

            for key, item in value.items():

                payload[
                    f"submission[{qid}][{key}]"
                ] = str(item)


    # --------------------------------------------------------
    # JOTFORM SUBMISSION ENDPOINT
    # --------------------------------------------------------

    url = (
        f"{JOTFORM_API_URL}"
        f"/form/{JOTFORM_FORM_ID}"
        f"/submissions"
    )


    response = requests.post(

        url,

        headers={
            "APIKEY": JOTFORM_API_KEY,
        },

        data=payload,

        timeout=30,
    )


    # --------------------------------------------------------
    # HTTP ERROR
    # --------------------------------------------------------

    if not response.ok:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text


        raise RuntimeError(
            "Jotform API submission failed. "
            f"HTTP {response.status_code}: "
            f"{error_data}"
        )


    # --------------------------------------------------------
    # PARSE RESPONSE
    # --------------------------------------------------------

    try:

        result = response.json()

    except Exception:

        raise RuntimeError(
            "Jotform returned an invalid JSON response: "
            f"{response.text}"
        )


    # --------------------------------------------------------
    # JOTFORM API ERROR
    # --------------------------------------------------------

    if result.get("responseCode") != 200:

        raise RuntimeError(
            "Jotform submission failed: "
            f"{result}"
        )


    # --------------------------------------------------------
    # SUCCESS
    # --------------------------------------------------------

    return result

# ============================================================
# BUILD PREFILLED JOTFORM URL
# ============================================================

def build_prefill_url(
    evidence: dict,
    min_status: str = "established"
) -> str:
    """
    Build a Jotform URL containing the currently available
    application information.

    This is useful for applicant review.

    The actual API submission is handled separately by
    submit_application().
    """

    from urllib.parse import urlencode

    params = {}

    # --------------------------------------------------------
    # Simple fields
    # --------------------------------------------------------

    for field, config in KNOWN_FIELD_MAP.items():

        value = _value(evidence, field)

        if value is None:
            continue

        status = (
            evidence.get(field, {})
            .get("status")
        )

        # Only include completed fields.
        if status not in (
            "established",
            "verified",
        ):
            continue

        params[config["name"]] = str(value)


    # --------------------------------------------------------
    # Composed fields
    # --------------------------------------------------------

    composed = build_composed_answers(
        evidence
    )


    # Motivation + personal involvement
    if "motivation_to_apply" in composed:

        # q13 is the currently assumed field name.
        params[
            "q13_motivation"
        ] = composed[
            "motivation_to_apply"
        ]


    # Goals
    if "goals" in composed:

        # q14 is the currently assumed field name.
        params[
            "q14_goals"
        ] = composed["goals"]


    # Market
    if "market_overview" in composed:

        params[
            "q17_market"
        ] = composed[
            "market_overview"
        ]


    # --------------------------------------------------------
    # Build URL
    # --------------------------------------------------------

    query_string = urlencode(
        params,
        doseq=True
    )

    return (
        f"https://form.jotform.com/"
        f"{JOTFORM_FORM_ID}"
        f"?{query_string}"
    )

# ============================================================
# OPTIONAL: GET SUBMISSION
# ============================================================

def get_submission(
    submission_id: str
) -> Dict[str, Any]:
    """
    Retrieve a Jotform submission after it has been created.
    """

    _check_api_key()

    url = (
        f"{JOTFORM_API_URL}"
        f"/submission/{submission_id}"
    )

    response = requests.get(

        url,

        headers={
            "APIKEY": JOTFORM_API_KEY,
        },

        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if result.get("responseCode") != 200:

        raise RuntimeError(
            f"Could not retrieve submission: "
            f"{result}"
        )

    return result


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print_form_questions()