import os
import json
import re
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, create_model

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_EXTRACTION_MODEL", "gemini-3.6-flash")

# =========================================================
# Complete Field Definitions - Hackathon Requirements
# =========================================================

FIELD_DEFINITIONS = {
    # Section 1.1 - Company Profile
    "company_name": "Registered or trading business name",
    "registration_number": "Business licence or registration number (CRITICAL)",
    "address": "Business address (town, district, etc.)",
    "mobile_number": "Applicant's mobile phone number",
    "email": "Applicant's email address (if available)",
    "business_organization": "Legal form: sole proprietor, PLC, cooperative, etc.",
    "years_in_operation": "Number of years business has operated",
    "business_type": "Business sector or industry (e.g., manufacturing, services, trade)",
    "women_ownership_percent": "Percentage owned by women",
    "men_ownership_percent": "Percentage owned by men",
    
    # Section 1.2 - Company Overview
    "company_overview": "What the business does (summary)",
    "sales_current": "Most recent sales/revenue figure",
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
    "youth_employees_current": "Current employees aged 15-29",
    "youth_employees_2022": "Youth employees in 2022",
    "youth_employees_2023": "Youth employees in 2023",
    "youth_employees_2024": "Youth employees in 2024",
    "youth_employees_2025": "Youth employees in 2025",
    "youth_employees_2026": "Youth employees in 2026",
    
    # Section 1.3
    "motivation_to_apply": "Why applicant is applying for funding",
    "personal_involvement": "Applicant's role in the business",
    
    # Section 1.4
    "short_term_goals": "Short-term business goals (0-12 months)",
    "long_term_goals": "Long-term business goals (1-5 years)",
    
    # Section 1.5
    "market_overview": "Description of the market",
    "target_customers": "Who the business sells to",
    "geographies_served": "Where the business sells/operates",
    "competitive_advantage": "What makes the business different",
    "market_challenges": "Market challenges described",
    
    # Section 1.6
    "products_services": "Products or services provided",
    "product_service_uniqueness": "What is unique about the offering",
    
    # Section 1.7
    "local_raw_material_percentage": "Percentage of raw materials sourced locally",
    
    # Section 1.8
    "management_team": "People managing the business",
    "organogram": "Reporting structure description",
    
    # Section 2.1 - 2.7
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

# =========================================================
# Extraction Model
# =========================================================

class Status(str):
    established = "established"
    unverified = "unverified" 
    missing = "missing"
    contradictory = "contradictory"

class Source(str):
    voice_note = "voice_note"
    license_photo = "license_photo"
    workshop_photo = "workshop_photo"

class Evidence(BaseModel):
    value: Optional[str] = None
    status: str = "missing"
    source: Optional[str] = None
    confidence: float = 0.0
    note: str = "Not mentioned in available evidence"

# Create the full extraction model
ExtractionResult = create_model(
    "ExtractionResult",
    **{
        name: (Evidence, Field(description=desc))
        for name, desc in FIELD_DEFINITIONS.items()
    },
)

# =========================================================
# System Instruction
# =========================================================

SYSTEM_INSTRUCTION = """
You are an SME funding intake assistant for Ethiopian businesses.

CRITICAL RULES:
1. Extract ONLY information explicitly stated
2. NEVER invent, estimate, or calculate values
3. Preserve original language for all values
4. For numbers without a year → use "_current" field
5. For "about", "around", "approximately" → status="unverified"
6. If multiple sources conflict → status="contradictory"
7. Use source="voice_note" for speech, "license_photo" for licence, "workshop_photo" for photos

ALLOWED STATUS VALUES: "established", "unverified", "missing", "contradictory"
ALLOWED SOURCE VALUES: "voice_note", "license_photo", "workshop_photo"

Return ONLY JSON matching the schema.
"""

# =========================================================
# Extraction Function
# =========================================================

def extract_evidence(
    transcript: str,
    licence_data: dict = None,
    workshop_data: dict = None,
    max_retries: int = 1,
) -> dict:
    """
    Extract evidence with fallback for rate limits
    """
    
    # Build prompt
    blocks = [
        "Extract evidence from the applicant information below.",
        "",
        "VOICE NOTE TRANSCRIPT:",
        transcript or "(No transcript provided)",
        "",
    ]
    
    if licence_data:
        blocks.append("LICENCE PHOTO EVIDENCE:")
        blocks.append(json.dumps(licence_data, ensure_ascii=False))
        blocks.append("")
    
    if workshop_data:
        blocks.append("WORKSHOP PHOTO EVIDENCE:")
        blocks.append(json.dumps(workshop_data, ensure_ascii=False))
        blocks.append("")
    
    blocks.append("AVAILABLE FIELDS TO EXTRACT:")
    blocks.append("\n".join(f"- {k}: {v}" for k, v in FIELD_DEFINITIONS.items()))
    blocks.append("")
    blocks.append(
        'Return JSON with fields that have evidence. Use status: "established", "unverified", or "missing".'
    )
    
    prompt = "\n".join(blocks)
    
    # Try extraction with retry
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    temperature=0,
                ),
            )
            
            # Parse and validate
            data = json.loads(response.text)
            
            # Ensure all fields exist
            for field in FIELD_DEFINITIONS:
                if field not in data:
                    data[field] = {
                        "value": None,
                        "status": "missing",
                        "source": None,
                        "confidence": 0.0,
                        "note": "Not mentioned in available evidence",
                    }
            
            return data
            
        except Exception as e:
            if "429" in str(e) and attempt < max_retries:
                import time
                wait_time = 10 * (attempt + 1)
                print(f"Rate limit hit, waiting {wait_time}s...")
                time.sleep(wait_time)
                continue
            raise
    
    raise Exception("Max retries exceeded")