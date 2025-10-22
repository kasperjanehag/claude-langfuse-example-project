"""Pydantic models for compliance obligations and controls - Simplified."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Obligation(BaseModel):
    """
    Model representing a legal/regulatory obligation.

    Parsed from obligations register (e.g., from GDPR, DORA, NIS2, etc.).
    Simplified to include only essential fields.
    """

    obligation_id: str = Field(..., description="Unique identifier for the obligation")
    obligation: str = Field(..., description="Atomic description of what must be done")
    framework_source: str = Field(..., description="Source framework (e.g., GDPR (EU) 2016/679)")
    clause_source: str = Field(..., description="Specific clause/article reference")
    domain: Optional[str] = Field(None, description="Domain classification")
    impact: Optional[str] = Field(None, description="Impact level (Critical/Elevated/etc.)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "obligation_id": "OBL-GDPR-2",
                "obligation": "Ensure personal data processing is conducted in a transparent manner",
                "framework_source": "GDPR (EU) 2016/679",
                "clause_source": "5.1.a",
                "domain": "Data protection",
                "impact": "Critical",
            }
        }


class ControlObjective(BaseModel):
    """
    Model representing a context-less control objective.

    Control objectives express the operational intent behind obligations
    without specifying how to achieve them. Multiple obligations may
    map to the same objective.
    """

    objective_id: str = Field(..., description="Unique identifier for this objective")
    objective_name: str = Field(..., description="Short descriptive name")
    description: str = Field(
        ..., description="What needs to be achieved (operational intent)"
    )
    domain: str = Field(..., description="Domain classification")
    intent: Optional[str] = Field(
        None, description="Why this objective matters from control perspective"
    )
    linked_obligation_ids: List[str] = Field(
        ..., description="Obligation IDs that this objective satisfies"
    )
    rationale: Optional[str] = Field(
        None, description="Rationale for this objective (especially for LLM-generated ones)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "objective_id": "OBJ-TRANS-1",
                "objective_name": "Transparency in data processing",
                "description": "Ensure all personal data processing activities are clearly communicated to data subjects",
                "domain": "Data protection",
                "linked_obligation_ids": ["OBL-GDPR-2"],
            }
        }


class ControlVariant(BaseModel):
    """
    Model representing a control implementation with multiple context variants.

    This model combines:
    - Base control description
    - Context-specific variants (startup, SME, enterprise)
    - Jurisdiction-specific requirements

    One ControlVariant contains ALL size variants for a single control.
    """

    variant_id: str = Field(..., description="Unique identifier for this control variant")
    objective_id: str = Field(..., description="Control objective this implements")
    variant_name: str = Field(..., description="Short descriptive name")
    base_description: str = Field(
        ..., description="Core control description (context-independent)"
    )
    domain: str = Field(..., description="Domain classification (e.g., 'Data protection')")

    # Context-specific variants
    variants: List[Dict[str, Any]] = Field(
        ...,
        description="List of variants for different contexts. Each dict contains: "
        "variant_type (str), applies_if (str), description_additions (str), "
        "evidence_requirements (List[str]), review_interval (str)",
    )

    # Jurisdiction-specific requirements
    jurisdiction_requirements: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping of jurisdiction code to list of additional requirements. "
        "Example: {'SE': ['Plain Swedish language', 'Comply with IMY guidance'], 'FR': [...]}",
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "variant_id": "CV-TRANS-1",
                "objective_id": "OBJ-TRANS-1",
                "variant_name": "Privacy notice management system",
                "base_description": "Establish and maintain a systematic approach to privacy notices",
                "domain": "Data protection",
                "variants": [
                    {
                        "variant_type": "startup",
                        "applies_if": "employee_count < 50",
                        "description_additions": "Use standardized templates in shared documents",
                        "evidence_requirements": [
                            "Privacy notice template documents",
                            "Review and approval records",
                        ],
                        "review_interval": "12 months",
                    },
                    {
                        "variant_type": "sme",
                        "applies_if": "employee_count >= 50 and employee_count < 1000",
                        "description_additions": "Implement notice registry in document management system",
                        "evidence_requirements": [
                            "DMS export showing notice registry",
                            "Approval workflow logs",
                        ],
                        "review_interval": "6 months",
                    },
                ],
                "jurisdiction_requirements": {
                    "SE": [
                        "Notices must be written in plain Swedish language",
                        "Comply with IMY guidance on transparency",
                    ]
                },
            }
        }


class Control(BaseModel):
    """
    Model representing a generated control (output).

    Controls are company-specific implementations generated by combining:
    - ControlObjective (what to achieve)
    - ControlVariant (how to implement)
    - CompanyContext (company-specific parameters)
    """

    control_id: str = Field(..., description="Unique identifier for the control")
    control_name: str = Field(..., description="Short descriptive name")
    control_description: str = Field(
        ..., description="Detailed, actionable description of what to do"
    )
    linked_obligation_ids: str = Field(
        ..., description="Semicolon-separated obligation IDs this control addresses"
    )
    domain: Optional[str] = Field(None, description="Domain classification")
    expected_evidence: Optional[str] = Field(
        None, description="What evidence/artifacts prove this control exists"
    )
    review_interval: Optional[str] = Field(
        None, description="How often to review this control (e.g., '6 months')"
    )
    impact: Optional[str] = Field(None, description="Impact level if this control fails")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "control_id": "CV-TRANS-1-SME",
                "control_name": "Privacy notice management system",
                "control_description": "Establish and maintain privacy notices...",
                "linked_obligation_ids": "OBL-GDPR-2",
                "domain": "Data protection",
                "expected_evidence": "DMS export, approval logs, readability tests",
                "review_interval": "6 months",
                "impact": "Critical",
            }
        }


class CompanyContext(BaseModel):
    """
    Model representing company-specific context for control generation.

    Simplified to include only essential fields for variant selection.
    """

    company_name: str = Field(..., description="Company name")
    employee_count: Optional[int] = Field(None, description="Number of employees")
    industry: str = Field(..., description="Primary industry (e.g., Fintech, SaaS)")
    jurisdictions: List[str] = Field(
        default_factory=list,
        description="List of jurisdictions company operates in (e.g., ['SE', 'EU'])",
    )

    # Optional context fields
    risk_appetite: Optional[str] = Field(
        None, description="Risk tolerance level (Low/Medium/High)"
    )
    compliance_maturity: Optional[str] = Field(
        None, description="Compliance maturity level (Initial/Developing/Mature)"
    )

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "company_name": "Acme Corporation",
                "employee_count": 250,
                "industry": "SaaS",
                "jurisdictions": ["SE", "EU"],
                "risk_appetite": "Low",
                "compliance_maturity": "Developing",
            }
        }
