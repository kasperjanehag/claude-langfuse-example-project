# System Design: Two-Stage LLM-Driven Control Generation System

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Data Structures](#data-structures)
4. [Tech Stack](#tech-stack)
5. [Two-Stage Flow](#two-stage-flow)
6. [Cybersecurity Examples](#cybersecurity-examples)
7. [Registry System](#registry-system)
8. [LLM Integration](#llm-integration)
9. [Observability](#observability)
10. [API Reference](#api-reference)

## Overview

The Two-Stage LLM-Driven Control Generation System transforms compliance obligations into actionable, context-aware security controls through intelligent semantic mapping. The system uses large language models to understand the semantic intent of obligations and generate appropriate controls tailored to company context.

### Key Principles

1. **Semantic Understanding**: LLMs analyze obligation text to understand true intent, not just keywords
2. **Two-Stage Separation**: Context-less semantic layer (Stage 1) separated from context-aware implementation (Stage 2)
3. **Growing Knowledge**: Registries grow over time, moving toward deterministic lookups
4. **Multi-Mapping Support**: One obligation can map to multiple objectives; multiple obligations can consolidate into one control
5. **Auto-Generation**: LLM decides when to match existing or generate new objectives/variants

### Perfect World End State

As registries mature:
- **Fast**: New obligations → instant registry lookups (no LLM needed)
- **Consistent**: Same obligations → always same objectives
- **Deterministic**: Any company context → predictable variant selection
- **Cost-Effective**: System becomes instant and near-zero marginal cost

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: Compliance Obligations                                  │
│  (Legal/regulatory requirements from frameworks)                │
│                                                                  │
│  Example:                                                       │
│  - SOC 2: "Implement logical access controls"                  │
│  - NIST: "Establish incident response capability"              │
│  - ISO 27001: "Implement vulnerability management"             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Obligations → Control Objectives                      │
│  (Context-less semantic understanding)                          │
│                                                                  │
│  Component: LLMObligationMapper                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Load all existing objectives from registry          │  │
│  │  2. Build prompt with obligation + existing objectives  │  │
│  │  3. LLM analyzes semantic intent                        │  │
│  │  4. LLM decides: MATCH existing OR GENERATE new         │  │
│  │  5. Auto-add new objectives to registry                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  LLM Decision Logic:                                            │
│  - Analyze: What capability must exist to satisfy obligation?  │
│  - Match: Do any existing objectives cover this intent?        │
│  - Generate: If no match, create new context-less objective    │
│  - Multi-map: One obligation can map to N objectives           │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Control Objectives   │
                │  Registry (JSON)      │
                │                       │
                │  Stable semantic      │
                │  layer that grows     │
                │  over time            │
                └───────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: Objectives + Context → Control Variants → Controls    │
│  (Context-aware implementation selection)                       │
│                                                                  │
│  Component: LLMVariantMapper                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Load existing variants from registry (by domain)    │  │
│  │  2. Build prompt with objective + context + variants    │  │
│  │  3. LLM evaluates implementation needs                  │  │
│  │  4. LLM decides: MATCH existing OR GENERATE new variant │  │
│  │  5. Auto-add new variants to registry                   │  │
│  │  6. Select size-appropriate variant (startup/SME/ent)   │  │
│  │  7. Apply jurisdiction-specific requirements            │  │
│  │  8. Build final control                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Context Inputs:                                                │
│  - Company size (employee_count)                                │
│  - Industry                                                     │
│  - Jurisdictions (US, EU, etc.)                                 │
│  - Risk appetite (Low/Medium/High)                              │
│  - Compliance maturity (Initial/Developing/Managed/Optimized)   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Control Variants     │
                │  Registry (JSON)      │
                │                       │
                │  Implementation       │
                │  templates with       │
                │  size variants        │
                └───────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: Generated Controls                                     │
│  (Company-specific, actionable controls)                        │
│                                                                  │
│  Includes:                                                      │
│  - Control ID (CV-ACCESSCTRL-1-SME)                            │
│  - Control name and description                                │
│  - Linked obligations                                           │
│  - Expected evidence                                            │
│  - Review interval                                              │
│  - Impact level                                                 │
│  - Jurisdiction-specific requirements                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Structures

### Core Pydantic Models

All data structures use Pydantic v2 for validation and serialization.

#### 1. Obligation

**Purpose**: Represents a legal/regulatory requirement from a compliance framework.

```python
from pydantic import BaseModel, Field
from typing import Optional

class Obligation(BaseModel):
    """
    A compliance obligation from a regulatory framework.

    Example (Cybersecurity):
    - Framework: SOC 2 Type II
    - Obligation: "The entity implements controls to prevent or
                   detect and act upon the introduction of
                   unauthorized or malicious software"
    """
    obligation_id: str = Field(
        description="Unique identifier (e.g., 'OBL-SOC2-CC6.1')"
    )
    obligation: str = Field(
        description="Full text of the obligation"
    )
    framework_source: str = Field(
        description="Source framework (e.g., 'SOC 2', 'NIST CSF', 'ISO 27001')"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Domain/category (e.g., 'Access Control', 'Incident Response')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "obligation_id": "OBL-SOC2-CC6.1",
                "obligation": "The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software to meet the entity's objectives",
                "framework_source": "SOC 2 Type II - CC6.1",
                "domain": "Logical Access"
            }
        }
```

**Storage**: Typically loaded from Excel/CSV files or compliance databases.

#### 2. ControlObjective

**Purpose**: Context-less semantic abstraction representing what operational capability must exist.

```python
from typing import List, Optional

class ControlObjective(BaseModel):
    """
    Context-less semantic abstraction of what must be achieved.

    Key Properties:
    - Reusable across different companies
    - Framework-agnostic
    - Describes capability, not implementation
    - Contains semantic intent and rationale

    Example (Cybersecurity):
    Instead of: "Implement antivirus for Windows endpoints"
    Use: "Malware prevention and detection capability"
    """
    objective_id: str = Field(
        description="Unique identifier (e.g., 'OBJ-MALWARE-1')"
    )
    objective_name: str = Field(
        description="Clear, reusable name"
    )
    description: str = Field(
        description="What systematic capability this establishes"
    )
    domain: str = Field(
        description="Security domain (e.g., 'Endpoint Security', 'Network Security')"
    )
    intent: Optional[str] = Field(
        default=None,
        description="Why this objective matters from control perspective"
    )
    linked_obligation_ids: List[str] = Field(
        default_factory=list,
        description="Obligations that map to this objective"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Why this exists as separate objective (LLM-generated)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "objective_id": "OBJ-MALWARE-1",
                "objective_name": "Malware prevention and detection",
                "description": "Establish systematic capability to prevent malicious software from executing and detect malware that evades prevention",
                "domain": "Endpoint Security",
                "intent": "Protect systems from compromise through malicious software by implementing defense-in-depth controls",
                "linked_obligation_ids": ["OBL-SOC2-CC6.1", "OBL-NIST-PR.DS-5"],
                "rationale": "Fundamental security capability distinct from vulnerability management and access control"
            }
        }
```

**Storage**: `data/control_registry/objectives.json`

**ID Format**: `OBJ-{DOMAIN_PREFIX}-{NUMBER}` (e.g., `OBJ-MALWARE-1`, `OBJ-ACCESSCTRL-2`)

#### 3. ControlVariant

**Purpose**: Implementation template with multiple size-specific variants and jurisdiction requirements.

```python
from typing import Dict, List, Any

class ControlVariant(BaseModel):
    """
    Implementation template for a control objective.

    Key Properties:
    - Contains multiple size variants (startup/SME/enterprise)
    - Each variant has different implementation approaches
    - Includes jurisdiction-specific requirements
    - Reusable across similar contexts

    Example Structure:
    - Base description (applies to all)
    - Startup variant (lightweight, < 50 employees)
    - SME variant (structured, 50-1000 employees)
    - Enterprise variant (comprehensive, 1000+ employees)
    - Jurisdiction requirements (US, EU, etc.)
    """
    variant_id: str = Field(
        description="Unique identifier (e.g., 'CV-MALWARE-1')"
    )
    objective_id: str = Field(
        description="Which objective this implements"
    )
    variant_name: str = Field(
        description="Implementation name"
    )
    base_description: str = Field(
        description="Core control description (applies to all sizes)"
    )
    domain: str = Field(
        description="Security domain"
    )
    variants: List[Dict[str, Any]] = Field(
        description="Size-specific implementation variants"
    )
    jurisdiction_requirements: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Jurisdiction-specific requirements by country/region code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "variant_id": "CV-MALWARE-1",
                "objective_id": "OBJ-MALWARE-1",
                "variant_name": "Endpoint malware protection",
                "base_description": "Deploy and maintain anti-malware solutions on all endpoints with centralized management, real-time scanning, and regular updates",
                "domain": "Endpoint Security",
                "variants": [
                    {
                        "variant_type": "startup",
                        "applies_if": "employee_count < 50",
                        "description_additions": "Deploy commercial endpoint protection (e.g., Microsoft Defender, CrowdStrike) with cloud management console. Configure automatic updates and scanning. Review alerts weekly.",
                        "evidence_requirements": [
                            "Endpoint protection deployment list",
                            "Configuration screenshots",
                            "Weekly alert review logs"
                        ],
                        "review_interval": "12 months"
                    },
                    {
                        "variant_type": "sme",
                        "applies_if": "employee_count >= 50 and employee_count < 1000",
                        "description_additions": "Deploy enterprise EDR solution with SOAR integration. Establish SOC or managed security service for 24/7 monitoring. Implement automated threat hunting and incident response playbooks. Conduct monthly threat intelligence reviews.",
                        "evidence_requirements": [
                            "EDR deployment documentation",
                            "SOC/MSSP service agreement",
                            "Automated playbook configurations",
                            "Monthly threat intelligence reports",
                            "Incident response logs"
                        ],
                        "review_interval": "6 months"
                    },
                    {
                        "variant_type": "enterprise",
                        "applies_if": "employee_count >= 1000",
                        "description_additions": "Deploy multi-layered malware protection including EDR, network sandboxing, email gateway protection, and application whitelisting. Establish 24/7 SOC with dedicated threat hunting team. Integrate with SIEM for correlation. Conduct continuous threat intelligence analysis and adversary simulation exercises.",
                        "evidence_requirements": [
                            "Comprehensive security architecture documentation",
                            "EDR/XDR platform deployment records",
                            "SOC operating procedures",
                            "Threat hunting reports",
                            "SIEM integration documentation",
                            "Adversary simulation exercise reports",
                            "Quarterly executive security reports"
                        ],
                        "review_interval": "3 months"
                    }
                ],
                "jurisdiction_requirements": {
                    "US": [
                        "Maintain evidence of malware protection for CMMC/DFARS compliance",
                        "Support eDiscovery requirements under FRCP"
                    ],
                    "EU": [
                        "Ensure EDR solution complies with GDPR data protection requirements",
                        "Document processing of endpoint data under Article 30 GDPR"
                    ]
                }
            }
        }
```

**Storage**: `data/control_registry/control_variants.json`

**ID Format**: `CV-{OBJECTIVE_ID}-{NUMBER}` (e.g., `CV-MALWARE-1`, `CV-MALWARE-2`)

#### 4. Control

**Purpose**: Final generated, company-specific control ready for implementation.

```python
class Control(BaseModel):
    """
    Final generated control tailored to company context.

    This is the output of Stage 2 after:
    - Selecting appropriate size variant
    - Applying jurisdiction requirements
    - Linking to source obligations
    """
    control_id: str = Field(
        description="Unique identifier including size (e.g., 'CV-MALWARE-1-SME')"
    )
    control_name: str = Field(
        description="Control name"
    )
    control_description: str = Field(
        description="Complete control description with size variant and jurisdiction requirements"
    )
    linked_obligation_ids: str = Field(
        description="Semicolon-separated obligation IDs (e.g., 'OBL-SOC2-CC6.1; OBL-NIST-PR.DS-5')"
    )
    domain: str = Field(
        description="Security domain"
    )
    expected_evidence: Optional[str] = Field(
        default=None,
        description="Semicolon-separated evidence requirements"
    )
    review_interval: str = Field(
        default="12 months",
        description="How often to review (e.g., '3 months', '6 months')"
    )
    impact: str = Field(
        default="Medium",
        description="Impact level: Critical, High, Medium, Low"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "control_id": "CV-MALWARE-1-SME",
                "control_name": "Endpoint malware protection",
                "control_description": "Deploy and maintain anti-malware solutions on all endpoints...\n\nDeploy enterprise EDR solution with SOAR integration...\n\nJurisdiction-specific requirements:\n- US: Maintain evidence of malware protection for CMMC/DFARS compliance\n- EU: Ensure EDR solution complies with GDPR data protection requirements",
                "linked_obligation_ids": "OBL-SOC2-CC6.1; OBL-NIST-PR.DS-5",
                "domain": "Endpoint Security",
                "expected_evidence": "EDR deployment documentation; SOC/MSSP service agreement; Automated playbook configurations; Monthly threat intelligence reports; Incident response logs",
                "review_interval": "6 months",
                "impact": "Critical"
            }
        }
```

**Storage**: Generated files in `data/obligations/generated_controls/` with format `{generation_id}.json`

#### 5. CompanyContext

**Purpose**: Company information used for tailoring controls.

```python
class CompanyContext(BaseModel):
    """
    Company-specific context for control generation.

    This drives Stage 2 variant selection and jurisdictional requirements.
    """
    company_name: str = Field(
        description="Company name"
    )
    employee_count: int = Field(
        description="Number of employees (drives size variant selection)"
    )
    industry: str = Field(
        description="Industry sector (e.g., 'Technology', 'Healthcare', 'Finance')"
    )
    jurisdictions: List[str] = Field(
        description="List of applicable jurisdictions (e.g., ['US', 'EU', 'UK'])"
    )
    risk_appetite: str = Field(
        description="Risk appetite: Low, Medium, High"
    )
    compliance_maturity: str = Field(
        description="Maturity level: Initial, Developing, Managed, Optimized"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "company_name": "SecureTech Inc",
                "employee_count": 350,
                "industry": "SaaS Security",
                "jurisdictions": ["US", "EU"],
                "risk_appetite": "Low",
                "compliance_maturity": "Developing"
            }
        }
```

**Size Thresholds**:
- **Startup**: `employee_count < 50`
- **SME**: `50 <= employee_count < 1000`
- **Enterprise**: `employee_count >= 1000`

## Tech Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.9+ | Core implementation language |
| **Data Validation** | Pydantic | 2.x | Data models and validation |
| **LLM Provider** | OpenAI API | Latest | Semantic mapping and generation |
| **Observability** | Langfuse | 3.x | LLM call tracing and monitoring |
| **Storage** | JSON files | - | Registry persistence |
| **Configuration** | pydantic-settings | 2.x | Environment configuration |
| **Data Loading** | pandas + openpyxl | Latest | Excel obligation loading |

### Dependencies

```toml
# pyproject.toml
[project]
dependencies = [
    "openai>=1.0.0",           # OpenAI API client
    "langfuse>=3.0.0",         # Observability and tracing
    "pydantic>=2.0.0",         # Data validation
    "pydantic-settings>=2.0.0", # Configuration management
    "pandas>=2.0.0",           # Data manipulation
    "openpyxl>=3.0.0",         # Excel file reading
    "python-dotenv>=1.0.0",    # Environment variable loading
]
```

### Infrastructure

```yaml
# docker-compose.yml
services:
  langfuse-server:
    image: langfuse/langfuse:3
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
      - NEXTAUTH_SECRET=mysecret
      - SALT=mysalt
      - NEXTAUTH_URL=http://localhost:3000

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=postgres
```

### Configuration

```python
# src/agent_sdk/utils/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Config(BaseSettings):
    """Application configuration from environment variables."""

    # OpenAI Configuration
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        alias="OPENAI_BASE_URL"
    )
    model: str = Field(
        default="gpt-4o-mini",
        alias="OPENAI_MODEL"
    )

    # Langfuse Configuration
    langfuse_public_key: str = Field(alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field(alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(
        default="http://localhost:3000",
        alias="LANGFUSE_HOST"
    )

    # Registry Paths
    objectives_registry_path: str = Field(
        default="data/control_registry/objectives.json"
    )
    variants_registry_path: str = Field(
        default="data/control_registry/control_variants.json"
    )

    # Obligations Source
    obligations_excel_path: str = Field(
        default="data/obligations/Obligations and Controls example.xlsx"
    )

    # Output Directory
    generated_controls_dir: str = Field(
        default="data/obligations/generated_controls"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
```

## Two-Stage Flow

### Stage 1: Obligations → Control Objectives

**Component**: `LLMObligationMapper`

**Input**: List of Obligation objects

**Output**: Dict mapping obligation_id → List[ControlObjective]

**Process**:

```python
class LLMObligationMapper:
    def __init__(self, objective_registry: ObjectiveRegistry, config: Config):
        self.objective_registry = objective_registry
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )

    def map_obligation(
        self,
        obligation: Obligation,
        generation_id: Optional[str] = None
    ) -> List[ControlObjective]:
        """
        Map single obligation to objectives using LLM.

        Steps:
        1. Load all existing objectives from registry
        2. Build prompt with obligation + existing objectives
        3. Call LLM to analyze semantic intent
        4. Parse structured JSON response
        5. Process matched objectives (fetch from registry)
        6. Process new objectives (create and add to registry)
        7. Return list of objectives
        """

        # Step 1: Get existing objectives
        existing_objectives = self.objective_registry.get_all()

        # Step 2: Build prompt
        prompt = self._build_mapping_prompt(obligation, existing_objectives)

        # Step 3: Call LLM
        response = self.client.chat.completions.create(
            model=self.config.model,
            max_completion_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Step 4: Parse response
        result = self._parse_llm_response(response.choices[0].message.content)
        # Expected format:
        # {
        #   "analysis": "Brief analysis...",
        #   "matched_objective_ids": ["OBJ-MALWARE-1", "OBJ-ACCESSCTRL-1"],
        #   "new_objectives": [
        #     {
        #       "objective_name": "...",
        #       "description": "...",
        #       "domain": "...",
        #       "intent": "...",
        #       "rationale": "..."
        #     }
        #   ],
        #   "reasoning": "Explanation..."
        # }

        # Step 5: Process matched objectives
        objectives = []
        for obj_id in result.get("matched_objective_ids", []):
            obj = self.objective_registry.get_by_id(obj_id)
            if obj:
                objectives.append(obj)

        # Step 6: Process new objectives
        for new_obj_data in result.get("new_objectives", []):
            new_obj = self._create_and_register_objective(
                new_obj_data,
                obligation,
                generation_id
            )
            objectives.append(new_obj)

        # Step 7: Return
        return objectives
```

**LLM Prompt Structure**:

```
You are a compliance expert mapping legal obligations to control objectives.

CONTROL OBJECTIVES are context-less semantic abstractions that describe
what operational capability needs to exist. They are reusable across
different companies and contexts.

EXISTING OBJECTIVES REGISTRY:
ID: OBJ-MALWARE-1
Name: Malware prevention and detection
Description: Establish systematic capability to prevent malicious software...
Domain: Endpoint Security
Intent: Protect systems from compromise...

[... more objectives ...]

OBLIGATION TO MAP:
ID: OBL-SOC2-CC6.1
Text: The entity implements controls to prevent or detect and act upon
      the introduction of unauthorized or malicious software
Framework: SOC 2 Type II - CC6.1
Domain: Logical Access

YOUR TASK:
1. Analyze what this obligation semantically requires
2. Check if any EXISTING objectives already cover this requirement
   - Match if semantic intent aligns, even if wording differs
   - Be generous with matching - better to reuse than create duplicates
3. If NO existing objective covers a requirement, generate a NEW objective
   - Make it reusable (context-less, focused on capability)
   - Ensure it's distinct from existing objectives

OUTPUT FORMAT (JSON):
{
  "analysis": "Brief analysis of what this obligation requires (2-3 sentences)",
  "matched_objective_ids": ["OBJ-MALWARE-1"],
  "new_objectives": [],
  "reasoning": "Explain your matching decision (2-3 sentences)"
}
```

**Registry Auto-Update**:

When LLM generates new objectives, they are automatically added to the registry:

```python
def _create_and_register_objective(
    self,
    obj_data: Dict,
    source_obligation: Obligation,
    generation_id: Optional[str]
) -> ControlObjective:
    """
    Create new objective and add to registry.

    ID generation:
    - Extract domain prefix (e.g., "Endpoint Security" → "ENDPOINTSEC")
    - Find existing IDs with same prefix
    - Increment: OBJ-ENDPOINTSEC-1, OBJ-ENDPOINTSEC-2, etc.
    """
    domain = obj_data.get("domain", "General")
    new_id = self.objective_registry.generate_next_id(domain)

    objective = ControlObjective(
        objective_id=new_id,
        objective_name=obj_data["objective_name"],
        description=obj_data["description"],
        domain=domain,
        intent=obj_data.get("intent", ""),
        linked_obligation_ids=[source_obligation.obligation_id],
        rationale=obj_data.get("rationale")
    )

    # Auto-add to registry (persists to JSON)
    self.objective_registry.add_objective(objective)

    return objective
```

### Stage 2: Objectives + Context → Control Variants → Controls

**Component**: `LLMVariantMapper`

**Input**:
- List of ControlObjective objects
- CompanyContext object
- Mapping of obligations to objectives (for linking)

**Output**: List of Control objects

**Process**:

```python
class LLMVariantMapper:
    def __init__(self, variant_registry: VariantRegistry, config: Config):
        self.variant_registry = variant_registry
        self.config = config
        self.client = openai.OpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )

    def map_objective_to_variant(
        self,
        objective: ControlObjective,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[ControlVariant]:
        """
        Map objective + context to control variant using LLM.

        Steps:
        1. Load existing variants from registry (filter by domain)
        2. Build prompt with objective + context + existing variants
        3. Call LLM to evaluate implementation needs
        4. Parse structured JSON response
        5. Process matched variant (fetch from registry)
        6. Process new variant (create and add to registry)
        7. Return variant
        """

        # Step 1: Get existing variants
        existing_variants = self.variant_registry.get_by_domain(objective.domain)

        # Step 2: Build prompt
        prompt = self._build_variant_mapping_prompt(
            objective,
            company_context,
            existing_variants
        )

        # Step 3: Call LLM
        response = self.client.chat.completions.create(
            model=self.config.model,
            max_completion_tokens=6000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Step 4: Parse response
        result = self._parse_llm_response(response.choices[0].message.content)
        # Expected format:
        # {
        #   "analysis": "Brief analysis...",
        #   "matched_variant_ids": ["CV-MALWARE-1"],
        #   "new_variants": [
        #     {
        #       "variant_name": "...",
        #       "base_description": "...",
        #       "variants": [
        #         {
        #           "variant_type": "startup",
        #           "applies_if": "employee_count < 50",
        #           "description_additions": "...",
        #           "evidence_requirements": [...],
        #           "review_interval": "12 months"
        #         },
        #         ...
        #       ],
        #       "jurisdiction_requirements": {
        #         "US": [...],
        #         "EU": [...]
        #       }
        #     }
        #   ],
        #   "reasoning": "Explanation..."
        # }

        # Step 5: Process matched variant
        if result.get("matched_variant_ids"):
            variant_id = result["matched_variant_ids"][0]
            return self.variant_registry.get_by_id(variant_id)

        # Step 6: Process new variant
        if result.get("new_variants"):
            return self._create_and_register_variant(
                result["new_variants"][0],
                objective,
                generation_id
            )

        return None

    def select_variant_and_build_control(
        self,
        variant: ControlVariant,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[Control]:
        """
        Select appropriate size variant and build final control.

        Steps:
        1. Evaluate which size variant applies based on employee_count
        2. Apply jurisdiction-specific requirements
        3. Build complete control description
        4. Build evidence requirements string
        5. Create Control object
        """

        # Step 1: Select size variant
        selected_variant = None
        for var in variant.variants:
            applies_if = var.get("applies_if", "")
            if self._evaluate_applies_if(applies_if, company_context):
                selected_variant = var
                break

        if not selected_variant:
            selected_variant = variant.variants[0]  # Default to first

        # Step 2: Apply jurisdiction requirements
        applicable_requirements = []
        for jurisdiction in company_context.jurisdictions:
            if jurisdiction in variant.jurisdiction_requirements:
                reqs = variant.jurisdiction_requirements[jurisdiction]
                applicable_requirements.extend(reqs)

        # Step 3: Build description
        description = variant.base_description
        if selected_variant.get("description_additions"):
            description += f"\n\n{selected_variant['description_additions']}"

        if applicable_requirements:
            description += "\n\nJurisdiction-specific requirements:\n"
            for req in applicable_requirements:
                description += f"- {req}\n"

        # Step 4: Build evidence
        evidence = selected_variant.get("evidence_requirements", [])
        evidence_str = "; ".join(evidence) if evidence else None

        # Step 5: Create Control
        control = Control(
            control_id=f"{variant.variant_id}-{selected_variant['variant_type'].upper()}",
            control_name=variant.variant_name,
            control_description=description,
            linked_obligation_ids="; ".join(linked_obligation_ids),
            domain=variant.domain,
            expected_evidence=evidence_str,
            review_interval=selected_variant.get("review_interval", "12 months"),
            impact="Critical"  # TODO: Derive from obligation impact
        )

        return control

    def _evaluate_applies_if(
        self,
        applies_if: str,
        company_context: CompanyContext
    ) -> bool:
        """
        Evaluate applies_if condition.

        Example: "employee_count < 50" → True/False
        """
        try:
            context_vars = {
                "employee_count": company_context.employee_count or 0
            }
            result = eval(applies_if, {"__builtins__": {}}, context_vars)
            return bool(result)
        except Exception:
            return False
```

## Cybersecurity Examples

### Example 1: Malware Protection

#### Input Obligation

```json
{
  "obligation_id": "OBL-SOC2-CC6.1",
  "obligation": "The entity implements controls to prevent or detect and act upon the introduction of unauthorized or malicious software to meet the entity's objectives",
  "framework_source": "SOC 2 Type II - CC6.1",
  "domain": "Logical Access"
}
```

#### Stage 1 Output: Control Objective

```json
{
  "objective_id": "OBJ-MALWARE-1",
  "objective_name": "Malware prevention and detection",
  "description": "Establish systematic capability to prevent malicious software from executing on organizational systems and detect malware that evades prevention controls through continuous monitoring and threat intelligence",
  "domain": "Endpoint Security",
  "intent": "Protect systems from compromise through malicious software by implementing defense-in-depth controls including prevention, detection, and response capabilities",
  "linked_obligation_ids": ["OBL-SOC2-CC6.1", "OBL-NIST-PR.DS-5", "OBL-ISO27001-A.12.2.1"],
  "rationale": "Fundamental security capability distinct from vulnerability management (which addresses software flaws) and access control (which addresses authentication/authorization). Malware protection specifically addresses malicious code introduction and execution."
}
```

#### Stage 2 Input: Company Context

```json
{
  "company_name": "SecureTech Inc",
  "employee_count": 350,
  "industry": "SaaS Security",
  "jurisdictions": ["US", "EU"],
  "risk_appetite": "Low",
  "compliance_maturity": "Developing"
}
```

#### Stage 2 Output: Generated Control (SME Variant)

```json
{
  "control_id": "CV-MALWARE-1-SME",
  "control_name": "Endpoint malware protection",
  "control_description": "Deploy and maintain anti-malware solutions on all endpoints with centralized management, real-time scanning, and regular updates.\n\nDeploy enterprise EDR solution with SOAR integration. Establish SOC or managed security service for 24/7 monitoring. Implement automated threat hunting and incident response playbooks. Conduct monthly threat intelligence reviews.\n\nJurisdiction-specific requirements:\n- US: Maintain evidence of malware protection for CMMC/DFARS compliance if handling CUI\n- US: Support eDiscovery requirements under FRCP for security incident investigations\n- EU: Ensure EDR solution complies with GDPR data protection requirements for endpoint data processing\n- EU: Document processing of endpoint data under Article 30 GDPR (Records of Processing Activities)",
  "linked_obligation_ids": "OBL-SOC2-CC6.1; OBL-NIST-PR.DS-5",
  "domain": "Endpoint Security",
  "expected_evidence": "EDR deployment documentation; SOC/MSSP service agreement; Automated playbook configurations; Monthly threat intelligence reports; Incident response logs; Malware detection and remediation records",
  "review_interval": "6 months",
  "impact": "Critical"
}
```

### Example 2: Access Control

#### Input Obligation

```json
{
  "obligation_id": "OBL-NIST-PR.AC-1",
  "obligation": "Identities and credentials are issued, managed, verified, revoked, and audited for authorized devices, users and processes",
  "framework_source": "NIST Cybersecurity Framework - PR.AC-1",
  "domain": "Identity and Access Management"
}
```

#### Stage 1 Output: Control Objective

```json
{
  "objective_id": "OBJ-ACCESSCTRL-1",
  "objective_name": "Identity lifecycle management",
  "description": "Establish systematic capability to manage the complete lifecycle of digital identities including provisioning, authentication, authorization, modification, and deprovisioning with appropriate audit trails",
  "domain": "Identity and Access Management",
  "intent": "Ensure only authorized individuals and systems have appropriate access to resources through rigorous identity management processes and technical controls",
  "linked_obligation_ids": ["OBL-NIST-PR.AC-1", "OBL-ISO27001-A.9.2.1", "OBL-SOC2-CC6.2"],
  "rationale": "Core IAM capability that underpins all access control mechanisms. Distinct from authentication mechanisms (MFA, SSO) and authorization policies (RBAC, ABAC), this objective focuses on the lifecycle management of identities themselves."
}
```

#### Stage 2 Output: Generated Control (Enterprise Variant)

```json
{
  "control_id": "CV-ACCESSCTRL-1-ENTERPRISE",
  "control_name": "Enterprise identity lifecycle management",
  "control_description": "Implement comprehensive identity lifecycle management system integrated with HR systems, with automated provisioning/deprovisioning, access reviews, and audit capabilities.\n\nDeploy enterprise IAM platform (e.g., Okta, Azure AD) with automated provisioning via SCIM. Integrate with HR system for joiner/mover/leaver workflows. Implement role-based access control (RBAC) framework with formal role definitions. Establish automated access reviews conducted quarterly. Deploy privileged access management (PAM) solution for administrative accounts. Maintain complete audit trail of all identity changes. Conduct annual access recertification campaigns.\n\nJurisdiction-specific requirements:\n- US: Implement controls to support SOX compliance for financial system access\n- US: Maintain audit logs for minimum 7 years per SEC requirements\n- EU: Implement GDPR Article 32 technical measures for identity data protection\n- EU: Support data subject access requests (DSAR) for identity information within 30 days",
  "linked_obligation_ids": "OBL-NIST-PR.AC-1; OBL-ISO27001-A.9.2.1; OBL-SOC2-CC6.2",
  "domain": "Identity and Access Management",
  "expected_evidence": "IAM platform documentation; SCIM integration configuration; HR system integration documentation; RBAC role definition matrix; Quarterly access review reports; PAM solution deployment documentation; Identity change audit logs; Annual recertification campaign results; Data flow diagrams showing identity data processing",
  "review_interval": "3 months",
  "impact": "Critical"
}
```

### Example 3: Vulnerability Management

#### Input Obligation

```json
{
  "obligation_id": "OBL-ISO27001-A.12.6.1",
  "obligation": "Information about technical vulnerabilities of information systems being used shall be obtained in a timely fashion, the organization's exposure to such vulnerabilities evaluated and appropriate measures taken to address the associated risk",
  "framework_source": "ISO 27001:2022 - A.12.6.1",
  "domain": "System Security"
}
```

#### Stage 1 Output: Control Objective

```json
{
  "objective_id": "OBJ-VULN-1",
  "objective_name": "Vulnerability identification and remediation",
  "description": "Establish systematic capability to identify, assess, prioritize, and remediate technical vulnerabilities in organizational systems and applications through continuous scanning, threat intelligence, and coordinated patching processes",
  "domain": "Vulnerability Management",
  "intent": "Reduce attack surface by proactively identifying and remediating security weaknesses before they can be exploited by threat actors",
  "linked_obligation_ids": ["OBL-ISO27001-A.12.6.1", "OBL-NIST-PR.IP-12", "OBL-PCI-DSS-11.2"],
  "rationale": "Distinct from malware protection (which addresses malicious code) and patch management (which is one remediation method). This objective encompasses the complete vulnerability lifecycle from discovery through remediation validation."
}
```

#### Stage 2 Output: Generated Control (Startup Variant)

```json
{
  "control_id": "CV-VULN-1-STARTUP",
  "control_name": "Basic vulnerability management",
  "control_description": "Implement vulnerability scanning and patching processes to identify and remediate security weaknesses in organizational systems.\n\nDeploy cloud-based vulnerability scanner (e.g., Qualys, Tenable Cloud) for weekly authenticated scans of all systems. Subscribe to vulnerability intelligence feeds (NVD, vendor advisories). Establish patching SLA: Critical vulnerabilities within 15 days, High within 30 days, Medium within 60 days. Maintain inventory of all systems and applications. Review scan results monthly and track remediation in ticketing system. Implement automated patching for operating systems where feasible.\n\nJurisdiction-specific requirements:\n- US: Prioritize vulnerabilities in systems containing CUI per NIST SP 800-171\n- EU: Include vulnerability management in GDPR Article 32 security measures documentation",
  "linked_obligation_ids": "OBL-ISO27001-A.12.6.1",
  "domain": "Vulnerability Management",
  "expected_evidence": "Vulnerability scanner deployment documentation; Weekly scan reports; System/application inventory; Patching SLA policy; Monthly vulnerability review meeting minutes; Remediation tracking tickets; Automated patching configuration evidence",
  "review_interval": "12 months",
  "impact": "High"
}
```

### Example 4: Incident Response

#### Input Obligation

```json
{
  "obligation_id": "OBL-NIST-RS-1",
  "obligation": "Response plans (Incident Response and Business Continuity) that address roles, responsibilities, and management commitment are maintained and managed",
  "framework_source": "NIST Cybersecurity Framework - RS.CO-1",
  "domain": "Incident Response"
}
```

#### Stage 1 Output: Control Objective

```json
{
  "objective_id": "OBJ-INCIDENT-1",
  "objective_name": "Incident response capability",
  "description": "Establish systematic capability to detect, analyze, contain, eradicate, and recover from security incidents through documented procedures, trained personnel, and appropriate tooling with continuous improvement through lessons learned",
  "domain": "Incident Response",
  "intent": "Minimize business impact from security incidents through rapid, coordinated response and enable organizational resilience against cyber threats",
  "linked_obligation_ids": ["OBL-NIST-RS-1", "OBL-ISO27001-A.16.1.1", "OBL-SOC2-CC7.4"],
  "rationale": "Comprehensive incident management capability distinct from individual detection controls (SIEM, EDR) and recovery mechanisms (backups, DR). Encompasses people, process, and technology for complete incident lifecycle."
}
```

#### Stage 2 Output: Generated Control (SME Variant)

```json
{
  "control_id": "CV-INCIDENT-1-SME",
  "control_name": "Incident response program",
  "control_description": "Establish formal incident response capability with documented procedures, trained team, and integration with security monitoring tools.\n\nDevelop and maintain incident response plan with defined roles (Incident Commander, Technical Lead, Communications Lead). Establish incident classification framework (P1-Critical, P2-High, P3-Medium, P4-Low). Deploy SOAR platform or ticketing system for incident tracking. Conduct tabletop exercises semi-annually. Establish on-call rotation for security incidents. Integrate with SIEM and EDR tools for automated alert enrichment. Maintain incident response runbooks for common scenarios. Conduct post-incident reviews for all P1/P2 incidents. Report metrics quarterly to senior management.\n\nJurisdiction-specific requirements:\n- US: Ensure breach notification procedures comply with state laws (typically 30-60 days)\n- US: Maintain cyber insurance and coordinate with carrier during incidents\n- EU: Implement GDPR Article 33 breach notification within 72 hours to supervisory authority\n- EU: Maintain breach notification templates and DPA contact information",
  "linked_obligation_ids": "OBL-NIST-RS-1; OBL-ISO27001-A.16.1.1",
  "domain": "Incident Response",
  "expected_evidence": "Incident response plan; Role definitions and assignments; Incident classification framework; SOAR/ticketing system screenshots; Tabletop exercise reports; On-call schedule; SIEM/EDR integration documentation; Incident response runbooks; Post-incident review reports; Quarterly metrics reports to management; Breach notification procedures",
  "review_interval": "6 months",
  "impact": "Critical"
}
```

### Example 5: Multi-Objective Mapping

Some complex obligations map to multiple objectives.

#### Input Obligation

```json
{
  "obligation_id": "OBL-PCI-DSS-3.1",
  "obligation": "Keep cardholder data storage to a minimum by implementing data retention and disposal policies, procedures and processes",
  "framework_source": "PCI DSS 4.0 - Requirement 3.1",
  "domain": "Data Security"
}
```

#### Stage 1 Output: Multiple Objectives

**Objective 1: Data Minimization**
```json
{
  "objective_id": "OBJ-DATAMIN-1",
  "objective_name": "Data minimization and retention",
  "description": "Establish systematic capability to minimize data collection to only what is necessary, enforce retention schedules, and securely dispose of data at end-of-life",
  "domain": "Data Governance",
  "intent": "Reduce data-related risk exposure by limiting the volume and retention period of sensitive data",
  "linked_obligation_ids": ["OBL-PCI-DSS-3.1", "OBL-GDPR-5c", "OBL-CCPA-1798.100"],
  "rationale": "Fundamental data governance capability applicable across all data types, not just PCI cardholder data"
}
```

**Objective 2: Secure Data Disposal**
```json
{
  "objective_id": "OBJ-DISPOSAL-1",
  "objective_name": "Secure data disposal",
  "description": "Establish systematic capability to securely dispose of sensitive data from all media types (electronic, paper, removable media) with appropriate verification and documentation",
  "domain": "Data Security",
  "intent": "Prevent unauthorized data recovery from disposed media through cryptographic erasure, degaussing, or physical destruction",
  "linked_obligation_ids": ["OBL-PCI-DSS-3.1", "OBL-NIST-800-88", "OBL-ISO27001-A.8.10"],
  "rationale": "Technical security control distinct from retention policies (which govern when to dispose) - this addresses how to securely dispose"
}
```

**Result**: One obligation (OBL-PCI-DSS-3.1) maps to two objectives (OBJ-DATAMIN-1 and OBJ-DISPOSAL-1), and each objective will generate its own control in Stage 2.

## Registry System

### ObjectiveRegistry

**Purpose**: Persistent storage and management of control objectives.

**File**: `data/control_registry/objectives.json`

```json
{
  "objectives": [
    {
      "objective_id": "OBJ-MALWARE-1",
      "objective_name": "Malware prevention and detection",
      "description": "...",
      "domain": "Endpoint Security",
      "intent": "...",
      "linked_obligation_ids": ["OBL-SOC2-CC6.1", "OBL-NIST-PR.DS-5"],
      "rationale": "..."
    },
    {
      "objective_id": "OBJ-ACCESSCTRL-1",
      "objective_name": "Identity lifecycle management",
      "description": "...",
      "domain": "Identity and Access Management",
      "intent": "...",
      "linked_obligation_ids": ["OBL-NIST-PR.AC-1"],
      "rationale": "..."
    }
  ]
}
```

**Class Implementation**:

```python
class ObjectiveRegistry:
    """Registry for storing and retrieving control objectives."""

    def __init__(self, registry_path: Optional[str] = None):
        if registry_path is None:
            registry_path = "data/control_registry/objectives.json"
        self.registry_path = Path(registry_path)
        self.objectives: List[ControlObjective] = self._load_objectives()
        self.index: Dict[str, ControlObjective] = {
            obj.objective_id: obj for obj in self.objectives
        }

    def get_all(self) -> List[ControlObjective]:
        """Get all objectives."""
        return self.objectives

    def get_by_id(self, objective_id: str) -> Optional[ControlObjective]:
        """Get objective by ID."""
        return self.index.get(objective_id)

    def get_by_domain(self, domain: str) -> List[ControlObjective]:
        """Get all objectives in a domain."""
        return [obj for obj in self.objectives if obj.domain == domain]

    def add_objective(self, objective: ControlObjective) -> None:
        """Add new objective to registry and persist."""
        self.objectives.append(objective)
        self.index[objective.objective_id] = objective
        self._save_objectives()

    def generate_next_id(self, domain: str) -> str:
        """
        Generate next available objective ID for a domain.

        Example: "Endpoint Security" → "OBJ-ENDPOINTSEC-1"
        """
        domain_prefix = domain.upper().replace(" ", "").replace("-", "")[:12]

        # Find existing IDs with this prefix
        existing_ids = [
            obj.objective_id for obj in self.objectives
            if obj.objective_id.startswith(f"OBJ-{domain_prefix}-")
        ]

        if not existing_ids:
            return f"OBJ-{domain_prefix}-1"

        # Extract numbers and find max
        numbers = []
        for obj_id in existing_ids:
            parts = obj_id.split("-")
            if len(parts) >= 3:
                try:
                    numbers.append(int(parts[-1]))
                except ValueError:
                    continue

        max_num = max(numbers) if numbers else 0
        return f"OBJ-{domain_prefix}-{max_num + 1}"

    def _load_objectives(self) -> List[ControlObjective]:
        """Load objectives from JSON file."""
        if not self.registry_path.exists():
            return []

        with open(self.registry_path, "r") as f:
            data = json.load(f)
            return [ControlObjective(**obj) for obj in data.get("objectives", [])]

    def _save_objectives(self) -> None:
        """Save objectives to JSON file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "objectives": [obj.model_dump() for obj in self.objectives]
        }

        with open(self.registry_path, "w") as f:
            json.dump(data, f, indent=2)
```

### VariantRegistry

**Purpose**: Persistent storage and management of control variants.

**File**: `data/control_registry/control_variants.json`

```json
{
  "variants": [
    {
      "variant_id": "CV-MALWARE-1",
      "objective_id": "OBJ-MALWARE-1",
      "variant_name": "Endpoint malware protection",
      "base_description": "Deploy and maintain anti-malware solutions...",
      "domain": "Endpoint Security",
      "variants": [
        {
          "variant_type": "startup",
          "applies_if": "employee_count < 50",
          "description_additions": "...",
          "evidence_requirements": [...],
          "review_interval": "12 months"
        },
        {
          "variant_type": "sme",
          "applies_if": "employee_count >= 50 and employee_count < 1000",
          "description_additions": "...",
          "evidence_requirements": [...],
          "review_interval": "6 months"
        },
        {
          "variant_type": "enterprise",
          "applies_if": "employee_count >= 1000",
          "description_additions": "...",
          "evidence_requirements": [...],
          "review_interval": "3 months"
        }
      ],
      "jurisdiction_requirements": {
        "US": ["..."],
        "EU": ["..."]
      }
    }
  ]
}
```

**Class Implementation**: Similar to ObjectiveRegistry with methods like `get_by_objective()`, `get_by_domain()`, etc.

## LLM Integration

### OpenAI Client Setup

```python
import openai
from langfuse.decorators import langfuse_context, observe

class LLMObligationMapper:
    def __init__(self, objective_registry: ObjectiveRegistry, config: Config):
        self.client = openai.OpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.config = config

    @observe(name="map_obligation_to_objectives")
    def map_obligation(
        self,
        obligation: Obligation,
        generation_id: Optional[str] = None
    ) -> List[ControlObjective]:
        # Build prompt
        prompt = self._build_mapping_prompt(obligation, existing_objectives)

        # Update Langfuse trace
        langfuse_context.update_current_observation(
            metadata={
                "generation_id": generation_id,
                "obligation_id": obligation.obligation_id,
                "num_existing_objectives": len(existing_objectives),
            }
        )

        # Call OpenAI
        response = self.client.chat.completions.create(
            model=self.config.model,
            max_completion_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract and parse
        response_text = response.choices[0].message.content
        result = self._parse_llm_response(response_text)

        # Process results
        objectives = self._process_mapping_result(result, obligation, generation_id)

        # Update trace with results
        langfuse_context.update_current_observation(
            metadata={
                "num_objectives_mapped": len(objectives),
                "objective_ids": [obj.objective_id for obj in objectives],
            }
        )

        return objectives
```

### Response Parsing

LLM responses may be wrapped in markdown code blocks:

```python
def _parse_llm_response(self, response_text: str) -> Dict:
    """
    Parse JSON response from LLM.

    Handles markdown code blocks:
    ```json
    {...}
    ```
    """
    try:
        # Find JSON in response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            json_text = response_text.strip()

        result = json.loads(json_text)
        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse LLM response as JSON: {e}")
        raise ValueError(f"Invalid JSON response from LLM: {e}")
```

## Observability

### Langfuse Integration

All LLM calls are traced using Langfuse decorators:

```python
from langfuse.decorators import langfuse_context, observe

@observe(name="stage_1_obligations_to_objectives")
def stage_1_map_obligations_to_objectives(
    self,
    obligations: List[Obligation],
    generation_id: Optional[str] = None
) -> Dict[str, List[ControlObjective]]:
    """
    Stage 1: Map obligations to objectives using LLM.

    This function is automatically traced by Langfuse.
    All nested @observe functions are captured as sub-traces.
    """
    logger.info(f"STAGE 1: Mapping {len(obligations)} obligations to objectives")

    # Update trace metadata
    langfuse_context.update_current_observation(
        metadata={
            "generation_id": generation_id,
            "num_obligations": len(obligations),
        }
    )

    # Call LLM mapper (also @observe decorated)
    mapping = self.obligation_mapper.map_obligations_batch(
        obligations,
        generation_id
    )

    # Calculate statistics
    unique_objectives = set()
    for objs in mapping.values():
        unique_objectives.update(obj.objective_id for obj in objs)

    # Update trace with results
    langfuse_context.update_current_observation(
        metadata={
            "num_unique_objectives": len(unique_objectives),
            "total_mappings": sum(len(objs) for objs in mapping.values()),
        }
    )

    return mapping
```

### Trace Hierarchy

```
generate_controls_from_excel (root trace)
├── stage_1_obligations_to_objectives
│   ├── map_obligations_batch
│   │   ├── map_obligation (OBL-SOC2-CC6.1)
│   │   ├── map_obligation (OBL-NIST-PR.AC-1)
│   │   └── map_obligation (OBL-ISO27001-A.12.6.1)
│   └── [Results: 5 obligations → 4 objectives]
└── stage_2_objectives_to_controls
    ├── map_objective_to_variant (OBJ-MALWARE-1)
    ├── select_variant_and_build_control
    ├── map_objective_to_variant (OBJ-ACCESSCTRL-1)
    ├── select_variant_and_build_control
    └── [Results: 4 objectives → 4 controls]
```

### Viewing Traces

1. Navigate to http://localhost:3000
2. Go to "Traces" → "Recent traces"
3. Filter by `generation_id = 'gen_20251021_221940_2c2836'`
4. Click on a trace to see:
   - LLM prompts sent
   - LLM responses received
   - Metadata (obligation IDs, objective IDs, etc.)
   - Timing information
   - Token usage
   - Error logs (if any)

## API Reference

### ControlGenerationAgent

Main orchestration class.

```python
class ControlGenerationAgent:
    """
    Main agent for control generation.

    Orchestrates two-stage LLM-driven system:
    - Stage 1: Obligations → Objectives
    - Stage 2: Objectives + Context → Controls
    """

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize agent with configuration.

        Args:
            config: Application configuration (defaults to Config())
        """

    def generate_controls(
        self,
        obligations: List[Obligation],
        company_context: CompanyContext,
        generation_id: Optional[str] = None
    ) -> List[Control]:
        """
        Generate controls from obligations using two-stage system.

        Args:
            obligations: List of compliance obligations
            company_context: Company context for tailoring
            generation_id: Optional generation ID for tracing

        Returns:
            List of generated Control objects

        Example:
            >>> agent = ControlGenerationAgent()
            >>> obligations = [...]
            >>> context = CompanyContext(
            ...     company_name="SecureTech Inc",
            ...     employee_count=350,
            ...     industry="SaaS",
            ...     jurisdictions=["US", "EU"],
            ...     risk_appetite="Low",
            ...     compliance_maturity="Developing"
            ... )
            >>> controls = agent.generate_controls(obligations, context)
        """

    def generate_controls_from_excel(
        self,
        excel_path: str,
        company_context: CompanyContext,
        generation_id: Optional[str] = None
    ) -> List[Control]:
        """
        Generate controls from obligations in Excel file.

        Args:
            excel_path: Path to Excel file with obligations
            company_context: Company context for tailoring
            generation_id: Optional generation ID for tracing

        Returns:
            List of generated Control objects

        Excel Format:
            Required columns:
            - Obligation ID
            - Obligation
            - Framework/Standard Source
            - Domain (optional)
        """
```

### LLMObligationMapper

Stage 1 mapper.

```python
class LLMObligationMapper:
    """
    Maps obligations to control objectives using LLM reasoning.

    This is Stage 1 of the two-stage system.
    """

    def __init__(
        self,
        objective_registry: ObjectiveRegistry,
        config: Optional[Config] = None
    ):
        """Initialize mapper with registry and config."""

    @observe(name="map_obligation_to_objectives")
    def map_obligation(
        self,
        obligation: Obligation,
        generation_id: Optional[str] = None
    ) -> List[ControlObjective]:
        """
        Map single obligation to objectives using LLM.

        Args:
            obligation: Obligation to map
            generation_id: Optional generation ID for tracing

        Returns:
            List of ControlObjective objects (matched or newly generated)

        Process:
            1. Load existing objectives from registry
            2. Build prompt with obligation + existing objectives
            3. Call LLM to analyze semantic intent
            4. Parse structured JSON response
            5. Fetch matched objectives from registry
            6. Create and register new objectives
            7. Return all objectives
        """

    @observe(name="map_obligations_to_objectives_batch")
    def map_obligations_batch(
        self,
        obligations: List[Obligation],
        generation_id: Optional[str] = None
    ) -> Dict[str, List[ControlObjective]]:
        """
        Map multiple obligations to objectives.

        Args:
            obligations: List of obligations to map
            generation_id: Optional generation ID for tracing

        Returns:
            Dictionary mapping obligation_id → List[ControlObjective]
        """
```

### LLMVariantMapper

Stage 2 mapper.

```python
class LLMVariantMapper:
    """
    Maps control objectives + context to control variants using LLM reasoning.

    This is Stage 2 of the two-stage system.
    """

    def __init__(
        self,
        variant_registry: VariantRegistry,
        config: Optional[Config] = None
    ):
        """Initialize mapper with registry and config."""

    @observe(name="map_objective_to_variant")
    def map_objective_to_variant(
        self,
        objective: ControlObjective,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[ControlVariant]:
        """
        Map objective + context to control variant using LLM.

        Args:
            objective: Control objective to implement
            company_context: Company context for tailoring
            linked_obligation_ids: Obligation IDs this control addresses
            generation_id: Optional generation ID for tracing

        Returns:
            ControlVariant object (matched or newly generated)

        Process:
            1. Load existing variants from registry (filter by domain)
            2. Build prompt with objective + context + variants
            3. Call LLM to evaluate implementation needs
            4. Parse structured JSON response
            5. Fetch matched variant or create new variant
            6. Register new variant to registry
            7. Return variant
        """

    @observe(name="select_variant_and_build_control")
    def select_variant_and_build_control(
        self,
        variant: ControlVariant,
        company_context: CompanyContext,
        linked_obligation_ids: List[str],
        generation_id: Optional[str] = None
    ) -> Optional[Control]:
        """
        Select appropriate size variant and build final control.

        Args:
            variant: ControlVariant with multiple size options
            company_context: Company context
            linked_obligation_ids: Obligation IDs this control addresses
            generation_id: Optional generation ID for tracing

        Returns:
            Control object tailored to company context

        Process:
            1. Evaluate which size variant applies (startup/SME/enterprise)
            2. Apply jurisdiction-specific requirements
            3. Build complete control description
            4. Build evidence requirements string
            5. Create Control object
            6. Return control
        """
```

---

**Document Version**: 1.0
**Last Updated**: 2025-10-21
**Authors**: System Architecture Team
