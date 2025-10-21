"""Example script for running receipt inspection evaluations."""

import asyncio
import json
import sys
import uuid
from pathlib import Path

from rich.console import Console
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.agents.receipt_inspection import ReceiptInspectionAgent
from agent_sdk.evals.metrics import (
    AuditCriteriaMetric,
    AuditDecisionMetric,
    ExtractionAccuracyMetric,
)
from agent_sdk.utils.config import Config
from agent_sdk.utils.langfuse_check import require_langfuse
from agent_sdk.utils.langfuse_datasets import LangfuseDatasetManager

console = Console()


async def evaluate_receipt(
    agent: ReceiptInspectionAgent,
    test_case: dict,
    metrics: list,
) -> dict:
    """
    Evaluate a single receipt test case.

    Args:
        agent: Receipt inspection agent
        test_case: Test case data
        metrics: List of evaluation metrics

    Returns:
        Evaluation results
    """
    receipt_id = test_case["receipt_id"]
    image_path = test_case.get("image_path", "data/images/placeholder.jpg")
    ground_truth = test_case["ground_truth"]

    console.print(f"\n[cyan]Evaluating {receipt_id}...[/cyan]")

    try:
        # Process receipt (simulated for now since we may not have real images)
        # In production, you would actually process the image
        receipt_details = await agent.extract_receipt_details(image_path, receipt_id)
        audit_decision = await agent.evaluate_receipt_for_audit(receipt_details)

        # Evaluate with metrics
        results = {
            "receipt_id": receipt_id,
            "description": test_case.get("description", ""),
            "passed": True,
            "metrics": {},
        }

        # Evaluate audit decision metrics
        for metric in metrics:
            if isinstance(metric, (AuditCriteriaMetric, AuditDecisionMetric)):
                score, explanation, passed = await metric.evaluate(
                    audit_decision, ground_truth
                )
            elif isinstance(metric, ExtractionAccuracyMetric):
                score, explanation, passed = await metric.evaluate(
                    receipt_details, ground_truth
                )
            else:
                continue

            results["metrics"][metric.name] = {
                "score": score,
                "explanation": explanation,
                "passed": passed,
            }

            if not passed:
                results["passed"] = False

        console.print(
            f"[{'green' if results['passed'] else 'red'}]"
            f"{'✓' if results['passed'] else '✗'} {receipt_id}[/]"
        )

        return results

    except FileNotFoundError:
        console.print(f"[yellow]⚠ Image not found: {image_path}[/yellow]")
        # Return simulated results for demo purposes
        return {
            "receipt_id": receipt_id,
            "description": test_case.get("description", ""),
            "passed": False,
            "metrics": {
                "error": {
                    "score": 0.0,
                    "explanation": f"Image file not found: {image_path}",
                    "passed": False,
                }
            },
        }
    except Exception as e:
        console.print(f"[red]✗ Error: {str(e)}[/red]")
        return {
            "receipt_id": receipt_id,
            "description": test_case.get("description", ""),
            "passed": False,
            "metrics": {
                "error": {
                    "score": 0.0,
                    "explanation": str(e),
                    "passed": False,
                }
            },
        }


async def main():
    """Run evaluation on all receipt test cases."""
    # Require Langfuse to be available
    require_langfuse()

    console.print("[bold cyan]Receipt Inspection Evaluation[/bold cyan]\n")

    # Load test cases
    test_cases_path = Path("data/datasets/receipt_test_cases.json")

    if not test_cases_path.exists():
        console.print(f"[red]Error: Test cases file not found: {test_cases_path}[/red]")
        return

    with open(test_cases_path) as f:
        test_cases = json.load(f)

    console.print(f"[yellow]Loaded {len(test_cases)} test cases[/yellow]")

    # Initialize Langfuse dataset manager
    try:
        dataset_manager = LangfuseDatasetManager()
        console.print("[dim]Langfuse dataset integration enabled[/dim]\n")
    except Exception as e:
        console.print(f"[yellow]Warning: Langfuse dataset not available: {str(e)}[/yellow]")
        console.print("[dim]Run 'python examples/setup_langfuse_dataset.py' to create the dataset[/dim]\n")
        dataset_manager = None

    # Initialize agent and metrics
    config = Config()
    agent = ReceiptInspectionAgent(config=config)

    metrics = [
        AuditDecisionMetric(),  # Most critical: is the final decision correct?
        AuditCriteriaMetric(),  # Are individual criteria correct?
        ExtractionAccuracyMetric(),  # How accurate is data extraction?
    ]

    console.print("[bold]Running evaluations...[/bold]")

    # Run evaluations
    results = []
    for test_case in test_cases:
        result = await evaluate_receipt(agent, test_case, metrics)
        results.append(result)

    # Calculate summary statistics
    total_cases = len(results)
    passed_cases = sum(1 for r in results if r["passed"])
    failed_cases = total_cases - passed_cases

    # Calculate metric averages
    metric_scores = {}
    for result in results:
        for metric_name, metric_result in result["metrics"].items():
            if metric_name not in metric_scores:
                metric_scores[metric_name] = []
            metric_scores[metric_name].append(metric_result["score"])

    metric_averages = {
        name: sum(scores) / len(scores)
        for name, scores in metric_scores.items()
        if scores
    }

    # Display summary
    console.print("\n[bold cyan]Evaluation Summary[/bold cyan]\n")

    # Overall results table
    overall_table = Table(title="Overall Results")
    overall_table.add_column("Metric", style="cyan")
    overall_table.add_column("Value", style="magenta")

    overall_table.add_row("Total Cases", str(total_cases))
    overall_table.add_row("Passed", f"[green]{passed_cases}[/green]")
    overall_table.add_row("Failed", f"[red]{failed_cases}[/red]")
    overall_table.add_row(
        "Pass Rate", f"{(passed_cases / total_cases * 100):.1f}%"
    )

    console.print(overall_table)

    # Metric averages table
    if metric_averages:
        console.print()
        metrics_table = Table(title="Metric Averages")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Average Score", style="magenta")

        for metric_name, avg_score in metric_averages.items():
            metrics_table.add_row(metric_name, f"{avg_score:.3f}")

        console.print(metrics_table)

    # Failed cases details
    if failed_cases > 0:
        console.print(f"\n[bold red]Failed Cases ({failed_cases}):[/bold red]")
        for result in results:
            if not result["passed"]:
                console.print(f"\n[red]✗ {result['receipt_id']}[/red]")
                console.print(f"  {result['description']}")
                for metric_name, metric_result in result["metrics"].items():
                    if not metric_result["passed"]:
                        console.print(
                            f"  • {metric_name}: {metric_result['explanation']}"
                        )

    console.print("\n[green]✓ Evaluation complete![/green]")
    console.print("[yellow]→ View detailed traces in Langfuse: http://localhost:3000[/yellow]\n")

    # Save results
    results_dir = Path("eval_results")
    results_dir.mkdir(exist_ok=True)

    results_file = results_dir / f"receipt_eval_{uuid.uuid4().hex[:8]}.json"
    with open(results_file, "w") as f:
        json.dump(
            {
                "summary": {
                    "total_cases": total_cases,
                    "passed": passed_cases,
                    "failed": failed_cases,
                    "pass_rate": passed_cases / total_cases,
                    "metric_averages": metric_averages,
                },
                "results": results,
            },
            f,
            indent=2,
        )

    console.print(f"[dim]Results saved to: {results_file}[/dim]\n")


if __name__ == "__main__":
    asyncio.run(main())
