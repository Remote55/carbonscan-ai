"""RunPod Serverless handler — entry point for GPU worker.

Configures RunPod to receive job events, download input from URL, run pipeline,
upload output, and notify API via webhook.

Deploy:
    docker build -f Dockerfile.gpu -t carbonscan-ml:v1 .
    docker tag carbonscan-ml:v1 <registry>/carbonscan-ml:v1
    docker push <registry>/carbonscan-ml:v1
    # Then create Serverless Endpoint on RunPod with this image
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import httpx

try:
    import runpod
except ImportError:
    runpod = None  # local dev without runpod installed

from pipeline.main import process_point_cloud


def download_file(url: str, dest: Path) -> Path:
    """Download a file via HTTPS."""
    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as response:
        response.raise_for_status()
        with dest.open("wb") as f:
            for chunk in response.iter_bytes(chunk_size=8192):
                f.write(chunk)
    return dest


def upload_file(url: str, file_path: Path) -> None:
    """Upload a file via signed PUT URL."""
    with file_path.open("rb") as f:
        response = httpx.put(url, content=f.read(), timeout=300)
        response.raise_for_status()


def notify_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    """POST job results back to API."""
    httpx.post(webhook_url, json=payload, timeout=30).raise_for_status()


def handler(event: dict[str, Any]) -> dict[str, Any]:
    """RunPod serverless handler.

    Event format (RunPod-defined):
        {
            "input": {
                "job_id": str,
                "input_url": str,          # signed GET URL
                "output_upload_url": str,  # signed PUT URL
                "webhook_url": str         # POST results here when done
            }
        }
    """
    input_data = event.get("input", {})
    job_id = input_data["job_id"]
    input_url = input_data["input_url"]
    output_url = input_data.get("output_upload_url")
    webhook_url = input_data.get("webhook_url")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        input_file = download_file(input_url, tmp_path / "input.las")
        output_file = tmp_path / "results.json"

        # Process
        result = process_point_cloud(
            input_file,
            output_path=output_file,
            progress_callback=lambda stage, pct: print(f"[{pct:3d}%] {stage}", flush=True),
        )

        # Upload output
        if output_url:
            upload_file(output_url, output_file)

        # Notify API
        payload = {
            "job_id": job_id,
            "status": "completed",
            "tree_count": result.summary.get("total_trees", 0),
            "total_carbon_kg": result.summary.get("total_carbon_kg", 0),
        }
        if webhook_url:
            notify_webhook(webhook_url, payload)

        return payload


if __name__ == "__main__":
    if runpod is None:
        raise RuntimeError("runpod package not installed. Run: pip install -e '.[runpod]'")
    runpod.serverless.start({"handler": handler})
