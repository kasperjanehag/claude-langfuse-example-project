# LLM Agent Template

A starter template for building LLM-powered agents using OpenAI structured outputs, Pydantic models, and Langfuse observability.

## What This Template Provides

This template demonstrates best practices for building LLM agents:

1. **OpenAI Structured Outputs**: Use Pydantic models to get reliable, typed responses from LLMs
2. **Langfuse Observability**: Track all LLM calls, prompts, and responses in one place
3. **Pydantic Models**: Type-safe data models for inputs, outputs, and LLM responses
4. **Configuration Management**: Environment-based config using Pydantic Settings
5. **Error Handling**: Proper error handling and logging patterns
6. **Project Structure**: Clean, modular code organization

## Quick Start

### Prerequisites

1. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com)

2. **Langfuse** (for observability):
   ```bash
   docker compose up -d
   # Visit http://localhost:3000 to get API keys
   ```

3. **Environment Variables**:
   Create a `.env` file:
   ```bash
   OPENAI_API_KEY=your_openai_key_here
   OPENAI_BASE_URL=https://api.openai.com/v1
   OPENAI_MODEL=gpt-4o

   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=http://localhost:3000
   ```

4. **Install Dependencies**:
   ```bash
   # Using UV (recommended)
   uv pip install -e .

   # Or using pip
   pip install -e .
   ```

### Running the Example

```bash
python examples/run_example.py
```

This will:
1. Load example items from `data/inputs/example_items.json`
2. Process them using an LLM with structured outputs
3. Save results to `data/outputs/`
4. Track everything in Langfuse at http://localhost:3000

## Project Structure

```
src/agent_sdk/
├── models/
│   ├── domain_models.py      # Your domain models (customize these!)
│   └── llm_responses.py      # Pydantic models for LLM responses
├── agents/
│   └── example_llm_agent.py  # Example agent showing patterns
└── utils/
    ├── config.py              # Configuration management
    └── langfuse_check.py      # Langfuse connectivity check

data/
├── inputs/                    # Input data files
│   └── example_items.json    # Example input data
└── outputs/                   # Generated outputs

examples/
└── run_example.py            # Example script
```

## Key Concepts

### 1. OpenAI Structured Outputs

Instead of parsing JSON from LLM responses manually:

```python
# ❌ Old way - fragile
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}]
)
result = json.loads(response.choices[0].message.content)  # Can fail!
```

Use structured outputs with Pydantic:

```python
# ✅ New way - type-safe
from pydantic import BaseModel, Field

class AnalysisResponse(BaseModel):
    summary: str = Field(description="Brief summary")
    confidence: float = Field(description="Confidence 0-1")

response = client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format=AnalysisResponse  # Enforces structure!
)
result: AnalysisResponse = response.choices[0].message.parsed
```

### 2. Langfuse Observability

Track all LLM interactions automatically:

```python
from langfuse.decorators import observe, langfuse_context

@observe(name="my_operation")
def process_item(item):
    # Automatically tracked in Langfuse
    result = llm_call(item)

    # Add custom metadata
    langfuse_context.update_current_observation(
        metadata={"item_id": item.id}
    )
    return result
```

View all traces at: http://localhost:3000/traces

### 3. Pydantic Models

Define your data models once, get:
- Type checking
- Validation
- JSON serialization/deserialization
- Auto-generated JSON schemas for LLMs

```python
from pydantic import BaseModel, Field

class InputItem(BaseModel):
    id: str
    content: str
    metadata: dict = {}
```

## Customizing for Your Use Case

### 1. Define Your Domain Models

Edit `src/agent_sdk/models/domain_models.py`:
- Replace `InputItem`, `ProcessedItem` with your models
- Add fields specific to your domain

### 2. Define LLM Response Structures

Edit `src/agent_sdk/models/llm_responses.py`:
- Create Pydantic models for what you want the LLM to return
- Use `Field(description=...)` to guide the LLM

### 3. Create Your Agent

Copy `src/agent_sdk/agents/example_llm_agent.py`:
- Update prompts for your task
- Implement your business logic
- Use `@observe` decorator for Langfuse tracking

### 4. Create Your Pipeline

Copy `examples/run_example.py`:
- Load your data
- Call your agent
- Save results

## Configuration

All configuration is in `src/agent_sdk/utils/config.py`:

```python
class Config(BaseSettings):
    openai_api_key: str
    openai_base_url: str
    model: str
    langfuse_public_key: str
    langfuse_secret_key: str
    # Add your own config fields...
```

Load from environment or `.env` file automatically.

## Best Practices

### Error Handling

Always wrap LLM calls in try/except:

```python
try:
    result = client.beta.chat.completions.parse(...)
except Exception as e:
    # Log to Langfuse
    langfuse_context.update_current_observation(
        metadata={"error": str(e)}
    )
    # Handle error
    return None
```

### Prompt Engineering

Use the Field descriptions - the LLM sees them:

```python
class Response(BaseModel):
    category: str = Field(
        description="Primary category: tech, business, or personal"
    )
    # LLM will see this description and follow it!
```

### Testing

Test with Langfuse:
1. Run your agent
2. Check Langfuse UI for traces
3. Verify prompts, responses, metadata
4. Use generation_id to link related operations

## Observability

### Langfuse Features

- **Traces**: See all LLM calls and their hierarchy
- **Prompts**: Version and track prompts
- **Scores**: Add quality scores to responses
- **Datasets**: Create test datasets
- **Analytics**: Cost, latency, token usage

### Adding Metadata

```python
langfuse_context.update_current_observation(
    metadata={
        "user_id": "user-123",
        "version": "v2",
        "custom_field": "value"
    }
)
```

### Searching Traces

Use generation_id to group related operations:
```python
generation_id = f"batch_{datetime.now()}"
for item in items:
    process(item, generation_id=generation_id)
```

Search in Langfuse UI: `metadata.generation_id: batch_20250122`

## Resources

- [OpenAI Structured Outputs Docs](https://platform.openai.com/docs/guides/structured-outputs)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Langfuse Documentation](https://langfuse.com/docs)

## License

MIT
