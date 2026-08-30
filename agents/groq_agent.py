import os
import json
import base64
import mimetypes
import re
from typing import Optional, List

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Add it to your .env file.")

client = Groq(api_key=GROQ_API_KEY)

TRANSCRIBE_MODEL = "whisper-large-v3"
EXTRACTION_MODEL = "openai/gpt-oss-120b"
VISION_MODEL = "qwen/qwen3.6-27b"

FIELD_DEFINITIONS = {
    "company_name": "Registered or trading business name",
    "registration_number": "Business licence or registration number",
    "address": "Business address (town, district, region)",
    "mobile_number": "Applicant mobile phone number",
    "email": "Applicant email address",
    "business_organization": "Legal form: sole proprietor, PLC, cooperative, etc.",
    "years_in_operation": "Number of years business has operated",
    "business_type": "Business sector or industry",
    "women_ownership_percent": "Percentage owned by women",
    "men_ownership_percent": "Percentage owned by men",
    "company_overview": "What the business does and how it operates",
    "sales_current": "Most recent sales/revenue figure without an explicit year",
    "sales_2022": "Sales explicitly attributed to 2022",
    "sales_2023": "Sales explicitly attributed to 2023",
    "sales_2024": "Sales explicitly attributed to 2024",
    "sales_2025": "Sales explicitly attributed to 2025",
    "sales_2026": "Sales explicitly attributed to 2026",
    "employees_current": "Current total employees",
    "employees_2022": "Total employees in 2022",
    "employees_2023": "Total employees in 2023",
    "employees_2024": "Total employees in 2024",
    "employees_2025": "Total employees in 2025",
    "employees_2026": "Total employees in 2026",
    "female_employees_current": "Current female employee count",
    "female_employees_2022": "Female employees in 2022",
    "female_employees_2023": "Female employees in 2023",
    "female_employees_2024": "Female employees in 2024",
    "female_employees_2025": "Female employees in 2025",
    "female_employees_2026": "Female employees in 2026",
    "youth_employees_current": "Current employees aged 18-24 when explicitly stated",
    "youth_employees_2022": "Youth employees in 2022",
    "youth_employees_2023": "Youth employees in 2023",
    "youth_employees_2024": "Youth employees in 2024",
    "youth_employees_2025": "Youth employees in 2025",
    "youth_employees_2026": "Youth employees in 2026",
    "motivation_to_apply": "Why applicant is applying for funding",
    "personal_involvement": "Applicant's role in the business",
    "short_term_goals": "Short-term goals (0-12 months)",
    "long_term_goals": "Long-term goals (1-5 years)",
    "market_overview": "Description of the market",
    "target_customers": "Who the business sells to",
    "geographies_served": "Where the business sells/operates",
    "competitive_advantage": "What makes the business different",
    "market_challenges": "Market challenges",
    "products_services": "Products or services provided",
    "product_service_uniqueness": "Unique features of products/services",
    "local_raw_material_percentage": "Percentage of locally sourced raw materials",
    "management_team": "People managing the business",
    "organogram": "Reporting structure description",
    "problems_to_address": "Problems funding should address",
    "requested_equipment": "Equipment requested",
    "requested_consultants": "Consulting support requested",
    "expected_results": "Expected results from funding",
    "priority_areas": "Priority areas named",
    "jobs_to_create": "Number of new jobs expected",
    "job_creation_explanation": "How jobs will be created",
    "new_job_positions": "Specific positions to be created",
    "social_environmental_impact": "Social or environmental impact",
    "occupational_safety_health": "Occupational safety and health practices",
}

FIELD_QUESTIONS = {
    "company_name": "What is the name of your company or business?",
    "registration_number": "What is your business registration or licence number?",
    "address": "What is your business address (city/town and region)?",
    "mobile_number": "What is your mobile phone number?",
    "email": "What is your email address, if you have one?",
    "business_organization": "What is the legal form of your business (sole proprietor, PLC, cooperative, etc.)?",
    "years_in_operation": "How many years has the business been operating?",
    "business_type": "What sector or type of business do you operate?",
    "women_ownership_percent": "What percentage of the business is owned by women?",
    "men_ownership_percent": "What percentage of the business is owned by men?",
    "company_overview": "Please briefly describe what your company does, its products/services, business model, and markets.",
    "sales_current": "What is your most recent annual sales or revenue figure?",
    "sales_2022": "What were your sales in 2022?",
    "sales_2023": "What were your sales in 2023?",
    "sales_2024": "What were your sales in 2024?",
    "sales_2025": "What are your projected sales for 2025?",
    "sales_2026": "What are your projected sales for 2026?",
    "employees_current": "How many employees do you currently have?",
    "employees_2022": "How many total employees did you have in 2022?",
    "employees_2023": "How many total employees did you have in 2023?",
    "employees_2024": "How many total employees did you have in 2024?",
    "employees_2025": "How many total employees are projected for 2025?",
    "employees_2026": "How many total employees are projected for 2026?",
    "female_employees_current": "How many female employees do you currently have?",
    "female_employees_2022": "How many female employees did you have in 2022?",
    "female_employees_2023": "How many female employees did you have in 2023?",
    "female_employees_2024": "How many female employees did you have in 2024?",
    "female_employees_2025": "How many female employees are projected for 2025?",
    "female_employees_2026": "How many female employees are projected for 2026?",
    "youth_employees_current": "How many current employees are aged 18-24?",
    "youth_employees_2022": "How many employees aged 18-24 did you have in 2022?",
    "youth_employees_2023": "How many employees aged 18-24 did you have in 2023?",
    "youth_employees_2024": "How many employees aged 18-24 did you have in 2024?",
    "youth_employees_2025": "How many employees aged 18-24 are projected for 2025?",
    "youth_employees_2026": "How many employees aged 18-24 are projected for 2026?",
    "motivation_to_apply": "Why are you applying for the SME Support Scheme?",
    "personal_involvement": "What is your role and involvement in the business?",
    "short_term_goals": "What are your short-term goals for the next 0-12 months?",
    "long_term_goals": "What are your long-term goals for the next 1-5 years?",
    "market_overview": "Describe your market and its potential.",
    "target_customers": "Who are your target customers?",
    "geographies_served": "Which cities, regions, or markets do you serve?",
    "competitive_advantage": "Why do customers choose your product/service over competitors?",
    "market_challenges": "What are the main challenges in your market?",
    "products_services": "What products or services do you provide?",
    "product_service_uniqueness": "What makes your product/service unique?",
    "local_raw_material_percentage": "What percentage of your raw materials are locally sourced?",
    "management_team": "Who are the key people in your management team? Include names and roles.",
    "organogram": "Please describe your company reporting/organizational structure.",
    "problems_to_address": "What business problems or challenges should the support address?",
    "requested_equipment": "What machinery or equipment do you need? Include quantity/purpose when known.",
    "requested_consultants": "What technical or consulting support do you need?",
    "expected_results": "What results do you expect from participating in the SME Support Scheme?",
    "priority_areas": "Which three priority areas are most important for your business (new product/service, diversification, new clients, new markets, production capacity, quality, financial sustainability)?",
    "jobs_to_create": "How many new jobs do you expect to create in the next 15 months?",
    "job_creation_explanation": "How will those new jobs be created?",
    "new_job_positions": "Which job positions will be created, and how many of each?",
    "social_environmental_impact": "What are the positive and negative social and environmental impacts of your business?",
    "occupational_safety_health": "What occupational safety and health practices does your business follow?",
}

TRANSLATED_QUESTIONS = {
    "am": {
        "company_name": "የኩባንያዎ ወይም የንግድዎ ስም ማን ነው?",
        "registration_number": "የንግድ ምዝገባ ወይም ፈቃድ ቁጥርዎ ስንት ነው?",
        "address": "የንግድዎ አድራሻ (ከተማ/ወረዳ እና ክልል) ምንድነው?",
        "mobile_number": "የሞባይል ስልክ ቁጥርዎ ስንት ነው?",
        "email": "ካለዎት የኢሜይል አድራሻዎ ምንድነው?",
        "years_in_operation": "ንግድዎ ለስንት ዓመታት ሰርቷል?",
        "business_type": "የንግድዎ ዘርፍ ወይም አይነት ምንድነው?",
        "company_overview": "ኩባንያዎ ምን እንደሚሰራ፣ ምርቶች/አገልግሎቶቹ እና ገበያውን በአጭሩ ይግለጹ።",
        "sales_current": "የቅርብ ጊዜ ዓመታዊ ሽያጭ ወይም ገቢዎ ስንት ነው?",
        "employees_current": "በአሁኑ ጊዜ ስንት ሰራተኞች አሉዎት?",
        "female_employees_current": "በአሁኑ ጊዜ ስንት ሴት ሰራተኞች አሉዎት?",
        "motivation_to_apply": "ለ SME Support Scheme ለምን ያመለክታሉ?",
        "personal_involvement": "በንግዱ ውስጥ ያለዎት ሚና ምንድነው?",
        "short_term_goals": "በቀጣይ 0-12 ወራት ምን ማሳካት ይፈልጋሉ?",
        "long_term_goals": "በቀጣይ 1-5 ዓመታት ምን ማሳካት ይፈልጋሉ?",
        "products_services": "ምን ምርቶች ወይም አገልግሎቶች ይሰጣሉ?",
        "requested_equipment": "ምን ዓይነት ማሽን ወይም መሳሪያ ያስፈልግዎታል?",
        "problems_to_address": "ድጋፉ ሊፈታቸው የሚገቡ የንግድ ችግሮች ምንድናቸው?",
        "jobs_to_create": "በቀጣይ 15 ወራት ስንት አዲስ ስራ መፍጠር ይጠብቃሉ?",
        "social_environmental_impact": "የንግድዎ ማህበራዊ እና አካባቢያዊ ተፅዕኖ ምንድነው?",
        "occupational_safety_health": "የሰራተኞች ደህንነትና ጤና ለመጠበቅ ምን ልምዶች አሉ?",
    },
    "om": {
        "company_name": "Maqaan dhaabbata ykn daldala keessanii maali?",
        "registration_number": "Lakkoofsi galmee ykn hayyama daldalaa keessanii meeqa?",
        "address": "Teessoon daldala keessanii (magaalaa fi naannoo) maali?",
        "mobile_number": "Lakkoofsi bilbila keessanii meeqa?",
        "email": "Yoo qabaattan, email keessan maali?",
        "years_in_operation": "Daldalli keessan waggaa meeqaaf hojjetaa jira?",
        "business_type": "Gosti ykn dameen daldala keessanii maali?",
        "company_overview": "Daldalli keessan maal akka hojjetu, oomishaalee/tajaajiloota fi gabaa isaa gabaabinaan ibsaa.",
        "sales_current": "Gurgurtaan ykn galiin waggaa yeroo ammaa keessanii meeqa?",
        "employees_current": "Yeroo ammaa hojjettoota meeqa qabdu?",
        "female_employees_current": "Yeroo ammaa hojjettoota dubartii meeqa qabdu?",
        "motivation_to_apply": "Maaliif SME Support Scheme irratti iyyattu?",
        "personal_involvement": "Gahee keessan daldala keessatti maali?",
        "short_term_goals": "Ji'oota 0-12 keessatti maal galmaan gahuu barbaaddu?",
        "long_term_goals": "Waggoota 1-5 keessatti maal galmaan gahuu barbaaddu?",
        "products_services": "Oomishaalee ykn tajaajiloota akkamii kennitu?",
        "requested_equipment": "Maashinaa ykn meeshaa akkamii barbaaddu?",
        "problems_to_address": "Rakkoolee daldalaa deeggarsi kun furu qabu maali?",
        "jobs_to_create": "Ji'oota 15 keessatti hojii haaraa meeqa uumuu jettu?",
        "social_environmental_impact": "Daldalli keessan hawaasaa fi naannoo irratti dhiibbaa maalii qaba?",
        "occupational_safety_health": "Nageenya fi fayyaa hojjettootaa eeguuf maal hojjettu?",
    },
}
# ============================================================
# ACTUAL APPLICATION QUESTIONS
# ============================================================

APPLICATION_QUESTIONS = [
    {
        "id": "company_profile",
        "question": "Company Profile",
        "fields": [
            "company_name",
            "registration_number",
            "address",
            "mobile_number",
            "email",
            "business_organization",
            "years_in_operation",
            "business_type",
            "women_ownership_percent",
            "men_ownership_percent",
            "company_overview",
        ],
        "required": True,
    },

    {
        "id": "growth_indicators",
        "question": "Growth Indicators",
        "fields": [
            "sales_2022",
            "sales_2023",
            "sales_2024",
            "sales_2025",
            "sales_2026",

            "employees_2022",
            "employees_2023",
            "employees_2024",
            "employees_2025",
            "employees_2026",

            "female_employees_2022",
            "female_employees_2023",
            "female_employees_2024",
            "female_employees_2025",
            "female_employees_2026",

            "youth_employees_2022",
            "youth_employees_2023",
            "youth_employees_2024",
            "youth_employees_2025",
            "youth_employees_2026",
        ],
        "required": True,
    },

    {
        "id": "motivation",
        "question": "Motivation to Apply and Personal Involvement",
        "fields": [
            "motivation_to_apply",
            "personal_involvement",
        ],
        "required": True,
    },

    {
        "id": "business_goals",
        "question": "Business Goals",
        "fields": [
            "short_term_goals",
            "long_term_goals",
        ],
        "required": True,
    },

    {
        "id": "market",
        "question": "Market Overview",
        "fields": [
            "market_overview",
            "target_customers",
            "geographies_served",
            "competitive_advantage",
            "market_challenges",
        ],
        "required": True,
    },

    {
        "id": "products_services",
        "question": "Main Products / Services",
        "fields": [
            "products_services",
            "product_service_uniqueness",
        ],
        "required": True,
    },

    {
        "id": "raw_materials",
        "question": "Raw Material Sourcing",
        "fields": [
            "local_raw_material_percentage",
        ],
        "required": False,
    },

    {
        "id": "management",
        "question": "Company Management Structure",
        "fields": [
            "management_team",
            "organogram",
        ],
        "required": True,
    },

    {
        "id": "intervention",
        "question": "Problems to be Addressed",
        "fields": [
            "problems_to_address",
        ],
        "required": True,
    },

    {
        "id": "equipment",
        "question": "Machinery and Equipment",
        "fields": [
            "requested_equipment",
        ],
        "required": False,
    },

    {
        "id": "consultants",
        "question": "Consultants",
        "fields": [
            "requested_consultants",
        ],
        "required": False,
    },

    {
        "id": "expected_results",
        "question": "Expected Results",
        "fields": [
            "expected_results",
            "priority_areas",
        ],
        "required": True,
    },

    {
        "id": "job_creation",
        "question": "Job Creation",
        "fields": [
            "jobs_to_create",
            "job_creation_explanation",
            "new_job_positions",
        ],
        "required": True,
    },

    {
        "id": "social_environmental",
        "question": "Social and Environmental Impact",
        "fields": [
            "social_environmental_impact",
        ],
        "required": True,
    },

    {
        "id": "osh",
        "question": "Occupational Safety and Health",
        "fields": [
            "occupational_safety_health",
        ],
        "required": True,
    },
]


def _empty_field(note="Not provided yet"):
    return {"value": None, "status": "missing", "source": None, "confidence": 0.0, "note": note}


def _normalize_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, list):
        values = [_normalize_value(v) for v in value]
        values = [str(v) for v in values if v not in (None, "")]
        return ", ".join(values) if values else None
    return str(value)


def _parse_json(text: str) -> dict:
    text = (text or "").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError(f"Model did not return valid JSON: {text[:500]}")
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("Model response was not a JSON object.")
    return data


def transcribe_audio(audio_bytes: bytes, language: str = "am", filename: str = "audio.mp3") -> str:
    if not audio_bytes:
        raise ValueError("Audio file is empty.")
    mime = mimetypes.guess_type(filename)[0] or "audio/mpeg"
    prompt = (
        "Ethiopian SME funding application. Preserve Amharic, Afaan Oromo, and English. "
        "Preserve business names, Ethiopian place names, phone numbers, registration numbers, "
        "birr/ETB amounts, years, percentages, employee counts, and equipment names. "
        "Do not translate or invent content."
    )
    response = client.audio.transcriptions.create(
        file=(os.path.basename(filename) or "audio.mp3", audio_bytes, mime),
        model=TRANSCRIBE_MODEL,
        language=language if language in {"en", "am", "om"} else None,
        prompt=prompt,
        response_format="text",
        temperature=0.0,
    )
    transcript = str(getattr(response, "text", response) or "").strip()
    if not transcript:
        raise ValueError("No speech was detected in the audio.")
    return transcript


def extract_from_transcript(transcript: str) -> dict:
    field_lines = "\n".join(f'"{k}": {v}' for k, v in FIELD_DEFINITIONS.items())
    prompt = f"""
Extract facts from this applicant transcript.

TRANSCRIPT:
{transcript}

FIELDS:
{field_lines}

Rules:
- Extract only facts explicitly stated in the transcript.
- Do not infer or invent.
- Preserve original language/value where practical.
- Put a value with no explicit year in the corresponding _current field.
- Year-specific fields require an explicit year.
- Return ONE JSON object containing only these field names.
- Use null when the field is not supported by the transcript.
""".strip()
    response = client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {"role": "system", "content": "You are a precise SME application fact extractor. Return JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=5000,
        response_format={"type": "json_object"},
    )
    return _parse_json(response.choices[0].message.content or "{}")


def _image_data_uri(file_bytes: bytes, filename: str) -> str:
    mime = mimetypes.guess_type(filename)[0] or "image/png"
    encoded = base64.b64encode(file_bytes).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def extract_from_image(file_bytes: bytes, filename: str, purpose: str) -> dict:
    if not file_bytes:
        return {}
    if len(file_bytes) > 15 * 1024 * 1024:
        raise ValueError(f"{filename} is larger than the 15 MB app limit.")
    if purpose == "license":
        instruction = (
            "Read this Ethiopian business licence. Extract only clearly visible, legible values. "
            "Focus on company/business name, registration/licence number, address, mobile number, and business type."
        )
    else:
        instruction = (
            "Inspect this workshop/business photo. Extract only directly visible text or clearly observable evidence. "
            "Do not guess facts that cannot be seen."
        )
    response = client.chat.completions.create(
        model=VISION_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": instruction + " Return JSON only."},
                {"type": "image_url", "image_url": {"url": _image_data_uri(file_bytes, filename)}},
            ],
        }],
        temperature=0,
        reasoning_effort="none",
        max_completion_tokens=1000,
        response_format={"type": "json_object"},
    )
    return _parse_json(response.choices[0].message.content or "{}")


def _merge(result: dict, field: str, value, source: str, confidence: float, note: str):
    value = _normalize_value(value)
    if value is None or field not in FIELD_DEFINITIONS:
        return
    current = result[field]
    # Document evidence can corroborate/override voice evidence for identity fields.
    if current.get("value") is None or source == "license_photo":
        result[field] = {
            "value": value,
            "status": "established",
            "source": source,
            "confidence": confidence,
            "note": note,
        }


def extract_evidence(transcript: str, licence_data: Optional[dict] = None, workshop_data: Optional[dict] = None) -> dict:
    if transcript and transcript.strip():
        raw = extract_from_transcript(transcript.strip())
    else:
        raw = {}

    result = {field: _empty_field() for field in FIELD_DEFINITIONS}
    for field in FIELD_DEFINITIONS:
        value = _normalize_value(raw.get(field))
        if value is not None:
            result[field] = {
                "value": value,
                "status": "established",
                "source": "voice_note",
                "confidence": 0.95,
                "note": "Explicitly extracted from applicant transcript.",
            }

    if licence_data and licence_data.get("bytes"):
        vision = extract_from_image(licence_data["bytes"], licence_data.get("filename", "license.png"), "license")
        for field in ["company_name", "registration_number", "address", "mobile_number", "business_type"]:
            _merge(result, field, vision.get(field), "license_photo", 0.98, "Explicitly visible on uploaded business licence.")

    if workshop_data and workshop_data.get("bytes"):
        vision = extract_from_image(workshop_data["bytes"], workshop_data.get("filename", "workshop.png"), "workshop")
        for field in ["company_name", "business_type", "products_services"]:
            _merge(result, field, vision.get(field), "workshop_photo", 0.85, "Supported by uploaded workshop photo evidence.")

    return result


def get_followup_questions(
    evidence: dict,
    language: str = "en"
) -> List[dict]:
    """
    Return missing information based on ACTUAL APPLICATION
    QUESTIONS rather than treating every extraction field
    as a separate form question.
    """

    translations = TRANSLATED_QUESTIONS.get(language, {})

    questions = []

    for application_question in APPLICATION_QUESTIONS:

        missing_fields = []

        for field in application_question["fields"]:

            entry = evidence.get(field) or {}

            value = entry.get("value")
            status = entry.get("status")

            if (
                status in {"missing", "unverified"}
                or value in (None, "")
            ):
                missing_fields.append(field)

        if not missing_fields:
            continue

        # ----------------------------------------------------
        # Build one natural question for the application item
        # ----------------------------------------------------

        question_id = application_question["id"]

        if question_id == "company_profile":

            question = (
                "I still need some company profile information. "
                "Please provide the missing details."
            )

        elif question_id == "growth_indicators":

            question = (
                "I need your growth figures for the required years, "
                "including sales and employee numbers."
            )

        elif question_id == "motivation":

            question = (
                "Why do you want to participate in the SME Support "
                "Scheme, and what is your involvement in the business?"
            )

        elif question_id == "business_goals":

            question = (
                "What are your short-term and long-term business goals?"
            )

        elif question_id == "market":

            question = (
                "Please describe your market, target customers, "
                "geographies served, competitive advantage, and "
                "main market challenges."
            )

        elif question_id == "products_services":

            question = (
                "What are your main products or services, and "
                "what makes them unique?"
            )

        elif question_id == "raw_materials":

            question = (
                "What percentage of your raw materials are "
                "locally sourced?"
            )

        elif question_id == "management":

            question = (
                "Please provide your core management team and "
                "describe your organizational structure."
            )

        elif question_id == "intervention":

            question = (
                "What business problems or challenges should "
                "the SME Support Scheme address?"
            )

        elif question_id == "equipment":

            question = (
                "What machinery or equipment are you requesting? "
                "Please include quantities and purposes if possible."
            )

        elif question_id == "consultants":

            question = (
                "What technical or consulting support do you need?"
            )

        elif question_id == "expected_results":

            question = (
                "What results do you expect from the support, "
                "and which three priority areas are most important?"
            )

        elif question_id == "job_creation":

            question = (
                "How many new jobs do you expect to create in "
                "the next 15 months, how will you create them, "
                "and what positions will be created?"
            )

        elif question_id == "social_environmental":

            question = (
                "Please explain the positive and negative social "
                "and environmental impacts of your business."
            )

        elif question_id == "osh":

            question = (
                "Please explain how your business addresses "
                "occupational safety and health."
            )

        else:

            question = application_question["question"]

        questions.append({
            "id": question_id,
            "question": question,
            "missing_fields": missing_fields,
            "required": application_question["required"],
        })

    return questions
def extract_followup_answer(
    question_fields: List[str],
    answer: str
) -> dict:
    """
    Extract only information relevant to the current
    follow-up question.
    """

    if not answer or not answer.strip():
        return {}

    fields = {
        field: FIELD_DEFINITIONS[field]
        for field in question_fields
        if field in FIELD_DEFINITIONS
    }

    field_lines = "\n".join(
        f'"{k}": {v}'
        for k, v in fields.items()
    )

    prompt = f"""
Extract information from the applicant's answer.

APPLICANT ANSWER:
{answer}

AVAILABLE FIELDS:
{field_lines}

RULES:
- Extract only explicitly stated information.
- Do not invent or infer.
- Only return fields supported by the answer.
- If a value is not present, return null.
- Return JSON only.
"""

    response = client.chat.completions.create(
        model=EXTRACTION_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract structured SME application "
                    "information from applicant answers. "
                    "Return JSON only."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
        reasoning_effort="low",
        max_completion_tokens=2000,
        response_format={
            "type": "json_object"
        },
    )

    return _parse_json(
        response.choices[0].message.content or "{}"
    )
def apply_followup_answer(
    evidence: dict,
    extracted: dict
) -> dict:
    """
    Add newly extracted information to the existing
    application evidence.
    """

    for field, value in extracted.items():

        if field not in FIELD_DEFINITIONS:
            continue

        value = _normalize_value(value)

        if value is None:
            continue

        evidence[field] = {
            "value": value,
            "status": "established",
            "source": "followup_answer",
            "confidence": 0.95,
            "note": "Explicitly provided during follow-up interview.",
        }

    return evidence