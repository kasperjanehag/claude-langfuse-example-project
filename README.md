# Claude Agent SDK Starter

A production-ready starter project demonstrating **eval-driven development** for LLM-based agent systems using Claude, Langfuse, and modern Python best practices.

## Overview

This project showcases how to build, evaluate, and iterate on AI agent systems using:

- **Evaluation-Driven Development**: Systematic approach to improving AI agents through measurable metrics
- **Langfuse Integration**: Complete observability with self-hosted tracing and monitoring
- **Customer Support Agent**: Real-world RAG-like example with knowledge base retrieval
- **Multiple Evaluation Metrics**: Faithfulness, answer relevance, and ground truth matching
- **Production Best Practices**: Type hints, async/await, structured logging, and comprehensive testing

Based on principles from [Hamel Husain and Shreya Shankar's guide to building eval systems](https://www.lennysnewsletter.com/p/building-eval-systems-that-improve).

## Features

### Agent System
- **Customer Support Agent** with RAG-like knowledge base retrieval
- Powered by Claude 3.5 Sonnet
- Structured responses with reasoning traces
- Full Langfuse observability integration

### Evaluation Framework
- **Faithfulness Metric**: Ensures responses are grounded in provided context
- **Answer Relevance Metric**: Validates responses address the query
- **Ground Truth Matching**: Compares against expected answers
- Automated evaluation pipeline with rich console output
- Results tracking and export

### Observability
- Self-hosted Langfuse setup with Docker Compose
- Automatic trace collection for all agent operations
- Token usage tracking
- Error monitoring and debugging

## Project Structure

```
claude-agent-sdk-starter/
├── src/
│   └── agent_sdk/
│       ├── agents/              # Agent implementations
│       │   └── customer_support.py
│       ├── evals/               # Evaluation framework
│       │   ├── evaluator.py
│       │   └── metrics.py
│       └── utils/               # Shared utilities
│           ├── config.py
│           └── models.py
├── data/
│   └── datasets/                # Test data and knowledge base
│       ├── test_cases.json
│       └── knowledge_base.json
├── examples/                    # Example scripts
│   ├── run_agent.py
│   ├── run_evaluation.py
│   └── interactive_agent.py
├── tests/                       # Unit and integration tests
├── docker-compose.yml           # Langfuse self-hosted setup
├── pyproject.toml              # Project configuration
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- Docker and Docker Compose
- Anthropic API key

### 1. Clone and Install

```bash
cd claude-agent-sdk-starter

# Create virtual environment and install dependencies with uv
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dependencies
uv pip install -e ".[dev]"

# Or use uv sync to install from lock file (faster)
uv sync --all-extras
```

### 2. Set Up Langfuse (Self-Hosted)

**Important**: Before starting Langfuse, update the secrets in `docker-compose.yml`:
- Change all passwords and secrets marked with `# CHANGEME`
- Use long, random passwords (minimum 32 characters)

```bash
# Start Langfuse and its dependencies
docker compose up -d

# Wait for services to be ready (2-3 minutes)
docker compose logs -f langfuse-web

# When you see "Ready", Langfuse is running
# Access UI at http://localhost:3000
```

**First-time setup in Langfuse UI**:
1. Navigate to http://localhost:3000
2. Create your account
3. Create a new project
4. Go to Settings → API Keys
5. Copy your Public Key and Secret Key

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your keys:
# - ANTHROPIC_API_KEY (from console.anthropic.com)
# - LANGFUSE_PUBLIC_KEY (from Langfuse UI)
# - LANGFUSE_SECRET_KEY (from Langfuse UI)
```

### 4. Run Examples

**Simple Agent Query**:
```bash
python examples/run_agent.py
```

**Interactive Mode**:
```bash
python examples/interactive_agent.py
```

**Run Evaluations**:
```bash
python examples/run_evaluation.py
```

The evaluation will:
- Process all 10 test cases from `data/datasets/test_cases.json`
- Evaluate each response using 3 metrics
- Display results in a rich console table
- Save detailed results to `eval_results/`
- Track all traces in Langfuse

## Eval-Driven Development Workflow

This project demonstrates the systematic approach to improving AI agents:

### 1. Define Metrics That Matter

Instead of generic scores, we measure what actually impacts user experience:

- **Faithfulness**: Does the agent hallucinate or stick to facts?
- **Answer Relevance**: Does it actually answer the question?
- **Ground Truth**: Does it match expected behavior?

See `src/agent_sdk/evals/metrics.py` for implementations.

### 2. Build a Test Dataset

Create test cases that represent real user scenarios:

```json
{
  "id": "test_001",
  "query": "How do I reset my password?",
  "ground_truth": {
    "expected_answer": "...",
    "context": "..."
  }
}
```

See `data/datasets/test_cases.json` for 10 example test cases.

### 3. Run Evaluations

```bash
python examples/run_evaluation.py
```

This produces:
- Pass/fail for each test case
- Scores for each metric
- Overall pass rate
- Detailed explanations
- Langfuse traces for debugging

### 4. Analyze and Iterate

1. **Review failures** in the console output
2. **Examine traces** in Langfuse (http://localhost:3000)
3. **Identify patterns**: Are failures in specific categories?
4. **Make improvements**:
   - Update prompts
   - Enhance retrieval
   - Add knowledge base entries
5. **Re-run evaluations** to measure improvement
6. **Track progress** over time using Langfuse datasets

### Example Output

```
Evaluation Summary

Overall Results
┏━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Value ┃
┡━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Cases │ 10    │
│ Passed      │ 8     │
│ Failed      │ 2     │
│ Pass Rate   │ 80.0% │
└─────────────┴───────┘

Metric Averages
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Metric            ┃ Average Score ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ faithfulness      │ 0.85          │
│ answer_relevance  │ 0.90          │
│ ground_truth_match│ 0.72          │
└───────────────────┴───────────────┘
```

## Langfuse Features

### Viewing Traces

1. Go to http://localhost:3000
2. Navigate to "Traces"
3. Click on any trace to see:
   - Full prompt and completion
   - Token usage
   - Latency
   - Evaluation scores
   - Nested observations (retrieval, generation, etc.)

### Creating Datasets

Langfuse datasets let you version and track test sets:

1. In Langfuse UI: Datasets → Create Dataset
2. Add test cases manually or import from traces
3. Run evaluations against datasets
4. Compare results across versions

### Monitoring Production

When deploying to production:

1. Keep the Langfuse decorator (`@observe`) on your functions
2. Point `LANGFUSE_HOST` to your production Langfuse instance
3. Monitor:
   - Average response quality scores
   - Token usage trends
   - Error rates
   - Latency percentiles

## Customization

### Adding New Metrics

Create a new metric in `src/agent_sdk/evals/metrics.py`:

```python
class CustomMetric(Metric):
    def __init__(self):
        super().__init__(name="custom_metric", threshold=0.8)

    async def evaluate(self, query, response, ground_truth):
        # Your evaluation logic
        score = ...
        explanation = ...
        passed = score >= self.threshold
        return score, explanation, passed
```

Add to evaluator in `src/agent_sdk/evals/evaluator.py`:

```python
self.metrics = [
    FaithfulnessMetric(config),
    AnswerRelevanceMetric(config),
    CustomMetric(),  # Add your metric
]
```

### Adding Test Cases

Edit `data/datasets/test_cases.json`:

```json
{
  "id": "test_011",
  "query": "Your question here",
  "context": {...},
  "ground_truth": {
    "expected_answer": "Expected response",
    "context": "Supporting documentation"
  }
}
```

### Expanding Knowledge Base

Add entries to `data/datasets/knowledge_base.json`:

```json
{
  "id": "kb_013",
  "title": "New Topic",
  "category": "category_name",
  "content": "Detailed information...",
  "tags": ["tag1", "tag2"]
}
```

### Using Different Models

Update `src/agent_sdk/utils/config.py` or set environment variable:

```bash
export MODEL=claude-3-opus-20240229
```

## Development

### Running Tests

```bash
# Run all tests (uv will use the virtual environment)
uv run pytest

# With coverage
uv run pytest --cov=src/agent_sdk --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_agent.py
```

### Code Quality

```bash
# Format code
uv run black src/ tests/ examples/

# Lint
uv run ruff check src/ tests/ examples/

# Type checking
uv run mypy src/
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files
```

## Architecture Decisions

### Why Async/Await?
- Enables concurrent API calls during evaluation
- Better performance when processing multiple test cases
- Prepares codebase for production-scale concurrent requests

### Why Self-Hosted Langfuse?
- Complete data privacy
- No external dependencies for tracing
- Customizable retention and storage
- Free for unlimited usage

### Why LLM-as-Judge for Evals?
- Semantic understanding vs. keyword matching
- Scales to complex evaluation criteria
- Provides explanations for debugging
- Correlates well with human judgment

### Why Structured Test Cases?
- Version control for test data
- Easy to review and update
- Shareable across team
- Foundation for regression testing

## Troubleshooting

### Langfuse Not Starting

```bash
# Check service status
docker compose ps

# View logs
docker compose logs langfuse-web
docker compose logs langfuse-db

# Restart services
docker compose restart
```

### API Key Errors

```bash
# Verify .env file exists and has correct keys
cat .env

# Check environment variables are loaded
python -c "from agent_sdk.utils.config import Config; c = Config(); print(c.anthropic_api_key[:10] + '...')"
```

### Import Errors

```bash
# Ensure package is installed in editable mode
pip install -e .

# Verify Python path
python -c "import sys; print(sys.path)"
```

## Resources

### Documentation
- [Langfuse Docs](https://langfuse.com/docs)
- [Anthropic API Reference](https://docs.anthropic.com/)
- [Building Eval Systems (Lenny's Newsletter)](https://www.lennysnewsletter.com/p/building-eval-systems-that-improve)

### Related Projects
- [Langfuse Python SDK](https://github.com/langfuse/langfuse-python)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)

### Learning Resources
- [AI Evals Course by Hamel & Shreya](https://maven.com/parlance-labs/evals)
- [LLM Evaluation Guide](https://www.oreilly.com/library/view/building-llm-powered/9781098150228/)

## Contributing

Contributions are welcome! Areas for improvement:

- Additional evaluation metrics
- More example agents (code generation, data analysis, etc.)
- Integration with vector databases (Pinecone, Weaviate, etc.)
- Batch evaluation support
- CI/CD pipeline examples
- Production deployment guides

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Inspired by [Hamel Husain](https://twitter.com/HamelHusain) and [Shreya Shankar](https://twitter.com/sh_reya)'s work on LLM evaluations
- Built with [Anthropic's Claude](https://www.anthropic.com/claude)
- Observability powered by [Langfuse](https://langfuse.com/)

---

**Questions or Issues?**

Open an issue on GitHub or reach out to the maintainers.

**Happy Building!** 🚀
