"""Variant registry for persistent storage and management of control variants."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from agent_sdk.models.compliance import ControlVariant



class VariantRegistry:
    """
    Persistent registry for control variants.

    Stores variants in JSON format and provides methods for:
    - Loading existing variants
    - Adding new variants
    - Looking up variants by ID
    - Looking up variants by domain or objective
    - Generating new variant IDs

    The registry grows over time as LLM generates new variants.
    """

    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the variant registry.

        Args:
            registry_path: Path to variants JSON file.
                          Defaults to data/control_registry/control_variants.json
        """
        if registry_path is None:
            registry_path = "data/control_registry/control_variants.json"

        self.registry_path = Path(registry_path)
        self.variants = self._load_variants()
        self.index = {var.variant_id: var for var in self.variants}
        self.objective_index = self._build_objective_index()


    def _load_variants(self) -> List[ControlVariant]:
        """Load variants from JSON file."""
        if not self.registry_path.exists():
            self._ensure_registry_file()
            return []

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        variants = []
        for var_data in data.get("control_variants", []):
            variant = ControlVariant(**var_data)
            variants.append(variant)

        return variants

    def _build_objective_index(self) -> Dict[str, List[ControlVariant]]:
        """Build index of objective_id -> variants."""
        index = {}
        for variant in self.variants:
            if variant.objective_id not in index:
                index[variant.objective_id] = []
            index[variant.objective_id].append(variant)
        return index

    def _ensure_registry_file(self) -> None:
        """Ensure registry file and directory exist."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.registry_path.exists():
            data = {"control_variants": []}
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

    def get_all(self) -> List[ControlVariant]:
        """Get all variants in the registry."""
        return self.variants

    def get_by_id(self, variant_id: str) -> Optional[ControlVariant]:
        """
        Get variant by ID.

        Args:
            variant_id: Variant ID to look up

        Returns:
            ControlVariant if found, None otherwise
        """
        return self.index.get(variant_id)

    def get_by_objective(self, objective_id: str) -> List[ControlVariant]:
        """
        Get all variants for a specific objective.

        Args:
            objective_id: Objective ID to look up

        Returns:
            List of variants for that objective
        """
        return self.objective_index.get(objective_id, [])

    def get_by_domain(self, domain: str) -> List[ControlVariant]:
        """
        Get all variants for a specific domain.

        Args:
            domain: Domain name to filter by

        Returns:
            List of variants in that domain
        """
        return [var for var in self.variants if var.domain == domain]

    def add_variant(self, variant: ControlVariant) -> None:
        """
        Add new variant to registry and persist to disk.

        Args:
            variant: ControlVariant to add
        """
        if variant.variant_id in self.index:
            return

        self.variants.append(variant)
        self.index[variant.variant_id] = variant

        # Update objective index
        if variant.objective_id not in self.objective_index:
            self.objective_index[variant.objective_id] = []
        self.objective_index[variant.objective_id].append(variant)

        self._save_variants()


    def generate_next_id(self, objective_id: str) -> str:
        """
        Generate next available variant ID for an objective.

        Format: CV-{OBJECTIVE_SUFFIX}-{N}
        Example: CV-TRANS-1-2 (second variant for OBJ-TRANS-1)

        Args:
            objective_id: Objective ID (e.g., OBJ-TRANS-1)

        Returns:
            Next available variant ID
        """
        # Extract suffix from objective ID
        # OBJ-TRANS-1 -> TRANS-1
        if objective_id.startswith("OBJ-"):
            suffix = objective_id[4:]  # Remove "OBJ-" prefix
        else:
            suffix = objective_id

        # Find all existing variant IDs for this objective
        existing_ids = [
            var.variant_id
            for var in self.variants
            if var.objective_id == objective_id
        ]

        if not existing_ids:
            return f"CV-{suffix}"

        # Extract numbers and find max
        numbers = []
        for var_id in existing_ids:
            # CV-TRANS-1 or CV-TRANS-1-2
            parts = var_id.split("-")
            if len(parts) >= 4:  # CV-TRANS-1-2
                try:
                    num = int(parts[-1])
                    numbers.append(num)
                except ValueError:
                    continue
            else:  # CV-TRANS-1 (first variant, no number suffix)
                numbers.append(1)

        max_num = max(numbers) if numbers else 0
        return f"CV-{suffix}-{max_num + 1}"

    def _save_variants(self) -> None:
        """Persist variants to JSON file."""
        self._ensure_registry_file()

        data = {
            "control_variants": [var.model_dump() for var in self.variants]
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)


    def get_stats(self) -> Dict[str, any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        domains = set(var.domain for var in self.variants if var.domain)
        objectives = set(var.objective_id for var in self.variants if var.objective_id)

        return {
            "total_variants": len(self.variants),
            "domains": list(domains),
            "domain_count": len(domains),
            "objectives": list(objectives),
            "objective_count": len(objectives),
            "variant_ids": [var.variant_id for var in self.variants],
        }
