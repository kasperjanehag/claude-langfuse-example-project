"""Script to generate controls from obligations."""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.agents.control_generation import ControlGenerationAgent
from agent_sdk.models.compliance import CompanyContext
from agent_sdk.utils.config import Config
from agent_sdk.utils.langfuse_check import require_langfuse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(levelname)-8s - %(message)s", handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def create_mock_company_context() -> CompanyContext:
    """
    Create mock company context for demo purposes (simplified).

    In a real implementation, this would come from:
    - Company profile database
    - Configuration files
    - Interactive prompts
    - Integration with HR/IT systems
    """
    return CompanyContext(
        company_name="Acme Corporation",
        employee_count=250,
        industry="SaaS",
        jurisdictions=["SE", "EU"],
        risk_appetite="Low",
        compliance_maturity="Developing",
    )


def main():
    """Generate controls from obligations."""
    # Require Langfuse to be available
    require_langfuse()

    # Generate unique generation ID for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    generation_id = f"gen_{timestamp}_{uuid.uuid4().hex[:6]}"

    logger.info("=" * 70)
    logger.info("Two-Stage LLM-Driven Control Generation System")
    logger.info("=" * 70)
    logger.info("")
    logger.info(f"Generation ID: {generation_id}")
    logger.info("")
    logger.info("Architecture:")
    logger.info("  Stage 1: Obligations → Control Objectives (LLM semantic mapping)")
    logger.info("  Stage 2: Objectives + Context → Control Variants → Controls")
    logger.info("")

    # Initialize config and agent
    config = Config()
    agent = ControlGenerationAgent(config=config)

    # Show initial registry stats
    logger.info("Registry Status:")
    logger.info(f"  Objectives: {len(agent.objective_registry.get_all())}")
    logger.info(f"  Variants: {len(agent.variant_registry.get_all())}")
    logger.info("")

    # Create mock company context
    logger.info("Creating mock company context...")
    company_context = create_mock_company_context()
    logger.info(f"  Company: {company_context.company_name}")
    logger.info(f"  Employee Count: {company_context.employee_count}")
    logger.info(f"  Industry: {company_context.industry}")
    logger.info(f"  Jurisdictions: {', '.join(company_context.jurisdictions)}")
    logger.info(f"  Risk Appetite: {company_context.risk_appetite}")
    logger.info(f"  Compliance Maturity: {company_context.compliance_maturity}")
    logger.info("")

    # Load obligations and generate controls
    try:
        excel_path = config.obligations_excel_path
        logger.info(f"Loading obligations from: {excel_path}")
        logger.info("")

        # Generate controls
        logger.info("Generating controls...")
        controls = agent.generate_controls_from_excel(
            excel_path=excel_path,
            company_context=company_context,
            generation_id=generation_id,
        )
        logger.info("")

        # Show registry growth
        logger.info("=" * 70)
        logger.info("Generation Summary")
        logger.info("=" * 70)
        logger.info(f"Generated {len(controls)} controls")
        logger.info("")
        logger.info("Registry Status After Generation:")
        logger.info(f"  Objectives: {len(agent.objective_registry.get_all())}")
        logger.info(f"  Variants: {len(agent.variant_registry.get_all())}")
        logger.info("")
        logger.info("Controls Generated:")
        logger.info("=" * 70)
        logger.info("")

        for control in controls:
            logger.info(f"{control.control_id}: {control.control_name}")
            logger.info(f"  Linked obligations: {control.linked_obligation_ids}")
            logger.info(f"  Domain: {control.domain}")
            logger.info(f"  Impact: {control.impact}")
            logger.info(f"  Review interval: {control.review_interval}")
            logger.info("")

        # Save to JSON
        output_dir = Path(config.generated_controls_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use generation_id in filename for easy correlation
        output_file = output_dir / f"{generation_id}.json"

        # Convert controls to dictionaries
        controls_data = {
            "metadata": {
                "generation_id": generation_id,
                "generated_at": datetime.now().isoformat(),
                "company_name": company_context.company_name,
                "employee_count": company_context.employee_count,
                "industry": company_context.industry,
                "jurisdictions": company_context.jurisdictions,
                "risk_appetite": company_context.risk_appetite,
                "compliance_maturity": company_context.compliance_maturity,
                "num_controls": len(controls),
                "generation_method": "objectives_variants",
            },
            "controls": [control.model_dump() for control in controls],
        }

        with open(output_file, "w") as f:
            json.dump(controls_data, f, indent=2)

        logger.info("=" * 70)
        logger.info(f"Controls saved to: {output_file}")
        logger.info("")
        logger.info("View traces in Langfuse: http://localhost:3000")
        logger.info("  Navigate to: Traces → Recent traces")
        logger.info(f"  Search for: generation_id = '{generation_id}'")
        logger.info("=" * 70)
        logger.info("")

    except FileNotFoundError as e:
        logger.error(f"Error: Obligations file not found - {e}")
        logger.info("")
        logger.info("Make sure the obligations Excel file exists at:")
        logger.info(f"  {config.obligations_excel_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error generating controls: {str(e)}")
        logger.info("")
        logger.info("Troubleshooting:")
        logger.info("  1. Verify Langfuse is running (docker compose up -d)")
        logger.info("  2. Check your .env file has correct LANGFUSE_* keys")
        logger.info("  3. Ensure obligations Excel file exists and is readable")
        raise


if __name__ == "__main__":
    main()
