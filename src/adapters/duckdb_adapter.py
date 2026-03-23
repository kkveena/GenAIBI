from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import duckdb

from src.adapters.base_adapter import BaseSourceAdapter

# SQL that mirrors the dbt staging model: cast, alias, status map, net_val.
_STAGING_SQL = """
select
    cast(id as varchar)                      as call_id,
    cast(acct_id as varchar)                 as account_id,
    cast(mc_amt as decimal(18,2))            as margin_amount_usd,
    cast(collateral_val as decimal(18,2))    as collateral_amount_usd,
    cast(mc_amt as decimal(18,2))
        - cast(collateral_val as decimal(18,2)) as net_val,
    case
        when st_cd = 4 then 'CONFIRMED'
        when st_cd = 5 then 'PENDING'
        when st_cd = 0 then 'CANCELLED'
        else 'UNKNOWN'
    end                                      as status_name,
    cast(event_ts as timestamp)              as event_at
from margin_transactions
"""


class DuckDBAdapter(BaseSourceAdapter):
    """Adapter for JSON-file sources queried through DuckDB."""

    def __init__(self, json_glob: str = "./data/raw/*.json") -> None:
        self._conn = duckdb.connect(":memory:")
        self._json_glob = json_glob
        self._load_json_source()

    def _load_json_source(self) -> None:
        glob_path = Path(self._json_glob)
        parent = glob_path.parent
        pattern = glob_path.name

        json_files = sorted(parent.glob(pattern))
        if not json_files:
            raise FileNotFoundError(
                f"No JSON files found matching {self._json_glob}"
            )

        all_rows: list[dict[str, Any]] = []
        for fp in json_files:
            with open(fp) as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_rows.extend(data)
                else:
                    all_rows.append(data)

        self._conn.execute("drop table if exists margin_transactions")
        self._conn.execute(
            "create table margin_transactions as select * from read_json_auto(?)",
            [str(json_files[0])],
        )
        if len(json_files) > 1:
            for fp in json_files[1:]:
                self._conn.execute(
                    "insert into margin_transactions select * from read_json_auto(?)",
                    [str(fp)],
                )

    def execute_query(self, sql: str) -> list[dict[str, Any]]:
        result = self._conn.execute(sql)
        columns = [desc[0] for desc in result.description]
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def get_staged_data(self) -> list[dict[str, Any]]:
        return self.execute_query(_STAGING_SQL)

    def close(self) -> None:
        self._conn.close()
