# Semantic GenAI for BI

Deterministic, audit-ready natural-language business intelligence over margin and risk data.

## 1) Why this project exists

Traditional LLM-to-SQL patterns are powerful but risky for regulated BI because they can:
- guess field names, joins, and filters,
- perform weak or inconsistent calculations,
- answer correctly once and differently the next time,
- make audit and lineage hard.

This project takes a different path:
- **dbt is the semantic source of truth** for metrics, dimensions, aliases, and business logic.
- **Gemini/LLM acts as a reasoning and orchestration layer**, not a free-form SQL writer.
- **DuckDB is optional** and used only when the source is file-native JSON.
- **Direct SQL sourcing is preferred** when a curated consolidated view/table already exists.

Primary KPI: **calculation accuracy with zero-tolerance for hallucination**.

---

## 2) Phase plan

### Phase 1A — Semantic foundation first
Build the governed data contract.

Scope:
- Register raw source in dbt (`sources.yml`)
- Support **two ingestion modes**:
  - `json_duckdb`: raw JSON files queried through DuckDB
  - `sql_source`: curated SQL view/table registered directly in dbt
- Create staging model `stg_margin_calls.sql`
- Cast types, rename cryptic fields, map status codes, and compute `net_val`
- Define semantic model and metrics
- Add dbt tests and example validation queries

Deliverables:
- `sources.yml`
- `stg_margin_calls.sql`
- `margin_risk.yml` or equivalent semantic model YAML
- sample data
- deterministic query endpoint over governed metrics

### Phase 1B — Tool calling
Add a structured interface so the LLM calls approved tools instead of writing raw SQL.

Examples:
- `query_metric(metric, grain, filters, start_date, end_date)`
- `list_metrics()`
- `list_dimensions(metric)`
- `get_dimension_values(dimension)`

### Phase 1C — Eval harness
Add correctness checks before expanding to broader business questions.

Examples:
- golden prompts
- expected metric outputs
- filter correctness
- routing/tool-selection rate
- abstention rate
- narrative quality checks

---

## 3) Architecture

## 3.1 JSON-first path

`Raw JSON -> DuckDB -> dbt source -> dbt staging -> semantic model -> deterministic query tool -> LLM narration`

Use this when the source is still file-native and engineering has not exposed a curated SQL relation.

## 3.2 Direct SQL path

`Consolidated SQL view/table -> dbt source -> dbt staging -> semantic model -> deterministic query tool -> LLM narration`

Use this when a curated enterprise relation already exists.

## 3.3 Design rules

1. The LLM must **never invent formulas**.
2. The LLM must **never guess status code meaning**.
3. The LLM must **never write free-form warehouse SQL in production flow**.
4. All business calculations must live in dbt or approved query tooling.
5. Every answer must be traceable to:
   - a source relation,
   - a dbt model,
   - a governed metric,
   - and eventually an eval result.

---

## 4) Initial business scope

Start with 2-3 metrics only.

Recommended initial metrics:
- `net_margin_exposure`
- `high_risk_breaches`
- `total_margin_calls`

Recommended initial dimensions:
- `event_at` (day/month grain)
- `status_name`
- `account_id`

Illustrative formula:

`net_margin_exposure = SUM(margin_amount_usd - collateral_amount_usd)`

Filtered version for confirmed calls:

`status_name = 'CONFIRMED'`

---

## 5) Field mapping for Phase 1

Raw source fields expected from the current discussion:
- `id` or `call_id`
- `acct_id` or `account_id`
- `mc_amt`
- `collateral_val`
- `st_cd`
- `event_ts`

Canonical staged aliases:
- `call_id`
- `account_id`
- `margin_amount_usd`
- `collateral_amount_usd`
- `status_name`
- `event_at`
- `net_val`

Recommended status mapping:
- `4 -> CONFIRMED`
- `5 -> PENDING`
- `0 -> CANCELLED`
- else `UNKNOWN`

---

## 6) Proposed repository structure

```text
semantic-genai-bi/
├── README.md
├── claude.md
├── .env.example
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes_health.py
│   │   ├── routes_metrics.py
│   │   └── schemas.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── enums.py
│   ├── services/
│   │   ├── metric_service.py
│   │   ├── semantic_registry.py
│   │   └── query_executor.py
│   ├── adapters/
│   │   ├── duckdb_adapter.py
│   │   ├── sql_adapter.py
│   │   └── dbt_adapter.py
│   └── llm/
│       ├── prompt_templates.py
│       └── narration_service.py
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── sources.yml
│   │   ├── staging/
│   │   │   └── stg_margin_calls.sql
│   │   └── marts/
│   │       └── margin_risk.yml
│   └── tests/
├── data/
│   ├── raw/
│   └── sample/
├── evals/
│   ├── golden_queries.yaml
│   └── expected_results/
├── scripts/
│   ├── bootstrap.sh
│   ├── run_local.sh
│   └── seed_sample_data.py
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
```

---

## 7) Recommended implementation approach

### Step 1 — bootstrap the repo
Create:
- Python API skeleton
- dbt project
- sample source data
- config and logging

### Step 2 — implement source abstraction
Support:
- `SOURCE_MODE=json_duckdb`
- `SOURCE_MODE=sql_source`

The rest of the application should not care which physical ingestion mode is used.

### Step 3 — implement staging and semantic files
Create:
- `sources.yml`
- `stg_margin_calls.sql`
- `margin_risk.yml`

Important:
- compute `net_val` in staging or mart
- do not rely on the LLM to derive it ad hoc

### Step 4 — expose deterministic metric API
Phase 1 API should be **structured first**, not NL-first.

Recommended initial endpoints:
- `GET /health`
- `GET /metrics`
- `GET /dimensions`
- `POST /query-metric`
- `POST /explain-metric`

Example request:

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

### Step 5 — add LLM narration only after deterministic execution works
The LLM should receive:
- user question,
- selected metric,
- applied filters,
- returned numeric result,
- and optional chart/table rows.

The LLM should **only narrate** the answer and explain the metric used.

### Step 6 — add tool calling and evals later
After semantics are stable:
- add function-calling/tool-calling
- add an eval harness
- then expand question coverage

---

## 8) Local setup

## 8.1 Prerequisites
- Python 3.11+
- dbt core and the right adapter for your target platform
- DuckDB only if using `json_duckdb`
- a SQL database or warehouse if using `sql_source`

## 8.2 Example setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 8.3 Suggested environment variables

```bash
APP_ENV=dev
LOG_LEVEL=INFO
SOURCE_MODE=json_duckdb
RAW_JSON_GLOB=./data/raw/*.json
SQL_SOURCE_TABLE=vw_margin_transactions_consolidated
DBT_PROJECT_DIR=./dbt
DBT_PROFILES_DIR=./dbt
DEFAULT_TIMEZONE=UTC
LLM_PROVIDER=gemini
ENABLE_NARRATION=false
ENABLE_TOOL_CALLING=false
ENABLE_EVALS=false
```

For direct SQL mode:

```bash
SOURCE_MODE=sql_source
SQL_DSN=postgresql://user:pass@host:5432/dbname
SQL_SOURCE_SCHEMA=risk_ops
SQL_SOURCE_TABLE=vw_margin_transactions_consolidated
```

---

## 9) Validation strategy

### dbt/data validation
- source freshness where applicable
- not-null tests on core identifiers and timestamps
- accepted values for `status_name`
- reconciliation check for `net_val = margin_amount_usd - collateral_amount_usd`

### API validation
- unknown metric should fail fast
- unsupported dimension/grain should fail fast
- invalid filters should fail fast
- missing date range should use safe defaults or return validation errors

### LLM validation
- narration must not change numeric results
- narration must echo the governed metric and filters used
- if query cannot be grounded, the system must abstain

---

## 10) Non-goals for initial build

Do **not** do these in the first coding pass:
- general Text-to-SQL
- autonomous join discovery
- fuzzy schema inference in production path
- wide-open NL questions without a governed metric contract
- full multi-agent orchestration before deterministic metric execution works

---

## 11) Suggested milestone sequence

### Milestone 1
Repo scaffold + config + sample data

### Milestone 2
dbt source + staging model + semantic YAML

### Milestone 3
Deterministic metric API with one metric end to end

### Milestone 4
Add second and third KPIs

### Milestone 5
LLM narration on top of deterministic results

### Milestone 6
Tool calling interface

### Milestone 7
Eval harness

---

## 12) Manager-friendly message

This implementation is intentionally conservative:
- **semantics first**,
- **tool calling second**,
- **evals third**.

That sequencing reduces hallucination risk and makes every later LLM enhancement safer.

---

## 13) Immediate next coding target

Build a minimal but complete vertical slice:
1. Load sample source data
2. Stage and standardize fields in dbt
3. Publish `net_margin_exposure`
4. Query it via API
5. Return a deterministic JSON response
6. Add optional LLM narration behind a feature flag

That is the fastest path to a credible Phase 1 demo.
