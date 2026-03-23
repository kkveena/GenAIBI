#!/usr/bin/env bash
set -euo pipefail

echo "=== Semantic GenAI for BI — Bootstrap ==="

python -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

python scripts/seed_sample_data.py

echo "=== Bootstrap complete. Run: source .venv/bin/activate ==="
