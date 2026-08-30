import json
import streamlit as st
from dotenv import load_dotenv

from agents.groq_agent import (
    transcribe_audio,
    extract_evidence,
    get_followup_questions,
    FIELD_DEFINITIONS,
)
from agents.form_integration import (
    build_prefill_url,
    submit_application,
    validate_evidence,
    resolve_followup_value,
)

load_dotenv()

LANGUAGES = {
    "English": "en",
    "Amharic": "am",
    "Afaan Oromo": "om",
}

UI_TEXT = {
    "en": {
        "title": "🌱 SME Funding Application",
        "subtitle": "Turn your story into a funding application",
        "caption": "Impact Protocol Hackathon | Powered by Groq",
        "instructions_title": "📋 Instructions",
        "instructions": "1. Upload your voice note\n2. Upload your business licence\n3. Upload a workshop photo\n4. Process the application\n5. Review the populated form\n6. Answer follow-up questions until every field is complete",
        "data_note": "Audio and images are sent to Groq for processing. This app does not persist application data.",
        "api_ready": "✅ Groq API Ready",
        "step1": "📤 Step 1: Applicant Evidence",
        "voice_note": "🎙 Voice Note",
        "mock_transcript": "Use mock transcript for testing",
        "mock_placeholder": "Mock Transcript",
        "mock_default": "My name is Almaz Wolde. I run a spice mill in Bekoji Tera. My business is called Almaz Spice Mill. Registration number is 12345/2020. I have been operating for 5 years. I have 8 employees, 6 are women. Annual sales are 1.5 million birr. We need equipment for grinding and packaging.",
        "upload_voice": "Upload a voice note (Amharic, Afaan Oromo, or English)",
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
        "jotform_note": "Jotform URL prefilling depends on the real field parameter names in the target form. The in-app form below is the authoritative completed application data.",
        "ready": "🎯 Application complete and ready for review/submission!",
        "not_ready": "Complete all remaining fields before final submission.",
        "submit": "🚀 Submit Application to Jotform",
        "submitting": "Submitting application to Jotform...",
        "submitted": "✅ Application submitted successfully!",
        "submission_error": "❌ Application submission failed:",
        "start_over": "🗑️ Start Over",
        "footer": "🌱 Impact Protocol Hackathon | Applicant Path Challenge",
    },

    "am": {
        "title": "🌱 የአነስተኛ ንግድ የገንዘብ ድጋፍ ማመልከቻ",
        "subtitle": "ታሪክዎን ወደ የገንዘብ ድጋፍ ማመልከቻ ይቀይሩ",
        "caption": "Impact Protocol Hackathon | በ Groq የተጎላበተ",
        "instructions_title": "📋 መመሪያዎች",
        "instructions": "1. የድምጽ መልዕክት ይስቀሉ\n2. የንግድ ፈቃድ ይስቀሉ\n3. የስራ ቦታ ፎቶ ይስቀሉ\n4. ማመልከቻውን ያስኬዱ\n5. የተሞላውን ፎርም ይገምግሙ\n6. ሁሉም መስኮች እስኪሞሉ ድረስ ተከታይ ጥያቄዎችን ይመልሱ",
        "data_note": "ድምጽ እና ምስሎች ለማስኬድ ወደ Groq ይላካሉ። መተግበሪያው መረጃውን በቋሚነት አያስቀምጥም።",
        "api_ready": "✅ Groq ዝግጁ ነው",
        "step1": "📤 ደረጃ 1: የአመልካች ማስረጃ",
        "voice_note": "🎙 የድምጽ መልዕክት",
        "mock_transcript": "ለመሞከር የሙክ ጽሑፍ ይጠቀሙ",
        "mock_placeholder": "የሙክ ጽሑፍ",
        "mock_default": "ስሜ አልማዝ ወልደ ነው። በበቆጂ ቴራ የቅመማ ቅመም ወፍጮ እሰራለሁ። የንግድ ስሜ አልማዝ ቅመማ ቅመም ወፍጮ ነው። የምዝገባ ቁጥሬ 12345/2020 ነው። ለ5 ዓመታት ስሰራ ቆይቻለሁ። 8 ሰራተኞች አሉኝ፣ ከነሱ 6ቱ ሴቶች ናቸው። ዓመታዊ ሽያጬ 1.5 ሚሊዮን ብር ነው። ለመፍጨት እና ለማሸግ መሳሪያ ያስፈልጉኛል።",
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
        "jotform_note": "የJotform ቅድመ-መሙያ የሚሰራው የእውነተኛው ፎርም የመስክ መለያዎች ትክክል ከሆኑ ብቻ ነው።",
        "ready": "🎯 ማመልከቻው ተሟልቶ ለግምገማ/ማስገባት ዝግጁ ነው!",
        "not_ready": "ለመጨረሻ ማስገባት የቀሩትን መስኮች ይሙሉ።",
        "submit": "🚀 ማመልከቻውን ወደ Jotform ያስገቡ",
        "submitting": "ማመልከቻውን ወደ Jotform በማስገባት ላይ...",
        "submitted": "✅ ማመልከቻው በተሳካ ሁኔታ ገብቷል!",
        "submission_error": "❌ ማመልከቻውን ማስገባት አልተሳካም:",
        "start_over": "🗑️ እንደገና ጀምር",
        "footer": "🌱 Impact Protocol Hackathon | የአመልካች መንገድ",
    },
}

# Oromo falls back to English for UI labels.
UI_TEXT["om"] = UI_TEXT["en"]


SECTION_FIELDS = {
    "Company Profile": [
        "company_name", "registration_number", "address", "mobile_number",
        "email", "business_organization", "years_in_operation", "business_type",
    ],
    "Ownership": [
        "women_ownership_percent",
        "men_ownership_percent"
    ],
    "Company Overview & Growth": [
        "company_overview", "sales_current", "sales_2022", "sales_2023",
        "sales_2024", "sales_2025", "sales_2026",
    ],
    "Employees": [
        "employees_current", "employees_2022", "employees_2023",
        "employees_2024", "employees_2025", "employees_2026",
        "female_employees_current", "female_employees_2022",
        "female_employees_2023", "female_employees_2024",
        "female_employees_2025", "female_employees_2026",
        "youth_employees_current", "youth_employees_2022",
        "youth_employees_2023", "youth_employees_2024",
        "youth_employees_2025", "youth_employees_2026",
    ],
    "Business Goals & Market": [
        "motivation_to_apply", "personal_involvement",
        "short_term_goals", "long_term_goals",
        "market_overview", "target_customers",
        "geographies_served", "competitive_advantage",
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
    "company_overview", "motivation_to_apply",
    "personal_involvement", "short_term_goals",
    "long_term_goals", "market_overview",
    "target_customers", "geographies_served",
    "competitive_advantage", "market_challenges",
    "products_services", "product_service_uniqueness",
    "management_team", "organogram",
    "problems_to_address", "requested_equipment",
    "requested_consultants", "expected_results",
    "priority_areas", "job_creation_explanation",
    "new_job_positions", "social_environmental_impact",
    "occupational_safety_health",
}


def T(key):
    code = LANGUAGES[st.session_state.selected_language]
    return UI_TEXT.get(code, UI_TEXT["en"]).get(
        key,
        UI_TEXT["en"].get(key, key)
    )


def field_value(evidence, field):
    value = (evidence.get(field) or {}).get("value")
    return "" if value is None else str(value)


def missing_fields(evidence):
    return [
        field for field in FIELD_DEFINITIONS
        if (evidence.get(field) or {}).get("value") in (None, "")
        or (evidence.get(field) or {}).get("status")
        in {"missing", "unverified"}
    ]


def sync_widgets_from_evidence():
    evidence = st.session_state.evidence or {}

    for field in FIELD_DEFINITIONS:
        st.session_state[f"form_{field}"] = field_value(
            evidence,
            field
        )


def build_updated_evidence_from_widgets(evidence):
    updated = dict(evidence)

    for field in FIELD_DEFINITIONS:
        value = str(
            st.session_state.get(f"form_{field}", "")
        ).strip()

        old = dict(updated.get(field) or {})

        if value:
            updated[field] = {
                "value": value,
                "status": "established",
                "source": old.get("source") or "applicant_review",
                "confidence": max(
                    float(old.get("confidence", 0.0)),
                    0.95
                ),
                "note": old.get("note")
                or "Confirmed or edited in the application review form.",
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


st.set_page_config(
    page_title="SME Funding Application",
    page_icon="🌱",
    layout="wide"
)


for key, default in {
    "selected_language": "English",
    "evidence": None,
    "transcript": "",
    "pending_form_sync": False,
    "submission_result": None,
}.items():

    if key not in st.session_state:
        st.session_state[key] = default


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


st.title(T("title"))
st.subheader(T("subtitle"))
st.caption(T("caption"))


with st.sidebar:
    st.header(T("instructions_title"))
    st.markdown(T("instructions"))
    st.divider()
    st.caption(T("data_note"))
    st.success(T("api_ready"))


# =========================================================
# Step 1: inputs
# =========================================================

st.header(T("step1"))

col1, col2 = st.columns([2, 1])


with col1:

    st.subheader(T("voice_note"))

    use_mock = st.checkbox(
        T("mock_transcript"),
        key="use_mock"
    )

    if use_mock:

        mock_text = st.text_area(
            T("mock_placeholder"),
            value=T("mock_default"),
            height=140
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
                "flac"
            ],
            key="main_voice",
        )


with col2:

    st.subheader(T("documents"))

    license_photo = st.file_uploader(
        T("license"),
        type=["jpg", "jpeg", "png"],
        key="license_photo"
    )

    workshop_photo = st.file_uploader(
        T("workshop"),
        type=["jpg", "jpeg", "png", "webp"],
        key="workshop_photo"
    )


if st.button(
    T("process"),
    type="primary",
    use_container_width=True
):

    if not use_mock and not voice_file:
        st.error(T("error_voice"))
        st.stop()

    if use_mock and not mock_text.strip():
        st.error(T("error_mock"))
        st.stop()


    st.subheader(T("step1_transcript"))

    try:

        with st.spinner(T("transcribing")):

            if use_mock:

                transcript = mock_text.strip()
                st.info(T("using_mock"))

            else:

                transcript = transcribe_audio(
                    voice_file.getvalue(),
                    LANGUAGES[
                        st.session_state.selected_language
                    ],
                    voice_file.name,
                )


        st.session_state.transcript = transcript

        st.success(T("transcription_complete"))

        st.text_area(
            T("transcript_label"),
            transcript,
            height=180,
            key="transcript_display"
        )


    except Exception as exc:

        st.error(
            f"{T('transcription_error')} {exc}"
        )

        st.stop()


    st.subheader(T("step2_extract"))


    try:

        with st.spinner(T("extracting")):

            license_data = None

            if license_photo:

                license_data = {
                    "filename": license_photo.name,
                    "bytes": license_photo.getvalue()
                }


            workshop_data = None

            if workshop_photo:

                workshop_data = {
                    "filename": workshop_photo.name,
                    "bytes": workshop_photo.getvalue()
                }


            st.session_state.evidence = extract_evidence(
                st.session_state.transcript,
                licence_data=license_data,
                workshop_data=workshop_data,
            )

            st.session_state.pending_form_sync = True


        st.success(T("extraction_complete"))


    except Exception as exc:

        st.error(
            f"{T('extraction_error')} {exc}"
        )

        st.stop()


# =========================================================
# Step 3+ after extraction
# =========================================================

if st.session_state.evidence is not None:

    evidence = st.session_state.evidence


    # MUST happen before creating any form_* widget in this run.
    if st.session_state.pending_form_sync:

        sync_widgets_from_evidence()

        st.session_state.pending_form_sync = False


    # First-run initialization for widgets.
    for field in FIELD_DEFINITIONS:

        key = f"form_{field}"

        if key not in st.session_state:

            st.session_state[key] = field_value(
                evidence,
                field
            )


    # =====================================================
    # Step 3: Review
    # =====================================================

    st.subheader(T("step3_data"))

    total = len(FIELD_DEFINITIONS)

    established = sum(
        1
        for f in FIELD_DEFINITIONS
        if (evidence.get(f) or {}).get("status")
        == "established"
    )

    unverified = sum(
        1
        for f in FIELD_DEFINITIONS
        if (evidence.get(f) or {}).get("status")
        == "unverified"
    )

    missing = total - established - unverified


    a, b, c, d = st.columns(4)

    a.metric(
        T("established"),
        established
    )

    b.metric(
        T("unverified"),
        unverified
    )

    c.metric(
        T("missing"),
        missing
    )

    d.metric(
        T("total"),
        total
    )


    # Actual review form.
    for section, fields in SECTION_FIELDS.items():

        with st.expander(
            f"📂 {section}",
            expanded=True
        ):

            cols = st.columns(2)

            for idx, field in enumerate(fields):

                with cols[idx % 2]:

                    data = evidence.get(field) or {}

                    status = data.get(
                        "status",
                        "missing"
                    )

                    emoji = {
                        "established": "✅",
                        "unverified": "⚠️",
                        "missing": "❌",
                        "contradictory": "🔴"
                    }.get(
                        status,
                        "❓"
                    )

                    label = (
                        f"{emoji} "
                        f"{field.replace('_', ' ').title()}"
                    )


                    if field in LONG_FIELDS:

                        st.text_area(
                            label,
                            key=f"form_{field}",
                            height=90
                        )

                    else:

                        st.text_input(
                            label,
                            key=f"form_{field}"
                        )


                    if data.get("value") not in (
                        None,
                        ""
                    ):

                        st.caption(
                            f"{T('status')}: {status} | "
                            f"{T('confidence')}: "
                            f"{float(data.get('confidence', 0)):.2f}"
                        )


    if st.button(
        T("save_form"),
        use_container_width=True
    ):

        st.session_state.evidence = (
            build_updated_evidence_from_widgets(
                evidence
            )
        )

        st.session_state.pending_form_sync = True

        st.rerun()


    # =====================================================
    # Step 4: FOLLOW-UP LOOP
    # =====================================================

    st.subheader(T("step4_followup"))


    # IMPORTANT:
    # This function is called again on EVERY Streamlit run.
    #
    # After an answer is saved we call st.rerun().
    # Therefore the application checks the missing fields again.
    followups = get_followup_questions(
        st.session_state.evidence,
        LANGUAGES[
            st.session_state.selected_language
        ]
    )


    if followups:

        st.warning(
            T("remaining").format(
                len(followups)
            )
        )


        # -------------------------------------------------
        # Ask ONLY the next missing question.
        # -------------------------------------------------

        q = followups[0]

        field = q.get("field") or q.get("name")

        current = (
            st.session_state.evidence.get(field)
            or {}
        )


        st.markdown(
            f"### {field.replace('_', ' ').title()}"
        )

        st.info(
            f"📢 {q['question']}"
        )


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


        # -------------------------------------------------
        # Text answer
        # -------------------------------------------------

        if mode == "text":

            answer = st.text_area(
                T("answer_for").format(field),
                key=f"followup_text_{field}",
                placeholder=T("type_answer"),
                height=100,
            )


        # -------------------------------------------------
        # Voice answer
        # -------------------------------------------------

        else:

            recorder = getattr(
                st,
                "audio_input",
                None
            )

            audio_obj = None


            if recorder:

                audio_obj = recorder(
                    T("record_or_upload"),
                    key=f"followup_record_{field}"
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
                        "flac"
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
                            "followup.wav"
                        ),
                    )

                    st.caption(
                        f"{T('heard')} {answer}"
                    )


                except Exception as exc:

                    st.error(
                        f"{T('transcription_error')} {exc}"
                    )


        # -------------------------------------------------
        # Save ONE answer
        # -------------------------------------------------

        if st.button(
            T("save_followup"),
            type="primary",
            use_container_width=True
        ):

            if not answer or not str(answer).strip():

                st.warning(
                    "Enter an answer before continuing."
                )

            else:

                answer_text = str(
                    answer
                ).strip()


                # Update only the field that was asked.
                new_evidence = dict(
                    st.session_state.evidence
                )


                new_evidence[field] = resolve_followup_value(
                    st.session_state.evidence.get(field),
                    answer_text,
                    source="follow_up",
                )
                new_evidence[field]["note"] = (
                    new_evidence[field].get("note")
                    or f"Confirmed through {mode} follow-up answer."
                )


                st.session_state.evidence = (
                    new_evidence
                )


                # -------------------------------------------------
                # THIS IS THE LOOP:
                #
                # Save answer
                #      ↓
                # Rerun application
                #      ↓
                # get_followup_questions()
                #      ↓
                # Check missing fields again
                #      ↓
                # Ask next question
                # -------------------------------------------------

                st.rerun()


    else:

        st.success(
            T("no_remaining")
        )


    # =====================================================
    # Step 5: Export / Validate / Submit
    # =====================================================

    st.subheader(T("step5_export"))


    # Re-check one final time before submission.
    final_followups = get_followup_questions(
        st.session_state.evidence,
        LANGUAGES[
            st.session_state.selected_language
        ]
    )


    complete = len(final_followups) == 0


    if complete:

        st.success(T("ready"))


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        final_missing = missing_fields(
            st.session_state.evidence
        )

        validation_issues = validate_evidence(
            st.session_state.evidence
        )

        if final_missing or validation_issues:

            st.error(
                "Validation failed. "
                "Some fields are still incomplete or invalid."
            )

            if final_missing:
                st.write("Missing fields:", final_missing)

            if validation_issues:
                st.write("Validation issues:", validation_issues)

            complete = False


        else:

            st.success(
                "✅ Validation passed. "
                "All required application fields are complete."
            )


    else:

        st.warning(T("not_ready"))


    # -----------------------------------------------------
    # Prefilled Jotform URL
    # -----------------------------------------------------

    prefill_url = build_prefill_url(
        st.session_state.evidence,
        min_status="established"
    )

    st.link_button(
        T("jotform"),
        prefill_url,
        use_container_width=True
    )

    st.caption(
        T("jotform_note")
    )


    # -----------------------------------------------------
    # ACTUAL JOTFORM SUBMISSION
    # -----------------------------------------------------

    if complete:

        if st.button(
            T("submit"),
            type="primary",
            use_container_width=True
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

                        st.json(result)


            except Exception as exc:

                st.error(
                    f"{T('submission_error')} {exc}"
                )


    # -----------------------------------------------------
    # JSON
    # -----------------------------------------------------

    with st.expander(T("view_json")):

        st.json(
            st.session_state.evidence
        )


    # -----------------------------------------------------
    # Download
    # -----------------------------------------------------

    st.download_button(
        T("download"),
        json.dumps(
            st.session_state.evidence,
            indent=2,
            ensure_ascii=False
        ),
        "application_data.json",
        "application/json",
        use_container_width=True,
    )


    # -----------------------------------------------------
    # Start over
    # -----------------------------------------------------

    if st.button(T("start_over")):

        for field in FIELD_DEFINITIONS:

            st.session_state.pop(
                f"form_{field}",
                None
            )

            st.session_state.pop(
                f"followup_mode_{field}",
                None
            )

            st.session_state.pop(
                f"followup_text_{field}",
                None
            )

            st.session_state.pop(
                f"followup_record_{field}",
                None
            )

            st.session_state.pop(
                f"followup_audio_{field}",
                None
            )


        st.session_state.evidence = None
        st.session_state.transcript = ""
        st.session_state.pending_form_sync = False
        st.session_state.submission_result = None

        st.rerun()


st.divider()

st.caption(
    T("footer")
)