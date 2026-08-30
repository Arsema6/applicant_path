from typing import Any, Optional, Literal
from pydantic import BaseModel, Field


Status = Literal[
    "established",
    "unverified",
    "missing",
    "contradictory"
]


class EvidenceField(BaseModel):
    value: Optional[Any] = None
    status: Status = "missing"
    source: Optional[str] = None
    confidence: Optional[float] = None
    note: Optional[str] = None


class ProductService(BaseModel):
    product_service: EvidenceField
    market_served: EvidenceField
    distribution_channel: EvidenceField


class ManagementMember(BaseModel):
    name: EvidenceField
    position: EvidenceField
    gender: EvidenceField


class Equipment(BaseModel):
    description: EvidenceField
    quantity: EvidenceField
    estimated_total_price_etb: EvidenceField
    purpose: EvidenceField


class ConsultantRequest(BaseModel):
    problem_description: EvidenceField
    technical_expertise: EvidenceField


class NewJob(BaseModel):
    position: EvidenceField
    number_of_jobs: EvidenceField


class CompanyProfile(BaseModel):
    company_name: EvidenceField
    registration_number: EvidenceField
    address: EvidenceField
    mobile_number: EvidenceField
    email: EvidenceField
    business_organization: EvidenceField
    years_in_operation: EvidenceField
    business_type: EvidenceField
    women_ownership_percent: EvidenceField
    men_ownership_percent: EvidenceField


class GrowthIndicators(BaseModel):
    sales_2022: EvidenceField
    sales_2023: EvidenceField
    sales_2024: EvidenceField
    sales_2025: EvidenceField
    sales_2026: EvidenceField

    employees_2022: EvidenceField
    employees_2023: EvidenceField
    employees_2024: EvidenceField
    employees_2025: EvidenceField
    employees_2026: EvidenceField

    female_employees_2022: EvidenceField
    female_employees_2023: EvidenceField
    female_employees_2024: EvidenceField
    female_employees_2025: EvidenceField
    female_employees_2026: EvidenceField

    youth_employees_2022: EvidenceField
    youth_employees_2023: EvidenceField
    youth_employees_2024: EvidenceField
    youth_employees_2025: EvidenceField
    youth_employees_2026: EvidenceField


class Application(BaseModel):

    # 1.1
    company_profile: CompanyProfile

    # 1.2
    company_overview: EvidenceField
    growth_indicators: GrowthIndicators

    # 1.3
    motivation_to_apply: EvidenceField
    personal_involvement: EvidenceField

    # 1.4
    short_term_goals: EvidenceField
    long_term_goals: EvidenceField

    # 1.5
    market_overview: EvidenceField
    target_customers: EvidenceField
    geographies_served: EvidenceField
    competitive_advantage: EvidenceField
    market_challenges: EvidenceField

    # 1.6
    products_services: list[ProductService] = Field(
        default_factory=list
    )
    product_service_uniqueness: EvidenceField

    # 1.7
    local_raw_material_percentage: EvidenceField

    # 1.8
    management_team: list[ManagementMember] = Field(
        default_factory=list
    )
    organogram: EvidenceField

    # 2.1
    problems_to_address: EvidenceField

    # 2.2
    equipment: list[Equipment] = Field(
        default_factory=list
    )

    # 2.3
    consultants: list[ConsultantRequest] = Field(
        default_factory=list
    )

    # 2.4
    expected_results: EvidenceField
    priority_areas: list[EvidenceField] = Field(
        default_factory=list
    )

    # 2.5
    job_creation: EvidenceField
    new_jobs: list[NewJob] = Field(
        default_factory=list
    )

    # 2.6
    social_environmental_impact: EvidenceField

    # 2.7
    occupational_safety_health: EvidenceField