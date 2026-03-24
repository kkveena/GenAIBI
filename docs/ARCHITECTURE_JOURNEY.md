# GenAI BI — Architecture Journey

> From raw JSON to governed metrics, narrated by AI.

This document traces the complete data journey in the GenAI BI Semantic Layer — from raw ingestion through deterministic query execution to optional LLM-powered narration.

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1 — Raw Data & DuckDB Ingestion](#phase-1--raw-data--duckdb-ingestion)
3. [Phase 2 — Raw SQL & Staging CTE](#phase-2--raw-sql--staging-cte)
4. [Phase 3 — dbt Semantic Layer](#phase-3--dbt-semantic-layer)
5. [Phase 4 — Request Validation](#phase-4--request-validation)
6. [Phase 5 — Services & Orchestration](#phase-5--services--orchestration)
7. [Phase 6 — Pydantic Models](#phase-6--pydantic-models)
8. [Phase 7 — Narration & LLM Integration](#phase-7--narration--llm-integration)
9. [Phase 8 — Final Result](#phase-8--final-result)
10. [Architecture Diagram](#architecture-diagram)
11. [Core Principles](#core-principles)

---

## Overview

GenAI BI is a **governed semantic layer** for margin-call risk analytics. It ensures every metric result is deterministic, auditable, and traceable — while optionally leveraging an LLM (Google Gemini) for natural-language query translation and result narration.

**Key guarantee:** The LLM never computes numbers. All numeric results come from governed metric definitions executed as deterministic SQL.

---

## Phase 1 — Raw Data & DuckDB Ingestion

### The Starting Point: Raw JSON

The journey begins with raw margin-call transaction data stored as JSON files in `data/raw/`.

```json
{
  "id": "MC-001",
  "acct_id": "ACCT-100",
  "mc_amt": 7500000.00,
  "collateral_val": 5000000.00,
  "st_cd": 4,
  "event_ts": "2025-01-05T10:30:00Z"
}
```

Fields use cryptic abbreviations (`mc_amt`, `st_cd`, `acct_id`) and raw codes (status `4` = CONFIRMED) — typical of upstream source systems.

### DuckDB Adapter

The `DuckDBAdapter` (`src/adapters/duckdb_adapter.py`) loads all JSON files matching a configurable glob pattern into an **in-memory DuckDB** table called `margin_transactions`.

```
JSON files  →  DuckDB (in-memory)  →  margin_transactions table
```

An abstract `BaseSourceAdapter` interface and `AdapterFactory` (`src/adapters/`) enable swapping to a SQL database source without changing any business logic — the application is fully source-agnostic.

| Mode | Adapter | Status |
|------|---------|--------|
| `json_duckdb` | `DuckDBAdapter` | Active (default) |
| `sql_source` | `SQLSourceAdapter` | Stub (Phase 2) |

---

## Phase 2 — Raw SQL & Staging CTE

### From Raw Fields to Business Names

Before any metric query runs, the `QueryExecutor` (`src/services/query_executor.py`) wraps every query with a **staging CTE** that transforms raw fields into clean, typed, business-friendly columns:

```sql
WITH stg_margin_calls AS (
  SELECT
    CAST(id        AS VARCHAR)        AS call_id,
    CAST(acct_id   AS VARCHAR)        AS account_id,
    CAST(mc_amt    AS DECIMAL(18,2))  AS margin_amount_usd,
    CAST(collateral_val AS DECIMAL(18,2)) AS collateral_amount_usd,
    CAST(mc_amt AS DECIMAL(18,2))
      - CAST(collateral_val AS DECIMAL(18,2)) AS net_val,
    CASE
      WHEN st_cd = 4 THEN 'CONFIRMED'
      WHEN st_cd = 5 THEN 'PENDING'
      WHEN st_cd = 0 THEN 'CANCELLED'
      ELSE 'UNKNOWN'
    END AS status_name,
    CAST(event_ts AS TIMESTAMP)       AS event_at
  FROM margin_transactions
)
-- metric query follows here
```

**What this CTE achieves:**

| Transformation | Example |
|----------------|---------|
| Type casting | `mc_amt` → `DECIMAL(18,2)` |
| Alias mapping | `mc_amt` → `margin_amount_usd` |
| Status decoding | `st_cd = 4` → `CONFIRMED` |
| Derived column | `net_val = margin_amount_usd − collateral_amount_usd` |
| Timestamp cast | `event_ts` (string) → `TIMESTAMP` |

This mirrors the dbt staging model exactly, ensuring consistency between the runtime SQL path and the dbt semantic layer.

---

## Phase 3 — dbt Semantic Layer

### dbt as the Source of Truth

The `dbt/` directory contains the **canonical semantic definitions** that the application's in-memory registry mirrors.

### Sources (`dbt/models/sources.yml`)

Declares two raw data sources — one for JSON/DuckDB mode, one for future SQL mode.

### Staging Model (`dbt/models/staging/stg_margin_calls.sql`)

Identical transformation to the runtime CTE — cast, alias, map status codes, compute `net_val`. Column-level tests enforce the data contract:

| Column | Tests |
|--------|-------|
| `call_id` | `not_null`, `unique` |
| `status_name` | `not_null`, `accepted_values: [CONFIRMED, PENDING, CANCELLED, UNKNOWN]` |
| `net_val` | `not_null` |
| `event_at` | `not_null` |

### Semantic Model & Metrics (`dbt/models/marts/margin_risk.yml`)

Defines the governed semantic model and three metrics:

| Metric | Aggregation | Measure | Default Filters |
|--------|-------------|---------|-----------------|
| `net_margin_exposure` | `SUM` | `net_val` | `status_name = CONFIRMED` |
| `high_risk_breaches` | `COUNT_DISTINCT` | `call_id` | `status_name = CONFIRMED`, `margin_amount_usd > $5M` |
| `total_margin_calls` | `COUNT_DISTINCT` | `call_id` | *(none)* |

**Dimensions:** `event_at` (time), `status_name` (categorical), `account_id` (categorical)

---

## Phase 4 — Request Validation

### Fail-Closed by Design

Every incoming request passes through a strict validation chain before any SQL executes. Unknown metrics, invalid grains, or unrecognized filter dimensions are **rejected immediately** — the system never guesses.

```
API Request (Pydantic validation)
       ↓
SemanticRegistry.get_metric()        → KeyError if unknown
       ↓
SemanticRegistry.validate_grain()    → ValueError if invalid
       ↓
SemanticRegistry.validate_filters()  → ValueError if unknown dimension
       ↓
QueryExecutor.execute_metric()       → SQL builds & executes
```

### Validation Examples

| Request | Result |
|---------|--------|
| `metric: "net_margin_exposure"` | Accepted |
| `metric: "unknown_metric"` | Rejected — `404 Not Found` |
| `grain: "week"` | Rejected — `400 Bad Request` (only day/month/year) |
| `filters: {"region": "US"}` | Rejected — `400 Bad Request` (unknown dimension) |

---

## Phase 5 — Services & Orchestration

### Service Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    MetricService (Facade)                 │
│  Orchestrates validation → execution → narration         │
├──────────────┬──────────────┬─────────────┬──────────────┤
│  Semantic    │  Query       │  Narration  │  NL Query    │
│  Registry    │  Executor    │  Service    │  Service     │
├──────────────┼──────────────┼─────────────┼──────────────┤
│ In-memory    │ SQL builder  │ LLM-powered │ NL → metric  │
│ metric/dim   │ + CTE        │ summaries   │ translation  │
│ definitions  │ wrapping     │ (optional)  │ (optional)   │
└──────────────┴──────┬───────┴─────────────┴──────────────┘
                      │
              ┌───────┴───────┐
              │ BaseAdapter   │
              ├───────────────┤
              │ DuckDB / SQL  │
              └───────────────┘
```

### Service Descriptions

| Service | File | Role |
|---------|------|------|
| **MetricService** | `src/services/metric_service.py` | Facade — coordinates all other services. Entry point for API routes. |
| **SemanticRegistry** | `src/services/semantic_registry.py` | In-memory store of metric and dimension definitions (mirrors dbt YAML). Provides validation methods. |
| **QueryExecutor** | `src/services/query_executor.py` | Builds deterministic SQL from metric definitions. Handles aggregation, grain, filters, date ranges, and CTE wrapping. |
| **NarrationService** | `src/llm/narration_service.py` | Feature-flagged LLM narration of query results. Falls back to a deterministic stub when disabled or on error. |
| **NLQueryService** | `src/llm/nl_query_service.py` | Translates natural-language questions into structured metric queries using Gemini. |
| **GeminiClient** | `src/llm/gemini_client.py` | Thin wrapper around Google Generative AI SDK (`gemini-2.0-flash`). |

---

## Phase 6 — Pydantic Models

All request/response contracts are defined as Pydantic models in `src/api/schemas.py`.

### Request Models

| Model | Key Fields | Used By |
|-------|------------|---------|
| `QueryMetricRequest` | `metric`, `grain`, `filters`, `start_date`, `end_date` | `POST /query-metric` |
| `ExplainMetricRequest` | `metric` | `POST /explain-metric` |
| `NLQueryRequest` | `question`, `execute` (bool) | `POST /nl-query` |

### Response Models

| Model | Key Fields | Used By |
|-------|------------|---------|
| `QueryMetricResponse` | `metric`, `grain`, `filters`, `time_window`, `rows`, `lineage`, `narration` | `POST /query-metric` |
| `ExplainMetricResponse` | `metric`, `description`, `formula`, `dimensions`, `default_filters`, `source_model` | `POST /explain-metric` |
| `NLQueryResponse` | `question`, `translated`, `result`, `error` | `POST /nl-query` |
| `MetricListResponse` | `metrics: list[MetricDefinition]` | `GET /metrics` |
| `DimensionListResponse` | `dimensions: list[DimensionDefinition]` | `GET /dimensions` |
| `HealthResponse` | `status`, `version`, `source_mode` | `GET /health` |
| `ErrorResponse` | `error`, `detail` | All error responses |

### Supporting Models

| Model | Purpose |
|-------|---------|
| `QueryResultRow` | Single row: `period` (str) + `value` (float) |
| `LineageInfo` | Full audit trail: source, staging model, metric, aggregation, filters, grain, time window |
| `MetricDefinition` | Metric metadata for listing endpoints |
| `DimensionDefinition` | Dimension metadata for listing endpoints |

### Internal Dataclasses (`src/services/semantic_registry.py`)

| Class | Purpose |
|-------|---------|
| `MetricDef` | Internal metric definition with `name`, `description`, `measure`, `aggregation`, `default_filters`, `threshold_filters` |
| `DimensionDef` | Internal dimension definition with `name`, `type`, `description` |

---

## Phase 7 — Narration & LLM Integration

### Feature-Flagged Design

LLM features are **disabled by default** and enabled via configuration:

| Flag | Default | Controls |
|------|---------|----------|
| `ENABLE_NARRATION` | `false` | Result summarization |
| `ENABLE_TOOL_CALLING` | `false` | Reserved for future use |

### Narration Flow

```
Query results (deterministic)
       ↓
  ENABLE_NARRATION = true?
       │
  No ──┤──→ return None (no narration)
       │
  Yes ─┤──→ Build prompt from template
       │         ↓
       │    Gemini available?
       │    ├─ Yes → GeminiClient.generate(prompt, temperature=0.2)
       │    └─ No  → Stub narration (deterministic summary)
       ↓
  narration string (or None)
```

### Prompt Template

The narration prompt (`src/llm/prompt_templates.py`) is carefully constrained:

> *"You are a BI narration assistant. Your job is to summarize the deterministic result of a governed metric query. Do NOT invent numbers, formulas, or field names. Only restate the data provided."*

### Natural Language Query Translation

The `NLQueryService` converts free-text questions into structured metric queries:

```
"What is the net margin exposure for January 2025?"
                    ↓
            Gemini (temperature=0.0)
                    ↓
{
  "metric": "net_margin_exposure",
  "grain": "month",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
                    ↓
         Standard validation & execution pipeline
```

The LLM only **selects** the metric and extracts parameters — it never writes SQL or computes results.

---

## Phase 8 — Final Result

### Complete Response Example

**Request:** `POST /query-metric`
```json
{
  "metric": "net_margin_exposure",
  "grain": "month",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31"
}
```

**Response:**
```json
{
  "metric": "net_margin_exposure",
  "grain": "month",
  "filters": {
    "status_name": "CONFIRMED"
  },
  "time_window": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "rows": [
    {
      "period": "2025-01-01",
      "value": 15500000.0
    }
  ],
  "lineage": {
    "source": "raw_app_data.margin_transactions",
    "staging_model": "stg_margin_calls",
    "metric_name": "net_margin_exposure",
    "aggregation": "sum",
    "filters_applied": { "status_name": "CONFIRMED" },
    "grain": "month",
    "time_window": { "start": "2025-01-01", "end": "2025-01-31" }
  },
  "narration": null
}
```

Every response includes **lineage** — a complete audit trail from raw source to final number.

### API Endpoints Summary

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Service health, version, source mode |
| `GET` | `/metrics` | List all governed metrics |
| `GET` | `/dimensions` | List all available dimensions |
| `POST` | `/query-metric` | Execute a governed metric query |
| `POST` | `/explain-metric` | Describe a metric's formula and dimensions |
| `POST` | `/nl-query` | Translate natural language → metric query (optionally execute) |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER / CLIENT                                 │
│                                                                         │
│   Natural Language Question          Structured Metric Query            │
│   "Net exposure for Jan 2025?"       { metric, grain, filters, ... }   │
└──────────────┬───────────────────────────────────┬──────────────────────┘
               │                                   │
               ▼                                   ▼
┌──────────────────────────┐         ┌──────────────────────────┐
│   POST /nl-query         │         │  POST /query-metric      │
│   NLQueryService         │         │                          │
│   (Gemini translation)   │────────▶│  Pydantic Validation     │
└──────────────────────────┘         └────────────┬─────────────┘
                                                  │
                                                  ▼
                                     ┌──────────────────────────┐
                                     │   SemanticRegistry       │
                                     │   • validate metric      │
                                     │   • validate grain       │
                                     │   • validate filters     │
                                     └────────────┬─────────────┘
                                                  │
                                                  ▼
                                     ┌──────────────────────────┐
                                     │   QueryExecutor          │
                                     │   • build staging CTE    │
                                     │   • build metric SQL     │
                                     │   • merge filters        │
                                     └────────────┬─────────────┘
                                                  │
                                                  ▼
                                     ┌──────────────────────────┐
                                     │   Adapter (DuckDB/SQL)   │
                                     │   • execute SQL          │
                                     │   • return rows          │
                                     └────────────┬─────────────┘
                                                  │
                                                  ▼
                                     ┌──────────────────────────┐
                                     │   NarrationService       │
                                     │   (if enabled)           │
                                     │   • Gemini or stub       │
                                     └────────────┬─────────────┘
                                                  │
                                                  ▼
                                     ┌──────────────────────────┐
                                     │   QueryMetricResponse    │
                                     │   • rows + lineage       │
                                     │   • optional narration   │
                                     └──────────────────────────┘
```

---

## Core Principles

| Principle | Description |
|-----------|-------------|
| **dbt is the semantic source of truth** | Business logic lives in dbt YAML, not in prompts or application code |
| **Source adapter abstraction** | Application is agnostic to JSON vs SQL ingestion via the adapter pattern |
| **LLM as reasoning layer, not calculator** | The LLM selects metrics and narrates results — it never generates SQL or computes numbers |
| **Fail closed** | Unknown metrics, filters, or grains are rejected immediately; the system never guesses |
| **Deterministic execution** | All numeric results come from governed metric definitions, never from LLM output |
| **Feature-flagged LLM features** | Narration and tool-calling are disabled by default; the system works fully without an LLM |
| **Audit-ready lineage** | Every response includes a complete trace from raw source to final result |
