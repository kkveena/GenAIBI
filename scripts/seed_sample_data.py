"""Seed sample data into the data/raw directory for local development."""
from __future__ import annotations

import json
import shutil
from pathlib import Path


SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def seed() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    sample_file = SAMPLE_DIR / "margin_transactions.json"
    if not sample_file.exists():
        raise FileNotFoundError(f"Sample data not found at {sample_file}")

    dest = RAW_DIR / "margin_transactions.json"
    shutil.copy2(sample_file, dest)
    print(f"Seeded {dest}")

    with open(dest) as f:
        rows = json.load(f)

    print(f"  {len(rows)} records loaded.")


if __name__ == "__main__":
    seed()
