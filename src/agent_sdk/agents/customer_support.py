"""Customer support agent implementation."""

import uuid
from typing import Dict, List, Optional

from anthropic import Anthropic
from langfuse.decorators import langfuse_context, observe

from agent_sdk.utils.config import Config
from agent_sdk.utils.models import AgentResponse, CustomerQuery, KnowledgeBase


class CustomerSupportAgent:
    """
    A customer support agent that uses Claude to answer customer queries.

    This agent demonstrates:
    - RAG-like pattern with knowledge base retrieval
    - Langfuse tracing integration
    - Structured responses with reasoning
    """

    def __init__(self, config: Optional[Config] = None, knowledge_base: Optional[List[KnowledgeBase]] = None):
        """
        Initialize the customer support agent.

        Args:
            config: Application configuration
            knowledge_base: List of knowledge base entries
        """
        self.config = config or Config()
        self.client = Anthropic(api_key=self.config.anthropic_api_key)
        self.knowledge_base = knowledge_base or []

    def _retrieve_relevant_docs(self, query: str, top_k: int = 3) -> List[KnowledgeBase]:
        """
        Simple keyword-based retrieval from knowledge base.

        In production, this would use vector embeddings and semantic search.

        Args:
            query: The customer query
            top_k: Number of documents to retrieve

        Returns:
            List of relevant knowledge base entries
        """
        # Simple keyword matching (in production, use embeddings)
        query_lower = query.lower()
        scored_docs = []

        for doc in self.knowledge_base:
            score = 0
            # Check title
            if any(word in doc.title.lower() for word in query_lower.split()):
                score += 2
            # Check content
            if any(word in doc.content.lower() for word in query_lower.split()):
                score += 1
            # Check tags
            if any(word in " ".join(doc.tags).lower() for word in query_lower.split()):
                score += 1

            if score > 0:
                scored_docs.append((score, doc))

        # Sort by score and return top_k
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        return [doc for _, doc in scored_docs[:top_k]]

    @observe(name="customer_support_agent")
    async def handle_query(self, query: CustomerQuery) -> AgentResponse:
        """
        Handle a customer support query.

        Args:
            query: The customer query

        Returns:
            Agent response with answer and metadata
        """
        langfuse_context.update_current_trace(
            user_id=query.customer_id,
            session_id=query.query_id,
            metadata={"query_context": query.context},
        )

        # Retrieve relevant documents
        relevant_docs = self._retrieve_relevant_docs(query.message)

        # Build context from retrieved documents
        context = self._build_context(relevant_docs)

        # Generate response using Claude
        response = await self._generate_response(
            query=query.message, context=context, query_obj=query
        )

        return response

    @observe(name="build_context")
    def _build_context(self, docs: List[KnowledgeBase]) -> str:
        """Build context string from retrieved documents."""
        if not docs:
            return "No relevant documentation found."

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"Document {i}: {doc.title}\n{doc.content}\n")

        return "\n".join(context_parts)

    @observe(name="generate_response")
    async def _generate_response(
        self, query: str, context: str, query_obj: CustomerQuery
    ) -> AgentResponse:
        """
        Generate a response using Claude.

        Args:
            query: The customer query
            context: Retrieved context from knowledge base
            query_obj: Original query object

        Returns:
            Agent response
        """
        system_prompt = """You are a helpful customer support agent. Your goal is to provide accurate,
helpful, and empathetic responses to customer queries.

When answering:
1. Base your answer on the provided documentation context
2. If the context doesn't contain the answer, politely say so and suggest alternatives
3. Be concise but thorough
4. Show empathy and professionalism

After your answer, provide a brief reasoning about your response approach."""

        user_message = f"""Customer Query: {query}

Relevant Documentation:
{context}

Please provide a helpful response to the customer query based on the documentation above.
Then, on a new line starting with 'REASONING:', explain your approach to answering this query."""

        try:
            message = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # Parse response and reasoning
            full_response = message.content[0].text
            response_text, reasoning = self._parse_response(full_response)

            # Track token usage
            langfuse_context.update_current_observation(
                usage={
                    "input": message.usage.input_tokens,
                    "output": message.usage.output_tokens,
                    "total": message.usage.input_tokens + message.usage.output_tokens,
                }
            )

            return AgentResponse(
                response_id=str(uuid.uuid4()),
                query_id=query_obj.query_id,
                message=response_text,
                reasoning=reasoning,
                metadata={
                    "model": self.config.model,
                    "input_tokens": message.usage.input_tokens,
                    "output_tokens": message.usage.output_tokens,
                },
            )

        except Exception as e:
            # Log error to Langfuse
            langfuse_context.update_current_observation(level="ERROR", status_message=str(e))

            return AgentResponse(
                response_id=str(uuid.uuid4()),
                query_id=query_obj.query_id,
                message=f"I apologize, but I encountered an error processing your request. Please try again.",
                metadata={"error": str(e)},
            )

    def _parse_response(self, response: str) -> tuple[str, Optional[str]]:
        """Parse response and reasoning from Claude's output."""
        if "REASONING:" in response:
            parts = response.split("REASONING:", 1)
            return parts[0].strip(), parts[1].strip()
        return response.strip(), None
