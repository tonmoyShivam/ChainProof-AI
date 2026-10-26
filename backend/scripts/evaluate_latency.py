#!/usr/bin/env python3
"""
Measure local hashing latency (and optional live API hash/register/verify latency).

Outputs measured timings only — does not invent targets or fabricate results.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.hashing import sha256_hex_of_bytes, sha256_hex_of_path  # noqa: E402


def timed(fn, repeats: int) -> list[float]:
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - start)
    return samples


def summarize(samples: list[float]) -> dict:
    return {
        "runs": len(samples),
        "min_s": min(samples),
        "max_s": max(samples),
        "mean_s": statistics.fmean(samples),
        "median_s": statistics.median(samples),
    }


def measure_api(api_base: str, artifact: Path, repeats: int) -> dict:
    """Optional live API timings — skipped silently if API is unreachable."""
    try:
        import httpx
    except ImportError as exc:  # pragma: no cover
        return {"skipped": True, "reason": f"httpx unavailable: {exc}"}

    base = api_base.rstrip("/")
    try:
        with httpx.Client(timeout=30.0) as client:
            health = client.get(f"{base}/api/v1/health")
            if health.status_code != 200:
                return {"skipped": True, "reason": f"health status {health.status_code}"}

            email = f"eval-{int(time.time())}@example.com"
            password = "password123"
            reg = client.post(
                f"{base}/api/v1/auth/register",
                json={"email": email, "password": password, "display_name": "Eval"},
            )
            if reg.status_code not in {200, 201}:
                return {"skipped": True, "reason": f"register failed: {reg.status_code}"}
            login = client.post(
                f"{base}/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            token = login.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            hash_samples: list[float] = []
            for _ in range(repeats):
                start = time.perf_counter()
                with artifact.open("rb") as fh:
                    resp = client.post(
                        f"{base}/api/v1/artifacts/hash",
                        files={"file": (artifact.name, fh, "application/octet-stream")},
                    )
                hash_samples.append(time.perf_counter() - start)
                if resp.status_code != 200:
                    return {"skipped": True, "reason": f"hash failed: {resp.status_code}"}

            with artifact.open("rb") as fh:
                start = time.perf_counter()
                reg_model = client.post(
                    f"{base}/api/v1/models/register",
                    headers=headers,
                    files={"file": (artifact.name, fh, "application/octet-stream")},
                    data={"name": "Eval Model", "version": "1.0.0"},
                )
                register_s = time.perf_counter() - start
            if reg_model.status_code not in {200, 201}:
                return {
                    "skipped": True,
                    "reason": f"model register failed: {reg_model.status_code} {reg_model.text[:200]}",
                    "hash_endpoint": summarize(hash_samples),
                }
            model_id = reg_model.json().get("id") or reg_model.json().get("model_id")

            verify_samples: list[float] = []
            for _ in range(min(repeats, 5)):
                with artifact.open("rb") as fh:
                    start = time.perf_counter()
                    ver = client.post(
                        f"{base}/api/v1/models/verify",
                        files={"file": (artifact.name, fh, "application/octet-stream")},
                        data={"model_id": str(model_id)},
                    )
                    verify_samples.append(time.perf_counter() - start)
                if ver.status_code != 200:
                    return {
                        "skipped": True,
                        "reason": f"verify failed: {ver.status_code}",
                        "hash_endpoint": summarize(hash_samples),
                        "register_once_s": register_s,
                    }

            return {
                "api_base": base,
                "artifact": str(artifact),
                "hash_endpoint": summarize(hash_samples),
                "register_once_s": register_s,
                "verify_endpoint": summarize(verify_samples),
            }
    except Exception as exc:  # noqa: BLE001 — evaluation script must never crash callers
        return {"skipped": True, "reason": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--size-kb", type=int, default=256, help="Synthetic payload size")
    parser.add_argument(
        "--file",
        type=Path,
        help="Optional real file to hash (e.g. examples/ai-demo/artifacts/demo_sentiment.json)",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default="",
        help="If set (e.g. http://127.0.0.1:8000), also measure live hash/register/verify",
    )
    args = parser.parse_args()

    payload = b"v" * (args.size_kb * 1024)
    mem_samples = timed(lambda: sha256_hex_of_bytes(payload), args.repeats)

    report: dict = {
        "measuredAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hash_sha256_in_memory": {
            "payload_bytes": len(payload),
            **summarize(mem_samples),
        },
    }

    if args.file and args.file.is_file():
        file_samples = timed(lambda: sha256_hex_of_path(args.file), args.repeats)
        report["hash_sha256_file"] = {
            "path": str(args.file),
            "payload_bytes": args.file.stat().st_size,
            **summarize(file_samples),
        }

    if args.api_base:
        artifact = args.file if args.file and args.file.is_file() else None
        if artifact is None:
            tmp = Path("/tmp/verityai-eval.pt")
            tmp.write_bytes(b"eval-weights-v1")
            artifact = tmp
        report["api"] = measure_api(args.api_base, artifact, max(3, min(args.repeats, 10)))

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
