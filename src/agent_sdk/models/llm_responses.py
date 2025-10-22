"""Pydantic models for LLM structured output responses."""

from typing import Dict, List

from pydantic import BaseModel, Field


# ============================================================================
# Stage 1: Obligation → Objectives Mapping Response Models
# ============================================================================


class NewObjectiveData(BaseModel):
    """Data for a newly generated control objective."""

    objective_name: str = Field(description="Clear, reusable name for the objective")
    description: str = Field(description="What systematic capability this establishes")
    domain: str = Field(description="Security/compliance domain")
    intent: str = Field(description="Why this objective matters from control perspective")
    rationale: str = Field(description="Why this is needed as a separate objective")


class ObligationMappingResponse(BaseModel):
    """Structured response from LLM for obligation → objectives mapping."""

    analysis: str = Field(description="Brief analysis of what this obligation requires (2-3 sentences)")
    matched_objective_ids: List[str] = Field(
        default_factory=list,
        description="Array of objective IDs that match (empty if none)"
    )
    new_objectives: List[NewObjectiveData] = Field(
        default_factory=list,
        description="Array of new objectives to create (empty if none needed)"
    )
    reasoning: str = Field(description="Explanation of matching and generation decisions (2-3 sentences)")


# ============================================================================
# Stage 2: Objective + Context → Variants Mapping Response Models
# ============================================================================


class SizeVariantData(BaseModel):
    """Data for a single size-specific variant (startup/SME/enterprise)."""

    variant_type: str = Field(description="Size category: startup, sme, or enterprise")
    applies_if: str = Field(description="Condition expression (e.g., 'employee_count < 50')")
    description_additions: str = Field(description="Size-specific implementation details")
    evidence_requirements: List[str] = Field(description="Evidence needed for this size variant")
    review_interval: str = Field(description="How often to review (e.g., '6 months')")


class NewVariantData(BaseModel):
    """Data for a newly generated control variant."""

    variant_name: str = Field(description="Descriptive implementation name")
    base_description: str = Field(description="Core control description (applies to all sizes)")
    variants: List[SizeVariantData] = Field(description="Size-specific variants (startup/SME/enterprise)")
    jurisdiction_requirements: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Jurisdiction-specific requirements by country/region code"
    )


class VariantMappingResponse(BaseModel):
    """Structured response from LLM for objective + context → variants mapping."""

    analysis: str = Field(description="Brief analysis of what implementation is needed (2-3 sentences)")
    matched_variant_ids: List[str] = Field(
        default_factory=list,
        description="Array with ONE variant ID if match found, empty if no match"
    )
    new_variants: List[NewVariantData] = Field(
        default_factory=list,
        description="Array with ONE new variant if needed, empty if matched existing"
    )
    reasoning: str = Field(description="Explanation of matching or generation decision (2-3 sentences)")
