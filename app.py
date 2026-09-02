import json
import io
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from agents.ai_agents import (
    transcribe_audio,
    synthesize_speech,
    extract_evidence,
    get_followup_questions,
    extract_followup_answer,
    FIELD_DEFINITIONS,
)

from agents.form_integration import (
    build_prefill_url,
    submit_application,
    validate_evidence,
    resolve_followup_value,
)


# =========================================================
# CONFIG
# =========================================================

load_dotenv()


LANGUAGES = {
    "English": "en",
    "Amharic": "am",
    "Afaan Oromo": "om",
}


# =========================================================
# UI TRANSLATIONS
# =========================================================

UI_TEXT = {
    "en": {
        "title": "🌱 SME Funding Application",
        "subtitle": "Turn your story into a funding application",
        "caption": "Impact Protocol Hackathon | Powered by OpenAI + Gemini",

        "instructions_title": "📋 Instructions",

        "instructions": (
            "1. Upload your voice note\n"
            "2. Upload your business licence\n"
            "3. Upload a workshop photo\n"
            "4. Process the application\n"
            "5. Review the populated form\n"
            "6. Answer follow-up questions until every field is complete"
        ),

        "data_note": (
            "Audio is sent to Gemini and text/images are sent to OpenAI for processing. "
            "This app does not persist application data."
        ),

        "api_ready": "✅ OpenAI + Gemini API Ready",

        "step1": "📤 Step 1: Applicant Evidence",
        "voice_note": "🎙 Voice Note",
        "mock_transcript": "Use mock transcript for testing",
        "mock_placeholder": "Mock Transcript",

        "mock_default": (
            "My name is Almaz Wolde. I run a spice mill in Bekoji Tera. "
            "My business is called Almaz Spice Mill. "
            "Registration number is 12345/2020. "
            "I have been operating for 5 years. "
            "I have 8 employees, 6 are women. "
            "Annual sales are 1.5 million birr. "
            "We need equipment for grinding and packaging."
        ),

        "upload_voice": (
            "Upload a voice note (Amharic, Afaan Oromo, or English)"
        ),

        "documents": "📸 Documents",
        "license": "Business Licence",
        "workshop": "Workshop Photo",
        "process": "🚀 Process Application",

        "error_voice": "Please upload a voice note or enable mock transcript.",
        "error_mock": "Please enter a mock transcript.",

        "step1_transcript": "📝 Step 1: Transcription",
        "transcribing": "Transcribing voice note...",
        "using_mock": "📝 Using mock transcript",
        "transcription_complete": "✅ Transcription complete!",
        "transcription_error": "❌ Transcription failed:",
        "transcript_label": "Transcript",

        "step2_extract": "🔍 Step 2: Information Extraction",
        "extracting": "Extracting and analyzing application data...",
        "extraction_complete": "✅ Extraction complete!",
        "extraction_error": "❌ Extraction failed:",

        "step3_data": "📋 Step 3: Review & Auto-Populated Application",

        "established": "✅ Established",
        "unverified": "⚠️ Unverified",
        "missing": "❌ Missing",
        "total": "📊 Total",

        "status": "Status",
        "confidence": "Confidence",

        "step4_followup": "❓ Step 4: Complete Missing Information",

        "remaining": "⚠️ {} fields still need information",
        "no_remaining": "🎉 All application fields are complete!",

        "answer_mode": "Answer method",
        "mode_text": "✏️ Text",
        "mode_voice": "🎙 Voice",

        "answer_for": "Answer for {}",
        "type_answer": "Enter the applicant's answer...",
        "record_or_upload": "Record or upload an audio answer",
        "heard": "🗣️ Heard:",

        "save_followup": "🔄 Save Answer & Continue",
        "save_form": "💾 Save Reviewed Form",

        "step5_export": "📤 Step 5: Export & Submit",

        "view_json": "📄 View Full Application JSON",
        "download": "⬇️ Download Application Data",

        "jotform": "📝 Open Prefilled Jotform",

        "jotform_note": (
            "Jotform URL prefilling depends on the real field parameter "
            "names in the target form. The in-app form below is the "
            "authoritative completed application data."
        ),

        "ready": "🎯 Application complete and ready for review/submission!",
        "not_ready": "Complete all remaining fields before final submission.",

        "submit": "🚀 Submit Application to Jotform",
        "submitting": "Submitting application to Jotform...",
        "submitted": "✅ Application submitted successfully!",
        "submission_error": "❌ Application submission failed:",

        "start_over": "🗑️ Start Over",

        "footer": (
            "🌱 Impact Protocol Hackathon | Applicant Path Challenge"
        ),

        "followup_error": "Follow-up question could not be generated.",
        "followup_answer_error": "Enter an answer before continuing.",
        "next_question": "Next question",
        "current_answer": "Current answer",
        "image_compressed": "Images optimized for processing.",
    },

    "am": {
        "title": "🌱 የአነስተኛ ንግድ የገንዘብ ድጋፍ ማመልከቻ",

        "subtitle": (
            "ታሪክዎን ወደ የገንዘብ ድጋፍ ማመልከቻ ይቀይሩ"
        ),

        "caption": "Impact Protocol Hackathon | በ OpenAI + Gemini የተጎላበተ",

        "instructions_title": "📋 መመሪያዎች",

        "instructions": (
            "1. የድምጽ መልዕክት ይስቀሉ\n"
            "2. የንግድ ፈቃድ ይስቀሉ\n"
            "3. የስራ ቦታ ፎቶ ይስቀሉ\n"
            "4. ማመልከቻውን ያስኬዱ\n"
            "5. የተሞላውን ፎርም ይገምግሙ\n"
            "6. ሁሉም መስኮች እስኪሞሉ ድረስ "
            "ተከታይ ጥያቄዎችን ይመልሱ"
        ),

        "data_note": (
            "ድምጽ ወደ Gemini፣ ጽሑፍ እና ምስሎች ወደ OpenAI ለማስኬድ ይላካሉ። "
            "መተግበሪያው መረጃውን በቋሚነት አያስቀምጥም።"
        ),

        "api_ready": "✅ OpenAI + Gemini ዝግጁ ናቸው",

        "step1": "📤 ደረጃ 1: የአመልካች ማስረጃ",
        "voice_note": "🎙 የድምጽ መልዕክት",
        "mock_transcript": "ለመሞከር የሙክ ጽሑፍ ይጠቀሙ",
        "mock_placeholder": "የሙክ ጽሑፍ",

        "mock_default": (
            "ስሜ አልማዝ ወልደ ነው። "
            "በበቆጂ ቴራ የቅመማ ቅመም ወፍጮ እሰራለሁ። "
            "የንግድ ስሜ አልማዝ ቅመማ ቅመም ወፍጮ ነው። "
            "የምዝገባ ቁጥሬ 12345/2020 ነው። "
            "ለ5 ዓመታት ስሰራ ቆይቻለሁ። "
            "8 ሰራተኞች አሉኝ፣ ከነሱ 6ቱ ሴቶች ናቸው። "
            "ዓመታዊ ሽያጬ 1.5 ሚሊዮን ብር ነው። "
            "ለመፍጨት እና ለማሸግ መሳሪያ ያስፈልጉኛል።"
        ),

        "upload_voice": "የድምጽ መልዕክት ይስቀሉ",

        "documents": "📸 ሰነዶች",
        "license": "የንግድ ፈቃድ",
        "workshop": "የስራ ቦታ ፎቶ",
        "process": "🚀 ማመልከቻውን ያስኬዱ",

        "error_voice": "እባክዎ የድምጽ መልዕክት ይስቀሉ።",
        "error_mock": "እባክዎ የሙክ ጽሑፍ ያስገቡ።",

        "step1_transcript": "📝 ደረጃ 1: ወደ ጽሑፍ መቀየር",
        "transcribing": "የድምጽ መልዕክቱን ወደ ጽሑፍ እየቀየረ...",
        "using_mock": "📝 የሙክ ጽሑፍ በመጠቀም ላይ",
        "transcription_complete": "✅ ወደ ጽሑፍ መቀየር ተጠናቀቀ!",
        "transcription_error": "❌ የጽሑፍ መቀየር አልተሳካም:",
        "transcript_label": "ጽሑፍ",

        "step2_extract": "🔍 ደረጃ 2: መረጃ ማውጣት",
        "extracting": "የማመልከቻ መረጃን እያወጣ...",
        "extraction_complete": "✅ መረጃ ተወጥቷል!",
        "extraction_error": "❌ መረጃ ማውጣት አልተሳካም:",

        "step3_data": "📋 ደረጃ 3: የተሞላውን ማመልከቻ ይገምግሙ",

        "established": "✅ ተረጋግጧል",
        "unverified": "⚠️ አልተረጋገጠም",
        "missing": "❌ ጠፍቷል",
        "total": "📊 ጠቅላላ",

        "status": "ሁኔታ",
        "confidence": "እምነት",

        "step4_followup": "❓ ደረጃ 4: የጎደለውን መረጃ ይሙሉ",

        "remaining": "⚠️ {} መስኮች አሁንም መረጃ ይፈልጋሉ",
        "no_remaining": "🎉 ሁሉም የማመልከቻ መስኮች ተሞልተዋል!",

        "answer_mode": "የመልስ መንገድ",
        "mode_text": "✏️ ጽሑፍ",
        "mode_voice": "🎙 ድምጽ",

        "answer_for": "ለ {} መልስ",
        "type_answer": "የአመልካቹን መልስ እዚህ ያስገቡ...",
        "record_or_upload": "መልስ ይቅረጹ ወይም የድምጽ ፋይል ይስቀሉ",
        "heard": "🗣️ የተሰማ:",

        "save_followup": "🔄 መልሱን አስቀምጥ እና ቀጥል",
        "save_form": "💾 የተገመገመውን ማመልከቻ አስቀምጥ",

        "step5_export": "📤 ደረጃ 5: ማውጣት እና ማስገባት",

        "view_json": "📄 ሙሉ የማመልከቻ JSON",
        "download": "⬇️ የማመልከቻ መረጃ ያውርዱ",

        "jotform": "📝 ወደ Prefilled Jotform ይሂዱ",

        "jotform_note": (
            "የJotform ቅድመ-መሙያ የሚሰራው "
            "የእውነተኛው ፎርም የመስክ መለያዎች ትክክል ከሆኑ ብቻ ነው።"
        ),

        "ready": (
            "🎯 ማመልከቻው ተሟልቶ ለግምገማ/ማስገባት ዝግጁ ነው!"
        ),

        "not_ready": (
            "ለመጨረሻ ማስገባት የቀሩትን መስኮች ይሙሉ።"
        ),

        "submit": "🚀 ማመልከቻውን ወደ Jotform ያስገቡ",
        "submitting": "ማመልከቻውን ወደ Jotform በማስገባት ላይ...",
        "submitted": "✅ ማመልከቻው በተሳካ ሁኔታ ገብቷል!",
        "submission_error": "❌ ማመልከቻውን ማስገባት አልተሳካም:",

        "start_over": "🗑️ እንደገና ጀምር",

        "footer": (
            "🌱 Impact Protocol Hackathon | የአመልካች መንገድ"
        ),

        "followup_error": "ተከታይ ጥያቄ ማመንጨት አልተቻለም።",
        "followup_answer_error": "እባክዎ መልስ ያስገቡ።",
        "next_question": "ቀጣይ ጥያቄ",
        "current_answer": "የአሁኑ መልስ",
        "image_compressed": "ምስሎቹ ለማስኬጃ ተመቻችተዋል።",
    },
}


# Oromo uses English UI for now.
UI_TEXT["om"] = UI_TEXT["en"]


# =========================================================
# APPLICATION FORM STRUCTURE
# =========================================================

SECTION_FIELDS = {
    "Company Profile": [
        "company_name",
        "registration_number",
        "address",
        "mobile_number",
        "email",
        "business_organization",
        "years_in_operation",
        "business_type",
    ],

    "Ownership": [
        "women_ownership_percent",
        "men_ownership_percent",
    ],

    "Company Overview & Growth": [
        "company_overview",
        "sales_current",
        "sales_2022",
        "sales_2023",
        "sales_2024",
        "sales_2025",
        "sales_2026",
    ],

    "Employees": [
        "employees_current",
        "employees_2022",
        "employees_2023",
        "employees_2024",
        "employees_2025",
        "employees_2026",

        "female_employees_current",
        "female_employees_2022",
        "female_employees_2023",
        "female_employees_2024",
        "female_employees_2025",
        "female_employees_2026",

        "youth_employees_current",
        "youth_employees_2022",
        "youth_employees_2023",
        "youth_employees_2024",
        "youth_employees_2025",
        "youth_employees_2026",
    ],

    "Business Goals & Market": [
        "motivation_to_apply",
        "personal_involvement",
        "short_term_goals",
        "long_term_goals",
        "market_overview",
        "target_customers",
        "geographies_served",
        "competitive_advantage",
        "market_challenges",
    ],

    "Products & Management": [
        "products_services",
        "product_service_uniqueness",
        "local_raw_material_percentage",
        "management_team",
        "organogram",
    ],

    "Requested Intervention": [
        "problems_to_address",
        "requested_equipment",
        "requested_consultants",
        "expected_results",
        "priority_areas",
        "jobs_to_create",
        "job_creation_explanation",
        "new_job_positions",
        "social_environmental_impact",
        "occupational_safety_health",
    ],
}


LONG_FIELDS = {
    "company_overview",
    "motivation_to_apply",
    "personal_involvement",
    "short_term_goals",
    "long_term_goals",
    "market_overview",
    "target_customers",
    "geographies_served",
    "competitive_advantage",
    "market_challenges",
    "products_services",
    "product_service_uniqueness",
    "management_team",
    "organogram",
    "problems_to_address",
    "requested_equipment",
    "requested_consultants",
    "expected_results",
    "priority_areas",
    "job_creation_explanation",
    "new_job_positions",
    "social_environmental_impact",
    "occupational_safety_health",
}


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def T(key):
    code = LANGUAGES.get(
        st.session_state.get("selected_language", "English"),
        "en",
    )

    return UI_TEXT.get(
        code,
        UI_TEXT["en"],
    ).get(
        key,
        UI_TEXT["en"].get(key, key),
    )


def field_label(field):
    return field.replace("_", " ").title()


def field_value(evidence, field):
    value = (evidence.get(field) or {}).get("value")

    if value is None:
        return ""

    return str(value)


def is_field_missing(evidence, field):
    data = evidence.get(field) or {}

    value = data.get("value")
    status = data.get("status")

    return (
        value in (None, "")
        or status in {"missing", "unverified"}
    )


def missing_fields(evidence):
    return [
        field
        for field in FIELD_DEFINITIONS
        if is_field_missing(evidence, field)
    ]


def sync_widgets_from_evidence():
    """
    IMPORTANT:
    This function is called ONLY before widgets are created.
    It prevents the Streamlit session-state widget error.
    """

    evidence = st.session_state.evidence or {}

    for field in FIELD_DEFINITIONS:

        key = f"form_{field}"

        # This function runs BEFORE the widgets are created, so it is
        # safe to overwrite the widget state here. This is necessary
        # after a follow-up answer changes the evidence because the
        # existing form_* value may still contain the old empty value.
        st.session_state[key] = field_value(
            evidence,
            field,
        )


def build_updated_evidence_from_widgets(evidence):

    updated = dict(evidence)

    for field in FIELD_DEFINITIONS:

        key = f"form_{field}"

        value = str(
            st.session_state.get(key, "")
        ).strip()

        old = dict(
            updated.get(field) or {}
        )

        if value:

            updated[field] = {
                "value": value,
                "status": "established",
                "source": (
                    old.get("source")
                    or "applicant_review"
                ),
                "confidence": max(
                    float(
                        old.get(
                            "confidence",
                            0.0,
                        )
                    ),
                    0.95,
                ),
                "note": (
                    old.get("note")
                    or
                    "Confirmed or edited in the application review form."
                ),
            }

        else:

            updated[field] = {
                "value": None,
                "status": "missing",
                "source": None,
                "confidence": 0.0,
                "note": "Not provided.",
            }

    return updated


# =========================================================
# IMAGE COMPRESSION
# =========================================================

def prepare_image_for_upload(
    uploaded_file,
    max_dimension=1400,
    max_bytes=650_000,
):
    """
    Reduce image size before sending it to the API.

    This prevents:
        413 Request Entity Too Large

    The original uploaded file is never modified.
    """

    if uploaded_file is None:
        return None

    original_bytes = uploaded_file.getvalue()

    try:
        image = Image.open(
            io.BytesIO(original_bytes)
        )

        image.load()

        # Convert formats that JPEG cannot handle.
        if image.mode in (
            "RGBA",
            "LA",
            "P",
        ):
            background = Image.new(
                "RGB",
                image.size,
                "white",
            )

            if image.mode == "P":
                image = image.convert("RGBA")

            if image.mode in (
                "RGBA",
                "LA",
            ):
                background.paste(
                    image,
                    mask=image.getchannel("A"),
                )

                image = background

            else:
                image = image.convert("RGB")

        else:
            image = image.convert("RGB")

        # Resize while preserving aspect ratio.
        width, height = image.size

        scale = min(
            1.0,
            max_dimension / max(width, height),
        )

        if scale < 1.0:

            new_size = (
                max(1, int(width * scale)),
                max(1, int(height * scale)),
            )

            image = image.resize(
                new_size,
                Image.Resampling.LANCZOS,
            )

        # Compress progressively.
        quality = 80

        while quality >= 35:

            output = io.BytesIO()

            image.save(
                output,
                format="JPEG",
                quality=quality,
                optimize=True,
            )

            data = output.getvalue()

            if len(data) <= max_bytes:
                return {
                    "filename": (
                        uploaded_file.name
                       .rsplit(".", 1)[0]
                        + ".jpg"
                    ),
                    "bytes": data,
                }

            quality -= 10

        # Last-resort smaller image.
        width, height = image.size

        while True:

            width = int(width * 0.75)
            height = int(height * 0.75)

            if width < 500 or height < 500:
                break

            smaller = image.resize(
                (width, height),
                Image.Resampling.LANCZOS,
            )

            output = io.BytesIO()

            smaller.save(
                output,
                format="JPEG",
                quality=45,
                optimize=True,
            )

            data = output.getvalue()

            if len(data) <= max_bytes:

                return {
                    "filename": (
                        uploaded_file.name
                        .rsplit(".", 1)[0]
                        + ".jpg"
                    ),
                    "bytes": data,
                }

        # Return final compressed version even if slightly over target.
        output = io.BytesIO()

        image.thumbnail(
            (700, 700),
            Image.Resampling.LANCZOS,
        )

        image.save(
            output,
            format="JPEG",
            quality=40,
            optimize=True,
        )

        return {
            "filename": (
                uploaded_file.name
                .rsplit(".", 1)[0]
                + ".jpg"
            ),
            "bytes": output.getvalue(),
        }

    except Exception:
        # If PIL cannot process the file, return original.
        return {
            "filename": uploaded_file.name,
            "bytes": original_bytes,
        }


# =========================================================
# FOLLOW-UP QUESTION NORMALIZATION
# =========================================================

def normalize_followup_questions(
    raw_questions,
    evidence,
):
    """
    Converts whatever get_followup_questions() returns
    into a reliable structure:

        {
            "field": "...",
            "question": "..."
        }

    Handles:

    1. {"field": "...", "question": "..."}
    2. {"name": "...", "question": "..."}
    3. {"question": "..."}   <-- your current problem
    4. plain strings
    """

    missing = missing_fields(evidence)

    if not missing:
        return []

    if raw_questions is None:
        raw_questions = []

    if isinstance(
        raw_questions,
        dict,
    ):
        raw_questions = [raw_questions]

    if isinstance(
        raw_questions,
        str,
    ):
        raw_questions = [raw_questions]

    normalized = []

    used_fields = set()

    for index, item in enumerate(raw_questions):

        question = None
        field = None

        # -----------------------------------------------
        # Dictionary response
        # -----------------------------------------------

        if isinstance(item, dict):

            field = (
                item.get("field")
                or item.get("name")
                or item.get("field_name")
                or item.get("key")
            )

            question = (
                item.get("question")
                or item.get("text")
                or item.get("prompt")
            )

        # -----------------------------------------------
        # Plain string response
        # -----------------------------------------------

        elif isinstance(item, str):

            question = item

        # -----------------------------------------------
        # Find field
        # -----------------------------------------------

        if field not in missing:

            field = None

        if field is None:

            # Use the next missing field that has not
            # already been assigned.
            for candidate in missing:

                if candidate not in used_fields:

                    field = candidate
                    break

        if field is None:
            continue

        used_fields.add(field)

        # -----------------------------------------------
        # If the AI did not provide a question,
        # generate a deterministic fallback.
        # -----------------------------------------------

        if not question:

            question = (
                f"Please provide information for "
                f"{field_label(field)}."
            )

        normalized.append(
            {
                "field": field,
                "question": str(question).strip(),
            }
        )

    # ---------------------------------------------------
    # IMPORTANT:
    #
    # Every missing field now gets its own question from
    # get_followup_questions(), but this stays as a safety
    # net in case a field is ever dropped upstream.
    #
    # We therefore guarantee that every missing field
    # has a follow-up question.
    # ---------------------------------------------------

    existing_fields = {
        item["field"]
        for item in normalized
    }

    for field in missing:

        if field in existing_fields:
            continue

        normalized.append(
            {
                "field": field,
                "question": (
                    f"Please provide information for "
                    f"{field_label(field)}."
                ),
            }
        )

    return normalized


def get_safe_followups(evidence, language):
    """
    Safely calls the agent and guarantees that every
    returned follow-up has a field.
    """

    try:

        raw = get_followup_questions(
            evidence,
            language,
        )

        return normalize_followup_questions(
            raw,
            evidence,
        )

    except Exception as exc:

        # Do not completely break the application if
        # the LLM follow-up generator fails.
        st.warning(
            f"{T('followup_error')} {exc}"
        )

        # Deterministic fallback.
        return [
            {
                "field": field,
                "question": (
                    f"Please provide information for "
                    f"{field_label(field)}."
                ),
            }
            for field in missing_fields(evidence)
        ]


# =========================================================
# SESSION STATE
# =========================================================

st.set_page_config(
    page_title="SME Funding Application",
    page_icon="🌱",
    layout="wide",
)


DEFAULT_STATE = {
    "selected_language": "English",
    "evidence": None,
    "transcript": "",
    "pending_form_sync": False,
    "submission_result": None,
    "processed": False,
}


for key, default in DEFAULT_STATE.items():

    if key not in st.session_state:

        st.session_state[key] = default


# =========================================================
# LANGUAGE
# =========================================================

language = st.selectbox(
    "🌍 Select Language / ቋንቋ / Afaan",
    list(LANGUAGES.keys()),
    index=list(LANGUAGES.keys()).index(
        st.session_state.selected_language
    ),
)


if language != st.session_state.selected_language:

    st.session_state.selected_language = language

    st.rerun()


# =========================================================
# HEADER
# =========================================================

st.title(
    T("title")
)

st.subheader(
    T("subtitle")
)

st.caption(
    T("caption")
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header(
        T("instructions_title")
    )

    st.markdown(
        T("instructions")
    )

    st.divider()

    st.caption(
        T("data_note")
    )

    st.success(
        T("api_ready")
    )


# =========================================================
# STEP 1
# =========================================================

st.header(
    T("step1")
)


col1, col2 = st.columns(
    [2, 1]
)


with col1:

    st.subheader(
        T("voice_note")
    )

    use_mock = st.checkbox(
        T("mock_transcript"),
        key="use_mock",
    )

    if use_mock:

        mock_text = st.text_area(
            T("mock_placeholder"),
            value=T("mock_default"),
            height=140,
            key="mock_text",
        )

        voice_file = None

    else:

        mock_text = ""

        voice_file = st.file_uploader(
            T("upload_voice"),
            type=[
                "mp3",
                "wav",
                "m4a",
                "webm",
                "ogg",
                "flac",
            ],
            key="main_voice",
        )


with col2:

    st.subheader(
        T("documents")
    )

    license_photo = st.file_uploader(
        T("license"),
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="license_photo",
    )

    workshop_photo = st.file_uploader(
        T("workshop"),
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="workshop_photo",
    )


# =========================================================
# PROCESS APPLICATION
# =========================================================

if st.button(
    T("process"),
    type="primary",
    use_container_width=True,
):

    # -----------------------------------------------------
    # Validate input
    # -----------------------------------------------------

    if not use_mock and not voice_file:

        st.error(
            T("error_voice")
        )

        st.stop()

    if use_mock and not mock_text.strip():

        st.error(
            T("error_mock")
        )

        st.stop()

    # -----------------------------------------------------
    # STEP 1: TRANSCRIPTION
    # -----------------------------------------------------

    st.subheader(
        T("step1_transcript")
    )

    try:

        with st.spinner(
            T("transcribing")
        ):

            if use_mock:

                transcript = mock_text.strip()

                st.info(
                    T("using_mock")
                )

            else:

                transcript = transcribe_audio(
                    voice_file.getvalue(),
                    LANGUAGES[
                        st.session_state.selected_language
                    ],
                    voice_file.name,
                )

        st.session_state.transcript = transcript

        st.success(
            T("transcription_complete")
        )

        st.text_area(
            T("transcript_label"),
            transcript,
            height=180,
            key="transcript_display",
        )

    except Exception as exc:

        st.error(
            f"{T('transcription_error')} {exc}"
        )

        st.stop()

    # -----------------------------------------------------
    # STEP 2: EXTRACTION
    # -----------------------------------------------------

    st.subheader(
        T("step2_extract")
    )

    try:

        with st.spinner(
            T("extracting")
        ):

            # ---------------------------------------------
            # Compress images before sending them to the API.
            # ---------------------------------------------

            license_data = None

            if license_photo:

                license_data = (
                    prepare_image_for_upload(
                        license_photo
                    )
                )

            workshop_data = None

            if workshop_photo:

                workshop_data = (
                    prepare_image_for_upload(
                        workshop_photo
                    )
                )

            if license_data or workshop_data:

                st.caption(
                    T("image_compressed")
                )

            # ---------------------------------------------
            # Extract
            # ---------------------------------------------

            extracted = extract_evidence(
                st.session_state.transcript,
                licence_data=license_data,
                workshop_data=workshop_data,
            )

            if not isinstance(
                extracted,
                dict,
            ):
                raise ValueError(
                    "Extraction returned an invalid format."
                )

            st.session_state.evidence = extracted

            st.session_state.pending_form_sync = True

            st.session_state.processed = True

            st.session_state.submission_result = None

        st.success(
            T("extraction_complete")
        )

    except Exception as exc:

        st.error(
            f"{T('extraction_error')} {exc}"
        )

        # Give a useful explanation for 413.
        if (
            "413" in str(exc)
            or
            "Request Entity Too Large" in str(exc)
            or
            "request_too_large" in str(exc)
        ):

            st.warning(
                "The image/audio request was too large for the "
                "API. Images are now automatically resized and "
                "compressed before extraction. If this still "
                "occurs, the next optimization should be made "
                "inside agents/ai_agents.py."
            )

        st.stop()


# =========================================================
# STEP 3+
# =========================================================

if st.session_state.evidence is not None:

    evidence = st.session_state.evidence


    # =====================================================
    # SYNC FORM WIDGETS
    # =====================================================

    if st.session_state.pending_form_sync:

        # This happens BEFORE widgets are created.
        sync_widgets_from_evidence()

        st.session_state.pending_form_sync = False


    # =====================================================
    # INITIALIZE WIDGET STATE
    # =====================================================

    for field in FIELD_DEFINITIONS:

        key = f"form_{field}"

        if key not in st.session_state:

            st.session_state[key] = (
                field_value(
                    evidence,
                    field,
                )
            )


    # =====================================================
    # STEP 3: REVIEW
    # =====================================================

    st.subheader(
        T("step3_data")
    )


    total = len(
        FIELD_DEFINITIONS
    )


    established = sum(
        1
        for f in FIELD_DEFINITIONS
        if (
            evidence.get(f) or {}
        ).get("status")
        == "established"
    )


    unverified = sum(
        1
        for f in FIELD_DEFINITIONS
        if (
            evidence.get(f) or {}
        ).get("status")
        == "unverified"
    )


    missing = sum(
        1
        for f in FIELD_DEFINITIONS
        if is_field_missing(
            evidence,
            f,
        )
    )


    a, b, c, d = st.columns(4)


    a.metric(
        T("established"),
        established,
    )

    b.metric(
        T("unverified"),
        unverified,
    )

    c.metric(
        T("missing"),
        missing,
    )

    d.metric(
        T("total"),
        total,
    )


    # =====================================================
    # REVIEW FORM
    # =====================================================

    for section, fields in SECTION_FIELDS.items():

        with st.expander(
            f"📂 {section}",
            expanded=True,
        ):

            cols = st.columns(2)

            for idx, field in enumerate(fields):

                with cols[idx % 2]:

                    data = (
                        evidence.get(field)
                        or {}
                    )

                    status = data.get(
                        "status",
                        "missing",
                    )

                    emoji = {
                        "established": "✅",
                        "unverified": "⚠️",
                        "missing": "❌",
                        "contradictory": "🔴",
                    }.get(
                        status,
                        "❓",
                    )

                    label = (
                        f"{emoji} "
                        f"{field_label(field)}"
                    )


                    if field in LONG_FIELDS:

                        st.text_area(
                            label,
                            key=f"form_{field}",
                            height=100,
                        )

                    else:

                        st.text_input(
                            label,
                            key=f"form_{field}",
                        )


                    if data.get("value") not in (
                        None,
                        "",
                    ):

                        st.caption(
                            f"{T('status')}: {status} | "
                            f"{T('confidence')}: "
                            f"{float(data.get('confidence', 0)):.2f}"
                        )


    # =====================================================
    # SAVE REVIEWED FORM
    # =====================================================

    if st.button(
        T("save_form"),
        use_container_width=True,
    ):

        updated = (
            build_updated_evidence_from_widgets(
                st.session_state.evidence
            )
        )

        st.session_state.evidence = updated

        # We need widgets to reflect the new evidence
        # on the next run.
        st.session_state.pending_form_sync = True

        st.rerun()


    # =====================================================
    # STEP 4: FOLLOW-UP LOOP
    # =====================================================

    st.subheader(
        T("step4_followup")
    )


    # -----------------------------------------------------
    # Calculate missing fields directly from evidence.
    #
    # This is the source of truth.
    # -----------------------------------------------------

    current_missing = missing_fields(
        st.session_state.evidence
    )


    if current_missing:

        st.warning(
            T("remaining").format(
                len(current_missing)
            )
        )


        # -------------------------------------------------
        # Get AI questions.
        #
        # normalize_followup_questions() guarantees that
        # every question has a real field.
        # -------------------------------------------------

        followups = get_safe_followups(
            st.session_state.evidence,
            LANGUAGES[
                st.session_state.selected_language
            ],
        )


        if not followups:

            # Absolute fallback.
            followups = [
                {
                    "field": current_missing[0],
                    "question": (
                        f"Please provide information for "
                        f"{field_label(current_missing[0])}."
                    ),
                }
            ]


        # -------------------------------------------------
        # ALWAYS ask ONE question.
        # -------------------------------------------------

        q = followups[0]


        field = q["field"]

        question = q["question"]


        # Safety check.
        if field not in current_missing:

            field = current_missing[0]

            question = (
                f"Please provide information for "
                f"{field_label(field)}."
            )


        current = (
            st.session_state.evidence.get(field)
            or {}
        )


        # -------------------------------------------------
        # Question header
        # -------------------------------------------------

        st.markdown(
            f"### {field_label(field)}"
        )


        st.info(
            f"📢 {question}"
        )


        # -------------------------------------------------
        # Voice playback of the question.
        #
        # The question is always shown as text above; this
        # adds an audio version too, generated once per
        # field/language and cached for reruns.
        # -------------------------------------------------

        question_lang = LANGUAGES[
            st.session_state.selected_language
        ]

        audio_cache_key = f"followup_qaudio_{field}_{question_lang}"

        if audio_cache_key not in st.session_state:

            st.session_state[audio_cache_key] = synthesize_speech(
                question,
                question_lang,
            )

        question_audio = st.session_state.get(audio_cache_key)

        if question_audio:

            st.audio(
                question_audio,
                format="audio/wav",
            )


        # -------------------------------------------------
        # Existing value
        # -------------------------------------------------

        if current.get("value") not in (
            None,
            "",
        ):

            st.caption(
                f"{T('current_answer')}: "
                f"{current.get('value')}"
            )


        # -------------------------------------------------
        # Answer mode
        # -------------------------------------------------

        mode = st.radio(
            T("answer_mode"),
            ["text", "voice"],
            format_func=lambda x:
                T("mode_text")
                if x == "text"
                else T("mode_voice"),
            key=f"followup_mode_{field}",
            horizontal=True,
        )


        answer = None


        # =================================================
        # TEXT ANSWER
        # =================================================

        if mode == "text":

            answer = st.text_area(
                T("answer_for").format(
                    field_label(field)
                ),
                key=f"followup_text_{field}",
                placeholder=T("type_answer"),
                height=120,
            )


        # =================================================
        # VOICE ANSWER
        # =================================================

        else:

            recorder = getattr(
                st,
                "audio_input",
                None,
            )

            audio_obj = None


            if recorder:

                audio_obj = recorder(
                    T("record_or_upload"),
                    key=f"followup_record_{field}",
                )


            if audio_obj is None:

                audio_obj = st.file_uploader(
                    T("record_or_upload"),
                    type=[
                        "mp3",
                        "wav",
                        "m4a",
                        "webm",
                        "ogg",
                        "flac",
                    ],
                    key=f"followup_audio_{field}",
                )


            if audio_obj:

                try:

                    answer = transcribe_audio(
                        audio_obj.getvalue(),
                        LANGUAGES[
                            st.session_state.selected_language
                        ],
                        getattr(
                            audio_obj,
                            "name",
                            "followup.wav",
                        ),
                    )

                    st.caption(
                        f"{T('heard')} {answer}"
                    )

                except Exception as exc:

                    st.error(
                        f"{T('transcription_error')} {exc}"
                    )


        # =================================================
        # SAVE FOLLOW-UP ANSWER
        # =================================================

        if st.button(
            T("save_followup"),
            type="primary",
            use_container_width=True,
            key=f"save_followup_{field}",
        ):

            if (
                answer is None
                or
                not str(answer).strip()
            ):

                st.warning(
                    T("followup_answer_error")
                )

            else:

                answer_text = str(
                    answer
                ).strip()


                # -----------------------------------------
                # Create a new evidence object.
                # -----------------------------------------

                new_evidence = dict(
                    st.session_state.evidence
                )


                # -----------------------------------------
                # Accurately extract the value(s) from the
                # applicant's free-form answer instead of
                # storing the raw text verbatim.
                #
                # One targeted call: it always covers the
                # asked field, and opportunistically picks
                # up any OTHER still-missing fields the
                # applicant mentioned in the same answer
                # (e.g. "8 employees, 6 of them women" while
                # answering the employee-count question also
                # fills the female-employee-count field).
                # -----------------------------------------

                try:

                    extracted = extract_followup_answer(
                        field,
                        question,
                        answer_text,
                        st.session_state.evidence,
                    )

                except Exception as exc:

                    st.warning(
                        f"{T('followup_error')} {exc}"
                    )

                    extracted = {
                        field: answer_text,
                    }


                if field not in extracted:

                    extracted[field] = answer_text


                source_label = (
                    "follow_up_voice"
                    if mode == "voice"
                    else "follow_up_text"
                )


                for (
                    extracted_field,
                    extracted_value,
                ) in extracted.items():

                    resolved = resolve_followup_value(
                        st.session_state.evidence.get(
                            extracted_field
                        ),
                        extracted_value,
                        source=source_label,
                    )


                    if not isinstance(
                        resolved,
                        dict,
                    ):

                        resolved = {
                            "value": extracted_value,
                            "status": "established",
                            "source": source_label,
                            "confidence": 0.95,
                        }


                    # ---------------------------------------
                    # Guarantee value is present.
                    # ---------------------------------------

                    resolved["value"] = (
                        resolved.get("value")
                        or extracted_value
                    )


                    # ---------------------------------------
                    # Guarantee established status for
                    # missing/unverified fields.
                    #
                    # This is important because
                    # missing_fields() treats "unverified"
                    # as incomplete. "contradictory" is left
                    # alone on purpose, so conflicting
                    # answers surface for review instead of
                    # silently overwriting earlier evidence.
                    # ---------------------------------------

                    if not resolved.get("status"):

                        resolved["status"] = "established"

                    elif resolved.get("status") in (
                        "missing",
                        "unverified",
                    ):

                        resolved["status"] = "established"


                    resolved["source"] = (
                        resolved.get("source")
                        or source_label
                    )


                    resolved["confidence"] = max(
                        float(
                            resolved.get(
                                "confidence",
                                0.0,
                            )
                        ),
                        0.95,
                    )


                    resolved["note"] = (
                        resolved.get("note")
                        or
                        f"Confirmed through {mode} follow-up answer."
                    )


                    new_evidence[extracted_field] = resolved


                st.session_state.evidence = (
                    new_evidence
                )

                # The review form already has form_* widget state.
                # Synchronize it from the updated evidence on the
                # next run so the newly saved value becomes visible.
                st.session_state.pending_form_sync = True


                # -----------------------------------------
                # Clear old answer widget so the next
                # question starts clean.
                # -----------------------------------------

                st.session_state.pop(
                    f"followup_text_{field}",
                    None,
                )

                st.session_state.pop(
                    f"followup_audio_{field}",
                    None,
                )


                # -----------------------------------------
                # IMPORTANT:
                #
                # Rerun.
                #
                # On the next run:
                #
                # missing_fields()
                #       ↓
                # get_safe_followups()
                #       ↓
                # next missing field
                #       ↓
                # next question
                #
                # This continues until ALL fields are
                # complete.
                # -----------------------------------------

                st.rerun()


    else:

        st.success(
            T("no_remaining")
        )


    # =====================================================
    # STEP 5: EXPORT / VALIDATE / SUBMIT
    # =====================================================

    st.subheader(
        T("step5_export")
    )


    # -----------------------------------------------------
    # DO NOT rely only on the LLM follow-up generator.
    #
    # The application's actual evidence is authoritative.
    # -----------------------------------------------------

    final_missing = missing_fields(
        st.session_state.evidence
    )


    complete = (
        len(final_missing) == 0
    )


    if complete:

        st.success(
            T("ready")
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        validation_issues = validate_evidence(
            st.session_state.evidence
        )


        if validation_issues:

            st.error(
                "Validation failed. "
                "Some fields are invalid."
            )

            st.write(
                "Validation issues:",
                validation_issues,
            )

            complete = False

        else:

            st.success(
                "✅ Validation passed. "
                "All required application fields are complete."
            )


    else:

        st.warning(
            T("not_ready")
        )

        with st.expander(
            "🔎 Remaining fields"
        ):

            st.write(
                [
                    field_label(field)
                    for field in final_missing
                ]
            )


    # =====================================================
    # JOTFORM PREFILL
    # =====================================================

    try:

        prefill_url = build_prefill_url(
            st.session_state.evidence,
            min_status="established",
        )

        st.link_button(
            T("jotform"),
            prefill_url,
            use_container_width=True,
        )

        st.caption(
            T("jotform_note")
        )

    except Exception as exc:

        st.warning(
            f"Could not build Jotform URL: {exc}"
        )


    # =====================================================
    # ACTUAL JOTFORM SUBMISSION
    # =====================================================

    if complete:

        if st.button(
            T("submit"),
            type="primary",
            use_container_width=True,
        ):

            try:

                with st.spinner(
                    T("submitting")
                ):

                    result = submit_application(
                        st.session_state.evidence
                    )


                st.session_state.submission_result = result


                st.success(
                    T("submitted")
                )


                if result is not None:

                    with st.expander(
                        "📄 Submission Response"
                    ):

                        st.json(
                            result
                        )


            except Exception as exc:

                st.error(
                    f"{T('submission_error')} {exc}"
                )


    # =====================================================
    # JSON
    # =====================================================

    with st.expander(
        T("view_json")
    ):

        st.json(
            st.session_state.evidence
        )


    # =====================================================
    # DOWNLOAD
    # =====================================================

    st.download_button(
        T("download"),

        json.dumps(
            st.session_state.evidence,
            indent=2,
            ensure_ascii=False,
        ),

        "application_data.json",

        "application/json",

        use_container_width=True,
    )


    # =====================================================
    # START OVER
    # =====================================================

    if st.button(
        T("start_over")
    ):

        # ---------------------------------------------
        # Delete form widgets.
        # ---------------------------------------------

        for field in FIELD_DEFINITIONS:

            st.session_state.pop(
                f"form_{field}",
                None,
            )

            st.session_state.pop(
                f"followup_mode_{field}",
                None,
            )

            st.session_state.pop(
                f"followup_text_{field}",
                None,
            )

            st.session_state.pop(
                f"followup_record_{field}",
                None,
            )

            st.session_state.pop(
                f"followup_audio_{field}",
                None,
            )

            st.session_state.pop(
                f"save_followup_{field}",
                None,
            )

            for lang_code in LANGUAGES.values():

                st.session_state.pop(
                    f"followup_qaudio_{field}_{lang_code}",
                    None,
                )


        # ---------------------------------------------
        # Reset application.
        # ---------------------------------------------

        st.session_state.evidence = None

        st.session_state.transcript = ""

        st.session_state.pending_form_sync = False

        st.session_state.submission_result = None

        st.session_state.processed = False


        st.rerun()


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    T("footer")
)