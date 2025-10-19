"""Evaluation metrics for agent responses."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from anthropic import Anthropic
from langfuse.decorators import observe

from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AgentResponse, CustomerQuery


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
