"""LLM-driven mapping from obligations to control objectives (Stage 1)."""

from typing import Dict, List, Optional

import openai
from langfuse.decorators import langfuse_context, observe

from agent_sdk.models.compliance import ControlObjective, Obligation
from agent_sdk.models.llm_responses import NewObjectiveData, ObligationMappingResponse
from agent_sdk.registries.objective_registry import ObjectiveRegistry
from agent_sdk.utils.config import Config



class LLMObligationMapper:
    """
    Maps obligations to control objectives using LLM reasoning.

    This is Stage 1 of the two-stage system:
    - Analyzes obligation text to understand semantic intent
    - Matches to existing objectives in registry OR
    - Generates new objectives when no good match exists
    - Supports multi-objective mapping (1 obligation → N objectives)

    Uses OpenAI with temperature=0 for deterministic results.
    """

    def __init__(
        self,
        objective_registry: ObjectiveRegistry,
        config: Optional[Config] = None
    ):
        """
        Initialize the LLM obligation mapper.

        Args:
            objective_registry: Registry for storing and retrieving objectives
            config: Application configuration
        """
        self.objective_registry = objective_registry
        self.config = config or Config()
        self.client = openai.OpenAI(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url
        )

    @observe(name="map_obligation_to_objectives")
    def map_obligation(
        self,
        obligation: Obligation,
        generation_id: Optional[str] = None
    ) -> List[ControlObjective]:
        """
        Map a single obligation to control objectives.

        LLM analyzes the obligation and decides whether to:
        - Match to existing objective(s) in registry
        - Generate new objective(s)
        - Or both (some matches + some new)

        Args:
            obligation: Obligation to map
            generation_id: Optional generation ID for tracing

        Returns:
            List of ControlObjective objects (may be empty if no match/generation)
        """

        # Get existing objectives from registry
        existing_objectives = self.objective_registry.get_all()

        # Build prompt
        prompt = self._build_mapping_prompt(obligation, existing_objectives)

        # Update trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "obligation_id": obligation.obligation_id,
                "num_existing_objectives": len(existing_objectives),
            }
        )

        # Call OpenAI with structured output
        try:
            completion = self.client.beta.chat.completions.parse(
                model=self.config.model,
                # Note: temperature not specified - using model default
                max_completion_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
                response_format=ObligationMappingResponse,
            )

            # Extract parsed Pydantic object
            response = completion.choices[0].message.parsed

            # Process results
            objectives = self._process_mapping_result(response, obligation, generation_id)

            # Update trace
            langfuse_context.update_current_observation(
                metadata={
                    "num_objectives_mapped": len(objectives),
                    "objective_ids": [obj.objective_id for obj in objectives],
                }
            )

            return objectives

        except Exception as e:
            langfuse_context.update_current_observation(
                metadata={"error": str(e)}
            )
            return []

    def _build_mapping_prompt(
        self,
        obligation: Obligation,
        existing_objectives: List[ControlObjective]
    ) -> str:
        """Build prompt for obligation → objective mapping."""

        # Format existing objectives for prompt
        objectives_text = self._format_objectives_for_prompt(existing_objectives)

        prompt = f"""You are a compliance expert mapping legal obligations to control objectives.

CONTROL OBJECTIVES are context-less semantic abstractions that describe what operational capability needs to exist. They are reusable across different companies and contexts.

EXISTING OBJECTIVES REGISTRY:
{objectives_text}

OBLIGATION TO MAP:
ID: {obligation.obligation_id}
Text: {obligation.obligation}
Framework: {obligation.framework_source}
Domain: {obligation.domain if obligation.domain else "Not specified"}

YOUR TASK:
1. Analyze what this obligation semantically requires (what capability must exist to satisfy it)
2. Check if any EXISTING objectives already cover this requirement
   - An obligation can map to MULTIPLE existing objectives (common for complex obligations)
   - Match if the semantic intent aligns, even if wording differs
   - Be generous with matching - better to reuse existing objectives than create duplicates
3. If NO existing objective covers a requirement, generate a NEW objective
   - Make it reusable (context-less, focused on capability not specific obligation)
   - Ensure it's distinct from existing objectives
   - Only create new if truly necessary

OUTPUT FORMAT (JSON):
{{
  "analysis": "Brief analysis of what this obligation requires (2-3 sentences)",
  "matched_objective_ids": ["OBJ-XXX-1", "OBJ-YYY-2"],  // Array of IDs that match (empty if none)
  "new_objectives": [  // Array of new objectives to create (empty if none needed)
    {{
      "objective_name": "Clear, reusable name",
      "description": "What systematic capability this establishes",
      "domain": "{obligation.domain if obligation.domain else 'General'}",
      "intent": "Why this objective matters from control perspective",
      "rationale": "Why this is needed as a separate objective (not covered by existing)"
    }}
  ],
  "reasoning": "Explain your matching and generation decisions (2-3 sentences)"
}}

Important Guidelines:
- Be conservative about creating new objectives. Only create when existing truly don't fit.
- Focus on the semantic INTENT of the obligation, not literal word matching
- If obligation touches multiple areas, map to multiple objectives
- Ensure new objectives are reusable for similar obligations from other frameworks
"""

        return prompt

    def _format_objectives_for_prompt(
        self,
        objectives: List[ControlObjective]
    ) -> str:
        """Format objectives for inclusion in prompt."""

        if not objectives:
            return "No existing objectives yet."

        lines = []
        for obj in objectives:
            lines.append(f"ID: {obj.objective_id}")
            lines.append(f"Name: {obj.objective_name}")
            lines.append(f"Description: {obj.description}")
            lines.append(f"Domain: {obj.domain}")
            lines.append(f"Intent: {obj.intent}")
            lines.append("")  # Blank line between objectives

        return "\n".join(lines)

    def _process_mapping_result(
        self,
        result: ObligationMappingResponse,
        obligation: Obligation,
        generation_id: Optional[str]
    ) -> List[ControlObjective]:
        """
        Process LLM mapping result into ControlObjective objects.

        Handles both matched objectives and newly generated objectives.

        Args:
            result: Parsed Pydantic response from LLM
            obligation: Original obligation being mapped
            generation_id: Optional generation ID

        Returns:
            List of ControlObjective objects
        """
        objectives = []

        # Process matched objectives
        for obj_id in result.matched_objective_ids:
            obj = self.objective_registry.get_by_id(obj_id)
            if obj:
                objectives.append(obj)

        # Process new objectives
        for new_obj_data in result.new_objectives:
            new_obj = self._create_and_register_objective(
                new_obj_data,
                obligation,
                generation_id
            )
            if new_obj:
                objectives.append(new_obj)

        return objectives

    def _create_and_register_objective(
        self,
        obj_data: NewObjectiveData,
        source_obligation: Obligation,
        generation_id: Optional[str]
    ) -> Optional[ControlObjective]:
        """
        Create new objective from LLM data and add to registry.

        Args:
            obj_data: Pydantic model with objective fields
            source_obligation: Obligation that triggered this creation
            generation_id: Optional generation ID

        Returns:
            Created ControlObjective or None if creation failed
        """
        try:
            # Generate new ID
            domain = obj_data.domain or source_obligation.domain or "General"
            new_id = self.objective_registry.generate_next_id(domain)

            # Create objective
            objective = ControlObjective(
                objective_id=new_id,
                objective_name=obj_data.objective_name,
                description=obj_data.description,
                domain=domain,
                intent=obj_data.intent,
                linked_obligation_ids=[source_obligation.obligation_id],
                rationale=obj_data.rationale
            )

            # Add to registry (persists to JSON)
            self.objective_registry.add_objective(objective)

            return objective

        except Exception as e:
            return None

    @observe(name="map_obligations_to_objectives_batch")
    def map_obligations_batch(
        self,
        obligations: List[Obligation],
        generation_id: Optional[str] = None
    ) -> Dict[str, List[ControlObjective]]:
        """
        Map multiple obligations to control objectives.

        Processes each obligation individually (not batched in single LLM call).

        Args:
            obligations: List of obligations to map
            generation_id: Optional generation ID for tracing

        Returns:
            Dictionary mapping obligation_id to list of objectives
        """

        mapping = {}
        for obligation in obligations:
            objectives = self.map_obligation(obligation, generation_id)
            mapping[obligation.obligation_id] = objectives

        # Calculate summary statistics
        total_objectives = sum(len(objs) for objs in mapping.values())
        unique_objectives = set()
        for objs in mapping.values():
            unique_objectives.update(obj.objective_id for obj in objs)

        # Update trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "num_obligations": len(obligations),
                "num_unique_objectives": len(unique_objectives),
                "total_mappings": total_objectives,
            }
        )

        return mapping
