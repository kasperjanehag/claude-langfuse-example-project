# Two-Stage LLM-Driven Control Generation System

A compliance control generation system that uses OpenAI to transform legal obligations into context-aware, actionable controls through intelligent semantic mapping.

## Overview

This system uses a two-stage LLM-driven approach to generate tailored security and privacy controls:

**Stage 1: Obligations → Control Objectives** (Semantic Mapping Layer)
- LLM analyzes each obligation to understand its semantic intent
- Matches to existing objectives in registry OR generates new objectives
- Supports multi-objective mapping (1 obligation → N objectives)
- Builds a stable, reusable semantic layer

**Stage 2: Objectives + Context → Control Variants → Controls** (Implementation Layer)
- LLM evaluates objectives with company context
- Matches to existing variants in registry OR generates new variants
- Selects appropriate size variant (startup/SME/enterprise)
- Applies jurisdiction-specific requirements
- Generates final controls

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Obligations → Control Objectives              │
│  (Context-less semantic understanding)                  │
│                                                          │
│  LLM Obligation Mapper:                                 │
│  - Analyzes obligation intent                           │
│  - Matches existing objectives OR                       │
│  - Generates new objectives                             │
│  - Auto-adds to registry                                │
└─────────────────────────────────────────────────────────┘
                        ↓
        [Control Objectives Registry]
        (Stable semantic layer - grows over time)
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: Objectives + Context → Control Variants       │
│  (Context-aware implementation selection)               │
│                                                          │
│  LLM Variant Mapper:                                    │
│  - Matches existing variants OR                         │
│  - Generates new variants                               │
│  - Selects size variant                                 │
│  - Applies jurisdiction requirements                    │
│  - Auto-adds to registry                                │
└─────────────────────────────────────────────────────────┘
                        ↓
                   Controls
```

## Key Features

### LLM-Driven Mapping
- **Semantic Understanding**: OpenAI analyzes obligation text to understand true intent, not just keywords
- **Multi-Objective Support**: Complex obligations can map to multiple objectives
- **Automatic Generation**: LLM creates new objectives/variants when no good match exists
- **Deterministic**: Temperature=0 ensures consistent mappings

### Growing Registries
- **Objective Registry** (`data/control_registry/objectives.json`):
  - Stores all control objectives (context-less semantic layer)
  - Grows as LLM encounters new obligation types
  - Becomes more comprehensive over time

- **Variant Registry** (`data/control_registry/control_variants.json`):
  - Stores control implementation variants
  - Each variant has startup/SME/enterprise size options
  - Includes jurisdiction-specific requirements
  - Grows as LLM encounters new implementation needs

### Perfect World End State
Once registries mature:
- New obligations → fast registry lookups (no LLM needed)
- Same obligations always → same objectives (consistency)
- Any company context → deterministic variant selection
- System becomes instant and cost-free

## Key Models

- **Obligation**: Legal/regulatory requirement (simplified: ID, text, framework, domain)
- **ControlObjective**: Context-less semantic abstraction with intent and rationale
- **ControlVariant**: Implementation template with size variants and jurisdiction requirements
- **Control**: Final generated, company-specific control
- **CompanyContext**: Company information for tailoring (size, industry, jurisdictions)

## Quick Start

### Prerequisites

1. **OpenAI Credentials**:
   - Configure in `.env` file:
     - `OPENAI_API_KEY` - Your OpenAI API key
     - `OPENAI_BASE_URL` - API endpoint (defaults to OpenAI public API)
     - `OPENAI_MODEL` - Model to use (defaults to gpt-5-nano-2025-08-07)

2. **Langfuse** (for observability):
   ```bash
   docker compose up -d
   # Get keys from http://localhost:3000
   ```

3. **Environment**:
   ```bash
   # .env file should contain:
   # OPENAI_API_KEY=your_key
   # OPENAI_BASE_URL=https://api.openai.com/v1  (or custom gateway)
   # OPENAI_MODEL=gpt-5-nano-2025-08-07
   # LANGFUSE_PUBLIC_KEY=...
   # LANGFUSE_SECRET_KEY=...
   ```

4. **Dependencies**:
   ```bash
   pip install openai langfuse pandas openpyxl python-dotenv pydantic-settings
   ```

### Running

```bash
python examples/run_control_generation.py
```

This will:
1. **Stage 1**: Load 5 obligations → LLM maps to objectives
2. **Stage 2**: Take objectives + company context → LLM generates variants & controls
3. Save results to `data/obligations/generated_controls/`
4. Update registries with any new objectives/variants
5. Track everything in Langfuse at http://localhost:3000

### What to Expect

First run:
- LLM will likely match some existing objectives
- May generate a few new objectives if obligations are novel
- May generate new variants if implementation needs differ
- Registries will grow

Subsequent runs with same obligations:
- Should mostly match existing objectives (faster, cheaper)
- Registries continue to grow and stabilize

## Example Output

From 5 GDPR obligations:

```
STAGE 1: 5 obligations → 3 unique objectives (with multi-mapping)
STAGE 2: 3 objectives + SME context → 3 controls

Generated Controls:
- CV-FAIR-1-SME: Fairness assessment procedures
- CV-TRANS-1-SME: Privacy notice management system
- CV-PURPOSE-1-SME: Purpose limitation controls

Registry Growth:
- Objectives: 4 (started with 4, no new ones needed)
- Variants: 4 (started with 4, no new ones needed)
```

## Project Structure

```
src/agent_sdk/
├── models/
│   └── compliance.py          # 5 core Pydantic models
├── agents/
│   ├── llm_obligation_mapper.py   # Stage 1: Obligations → Objectives (LLM)
│   ├── llm_variant_mapper.py      # Stage 2: Objectives → Variants (LLM)
│   └── control_generation.py      # Main orchestration
├── registries/
│   ├── objective_registry.py      # Objective storage and management
│   └── variant_registry.py        # Variant storage and management
└── utils/
    ├── config.py                   # Configuration management
    └── langfuse_check.py           # Langfuse connectivity check

data/
├── control_registry/
│   ├── objectives.json         # Control objectives registry (grows over time)
│   └── control_variants.json   # Control variants registry (grows over time)
└── obligations/
    └── Obligations and Controls example.xlsx

docs/
└── FUTURE_CONSIDERATIONS.md    # Future enhancements and design decisions
```

## How It Works

### Stage 1: Obligation → Objectives Mapping

```python
# LLM analyzes obligation
obligation = "Process personal data fairly and transparently"

# LLM prompt includes all existing objectives for context
# LLM decides: Match existing OR generate new

# Result: Maps to 2 existing objectives
objectives = [
    "OBJ-FAIR-1: Fairness in personal data processing",
    "OBJ-TRANS-1: Transparency in data processing"
]

# If new objective needed, LLM generates:
new_objective = {
    "objective_name": "Clear name",
    "description": "What capability must exist",
    "intent": "Why this matters",
    "rationale": "Why this is separate from existing"
}
# Auto-added to registry
```

### Stage 2: Objective + Context → Variants

```python
# LLM evaluates objective with company context
objective = "OBJ-TRANS-1: Transparency in data processing"
context = {
    "employee_count": 250,  # SME
    "jurisdictions": ["SE", "EU"]
}

# LLM decides: Match existing variant OR generate new

# Result: Matches existing variant
variant = "CV-TRANS-1" (has startup/SME/enterprise options)

# Selects SME variant (applies_if: 50 <= employees < 1000)
selected = variant.variants["sme"]

# Applies Swedish jurisdiction requirements
requirements = ["Plain Swedish language", "GDPR Art 12 compliance", ...]

# Builds final control
control = Control(
    control_id="CV-TRANS-1-SME",
    control_name="Privacy notice management system",
    control_description="...",
    expected_evidence="...",
    review_interval="6 months"
)
```

## Configuration

Key settings in `src/agent_sdk/utils/config.py`:

```python
# LLM Configuration
model = "gpt-5-nano-2025-08-07"  # or other OpenAI model
temperature = 0.0  # Deterministic for consistency
openai_base_url = "https://api.openai.com/v1"  # or custom gateway

# Registry Paths
objectives_registry = "data/control_registry/objectives.json"
variants_registry = "data/control_registry/control_variants.json"

# Obligations Source
obligations_excel = "data/obligations/Obligations and Controls example.xlsx"
```

## Observability

All LLM calls and mapping decisions are traced in Langfuse:

- View at: http://localhost:3000
- Search by: `generation_id`
- Traces show:
  - Stage 1 LLM decisions (match vs generate)
  - Stage 2 LLM decisions (match vs generate)
  - Registry lookups and additions
  - Variant selection logic

## Future Enhancements

See `docs/FUTURE_CONSIDERATIONS.md` for detailed discussion of:

- Confidence scoring and thresholds
- Human review workflows
- Registry consolidation and deduplication
- Embedding-based similarity matching
- Historical consistency validation
- Performance optimization (batching, caching)
- Evaluation metrics and quality tracking

## Design Principles

1. **LLM as Decision Maker**: No confidence thresholds in v1 - LLM decides when to match vs generate
2. **Auto-Growing Registries**: New objectives and variants added automatically
3. **Deterministic**: Temperature=0 ensures consistent mappings
4. **Semantic Focus**: Intent-based matching, not keyword matching
5. **Simplicity First**: Complex features (consolidation, review workflows) deferred

## License

[Your license here]
