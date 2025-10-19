"""Main evaluator for running evaluations on agent systems."""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langfuse import Langfuse
from langfuse.decorators import observe
from rich.console import Console
from rich.progress import track
from rich.table import Table

from agent_sdk.agents.customer_support import CustomerSupportAgent
from agent_sdk.evals.metrics import AnswerRelevanceMetric, FaithfulnessMetric, GroundTruthMetric
from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AgentResponse, CustomerQuery, EvalResult


class Evaluator:
    """
    Evaluator for agent systems.

    This class orchestrates running evaluations on test datasets
    and tracking results in Langfuse.
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the evaluator.

        Args:
            config: Application configuration
        """
        self.config = config or Config()
        self.console = Console()

        # Initialize Langfuse
        if self.config.langfuse_public_key and self.config.langfuse_secret_key:
            self.langfuse = Langfuse(
                public_key=self.config.langfuse_public_key,
                secret_key=self.config.langfuse_secret_key,
                host=self.config.langfuse_host,
            )
        else:
            self.langfuse = None
            self.console.print(
                "[yellow]Warning: Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY[/yellow]"
            )

        # Initialize metrics
        self.metrics = [
            FaithfulnessMetric(config),
            AnswerRelevanceMetric(config),
            GroundTruthMetric(config),
        ]

    @observe(name="run_evaluation")
    async def run_evaluation(
        self,
        agent: CustomerSupportAgent,
        test_cases: List[Dict[str, Any]],
        output_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Run evaluation on a set of test cases.

        Args:
            agent: The agent to evaluate
            test_cases: List of test cases with queries and ground truth
            output_path: Optional path to save results

        Returns:
            Dictionary with evaluation results
        """
        self.console.print(f"\n[bold blue]Running evaluation on {len(test_cases)} test cases...[/bold blue]\n")

        all_results = []
        passed_count = 0
        failed_count = 0

        for test_case in track(test_cases, description="Evaluating"):
            # Create query
            query = CustomerQuery(
                query_id=str(uuid.uuid4()),
                customer_id=test_case.get("customer_id", "test_customer"),
                message=test_case["query"],
                context=test_case.get("context"),
            )

            # Get agent response
            response = await agent.handle_query(query)

            # Run all metrics
            case_results = []
            case_passed = True

            for metric in self.metrics:
                score, explanation, passed = await metric.evaluate(
                    query=query, response=response, ground_truth=test_case.get("ground_truth")
                )

                eval_result = EvalResult(
                    eval_id=str(uuid.uuid4()),
                    query_id=query.query_id,
                    response_id=response.response_id,
                    metric_name=metric.name,
                    score=score,
                    explanation=explanation,
                    passed=passed,
                    metadata={
                        "threshold": metric.threshold,
                        "test_case_id": test_case.get("id", "unknown"),
                    },
                )

                case_results.append(eval_result)

                if not passed:
                    case_passed = False

                # Send to Langfuse if configured
                if self.langfuse:
                    self._log_to_langfuse(eval_result, query, response)

            all_results.append(
                {
                    "test_case": test_case,
                    "query": query.model_dump(),
                    "response": response.model_dump(),
                    "eval_results": [r.model_dump() for r in case_results],
                    "passed": case_passed,
                }
            )

            if case_passed:
                passed_count += 1
            else:
                failed_count += 1

        # Generate summary
        summary = self._generate_summary(all_results, passed_count, failed_count)

        # Save results if output path provided
        if output_path:
            self._save_results(all_results, summary, output_path)

        # Display summary
        self._display_summary(summary)

        return summary

    def _log_to_langfuse(self, eval_result: EvalResult, query: CustomerQuery, response: AgentResponse):
        """Log evaluation result to Langfuse."""
        try:
            self.langfuse.score(
                name=eval_result.metric_name,
                value=eval_result.score,
                trace_id=query.query_id,
                comment=eval_result.explanation,
            )
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to log to Langfuse: {e}[/yellow]")

    def _generate_summary(
        self, all_results: List[Dict[str, Any]], passed_count: int, failed_count: int
    ) -> Dict[str, Any]:
        """Generate evaluation summary."""
        total = len(all_results)

        # Calculate metric averages
        metric_scores = {}
        for result in all_results:
            for eval_result in result["eval_results"]:
                metric_name = eval_result["metric_name"]
                if metric_name not in metric_scores:
                    metric_scores[metric_name] = []
                metric_scores[metric_name].append(eval_result["score"])

        metric_averages = {name: sum(scores) / len(scores) for name, scores in metric_scores.items()}

        return {
            "total_cases": total,
            "passed": passed_count,
            "failed": failed_count,
            "pass_rate": passed_count / total if total > 0 else 0,
            "metric_averages": metric_averages,
            "timestamp": datetime.now().isoformat(),
        }

    def _save_results(self, all_results: List[Dict[str, Any]], summary: Dict[str, Any], output_path: Path):
        """Save evaluation results to file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump({"summary": summary, "results": all_results}, f, indent=2, default=str)

        self.console.print(f"\n[green]Results saved to {output_path}[/green]")

    def _display_summary(self, summary: Dict[str, Any]):
        """Display evaluation summary in a rich table."""
        self.console.print("\n[bold]Evaluation Summary[/bold]\n")

        # Overall results table
        table = Table(title="Overall Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total Cases", str(summary["total_cases"]))
        table.add_row("Passed", f"[green]{summary['passed']}[/green]")
        table.add_row("Failed", f"[red]{summary['failed']}[/red]")
        table.add_row("Pass Rate", f"{summary['pass_rate']:.1%}")

        self.console.print(table)

        # Metric scores table
        if summary["metric_averages"]:
            self.console.print()
            metric_table = Table(title="Metric Averages")
            metric_table.add_column("Metric", style="cyan")
            metric_table.add_column("Average Score", style="magenta")

            for metric_name, avg_score in summary["metric_averages"].items():
                color = "green" if avg_score >= 0.7 else "yellow" if avg_score >= 0.5 else "red"
                metric_table.add_row(metric_name, f"[{color}]{avg_score:.2f}[/{color}]")

            self.console.print(metric_table)
