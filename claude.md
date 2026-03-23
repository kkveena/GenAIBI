# Claude Code instructions for this repository

Use this file as the project-specific coding brief.

## Mission

Build a deterministic Semantic GenAI for BI system where:
- dbt governs business meaning,
- source ingestion supports both JSON+DuckDB and direct SQL,
- the application exposes structured metric queries,
- the LLM narrates grounded results instead of inventing SQL or formulas.

This repo is for a **regulated, accuracy-first** BI workflow. Prioritize correctness, traceability, and maintainability over cleverness.

---

## Product intent

The system must answer questions such as:
- "What was the net exposure for confirmed calls last month?"
- "How many high-risk breaches occurred by month?"
- "Show total margin calls by status."

But the production path must be:
1. map question to governed metric request,
2. run deterministic execution,
3. narrate the grounded result.

Do **not** implement a free-form Text-to-SQL system as the default path.

---

## Architectural guardrails

### Guardrail 1 — dbt is the semantic source of truth
Put business logic in dbt models and semantic YAML.

Do not put business formulas in prompts.
Do not hardcode metric definitions in app code unless they mirror dbt metadata.

### Guardrail 2 — support two source modes
The codebase must support both:
- `json_duckdb`
- `sql_source`

Use a source adapter pattern so the rest of the app is agnostic to the physical source.

### Guardrail 3 — the LLM is not the calculator
The LLM may:
- select from approved metrics,
- select approved dimensions and filters,
- narrate returned results,
- explain which governed metric was used.

The LLM may **not**:
- invent SQL,
- invent formulas,
- infer unknown joins,
- reinterpret numeric results,
- silently repair ambiguous user intent.

### Guardrail 4 — fail closed
When inputs are not grounded in known metrics/dimensions/filters:
- return a validation error, or
- abstain with a clear message.

Never guess.

### Guardrail 5 — build tool calling later, not first
Phase 1 priority is the semantic foundation and deterministic API.
Tool calling is Phase 2.
Evals follow immediately after the first structured tool path works.

---

## Implementation priorities

### Priority 1
Create the repo scaffold and a runnable local development loop.

### Priority 2
Implement the source-to-staging semantic bridge:
- `sources.yml`
- `stg_margin_calls.sql`
- semantic model YAML

### Priority 3
Expose deterministic APIs:
- `GET /health`
- `GET /metrics`
- `GET /dimensions`
- `POST /query-metric`
- `POST /explain-metric`

### Priority 4
Add optional narration behind a feature flag.

### Priority 5
Add tool-calling wrappers and eval harness only after deterministic flow is stable.

---

## Phase 1 data contract

Expected raw fields include:
- `id` or `call_id`
- `acct_id` or `account_id`
- `mc_amt`
- `collateral_val`
- `st_cd`
- `event_ts`

Canonical staged fields must include:
- `call_id`
- `account_id`
- `margin_amount_usd`
- `collateral_amount_usd`
- `status_name`
- `event_at`
- `net_val`

Required status mapping:
- `4 -> CONFIRMED`
- `5 -> PENDING`
- `0 -> CANCELLED`
- fallback `UNKNOWN`

Required formula:
- `net_val = margin_amount_usd - collateral_amount_usd`

---

## Initial governed metrics

Implement these first:

### 1. `net_margin_exposure`
Definition:
- sum of `net_val`
- default filter path will often use `status_name = 'CONFIRMED'`

### 2. `high_risk_breaches`
Definition:
- count distinct `call_id`
- filter `status_name = 'CONFIRMED'`
- filter `margin_amount_usd > 5000000`

### 3. `total_margin_calls`
Definition:
- count distinct `call_id`

Keep the first demo small and reliable.

---

## Repo structure expectations

Prefer this structure unless there is a strong reason to change it:

```text
src/
  api/
  core/
  services/
  adapters/
  llm/
dbt/
  models/
    staging/
    marts/
tests/
evals/
scripts/
```

If you change the structure, update the README in the same commit.

---

## Coding standards

### General
- Python 3.11+
- type hints everywhere practical
- Pydantic for request/response schemas
- small focused modules
- avoid giant files
- avoid hidden global state
- use structured logging

### API
- validate all user inputs
- return deterministic JSON
- provide helpful error messages
- keep route handlers thin
- keep business logic in services

### Data layer
- isolate source adapters behind interfaces
- avoid source-specific branching all over the codebase
- keep staging logic in dbt, not Python, unless absolutely necessary

### LLM layer
- feature-flag all LLM behavior
- keep prompts versioned and explicit
- feed the LLM only grounded context
- require the response to restate the metric and filters used

### Testing
- every new service needs unit tests
- every endpoint needs at least one integration test
- metric logic should have contract tests or fixture-based checks

---

## Definition of done for the first usable slice

A task is not done until:
1. the code runs locally,
2. sample data loads,
3. dbt models build successfully,
4. one governed metric is queryable via API,
5. tests pass,
6. README is updated,
7. there is no hidden business logic in prompts.

---

## Safe defaults

Default to:
- `ENABLE_NARRATION=false`
- `ENABLE_TOOL_CALLING=false`
- `ENABLE_EVALS=false`

The first end-to-end demo must work without any LLM dependency.

---

## Preferred implementation order for Claude Code

When starting from an empty repo, do work in this order:

1. create repo skeleton
2. create `requirements.txt` or `pyproject.toml`
3. create config module and env loading
4. create FastAPI app with `/health`
5. create dbt project skeleton
6. create sample source data
7. create `sources.yml`
8. create `stg_margin_calls.sql`
9. create semantic YAML for first metrics
10. create query service and adapter abstraction
11. create `POST /query-metric`
12. add tests
13. add optional narration
14. add eval scaffolding

Do not jump to multi-agent features before step 11 is stable.

---

## Query API contract guidance

Prefer a structured request such as:

```json
{
  "metric": "net_margin_exposure",
  "grain": "month",
  "filters": {
    "status_name": "CONFIRMED"
  },
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

Response should contain:
- metric name
- applied filters
- grain
- time window
- rows or scalar result
- lineage metadata where practical
- optional narration only if enabled

---

## What not to do

Do not:
- build raw Text-to-SQL as the main interface
- let the LLM generate production SQL unchecked
- mix business logic into prompt templates
- hide important transformations in Python notebooks only
- over-design the eval framework before there is a stable metric query path
- introduce unnecessary frameworks too early

---

## Future phases

### Phase 2
Add tool calling.

Recommended tools:
- `list_metrics`
- `list_dimensions`
- `query_metric`
- `get_dimension_values`
- `explain_metric`

### Phase 3
Add evals.

Recommended eval categories:
- metric selection correctness
- filter correctness
- grain correctness
- abstention correctness
- result fidelity
- narrative faithfulness

### Phase 4
Add richer BI integrations and dashboard embedding.

---

## Human collaboration expectations

When working in Claude Code:
- explain the plan before large edits,
- make changes in small verifiable increments,
- run tests after meaningful edits,
- summarize exactly what changed,
- call out assumptions explicitly,
- flag blockers instead of guessing.

---

## Project thesis to preserve

The core thesis of this repo is:

**Move meaning and math into governed data definitions first. Add LLM reasoning, tool calling, and evals on top of that foundation.**

If a proposed change weakens that principle, do not implement it without explicit approval.
