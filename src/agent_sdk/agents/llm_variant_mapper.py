"""LLM-driven mapping from objectives + context to control variants (Stage 2)."""

from typing import Dict, List, Optional

import openai
from langfuse.decorators import langfuse_context, observe

from agent_sdk.models.compliance import CompanyContext, Control, ControlObjective, ControlVariant
from agent_sdk.models.llm_responses import NewVariantData, VariantMappingResponse
from agent_sdk.registries.variant_registry import VariantRegistry
from agent_sdk.utils.config import Config



class LLMVariantMapper:
    """
    Maps control objectives + company context to control variants using LLM reasoning.

    This is Stage 2 of the two-stage system:
    - Takes context-less objectives and company context
    - Matches to existing variants in registry OR
    - Generates new variants when no good match exists
    - Selects appropriate size variant (startup/SME/enterprise) based on context
    - Applies jurisdiction requirements

    Uses OpenAI with temperature=0 for deterministic results.
    """

    def __init__(
        self,
        variant_registry: VariantRegistry,
        config: Optional[Config] = None
    ):
        """
        Initialize the LLM variant mapper.

        Args:
            variant_registry: Registry for storing and retrieving variants
            config: Application configuration
        """
        self.variant_registry = variant_registry
        self.config = config or Config()
        self.client = openai.OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )

    @observe(name="map_objective_to_variant")
    def map_objective_to_variant(
        self,
        objective: ControlObjective,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[ControlVariant]:
        """
        Map an objective + context to a control variant.

        LLM analyzes the objective and context and decides whether to:
        - Match to existing variant in registry
        - Generate new variant

        Args:
            objective: Control objective to implement
            company_context: Company context for tailoring
            linked_obligation_ids: Obligation IDs this control addresses
            generation_id: Optional generation ID for tracing

        Returns:
            ControlVariant if found/generated, None otherwise
        """
        # Get existing variants from registry (filter by domain for efficiency)
        existing_variants = self.variant_registry.get_by_domain(objective.domain)

        # Build prompt
        prompt = self._build_variant_mapping_prompt(
            objective,
            company_context,
            existing_variants
        )

        # Update trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "objective_id": objective.objective_id,
                "num_existing_variants": len(existing_variants),
            }
        )

        # Call OpenAI with structured output
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.config.model,
                # Note: temperature not specified - using model default
                max_completion_tokens=6000,
                messages=[{"role": "user", "content": prompt}],
                response_format=VariantMappingResponse,
            )

            # Extract parsed Pydantic object
            response = completion.choices[0].message.parsed

            # Process result
            variant = self._process_mapping_result(
                response,
                objective,
                company_context,
                linked_obligation_ids,
                generation_id
            )

            # Update trace
            if variant:
                langfuse_context.update_current_observation(
                    metadata={
                        "variant_id": variant.variant_id,
                    }
                )

            return variant

        except Exception as e:
            langfuse_context.update_current_observation(
                metadata={"error": str(e)}
            )
            return None

    def _build_variant_mapping_prompt(
        self,
        objective: ControlObjective,
        company_context: CompanyContext,
        existing_variants: List[ControlVariant]
    ) -> str:
        """Build prompt for objective + context → variant mapping."""

        # Format existing variants for prompt
        variants_text = self._format_variants_for_prompt(existing_variants)

        prompt = f"""You are a compliance expert mapping control objectives to implementation variants.

CONTROL VARIANTS are context-specific implementations of control objectives. They contain:
- Multiple size-specific variants (startup/SME/enterprise) with different implementation approaches
- Jurisdiction-specific requirements that apply to certain regions

EXISTING VARIANTS REGISTRY:
{variants_text}

CONTROL OBJECTIVE TO IMPLEMENT:
ID: {objective.objective_id}
Name: {objective.objective_name}
Description: {objective.description}
Intent: {objective.intent}
Domain: {objective.domain}

COMPANY CONTEXT:
- Employee Count: {company_context.employee_count}
- Industry: {company_context.industry}
- Jurisdictions: {", ".join(company_context.jurisdictions)}
- Risk Appetite: {company_context.risk_appetite}
- Compliance Maturity: {company_context.compliance_maturity}

YOUR TASK:
1. Analyze what implementation variant(s) would fulfill this objective for this company context
2. Check if any EXISTING variants already provide appropriate implementation
   - Match if the variant's approach and size variants fit the objective + context
   - Be generous with matching - better to reuse existing variants
3. If NO existing variant fits, generate a NEW control variant
   - Must include variants for different company sizes (startup <50, SME 50-1000, enterprise 1000+)
   - Must include jurisdiction-specific requirements for company's jurisdictions
   - Make it reusable for similar contexts

OUTPUT FORMAT (JSON):
{{
  "analysis": "Brief analysis of what implementation is needed (2-3 sentences)",
  "matched_variant_ids": ["CV-XXX-1"],  // Array with ONE ID if match found, empty if no match
  "new_variants": [  // Array with ONE new variant if needed, empty if matched existing
    {{
      "variant_name": "Descriptive implementation name",
      "base_description": "Core control description explaining what this control does",
      "variants": [
        {{
          "variant_type": "startup",
          "applies_if": "employee_count < 50",
          "description_additions": "Lightweight approach suitable for startups...",
          "evidence_requirements": ["Policy document", "Training records", "..."],
          "review_interval": "12 months"
        }},
        {{
          "variant_type": "sme",
          "applies_if": "employee_count >= 50 and employee_count < 1000",
          "description_additions": "More structured approach for SMEs...",
          "evidence_requirements": ["Policy document", "Training records", "Process documentation", "..."],
          "review_interval": "6 months"
        }},
        {{
          "variant_type": "enterprise",
          "applies_if": "employee_count >= 1000",
          "description_additions": "Comprehensive approach for enterprises...",
          "evidence_requirements": ["Policy document", "Training records", "Process documentation", "Audit reports", "..."],
          "review_interval": "3 months"
        }}
      ],
      "jurisdiction_requirements": {{
        {self._format_jurisdiction_requirements_template(company_context)}
      }}
    }}
  ],
  "reasoning": "Explain your matching or generation decision (2-3 sentences)"
}}

Important Guidelines:
- Be conservative about creating new variants. Only create when existing truly don't fit.
- If you create a new variant, you MUST include all three size variants (startup/SME/enterprise)
- Jurisdiction requirements should be specific to that jurisdiction's unique requirements
- The base_description should explain what the control achieves (the "what")
- The variant description_additions explain how it's implemented for that company size
"""

        return prompt

    def _format_variants_for_prompt(
        self,
        variants: List[ControlVariant]
    ) -> str:
        """Format variants for inclusion in prompt."""

        if not variants:
            return "No existing variants in this domain yet."

        lines = []
        for var in variants:
            lines.append(f"ID: {var.variant_id}")
            lines.append(f"Objective: {var.objective_id}")
            lines.append(f"Name: {var.variant_name}")
            lines.append(f"Description: {var.base_description[:150]}...")
            lines.append(f"Size Variants: {len(var.variants)}")
            lines.append(f"Jurisdictions: {', '.join(var.jurisdiction_requirements.keys())}")
            lines.append("")  # Blank line between variants

        return "\n".join(lines)

    def _format_jurisdiction_requirements_template(
        self,
        company_context: CompanyContext
    ) -> str:
        """Format jurisdiction requirements template for prompt."""

        lines = []
        for jurisdiction in company_context.jurisdictions:
            lines.append(f'        "{jurisdiction}": ["Jurisdiction-specific requirement 1", "Requirement 2", "..."]')

        return ",\n".join(lines) if lines else '        "EU": ["Example requirement"]'

    def _process_mapping_result(
        self,
        result: VariantMappingResponse,
        objective: ControlObjective,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str]
    ) -> Optional[ControlVariant]:
        """
        Process LLM mapping result into ControlVariant object.

        Handles both matched variants and newly generated variants.

        Args:
            result: Parsed Pydantic response from LLM
            objective: Control objective being mapped
            company_context: Company context
            linked_obligation_ids: Obligation IDs
            generation_id: Optional generation ID

        Returns:
            ControlVariant object or None
        """
        # Check for matched variant
        if result.matched_variant_ids:
            variant_id = result.matched_variant_ids[0]  # Take first match
            variant = self.variant_registry.get_by_id(variant_id)
            if variant:
                return variant

        # Check for new variant
        if result.new_variants:
            new_variant_data = result.new_variants[0]  # Take first new variant
            variant = self._create_and_register_variant(
                new_variant_data,
                objective,
                generation_id
            )
            return variant

        return None

    def _create_and_register_variant(
        self,
        var_data: NewVariantData,
        objective: ControlObjective,
        generation_id: Optional[str]
    ) -> Optional[ControlVariant]:
        """
        Create new variant from LLM data and add to registry.

        Args:
            var_data: Pydantic model with variant fields
            objective: Objective this variant implements
            generation_id: Optional generation ID

        Returns:
            Created ControlVariant or None if creation failed
        """
        try:
            # Generate new ID
            new_id = self.variant_registry.generate_next_id(objective.objective_id)

            # Create variant - convert Pydantic list to list of dicts
            variant = ControlVariant(
                variant_id=new_id,
                objective_id=objective.objective_id,
                variant_name=var_data.variant_name,
                base_description=var_data.base_description,
                domain=objective.domain,
                variants=[v.model_dump() for v in var_data.variants],
                jurisdiction_requirements=var_data.jurisdiction_requirements
            )

            # Add to registry (persists to JSON)
            self.variant_registry.add_variant(variant)

            return variant

        except Exception as e:
            return None

    @observe(name="select_variant_and_build_control")
    def select_variant_and_build_control(
        self,
        variant: ControlVariant,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[Control]:
        """
        Select appropriate size variant and build final control.

        This method:
        1. Evaluates which size variant applies (startup/SME/enterprise)
        2. Applies jurisdiction requirements
        3. Builds the final Control object

        Args:
            variant: ControlVariant with multiple size options
            company_context: Company context
            linked_obligation_ids: Obligation IDs this control addresses
            generation_id: Optional generation ID

        Returns:
            Control object or None
        """

        # Select appropriate size variant
        selected_variant = None
        for var in variant.variants:
            # Simple evaluation of applies_if condition
            applies_if = var.get("applies_if", "")
            if self._evaluate_applies_if(applies_if, company_context):
                selected_variant = var
                break

        if not selected_variant:
            # Default to first variant
            selected_variant = variant.variants[0] if variant.variants else None

        if not selected_variant:
            return None

        # Build control ID
        control_id = f"{variant.variant_id}-{selected_variant['variant_type'].upper()}"

        # Apply jurisdiction requirements
        applicable_requirements = []
        for jurisdiction in company_context.jurisdictions:
            if jurisdiction in variant.jurisdiction_requirements:
                reqs = variant.jurisdiction_requirements[jurisdiction]
                applicable_requirements.extend(reqs)

        # Build control description
        description = variant.base_description
        if selected_variant.get("description_additions"):
            description += f"\n\n{selected_variant['description_additions']}"

        if applicable_requirements:
            description += "\n\nJurisdiction-specific requirements:\n"
            for req in applicable_requirements:
                description += f"- {req}\n"

        # Build evidence requirements
        evidence = selected_variant.get("evidence_requirements", [])
        evidence_str = "; ".join(evidence) if evidence else None

        # Create Control object
        control = Control(
            control_id=control_id,
            control_name=variant.variant_name,
            control_description=description,
            linked_obligation_ids="; ".join(linked_obligation_ids),
            domain=variant.domain,
            expected_evidence=evidence_str,
            review_interval=selected_variant.get("review_interval", "12 months"),
            impact="Critical"  # TODO: Derive from obligation impact
        )


        return control

    def _evaluate_applies_if(
        self,
        applies_if: str,
        company_context: CompanyContext
    ) -> bool:
        """
        Evaluate applies_if condition.

        Simple evaluation using company context variables.

        Args:
            applies_if: Condition string (e.g., "employee_count < 50")
            company_context: Company context

        Returns:
            True if condition matches, False otherwise
        """
        try:
            # Build safe evaluation context
            context_vars = {
                "employee_count": company_context.employee_count or 0
            }

            # Safely evaluate condition
            result = eval(applies_if, {"__builtins__": {}}, context_vars)
            return bool(result)

        except Exception as e:
            return False
