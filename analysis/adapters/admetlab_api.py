#!/usr/bin/env python3
"""Run one documented ADMETlab 3.0 batch request and cache the raw response."""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "https://admetlab3.scbdd.com/api/admet"
RAW_RESPONSE = ROOT / "data/raw/admetlab/admetlab_response.json"
RAW_TABLE = ROOT / "data/raw/admetlab/admetlab_predictions.csv"
RUN_METADATA = ROOT / "data/raw/admetlab/run_metadata.json"


def confirmed_compounds() -> list[dict[str, str]]:
    with (ROOT / "data/compounds/compound_manifest.csv").open(encoding="utf-8-sig", newline="") as handle:
        return [row for row in csv.DictReader(handle) if row["structure_confirmed"].lower() == "yes"]


def run(refresh: bool = False) -> Path:
    if RAW_RESPONSE.exists() and not refresh:
        return RAW_RESPONSE

    compounds = confirmed_compounds()
    payload = {
        "SMILES": [row["canonical_smiles"] for row in compounds],
        "feature": False,
        "uncertain": True,
    }
    started = datetime.now(timezone.utc).isoformat()
    response = requests.post(ENDPOINT, json=payload, timeout=300)
    response.raise_for_status()
    result = response.json()
    if result.get("status") != "success" or not isinstance(result.get("data", {}).get("data"), list):
        raise RuntimeError(f"ADMETlab returned an unexpected response: {result.get('status')!r}")

    RAW_RESPONSE.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    predictions = result["data"]["data"]
    if len(predictions) != len(compounds):
        raise RuntimeError(f"Expected {len(compounds)} ADMET rows, received {len(predictions)}")

    keys = sorted({key for row in predictions for key in row if key != "structure"})
    with RAW_TABLE.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["compound_id", "compound_name", *keys])
        writer.writeheader()
        for compound, prediction in zip(compounds, predictions, strict=True):
            cleaned = {key: value for key, value in prediction.items() if key != "structure"}
            writer.writerow({"compound_id": compound["compound_id"], "compound_name": compound["compound_name"], **cleaned})

    metadata = {
        "model": "ADMETlab 3.0",
        "endpoint": ENDPOINT,
        "request_started_utc": started,
        "request_completed_utc": datetime.now(timezone.utc).isoformat(),
        "input_manifest": "data/compounds/compound_manifest.csv",
        "compound_count": len(compounds),
        "feature": False,
        "uncertain": True,
        "task_id": result["data"].get("taskid"),
        "raw_response": str(RAW_RESPONSE.relative_to(ROOT)),
        "raw_table": str(RAW_TABLE.relative_to(ROOT)),
    }
    RUN_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return RAW_RESPONSE


def download_web_result(result_id: str) -> Path:
    """Cache the official CSV produced by a completed ADMETlab web run."""
    url = f"https://admetlab3.scbdd.com/server/result/{result_id}/download/csv"
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    if "csv" not in response.headers.get("content-type", "").lower() and b"," not in response.content[:500]:
        raise RuntimeError("ADMETlab download did not return a CSV file")
    RAW_TABLE.write_bytes(response.content)
    compounds = confirmed_compounds()
    metadata = {
        "model": "ADMETlab 3.0",
        "submission_mode": "official web batch screening",
        "result_id": result_id,
        "result_url": f"https://admetlab3.scbdd.com/server/result/{result_id}",
        "download_url": url,
        "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "input_manifest": "data/compounds/compound_manifest.csv",
        "compound_count": len(compounds),
        "raw_table": str(RAW_TABLE.relative_to(ROOT)),
        "api_note": "The documented /api/admet endpoint returned HTTP 404; the official web batch service completed successfully.",
    }
    RUN_METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return RAW_TABLE


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Run a new request even when a cached response exists")
    parser.add_argument("--result-id", help="Download a completed official web batch result by its result ID")
    args = parser.parse_args()
    print(download_web_result(args.result_id) if args.result_id else run(refresh=args.refresh))
