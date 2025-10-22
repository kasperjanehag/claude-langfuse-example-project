"""Objective registry for persistent storage and management of control objectives."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from agent_sdk.models.compliance import ControlObjective



class ObjectiveRegistry:
    """
    Persistent registry for control objectives.

    Stores objectives in JSON format and provides methods for:
    - Loading existing objectives
    - Adding new objectives
    - Looking up objectives by ID
    - Generating new objective IDs

    The registry grows over time as LLM generates new objectives.
    """

    def __init__(self, registry_path: Optional[str] = None):
        """
        Initialize the objective registry.

        Args:
            registry_path: Path to objectives JSON file.
                          Defaults to data/control_registry/objectives.json
        """
        if registry_path is None:
            registry_path = "data/control_registry/objectives.json"

        self.registry_path = Path(registry_path)
        self.objectives = self._load_objectives()
        self.index = {obj.objective_id: obj for obj in self.objectives}


    def _load_objectives(self) -> List[ControlObjective]:
        """Load objectives from JSON file."""
        if not self.registry_path.exists():
            self._ensure_registry_file()
            return []

        with open(self.registry_path, "r") as f:
            data = json.load(f)

        objectives = []
        for obj_data in data.get("objectives", []):
            objective = ControlObjective(**obj_data)
            objectives.append(objective)

        return objectives

    def _ensure_registry_file(self) -> None:
        """Ensure registry file and directory exist."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.registry_path.exists():
            data = {"objectives": []}
            with open(self.registry_path, "w") as f:
                json.dump(data, f, indent=2)

    def get_all(self) -> List[ControlObjective]:
        """Get all objectives in the registry."""
        return self.objectives

    def get_by_id(self, objective_id: str) -> Optional[ControlObjective]:
        """
        Get objective by ID.

        Args:
            objective_id: Objective ID to look up

        Returns:
            ControlObjective if found, None otherwise
        """
        return self.index.get(objective_id)

    def add_objective(self, objective: ControlObjective) -> None:
        """
        Add new objective to registry and persist to disk.

        Args:
            objective: ControlObjective to add
        """
        if objective.objective_id in self.index:
            return

        self.objectives.append(objective)
        self.index[objective.objective_id] = objective
        self._save_objectives()


    def generate_next_id(self, domain: str) -> str:
        """
        Generate next available objective ID for a domain.

        Format: OBJ-{DOMAIN}-{N}
        Example: OBJ-DATAPROTECTION-5

        Args:
            domain: Domain name (e.g., "Data protection")

        Returns:
            Next available objective ID
        """
        # Create domain prefix (uppercase, no spaces, max 12 chars)
        domain_prefix = domain.upper().replace(" ", "").replace("-", "")[:12]

        # Find all existing IDs for this domain
        existing_ids = [
            obj.objective_id
            for obj in self.objectives
            if obj.objective_id.startswith(f"OBJ-{domain_prefix}")
        ]

        if not existing_ids:
            return f"OBJ-{domain_prefix}-1"

        # Extract numbers and find max
        numbers = []
        for obj_id in existing_ids:
            try:
                num = int(obj_id.split("-")[-1])
                numbers.append(num)
            except (ValueError, IndexError):
                continue

        max_num = max(numbers) if numbers else 0
        return f"OBJ-{domain_prefix}-{max_num + 1}"

    def _save_objectives(self) -> None:
        """Persist objectives to JSON file."""
        self._ensure_registry_file()

        data = {
            "objectives": [obj.model_dump() for obj in self.objectives]
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)


    def get_by_domain(self, domain: str) -> List[ControlObjective]:
        """
        Get all objectives for a specific domain.

        Args:
            domain: Domain name to filter by

        Returns:
            List of objectives in that domain
        """
        return [obj for obj in self.objectives if obj.domain == domain]

    def get_stats(self) -> Dict[str, any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with registry stats
        """
        domains = set(obj.domain for obj in self.objectives if obj.domain)

        return {
            "total_objectives": len(self.objectives),
            "domains": list(domains),
            "domain_count": len(domains),
            "objective_ids": [obj.objective_id for obj in self.objectives],
        }
