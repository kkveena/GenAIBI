#!/usr/bin/env bash
set -euo pipefail

echo "=== Starting Semantic GenAI for BI (local) ==="
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
