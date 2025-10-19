"""Evaluation metrics for agent responses."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from anthropic import Anthropic
from langfuse.decorators import observe

from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AgentResponse, AuditDecision, CustomerQuery


class Metric(ABC):
    """Base class for evaluation metrics."""

    def __init__(self, name: str, threshold: Optional[float] = None):
        """
        Initialize the metric.

        Args:
            name: Name of the metric
            threshold: Threshold for passing (if applicable)
        """
        self.name = name
        self.threshold = threshold

    @abstractmethod
    async def evaluate(
        self, query: CustomerQuery, response: AgentResponse, ground_truth: Optional[Dict[str, Any]] = None
    ) -> tuple[float, str, bool]:
        """
        Evaluate a response.

        Args:
            query: The customer query
            response: The agent response
            ground_truth: Optional ground truth data

        Returns:
            Tuple of (score, explanation, passed)
        """
        pass


class FaithfulnessMetric(Metric):
    """
    Evaluate if the response is faithful to the provided context.

    This metric checks if the agent's response is grounded in the context
    and doesn't hallucinate information.
    """

    def __init__(self, config: Optional[Config] = None):
        super().__init__(name="faithfulness", threshold=0.7)
        self.config = config or Config()
        self.client = Anthropic(
            api_key=self.config.anthropic_api_key,
            base_url=self.config.anthropic_base_url
        )

    @observe(name="faithfulness_eval")
    async def evaluate(
        self, query: CustomerQuery, response: AgentResponse, ground_truth: Optional[Dict[str, Any]] = None
    ) -> tuple[float, str, bool]:
        """
        Evaluate faithfulness using LLM-as-judge.

        Args:
            query: The customer query
            response: The agent response
            ground_truth: Optional ground truth with context

        Returns:
            Tuple of (score, explanation, passed)
        """
        eval_prompt = f"""You are an expert evaluator. Assess if the agent's response is faithful to the provided context.

A response is faithful if:
1. All claims in the response can be traced back to the context
2. No information is hallucinated or made up
3. The response doesn't contradict the context

Customer Query: {query.message}

Agent Response: {response.message}

Context: {ground_truth.get('context', 'No context provided') if ground_truth else 'No context provided'}

Rate the faithfulness on a scale of 0.0 to 1.0, where:
- 1.0 = Completely faithful, all information grounded in context
- 0.5 = Partially faithful, some unsupported claims
- 0.0 = Not faithful, significant hallucination

Respond in this format:
SCORE: [0.0-1.0]
EXPLANATION: [Your reasoning]"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": eval_prompt}],
            )

            result = message.content[0].text
            score, explanation = self._parse_eval_result(result)

            return score, explanation, score >= self.threshold

        except Exception as e:
            return 0.0, f"Evaluation failed: {str(e)}", False

    def _parse_eval_result(self, result: str) -> tuple[float, str]:
        """Parse the evaluation result."""
        lines = result.strip().split("\n")
        score = 0.0
        explanation = ""

        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score = float(line.split("SCORE:")[1].strip())
                except ValueError:
                    pass
            elif line.startswith("EXPLANATION:"):
                explanation = line.split("EXPLANATION:")[1].strip()

        return score, explanation


class AnswerRelevanceMetric(Metric):
    """
    Evaluate if the response directly addresses the customer's question.

    This metric checks if the agent's response is relevant and helpful
    for the specific query asked.
    """

    def __init__(self, config: Optional[Config] = None):
        super().__init__(name="answer_relevance", threshold=0.7)
        self.config = config or Config()
        self.client = Anthropic(
            api_key=self.config.anthropic_api_key,
            base_url=self.config.anthropic_base_url
        )

    @observe(name="answer_relevance_eval")
    async def evaluate(
        self, query: CustomerQuery, response: AgentResponse, ground_truth: Optional[Dict[str, Any]] = None
    ) -> tuple[float, str, bool]:
        """
        Evaluate answer relevance using LLM-as-judge.

        Args:
            query: The customer query
            response: The agent response
            ground_truth: Optional ground truth data

        Returns:
            Tuple of (score, explanation, passed)
        """
        eval_prompt = f"""You are an expert evaluator. Assess if the agent's response is relevant to the customer's query.

A response is relevant if:
1. It directly addresses the question asked
2. It provides useful information for the customer's situation
3. It doesn't go off on tangents or provide unrelated information

Customer Query: {query.message}

Agent Response: {response.message}

Rate the relevance on a scale of 0.0 to 1.0, where:
- 1.0 = Perfectly relevant, directly answers the query
- 0.5 = Partially relevant, some useful information
- 0.0 = Not relevant, doesn't address the query

Respond in this format:
SCORE: [0.0-1.0]
EXPLANATION: [Your reasoning]"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": eval_prompt}],
            )

            result = message.content[0].text
            score, explanation = self._parse_eval_result(result)

            return score, explanation, score >= self.threshold

        except Exception as e:
            return 0.0, f"Evaluation failed: {str(e)}", False

    def _parse_eval_result(self, result: str) -> tuple[float, str]:
        """Parse the evaluation result."""
        lines = result.strip().split("\n")
        score = 0.0
        explanation = ""

        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score = float(line.split("SCORE:")[1].strip())
                except ValueError:
                    pass
            elif line.startswith("EXPLANATION:"):
                explanation = line.split("EXPLANATION:")[1].strip()

        return score, explanation


class GroundTruthMetric(Metric):
    """
    Compare response against ground truth expected answer.

    This is a simple exact match or semantic similarity metric.
    """

    def __init__(self, config: Optional[Config] = None):
        super().__init__(name="ground_truth_match", threshold=0.8)
        self.config = config or Config()
        self.client = Anthropic(
            api_key=self.config.anthropic_api_key,
            base_url=self.config.anthropic_base_url
        )

    @observe(name="ground_truth_eval")
    async def evaluate(
        self, query: CustomerQuery, response: AgentResponse, ground_truth: Optional[Dict[str, Any]] = None
    ) -> tuple[float, str, bool]:
        """
        Evaluate against ground truth.

        Args:
            query: The customer query
            response: The agent response
            ground_truth: Ground truth data with expected answer

        Returns:
            Tuple of (score, explanation, passed)
        """
        if not ground_truth or "expected_answer" not in ground_truth:
            return 0.0, "No ground truth provided", False

        expected = ground_truth["expected_answer"]

        eval_prompt = f"""You are an expert evaluator. Compare the agent's response to the expected answer.

Rate how well the response matches the expected answer on a scale of 0.0 to 1.0:
- 1.0 = Semantically equivalent, conveys the same information
- 0.5 = Partially matches, some key information present
- 0.0 = Completely different, doesn't match

Customer Query: {query.message}

Agent Response: {response.message}

Expected Answer: {expected}

Respond in this format:
SCORE: [0.0-1.0]
EXPLANATION: [Your reasoning]"""

        try:
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0.0,
                messages=[{"role": "user", "content": eval_prompt}],
            )

            result = message.content[0].text
            score, explanation = self._parse_eval_result(result)

            return score, explanation, score >= self.threshold

        except Exception as e:
            return 0.0, f"Evaluation failed: {str(e)}", False

    def _parse_eval_result(self, result: str) -> tuple[float, str]:
        """Parse the evaluation result."""
        lines = result.strip().split("\n")
        score = 0.0
        explanation = ""

        for line in lines:
            if line.startswith("SCORE:"):
                try:
                    score = float(line.split("SCORE:")[1].strip())
                except ValueError:
                    pass
            elif line.startswith("EXPLANATION:"):
                explanation = line.split("EXPLANATION:")[1].strip()

        return score, explanation


# Receipt Inspection Metrics
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
