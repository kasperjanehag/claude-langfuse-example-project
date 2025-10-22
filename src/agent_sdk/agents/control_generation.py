"""Control generation agent using two-stage LLM-driven system."""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd
from langfuse.decorators import langfuse_context, observe

from agent_sdk.agents.llm_obligation_mapper import LLMObligationMapper
from agent_sdk.agents.llm_variant_mapper import LLMVariantMapper
from agent_sdk.models.compliance import (
    CompanyContext,
    Control,
    ControlObjective,
    Obligation,
)
from agent_sdk.registries.objective_registry import ObjectiveRegistry
from agent_sdk.registries.variant_registry import VariantRegistry
from agent_sdk.utils.config import Config

logger = logging.getLogger(__name__)


class ControlGenerationAgent:
    """
    Two-stage LLM-driven control generation system.

    Architecture:
    Stage 1: Obligations → Control Objectives (LLM-driven semantic mapping)
    Stage 2: Objectives + Context → Control Variants → Controls (LLM-driven implementation)

    Both stages use Claude to match existing registry entries or generate new ones.
    Registries grow over time, becoming more comprehensive.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the control generation agent.

        Args:
            config: Application configuration
        """
        self.config = config or Config()

        # Initialize registries
        self.objective_registry = ObjectiveRegistry()
        self.variant_registry = VariantRegistry()

        # Initialize LLM mappers
        self.obligation_mapper = LLMObligationMapper(self.objective_registry, config)
        self.variant_mapper = LLMVariantMapper(self.variant_registry, config)

        logger.info(
            f"Initialized control generation agent with "
            f"{len(self.objective_registry.get_all())} objectives and "
            f"{len(self.variant_registry.get_all())} variants"
        )

    @observe(name="load_obligations_from_excel")
    def load_obligations_from_excel(self, excel_path: str) -> List[Obligation]:
        """
        Load obligations from Excel file.

        Reads from Obligations_register sheet and converts to Obligation objects.
        Only loads essential fields (simplified).

        Args:
            excel_path: Path to Excel file with Obligations_register sheet

        Returns:
            List of Obligation objects
        """
        logger.info(f"Loading obligations from {excel_path}")

        # Read Excel file
        df = pd.read_excel(excel_path, sheet_name="Obligations_register")

        # Convert to Obligation objects (simplified fields only)
        obligations = []
        for _, row in df.iterrows():
            obligation = Obligation(
                obligation_id=row["Obligation_ID"],
                obligation=row["Obligation"],
                framework_source=row["Framework_source"],
                clause_source=row["Clause_source"],
                domain=row.get("Domains") if not pd.isna(row.get("Domains")) else None,
                impact=row.get("Impact") if not pd.isna(row.get("Impact")) else None,
            )
            obligations.append(obligation)

        logger.info(f"Loaded {len(obligations)} obligations")
        return obligations

    @observe(name="stage_1_map_obligations_to_objectives")
    def stage_1_map_obligations_to_objectives(
        self,
        obligations: List[Obligation],
        generation_id: Optional[str] = None
    ) -> Dict[str, List[ControlObjective]]:
        """
        Stage 1: Map obligations to control objectives using LLM.

        For each obligation, LLM decides:
        - Match to existing objective(s) in registry, OR
        - Generate new objective(s)
        - Or both (supports multi-objective mapping)

        Args:
            obligations: List of obligations to map
            generation_id: Optional generation ID for tracing

        Returns:
            Dictionary mapping obligation_id to list of objectives
        """
        logger.info(f"STAGE 1: Mapping {len(obligations)} obligations to objectives")

        # Use LLM mapper to process all obligations
        mapping = self.obligation_mapper.map_obligations_batch(obligations, generation_id)

        # Log results
        total_objectives = sum(len(objs) for objs in mapping.values())
        unique_objectives = set()
        for objs in mapping.values():
            unique_objectives.update(obj.objective_id for obj in objs)

        logger.info(
            f"STAGE 1 COMPLETE: {len(obligations)} obligations → "
            f"{len(unique_objectives)} unique objectives "
            f"({total_objectives} total mappings)"
        )

        # Update trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "num_obligations": len(obligations),
                "num_unique_objectives": len(unique_objectives),
            }
        )

        return mapping

    @observe(name="stage_2_map_objectives_to_variants")
    def stage_2_map_objectives_to_controls(
        self,
        objectives: List[ControlObjective],
        company_context: CompanyContext,
        obligation_to_objectives: Dict[str, List[ControlObjective]],
        generation_id: Optional[str] = None
    ) -> List[Control]:
        """
        Stage 2: Map objectives + context to control variants and build controls.

        For each objective, LLM decides:
        - Match to existing variant in registry, OR
        - Generate new variant

        Then selects appropriate size variant and builds final Control.

        Args:
            objectives: Unique list of objectives to implement
            company_context: Company context for tailoring
            obligation_to_objectives: Mapping from obligation_id to objectives (for linking)
            generation_id: Optional generation ID for tracing

        Returns:
            List of Control objects
        """
        logger.info(
            f"STAGE 2: Mapping {len(objectives)} objectives to control variants for context "
            f"(employee_count={company_context.employee_count}, jurisdictions={company_context.jurisdictions})"
        )

        controls = []

        # Build objective → obligations mapping (reverse of obligation → objectives)
        objective_to_obligations = {}
        for obligation_id, objs in obligation_to_objectives.items():
            for obj in objs:
                if obj.objective_id not in objective_to_obligations:
                    objective_to_obligations[obj.objective_id] = []
                objective_to_obligations[obj.objective_id].append(obligation_id)

        # Process each objective
        for objective in objectives:
            logger.info(f"Processing objective: {objective.objective_id}")

            # Get linked obligation IDs
            linked_obligation_ids = objective_to_obligations.get(objective.objective_id, [])

            # Stage 2a: Map objective to variant (match or generate)
            variant = self.variant_mapper.map_objective_to_variant(
                objective,
                company_context,
                linked_obligation_ids,
                generation_id
            )

            if not variant:
                logger.warning(f"No variant found/generated for objective {objective.objective_id}")
                continue

            # Stage 2b: Select size variant and build control
            control = self.variant_mapper.select_variant_and_build_control(
                variant,
                company_context,
                linked_obligation_ids,
                generation_id
            )

            if control:
                controls.append(control)
                logger.info(f"Generated control: {control.control_id}")

        logger.info(f"STAGE 2 COMPLETE: {len(objectives)} objectives → {len(controls)} controls")

        # Update trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "num_objectives": len(objectives),
                "num_controls": len(controls),
            }
        )

        return controls

    @observe(name="generate_controls_from_obligations")
    def generate_controls(
        self,
        obligations: List[Obligation],
        company_context: CompanyContext,
        generation_id: Optional[str] = None
    ) -> List[Control]:
        """
        Generate controls from obligations using two-stage LLM system.

        Stage 1: Obligations → Control Objectives (LLM semantic mapping)
        Stage 2: Objectives + Context → Control Variants → Controls

        Args:
            obligations: List of obligations to generate controls for
            company_context: Company context for tailoring controls
            generation_id: Optional unique ID for this generation run

        Returns:
            List of generated Control objects
        """
        logger.info(
            f"Generating controls for {len(obligations)} obligations "
            f"(two-stage LLM system)"
        )

        # Stage 1: Obligations → Objectives
        obligation_to_objectives = self.stage_1_map_obligations_to_objectives(
            obligations,
            generation_id
        )

        # Get unique objectives
        unique_objectives = {}
        for objs in obligation_to_objectives.values():
            for obj in objs:
                unique_objectives[obj.objective_id] = obj

        objectives_list = list(unique_objectives.values())

        # Stage 2: Objectives + Context → Controls
        controls = self.stage_2_map_objectives_to_controls(
            objectives_list,
            company_context,
            obligation_to_objectives,
            generation_id
        )

        logger.info(
            f"Control generation complete: {len(obligations)} obligations → "
            f"{len(objectives_list)} objectives → {len(controls)} controls"
        )

        return controls

    @observe(name="generate_controls_from_excel")
    def generate_controls_from_excel(
        self,
        excel_path: str,
        company_context: CompanyContext,
        generation_id: Optional[str] = None
    ) -> List[Control]:
        """
        Complete workflow: load obligations from Excel and generate controls.

        Args:
            excel_path: Path to Excel file with obligations
            company_context: Company context for tailoring controls
            generation_id: Optional unique ID for this generation run

        Returns:
            List of generated Control objects
        """
        # Generate unique ID if not provided
        if generation_id is None:
            generation_id = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"

        logger.info(f"Starting control generation run: {generation_id}")

        # Load obligations
        obligations = self.load_obligations_from_excel(excel_path)

        # Extract metadata for tracing
        frameworks = list(set(o.framework_source for o in obligations if o.framework_source))
        domains = list(set(o.domain for o in obligations if o.domain))

        # Update trace
        langfuse_context.update_current_trace(
            name="control_generation_run",
            metadata={
                "generation_id": generation_id,
                "num_obligations": len(obligations),
            },
            tags=self._generate_trace_tags(frameworks, domains, company_context),
        )

        # Generate controls using two-stage system
        controls = self.generate_controls(obligations, company_context, generation_id)

        # Update trace with final count
        langfuse_context.update_current_trace(
            metadata={
                "num_controls_generated": len(controls),
            }
        )

        logger.info(f"Control generation run {generation_id} complete: {len(controls)} controls")

        return controls

    def _generate_trace_tags(
        self,
        frameworks: List[str],
        domains: List[str],
        company_context: CompanyContext
    ) -> List[str]:
        """
        Generate tags for trace filtering and search.

        Args:
            frameworks: List of framework names
            domains: List of domain names
            company_context: Company context

        Returns:
            List of tags
        """
        tags = ["control-generation", "llm-driven"]

        # Add framework tags
        for framework in frameworks:
            framework_key = framework.split()[0].lower() if framework else None
            if framework_key:
                tags.append(framework_key)

        # Add domain tags
        for domain in domains:
            domain_tag = domain.lower().replace(" ", "-") if domain else None
            if domain_tag:
                tags.append(domain_tag)

        # Add company size tags
        if company_context.employee_count:
            if company_context.employee_count < 50:
                tags.append("startup")
            elif company_context.employee_count < 1000:
                tags.append("sme")
            else:
                tags.append("enterprise")

        if company_context.industry:
            tags.append(company_context.industry.lower())

        return tags
