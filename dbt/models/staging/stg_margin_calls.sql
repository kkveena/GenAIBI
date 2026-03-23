/*
    Staging model: stg_margin_calls
    Purpose: cast types, rename cryptic fields, map status codes, compute net_val.
    Source: raw margin transactions (JSON via DuckDB or direct SQL).
*/

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
from {{ source('raw_app_data', 'margin_transactions') }}
