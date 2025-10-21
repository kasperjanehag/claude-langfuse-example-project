"""Langfuse dataset integration utilities."""

import json
from typing import Any, Dict, List, Optional

from langfuse import Langfuse

from agent_sdk.utils.config import Config


class LangfuseDatasetManager:
    """
    Manager for Langfuse datasets.

    Provides functionality to:
    - Create datasets from test case JSON files
    - Update existing datasets
    - Link evaluation runs to datasets
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the dataset manager.

        Args:
            config: Application configuration
        """
        self.config = config or Config()
        self.client = Langfuse(
            public_key=self.config.langfuse_public_key,
            secret_key=self.config.langfuse_secret_key,
            host=self.config.langfuse_host,
        )

    def create_or_update_dataset(
        self,
        dataset_name: str,
        test_cases: List[Dict[str, Any]],
        description: Optional[str] = None,
    ) -> str:
        """
        Create or update a Langfuse dataset from test cases.

        Args:
            dataset_name: Name of the dataset
            test_cases: List of test case dictionaries
            description: Optional description of the dataset

        Returns:
            Dataset ID
        """
        # Create or get dataset
        try:
            dataset = self.client.get_dataset(dataset_name)
            print(f"Found existing dataset: {dataset_name}")
        except Exception:
            dataset = self.client.create_dataset(
                name=dataset_name,
                description=description or f"Receipt inspection test cases - {dataset_name}",
            )
            print(f"Created new dataset: {dataset_name}")

        # Add items to dataset
        for test_case in test_cases:
            receipt_id = test_case["receipt_id"]

            # Create input for the dataset item
            input_data = {
                "receipt_id": receipt_id,
                "image_path": test_case.get("image_path"),
                "description": test_case.get("description"),
            }

            # Create expected output (ground truth)
            expected_output = test_case.get("ground_truth", {})

            # Create dataset item
            try:
                self.client.create_dataset_item(
                    dataset_name=dataset_name,
                    input=input_data,
                    expected_output=expected_output,
                    metadata={
                        "test_case_id": test_case.get("id"),
                        "receipt_id": receipt_id,
                    },
                )
                print(f"  Added item: {receipt_id}")
            except Exception as e:
                print(f"  Warning: Could not add {receipt_id}: {str(e)}")

        return dataset.id if hasattr(dataset, 'id') else dataset_name

    def load_test_cases_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load test cases from a JSON file.

        Args:
            json_path: Path to the JSON file

        Returns:
            List of test case dictionaries
        """
        with open(json_path, "r") as f:
            return json.load(f)

    def create_dataset_from_json(
        self,
        dataset_name: str,
        json_path: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Create a Langfuse dataset from a JSON file.

        Args:
            dataset_name: Name of the dataset
            json_path: Path to the JSON file containing test cases
            description: Optional description of the dataset

        Returns:
            Dataset ID
        """
        test_cases = self.load_test_cases_from_json(json_path)
        return self.create_or_update_dataset(dataset_name, test_cases, description)

    def link_trace_to_dataset(
        self,
        trace_id: str,
        dataset_name: str,
        dataset_item_id: str,
    ):
        """
        Link a trace to a dataset item.

        Args:
            trace_id: Langfuse trace ID
            dataset_name: Name of the dataset
            dataset_item_id: ID of the dataset item
        """
        try:
            self.client.link_trace_to_dataset_item(
                trace_id=trace_id,
                dataset_name=dataset_name,
                dataset_item_id=dataset_item_id,
            )
        except Exception as e:
            print(f"Warning: Could not link trace to dataset: {str(e)}")

    def get_dataset(self, dataset_name: str):
        """
        Get a dataset by name.

        Args:
            dataset_name: Name of the dataset

        Returns:
            Dataset object
        """
        return self.client.get_dataset(dataset_name)

    def list_dataset_items(self, dataset_name: str) -> List[Any]:
        """
        List all items in a dataset.

        Args:
            dataset_name: Name of the dataset

        Returns:
            List of dataset items
        """
        dataset = self.get_dataset(dataset_name)
        return list(dataset.items)


def setup_receipt_inspection_dataset(
    dataset_name: str = "receipt_inspection_v1",
    test_cases_path: str = "data/datasets/receipt_test_cases.json",
) -> str:
    """
    Convenience function to set up the receipt inspection dataset.

    Args:
        dataset_name: Name for the dataset
        test_cases_path: Path to test cases JSON file

    Returns:
        Dataset ID
    """
    manager = LangfuseDatasetManager()

    description = (
        "Receipt inspection test cases for eval-driven development. "
        "Contains 20 test cases from Roboflow dataset covering various receipt types: "
        "gas stations, retail stores, auto services, with various audit conditions."
    )

    return manager.create_dataset_from_json(
        dataset_name=dataset_name,
        json_path=test_cases_path,
        description=description,
    )
