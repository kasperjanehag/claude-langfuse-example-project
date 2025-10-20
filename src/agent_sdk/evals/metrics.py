"""Evaluation metrics for receipt inspection agent."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from agent_sdk.utils.models import AuditDecision


class Metric(ABC):
    """Base class for evaluation metrics."""

    def __init__(self, name: str, threshold: float = 0.7):
        """
        Initialize the metric.

        Args:
            name: Name of the metric
            threshold: Threshold for passing
        """
        self.name = name
        self.threshold = threshold

    @abstractmethod
    async def evaluate(self, *args, **kwargs) -> tuple[float, str, bool]:
        """
        Evaluate the metric.

        Returns:
            Tuple of (score, explanation, passed)
        """
        pass


class AuditCriteriaMetric(Metric):
    """
    Evaluate if audit criteria were correctly assessed.

    This metric checks if each audit criterion (not_travel_related, amount_over_limit,
    math_error, handwritten_x) was correctly evaluated against ground truth.
    """

    def __init__(self):
        super().__init__(name="audit_criteria_accuracy", threshold=0.75)

    async def evaluate(
        self,
        audit_decision: AuditDecision,
        ground_truth: Dict[str, Any],
    ) -> tuple[float, str, bool]:
        """
        Evaluate audit criteria accuracy.

        Args:
            audit_decision: The audit decision made by the agent
            ground_truth: Ground truth audit decision

        Returns:
            Tuple of (score, explanation, passed)
        """
        if "audit_decision" not in ground_truth:
            return 0.0, "No ground truth audit decision provided", False

        gt_decision = ground_truth["audit_decision"]

        # Check each criterion
        criteria_checks = {
            "not_travel_related": audit_decision.not_travel_related == gt_decision.get("not_travel_related"),
            "amount_over_limit": audit_decision.amount_over_limit == gt_decision.get("amount_over_limit"),
            "math_error": audit_decision.math_error == gt_decision.get("math_error"),
            "handwritten_x": audit_decision.handwritten_x == gt_decision.get("handwritten_x"),
        }

        # Calculate accuracy
        correct_count = sum(criteria_checks.values())
        total_count = len(criteria_checks)
        score = correct_count / total_count

        # Build explanation
        incorrect = [k for k, v in criteria_checks.items() if not v]
        if incorrect:
            explanation = f"Incorrect criteria: {', '.join(incorrect)}. "
            explanation += f"Got {correct_count}/{total_count} criteria correct."
        else:
            explanation = "All audit criteria correctly evaluated."

        passed = score >= self.threshold

        return score, explanation, passed


class AuditDecisionMetric(Metric):
    """
    Evaluate if the final audit decision (needs_audit) is correct.

    This is the most critical metric - did the agent make the right final decision?
    """

    def __init__(self):
        super().__init__(name="audit_decision_correct", threshold=1.0)

    async def evaluate(
        self,
        audit_decision: AuditDecision,
        ground_truth: Dict[str, Any],
    ) -> tuple[float, str, bool]:
        """
        Evaluate if the final audit decision is correct.

        Args:
            audit_decision: The audit decision made by the agent
            ground_truth: Ground truth audit decision

        Returns:
            Tuple of (score, explanation, passed)
        """
        if "audit_decision" not in ground_truth:
            return 0.0, "No ground truth audit decision provided", False

        gt_decision = ground_truth["audit_decision"]
        expected_needs_audit = gt_decision.get("needs_audit")

        if audit_decision.needs_audit == expected_needs_audit:
            score = 1.0
            explanation = f"Correct audit decision: needs_audit={expected_needs_audit}"
            passed = True
        else:
            score = 0.0
            explanation = f"Incorrect audit decision. Expected needs_audit={expected_needs_audit}, got {audit_decision.needs_audit}"
            passed = False

        return score, explanation, passed


class ExtractionAccuracyMetric(Metric):
    """
    Evaluate accuracy of receipt detail extraction.

    Checks key fields like merchant, total, location, etc.
    """

    def __init__(self):
        super().__init__(name="extraction_accuracy", threshold=0.7)

    async def evaluate(
        self,
        receipt_details: Any,  # ReceiptDetails
        ground_truth: Dict[str, Any],
    ) -> tuple[float, str, bool]:
        """
        Evaluate extraction accuracy.

        Args:
            receipt_details: Extracted receipt details
            ground_truth: Ground truth receipt details

        Returns:
            Tuple of (score, explanation, passed)
        """
        if "details" not in ground_truth:
            return 0.0, "No ground truth details provided", False

        gt_details = ground_truth["details"]
        correct_fields = []
        incorrect_fields = []
        total_fields = 0

        # Check key fields
        key_fields = ["merchant", "total", "subtotal", "tax"]
        for field in key_fields:
            if field in gt_details and gt_details[field]:
                total_fields += 1
                extracted_value = getattr(receipt_details, field, None)
                expected_value = gt_details[field]

                if str(extracted_value).strip().lower() == str(expected_value).strip().lower():
                    correct_fields.append(field)
                else:
                    incorrect_fields.append(f"{field} (expected: {expected_value}, got: {extracted_value})")

        # Check location
        if "location" in gt_details and gt_details["location"]:
            total_fields += 1
            if receipt_details.location:
                location_match = (
                    receipt_details.location.city == gt_details["location"].get("city") and
                    receipt_details.location.state == gt_details["location"].get("state")
                )
                if location_match:
                    correct_fields.append("location")
                else:
                    incorrect_fields.append("location")
            else:
                incorrect_fields.append("location (missing)")

        # Calculate score
        if total_fields == 0:
            return 0.0, "No fields to evaluate", False

        score = len(correct_fields) / total_fields

        # Build explanation
        if incorrect_fields:
            explanation = f"Correct: {len(correct_fields)}/{total_fields}. Incorrect: {', '.join(incorrect_fields[:3])}"
        else:
            explanation = f"All {total_fields} key fields extracted correctly."

        passed = score >= self.threshold

        return score, explanation, passed
