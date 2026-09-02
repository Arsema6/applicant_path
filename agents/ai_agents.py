import os
import io
import json
import base64
import mimetypes
import re
import wave
from typing import Optional, List

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types

load_dotenv()

# --------------------------------------------------------------
# Gemini -- used for transcription, extraction, vision and TTS.
# Keeping the whole pipeline on Gemini avoids OpenAI credit/quota
# failures and reduces the number of external providers involved.
# --------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Add it to your .env file."
    )

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

TRANSCRIBE_MODEL = "gemini-2.5-flash"
TTS_MODEL = "gemini-2.5-flash-preview-tts"
TTS_VOICE = "Kore"
EXTRACTION_MODEL = "gemini-2.5-flash"
VISION_MODEL = "gemini-2.5-flash"

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


# Explicit extension -> MIME map. mimetypes.guess_type() is
# unreliable for some browser-recorded formats (m4a/webm are often
# missing from the system's mime database), and a wrong MIME label
# is a common cause of audio being "misheard": the model is told
# the container format is something it isn't.
_AUDIO_MIME_MAP = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".mp4": "audio/mp4",
    ".webm": "audio/webm",
    ".ogg": "audio/ogg",
    ".oga": "audio/ogg",
    ".flac": "audio/flac",
    ".aac": "audio/aac",
}


def _guess_audio_mime(filename: str) -> str:
    ext = os.path.splitext(filename or "")[1].lower()
    # st.audio_input() records browser microphone audio as WAV, so
    # that's the safest default when the extension is unknown --
    # NOT audio/mpeg, which silently breaks recorder-captured audio.
    return _AUDIO_MIME_MAP.get(ext, "audio/wav")


_LANGUAGE_NAMES = {
    "en": "English",
    "am": "Amharic",
    "om": "Afaan Oromo (Oromo)",
}


def transcribe_audio(audio_bytes: bytes, language: str = "am", filename: str = "audio.wav") -> str:
    """
    Speech-to-text via Gemini's native audio understanding.

    Gemini is used here instead of a Whisper-family model because
    its multilingual coverage is significantly broader -- in
    particular Afaan Oromo, which Whisper-based models do not
    reliably support, leading to garbled or empty transcripts.
    """
    if not audio_bytes:
        raise ValueError("Audio file is empty.")

    mime = _guess_audio_mime(filename)
    language_hint = _LANGUAGE_NAMES.get(language, "English, Amharic, or Afaan Oromo")

    prompt = (
        "You are transcribing a short voice recording from an Ethiopian "
        f"SME funding applicant. The speaker is most likely using "
        f"{language_hint}, but may switch languages mid-sentence -- "
        "transcribe exactly what is said, in whichever language(s) are "
        "actually spoken. Do not translate. Do not summarize. Do not "
        "invent words you are not confident about. Preserve business "
        "names, Ethiopian place names, phone numbers, registration "
        "numbers, birr/ETB amounts, years, percentages, and employee "
        "counts exactly as spoken, including numerals. "
        "Respond with ONLY the transcript text -- no labels, quotes, "
        "or commentary. If the audio contains no intelligible speech, "
        "respond with exactly: [NO_SPEECH]"
    )

    response = gemini_client.models.generate_content(
        model=TRANSCRIBE_MODEL,
        contents=[
            prompt,
            genai_types.Part.from_bytes(data=audio_bytes, mime_type=mime),
        ],
        config=genai_types.GenerateContentConfig(temperature=0.0),
    )

    transcript = (getattr(response, "text", None) or "").strip()
    # Some models wrap the answer in quotes despite instructions not to.
    transcript = transcript.strip('"').strip("'").strip()

    if not transcript or transcript == "[NO_SPEECH]":
        raise ValueError("No speech was detected in the audio.")

    return transcript


def synthesize_speech(text: str, language: str = "en") -> Optional[bytes]:
    """
    Text-to-speech for follow-up questions, via Gemini TTS, so an
    applicant can hear each question as well as read it.

    Returns WAV bytes, or None if speech could not be generated.
    Voice output is a convenience on top of the always-shown text
    question, so failures here are swallowed rather than raised --
    the follow-up flow must keep working even if TTS is unavailable.
    """
    if not text or not text.strip():
        return None

    try:
        response = gemini_client.models.generate_content(
            model=TTS_MODEL,
            contents=text.strip(),
            config=genai_types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=genai_types.SpeechConfig(
                    voice_config=genai_types.VoiceConfig(
                        prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                            voice_name=TTS_VOICE,
                        )
                    )
                ),
            ),
        )
        pcm_data = response.candidates[0].content.parts[0].inline_data.data
        if not pcm_data:
            return None
    except Exception:
        return None

    # Gemini TTS returns raw 24kHz/16-bit/mono PCM -- wrap it as a
    # WAV file so st.audio() can play it directly.
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm_data)
    return buffer.getvalue()


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
- Do not infer, invent, calculate, or use outside knowledge.
- Preserve the applicant's original language/value where practical.
- Put a value with no explicit year in the corresponding _current field.
- Year-specific fields require an explicit year.
- Return ONE JSON object containing only the field names above.
- Use null when the field is not supported by the transcript.
""".strip()

    response = gemini_client.models.generate_content(
        model=EXTRACTION_MODEL,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    return _parse_json(getattr(response, "text", None) or "{}")


def _image_part(file_bytes: bytes, filename: str):
    mime = mimetypes.guess_type(filename)[0] or "image/png"
    return genai_types.Part.from_bytes(data=file_bytes, mime_type=mime)


def extract_from_image(file_bytes: bytes, filename: str, purpose: str) -> dict:
    if not file_bytes:
        return {}
    if len(file_bytes) > 15 * 1024 * 1024:
        raise ValueError(f"{filename} is larger than the 15 MB app limit.")

    if purpose == "license":
        instruction = (
            "Read this Ethiopian business licence. Extract only clearly visible, "
            "legible values. Focus on company/business name, registration/licence "
            "number, address, mobile number, and business type."
        )
    else:
        instruction = (
            "Inspect this workshop/business photo. Extract only directly visible "
            "text or clearly observable evidence. Do not guess facts that cannot be seen."
        )

    prompt = instruction + " Return JSON only. Use only the fields that are supported by the image."
    response = gemini_client.models.generate_content(
        model=VISION_MODEL,
        contents=[prompt, _image_part(file_bytes, filename)],
        config=genai_types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
        ),
    )
    return _parse_json(getattr(response, "text", None) or "{}")


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


# ------------------------------------------------------------------
# One flattened, deterministic field order (topic-grouped, using the
# original APPLICATION_QUESTIONS groupings purely for ordering) so
# follow-up questions are asked in a sensible sequence: company
# profile first, then growth figures, then narrative sections, etc.
# ------------------------------------------------------------------

def _flattened_field_order() -> List[str]:
    order: List[str] = []
    seen = set()

    for group in APPLICATION_QUESTIONS:
        for field in group["fields"]:
            if field not in seen:
                order.append(field)
                seen.add(field)

    for field in FIELD_DEFINITIONS:
        if field not in seen:
            order.append(field)
            seen.add(field)

    return order


FIELD_ORDER = _flattened_field_order()


def _is_missing(entry: Optional[dict]) -> bool:
    entry = entry or {}
    value = entry.get("value")
    status = entry.get("status")
    return value in (None, "") or status in {"missing", "unverified"}


def get_followup_questions(
    evidence: dict,
    language: str = "en"
) -> List[dict]:
    """
    Return ONE question per ONE missing field, in a sensible topic
    order. Each item is {"field": ..., "question": ...} -- always
    a single concrete field, never a bundle -- so an applicant's
    answer can be reliably matched back to the field it belongs to
    and the follow-up loop reliably terminates once every field has
    been asked about.
    """

    translations = TRANSLATED_QUESTIONS.get(language, {})

    questions = []

    for field in FIELD_ORDER:

        if not _is_missing(evidence.get(field)):
            continue

        question = (
            translations.get(field)
            or FIELD_QUESTIONS.get(field)
            or f"Please provide information about {field.replace('_', ' ')}."
        )

        questions.append({
            "field": field,
            "question": question,
        })

    return questions


def extract_followup_answer(
    question_field: str,
    question_text: str,
    answer_text: str,
    evidence: dict,
) -> dict:
    """
    Use Gemini to turn one free-form follow-up answer into structured values.
    The asked field is always retained with the raw answer as a safe fallback.
    """
    answer_text = (answer_text or "").strip()
    if not answer_text:
        return {}

    other_missing = [
        f for f in FIELD_ORDER
        if f != question_field and _is_missing(evidence.get(f))
    ][:12]
    candidate_fields = [question_field] + other_missing
    field_lines = "\n".join(
        f"- {f}: {FIELD_DEFINITIONS[f]}"
        for f in candidate_fields
        if f in FIELD_DEFINITIONS
    )

    prompt = f"""
The applicant was asked this follow-up question:
"{question_text}"

The applicant's answer (typed or voice-transcribed, verbatim):
"{answer_text}"

From this answer, extract values ONLY for these fields:
{field_lines}

RULES:
- Extract only information explicitly stated in the answer.
- Do not infer, calculate, guess, or use outside knowledge.
- The field "{question_field}" was directly asked about; extract its value if addressed.
- Only include a field if the answer actually supports it.
- Preserve numbers, names, and original wording/language where practical.
- Return a single JSON object mapping field name -> extracted value.
""".strip()

    try:
        response = gemini_client.models.generate_content(
            model=EXTRACTION_MODEL,
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )
        extracted_raw = _parse_json(getattr(response, "text", None) or "{}")
    except Exception:
        extracted_raw = {}

    result = {}
    for field, value in extracted_raw.items():
        if field not in FIELD_DEFINITIONS:
            continue
        value = _normalize_value(value)
        if value is not None:
            result[field] = value

    if question_field not in result:
        result[question_field] = answer_text
    return result


def apply_followup_answer(
    evidence: dict,
    extracted: dict
) -> dict:
    """
    Add newly extracted information to the existing application
    evidence. Kept for callers that want a simple overwrite instead
    of resolve_followup_value()'s contradiction handling.
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