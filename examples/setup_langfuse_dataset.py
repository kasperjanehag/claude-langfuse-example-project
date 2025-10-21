"""Script to set up Langfuse dataset from test cases."""

import sys
from pathlib import Path

from rich.console import Console

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agent_sdk.utils.langfuse_check import require_langfuse
from agent_sdk.utils.langfuse_datasets import setup_receipt_inspection_dataset

console = Console()


def main():
    """Set up the receipt inspection dataset in Langfuse."""
    # Require Langfuse to be available
    require_langfuse()

    console.print("[bold cyan]Setting up Langfuse Dataset[/bold cyan]\n")

    try:
        console.print("[yellow]Creating dataset from test cases...[/yellow]")

        dataset_id = setup_receipt_inspection_dataset()

        console.print("\n[green]✓ Dataset created successfully![/green]")
        console.print(f"[dim]Dataset ID: {dataset_id}[/dim]")
        console.print("\n[yellow]→ View dataset in Langfuse: http://localhost:3000[/yellow]")
        console.print("[dim]   Navigate to: Datasets → receipt_inspection_v1[/dim]\n")

    except Exception as e:
        console.print(f"[red]✗ Error setting up dataset: {str(e)}[/red]")
        console.print("\n[yellow]Make sure:[/yellow]")
        console.print("  1. Langfuse is running (docker compose up -d)")
        console.print("  2. Your .env file has correct LANGFUSE_* keys")
        console.print("  3. You've created a project in Langfuse UI")
        raise


if __name__ == "__main__":
    main()
