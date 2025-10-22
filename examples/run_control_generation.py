"""Script to generate controls from obligations."""

import json
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

    print("=" * 70)
    print("Two-Stage LLM-Driven Control Generation System")
    print("=" * 70)
    print(f"\nGeneration ID: {generation_id}\n")
    print("Architecture:")
    print("  Stage 1: Obligations → Control Objectives (LLM semantic mapping)")
    print("  Stage 2: Objectives + Context → Control Variants → Controls\n")

    # Initialize config and agent
    config = Config()
    agent = ControlGenerationAgent(config=config)

    # Create mock company context
    company_context = create_mock_company_context()

    # Load obligations and generate controls
    try:
        excel_path = config.obligations_excel_path

        # Generate controls
        controls = agent.generate_controls_from_excel(
            excel_path=excel_path,
            company_context=company_context,
            generation_id=generation_id,
        )

        print(f"\nGenerated {len(controls)} controls")
        print(f"Generation ID: {generation_id}")

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

        print(f"\nControls saved to: {output_file}")
        print(f"View traces in Langfuse: http://localhost:3000")

    except FileNotFoundError as e:
        print(f"\nError: Obligations file not found - {e}")
        print(f"Make sure the obligations Excel file exists at: {config.obligations_excel_path}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError generating controls: {str(e)}")
        print("\nTroubleshooting:")
        print("  1. Verify Langfuse is running (docker compose up -d)")
        print("  2. Check your .env file has correct LANGFUSE_* and OPENAI_* keys")
        print("  3. Ensure obligations Excel file exists and is readable")
        raise


if __name__ == "__main__":
    main()
