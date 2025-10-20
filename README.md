# Claude Agent Eval Starter - Receipt Inspection

A production-ready starter project demonstrating **eval-driven development** for LLM-based agent systems using Claude, Langfuse, and modern Python best practices.

## Overview

This project showcases how to build, evaluate, and iterate on AI agent systems using a **receipt inspection and audit decision** use case:

- **Evaluation-Driven Development**: Systematic approach to improving AI agents through measurable metrics
- **Langfuse Integration**: Complete observability with self-hosted tracing and monitoring
- **Receipt Inspection Agent**: Vision-based extraction of structured data from receipt images and automated audit decisions
- **Multiple Evaluation Metrics**: Audit decision accuracy, criteria evaluation, and extraction accuracy
- **Production Best Practices**: Type hints, async/await, structured logging, and comprehensive testing

Based on principles from the [OpenAI Cookbook's Eval-Driven System Design guide](https://cookbook.openai.com/examples/partners/eval_driven_system_design/receipt_inspection) and [Hamel Husain and Shreya Shankar's guide to building eval systems](https://www.lennysnewsletter.com/p/building-eval-systems-that-improve).

## Features

### Agent System
- **Receipt Inspection Agent** with vision-based data extraction
- Automated audit decision making based on configurable criteria
- Powered by Claude 3.5 Sonnet with vision capabilities
- Structured outputs with reasoning traces
- Full Langfuse observability integration

### Use Case: Receipt Parsing and Audit Decisions

The system processes receipt images and makes audit decisions based on:

1. **NOT_TRAVEL_RELATED**: Identifies if expenses are not travel-related (office supplies, food, etc.)
2. **AMOUNT_OVER_LIMIT**: Flags receipts exceeding $50
3. **MATH_ERROR**: Detects arithmetic errors in receipt totals
4. **HANDWRITTEN_X**: Identifies receipts marked with handwritten "X"

A receipt needs auditing if **any** criterion is violated. This mirrors real-world expense validation workflows where certain receipts require human review.

### Evaluation Framework
- **Audit Decision Metric**: Validates final audit decision correctness
- **Audit Criteria Metric**: Evaluates accuracy of individual criterion assessments
- **Extraction Accuracy Metric**: Measures receipt data extraction quality
- Automated evaluation pipeline with rich console output
- Results tracking and export
- LLM-as-judge for nuanced evaluations

### Observability
- Self-hosted Langfuse setup with Docker Compose
- Automatic trace collection for all agent operations
- Token usage tracking
- Error monitoring and debugging

## Project Structure

```
claude-agent-eval-starter/
├── src/
│   └── agent_sdk/
│       ├── agents/              # Agent implementations
│       │   └── receipt_inspection.py
│       ├── evals/               # Evaluation framework
│       │   └── metrics.py       # Receipt-specific evaluation metrics
│       └── utils/               # Shared utilities
│           ├── config.py
│           └── models.py
├── data/
│   ├── datasets/                # Test data
│   │   └── receipt_test_cases.json
│   └── images/                  # Receipt images (not included)
├── examples/                    # Example scripts
│   ├── run_receipt_inspection.py
│   └── run_receipt_evaluation.py
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
cd claude-agent-eval-starter

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
# Access UI at http://localhost:3200
```

**First-time setup in Langfuse UI**:
1. Navigate to http://localhost:3200
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

**Process a Single Receipt**:
```bash
python examples/run_receipt_inspection.py
```

This will:
- Extract structured details from a receipt image
- Evaluate the receipt against audit criteria
- Display the audit decision and reasoning
- Track the operation in Langfuse

**Run Evaluations**:
```bash
python examples/run_receipt_evaluation.py
```

The evaluation will:
- Process all 10 test cases from `data/datasets/receipt_test_cases.json`
- Evaluate each receipt using 3 metrics:
  - Audit Decision Correctness (most critical)
  - Audit Criteria Accuracy
  - Extraction Accuracy
- Display results in rich console tables
- Save detailed results to `eval_results/`
- Track all traces in Langfuse

**Note**: The example scripts expect receipt images in `data/images/`. The repository includes test case definitions but not the actual images. You can:
- Add your own receipt images
- Modify the test cases to point to your images
- Use the structure as a template for your own receipt processing system

## Eval-Driven Development Workflow

This project demonstrates the systematic approach to improving AI agents through a receipt inspection use case:

### 1. Define Metrics That Matter

Instead of generic scores, we measure what actually impacts business outcomes:

- **Audit Decision Correctness**: Did the system make the right final decision? (Most critical)
- **Audit Criteria Accuracy**: Were individual criteria (travel-related, amount, math, marks) correctly evaluated?
- **Extraction Accuracy**: How accurately were receipt details extracted?

These metrics directly connect to business KPIs:
- False negatives (missing audit-worthy receipts) = compliance risk
- False positives (unnecessary audits) = wasted human review time
- Extraction errors = downstream decision errors

See `src/agent_sdk/evals/metrics.py` for implementations.

### 2. Build a Test Dataset

Create test cases that represent real receipt scenarios:

```json
{
  "id": "receipt_001",
  "receipt_id": "rec_walmart_supplies",
  "image_path": "data/images/walmart_supplies.jpg",
  "description": "Walmart receipt for office supplies",
  "ground_truth": {
    "details": {
      "merchant": "Walmart",
      "total": "54.96",
      "items": [...]
    },
    "audit_decision": {
      "not_travel_related": true,
      "amount_over_limit": true,
      "needs_audit": true,
      "reasoning": "..."
    }
  }
}
```

See `data/datasets/receipt_test_cases.json` for 10 example test cases covering:
- Travel expenses (gas, hotel, car rental)
- Non-travel expenses (office supplies, food)
- Edge cases (math errors, handwritten marks)
- Various amounts (under/over $50 threshold)

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
2. **Examine traces** in Langfuse (http://localhost:3200)
3. **Identify patterns**: Are failures in specific categories?
4. **Make improvements**:
   - Update prompts
   - Enhance retrieval
   - Add knowledge base entries
5. **Re-run evaluations** to measure improvement
6. **Track progress** over time using Langfuse datasets

### Example Output

```
Receipt Inspection Evaluation

Overall Results
┏━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric      ┃ Value ┃
┡━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Cases │ 10    │
│ Passed      │ 9     │
│ Failed      │ 1     │
│ Pass Rate   │ 90.0% │
└─────────────┴───────┘

Metric Averages
┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Metric                  ┃ Average Score ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ audit_decision_correct  │ 0.90          │
│ audit_criteria_accuracy │ 0.95          │
│ extraction_accuracy     │ 0.85          │
└─────────────────────────┴───────────────┘
```

## Langfuse Features

### Viewing Traces

1. Go to http://localhost:3200
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

### Modifying Audit Criteria

To change audit rules, edit the prompts in `src/agent_sdk/agents/receipt_inspection.py`:

```python
# Example: Change the amount threshold from $50 to $100
audit_prompt = """...
2. AMOUNT_OVER_LIMIT: The total amount exceeds $100  # Changed from $50
..."""
```

Or add new criteria:

```python
# Example: Add a new criterion for weekend expenses
class AuditDecision(BaseModel):
    # ... existing fields ...
    weekend_expense: bool = Field(
        description="True if the expense occurred on a weekend"
    )
```

### Adding New Metrics

Create a new metric in `src/agent_sdk/evals/metrics.py`:

```python
class CustomReceiptMetric(Metric):
    def __init__(self):
        super().__init__(name="custom_metric", threshold=0.8)

    async def evaluate(self, audit_decision, ground_truth):
        # Your evaluation logic for audit decisions
        score = ...
        explanation = ...
        passed = score >= self.threshold
        return score, explanation, passed
```

Add to evaluation script in `examples/run_receipt_evaluation.py`:

```python
metrics = [
    AuditDecisionMetric(),
    AuditCriteriaMetric(),
    CustomReceiptMetric(),  # Add your metric
]
```

### Adding Test Cases

Edit `data/datasets/receipt_test_cases.json`:

```json
{
  "id": "receipt_011",
  "receipt_id": "rec_your_test",
  "image_path": "data/images/your_receipt.jpg",
  "description": "Description of the test case",
  "ground_truth": {
    "details": {
      "merchant": "Merchant Name",
      "total": "99.99",
      ...
    },
    "audit_decision": {
      "not_travel_related": false,
      "amount_over_limit": true,
      "math_error": false,
      "handwritten_x": false,
      "needs_audit": true,
      "reasoning": "Expected reasoning..."
    }
  }
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

### Why Vision + Text (Two-Step Process)?
The receipt inspection agent uses a two-step process:
1. **Vision API** extracts structured data from receipt images
2. **Text-based LLM** makes audit decisions based on extracted data

This approach:
- Separates concerns (extraction vs. decision-making)
- Enables easier debugging (can examine extracted data)
- Allows for different evaluation metrics at each stage
- Mirrors real-world workflows (OCR → business logic)

Alternative: End-to-end vision model making decisions directly could reduce latency but sacrifices interpretability.

### Why These Specific Audit Criteria?
The four criteria (travel-related, amount limit, math errors, handwritten marks) are:
- **Business-aligned**: Map directly to real expense validation needs
- **Measurable**: Clear pass/fail evaluation
- **Diverse**: Test different capabilities (classification, arithmetic, OCR)
- **Representative**: Cover common edge cases in expense processing

### Why Async/Await?
- Enables concurrent API calls during evaluation
- Better performance when processing multiple test cases
- Prepares codebase for production-scale concurrent requests
- Critical for batch processing of receipt images

### Why Self-Hosted Langfuse?
- Complete data privacy (important for financial documents)
- No external dependencies for tracing
- Customizable retention and storage
- Free for unlimited usage

### Why Multiple Evaluation Metrics?
- **Audit Decision Correctness**: The ultimate business outcome
- **Audit Criteria Accuracy**: Diagnoses where the system fails
- **Extraction Accuracy**: Identifies OCR/vision issues

This layered approach helps pinpoint whether failures are due to:
1. Poor vision/extraction
2. Faulty business logic
3. Edge cases not covered in prompts

### Why Structured Test Cases?
- Version control for test data (Git-friendly JSON)
- Easy to review and update with domain experts
- Shareable across team (no proprietary formats)
- Foundation for regression testing
- Enables A/B testing of different prompts/models

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
- [OpenAI Cookbook: Eval-Driven System Design](https://cookbook.openai.com/examples/partners/eval_driven_system_design/receipt_inspection)
- [Langfuse Docs](https://langfuse.com/docs)
- [Anthropic API Reference](https://docs.anthropic.com/)
- [Claude Vision API Guide](https://docs.anthropic.com/claude/docs/vision)
- [Building Eval Systems (Lenny's Newsletter)](https://www.lennysnewsletter.com/p/building-eval-systems-that-improve)

### Related Projects
- [Langfuse Python SDK](https://github.com/langfuse/langfuse-python)
- [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)
- [OpenAI Cookbook](https://github.com/openai/openai-cookbook)

### Learning Resources
- [AI Evals Course by Hamel & Shreya](https://maven.com/parlance-labs/evals)
- [LLM Evaluation Guide](https://www.oreilly.com/library/view/building-llm-powered/9781098150228/)
- [Receipt Handwriting Detection Dataset](https://universe.roboflow.com/newreceipts/receipt-handwriting-detection) (CC BY 4.0)

## Contributing

Contributions are welcome! Areas for improvement:

- **Receipt-specific enhancements**:
  - Support for more receipt formats (European, Asian receipts)
  - Multi-page receipt handling
  - Receipt image preprocessing (rotation, denoising)
  - Integration with OCR services (Textract, Azure Form Recognizer)

- **Evaluation improvements**:
  - Additional audit criteria (merchant allowlists, category limits)
  - Business metric tracking (audit rate vs. accuracy trade-off)
  - A/B testing framework for prompt variations
  - Regression detection

- **General enhancements**:
  - Batch receipt processing pipeline
  - Real-time monitoring dashboards
  - CI/CD pipeline examples
  - Production deployment guides (Docker, Kubernetes)
  - Cost optimization strategies

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Receipt inspection use case based on [OpenAI's Eval-Driven System Design Cookbook](https://cookbook.openai.com/examples/partners/eval_driven_system_design/receipt_inspection)
- Eval-driven methodology inspired by [Hamel Husain](https://twitter.com/HamelHusain) and [Shreya Shankar](https://twitter.com/sh_reya)'s work on LLM evaluations
- Receipt images dataset from [Roboflow Receipt Handwriting Detection](https://universe.roboflow.com/newreceipts/receipt-handwriting-detection) (CC BY 4.0)
- Built with [Anthropic's Claude](https://www.anthropic.com/claude)
- Observability powered by [Langfuse](https://langfuse.com/)

---

**Questions or Issues?**

Open an issue on GitHub or reach out to the maintainers.

**Happy Building!** 🚀
