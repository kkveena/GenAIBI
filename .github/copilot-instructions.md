# AI Coding Instructions for Semantic GenAI for BI

This is a **regulated, accuracy-first** BI system. Prioritize correctness and traceability over cleverness.

## Architecture

**Data Flow:** Raw source → dbt staging → semantic registry (metrics/dimensions) → deterministic query API → optional LLM narration

**Two Source Modes:**
- `json_duckdb`: Raw JSON files queried through DuckDB (Phase 1A default)
- `sql_source`: Direct SQL view/table registered in dbt (production preference)

Source adapters in [src/adapters/](src/adapters/) abstract the physical source; all app code consumes through the `BaseSourceAdapter` interface.

## Five Core Guardrails

1. **dbt is semantic truth** — All business logic (metrics, calculations, field mappings) lives in dbt models, not app code. See [stg_margin_calls.sql](dbt/models/staging/stg_margin_calls.sql) for the canonical transform pattern.

2. **LLM never invents** — The LLM may select approved metrics/dimensions/filters and narrate results. It **cannot** write SQL, invent formulas, infer joins, or reinterpret numbers.

3. **Fail closed** — When user intent is ambiguous or ungrounded in known metrics, return a validation error. Never guess.

4. **Full lineage** — Every query result must trace back: user question → metric request → dbt model → data source → result. See `LineageInfo` schema in [src/api/schemas.py](src/api/schemas.py).

5. **Deterministic execution** — Same input → same output. No randomness. Useful for audits and evals.

## Key Files & Patterns

| File | Pattern |
|------|---------|
| [claude.md](claude.md) | Product intent and architectural guardrails; read first |
| [README.md](README.md) | Phase plan, business scope, design rules |
| [src/adapters/base_adapter.py](src/adapters/base_adapter.py) | Interface all adapters implement; never hardcode source logic elsewhere |
| [src/services/semantic_registry.py](src/services/semantic_registry.py) | In-memory metric/dimension definitions mirroring dbt YAML. Add new metrics here and in dbt simultaneously. |
| [dbt/models/staging/stg_margin_calls.sql](dbt/models/staging/stg_margin_calls.sql) | Canonical staging transform: cast types, rename fields, compute net_val, map status codes |
| [src/api/schemas.py](src/api/schemas.py) | Request/response contracts; define all input validation here |
| [tests/conftest.py](tests/conftest.py) | Shared fixtures; SAMPLE_DATA shows expected schema after transform |

## Configuration

[src/core/config.py](src/core/config.py) loads from `.env`. Key settings:
- `source_mode`: `json_duckdb` or `sql_source`
- `enable_narration`, `enable_tool_calling`, `enable_evals`: feature flags for Phase 1B/C
- `gemini_api_key`, `gemini_model`: LLM configuration
- `dbt_project_dir`, `dbt_profiles_dir`: dbt paths

## Workflows

### Local Development
```bash
bash scripts/run_local.sh  # Start FastAPI on :8000
pytest tests/             # Run all tests
```

### Adding a Metric
1. Define in dbt [margin_risk.yml](dbt/models/marts/margin_risk.yml)
2. Add `MetricDef` to `_METRICS` dict in [semantic_registry.py](src/services/semantic_registry.py)
3. Add tests to [tests/unit/test_semantic_registry.py](tests/unit/test_semantic_registry.py)
4. Register endpoint in [routes_metrics.py](src/api/routes_metrics.py)

### Staging New Source
1. Register source in dbt [sources.yml](dbt/models/sources.yml)
2. Create staging model in [stg_*.sql](dbt/models/staging/) following the `stg_margin_calls.sql` pattern
3. Map cryptic field names to canonical names (e.g., `st_cd` → `status_name`)
4. Add dbt tests and validation queries
5. Update [conftest.py](tests/conftest.py) with new sample data schema

### Testing Philosophy
- Unit tests in [tests/unit/](tests/unit/): adapters, enums, registry, metric queries
- Integration tests in [tests/integration/](tests/integration/): API routes
- Contract tests in [tests/contract/](tests/contract/): data schema validation
- Always test determinism: run twice, expect identical output

## Conventions

- **Naming**: Use snake_case for columns, PascalCase for classes, UPPERCASE for constants
- **Status codes**: Map to human-readable names in staging model (e.g., `st_cd: 4 → status_name: CONFIRMED`)
- **Null handling**: Explicit in dbt; assume non-null after staging
- **Timestamps**: Cast to UTC; use `event_at` for margin call events
- **Decimal precision**: `decimal(18,2)` for USD amounts

## Phase Sequencing

**Phase 1A (current)** — Semantic foundation: dbt, staging, deterministic API, basic evals  
**Phase 1B** — Tool calling: LLM selects from approved tools instead of writing SQL  
**Phase 1C** — Eval harness: golden prompts, routing correctness, abstention rate  
**Phase 2+** — Expand metrics, optimize queries, production hardening

Do **not** implement free-form Text-to-SQL as the default path.

## Critical Don'ts

- ❌ Don't put business formulas in LLM prompts
- ❌ Don't hardcode metric logic in Python (except as registry mirror of dbt YAML)
- ❌ Don't skip `LineageInfo` in query responses
- ❌ Don't let LLM write ad-hoc SQL in production flow
- ❌ Don't ignore ambiguous user intent; fail closed
