#!/usr/bin/env python3
"""
Run a sample prediction only after integrity verification succeeds.

Verification modes:
  --offline-hash   compare local SHA-256 to an expected digest (no chain)
  --api            call POST /api/v1/models/verify (requires running backend)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

from demo_classifier import load_demo_model


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def verify_offline(path: Path, expected_hash: str) -> tuple[bool, str, str]:
    actual = sha256_file(path)
    expected = expected_hash.lower().removeprefix("0x")
    return actual == expected, expected, actual


def verify_via_api(
    *,
    api_base: str,
    model_id: str,
    path: Path,
) -> tuple[str, str | None, str | None]:
    boundary = "verityaidemoboundary"
    file_bytes = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model_id"\r\n\r\n'
        f"{model_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: application/json\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    request = urllib.request.Request(
        f"{api_base.rstrip('/')}/api/v1/models/verify",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as decode_exc:
            raise RuntimeError(f"Verify API failed ({exc.code}): {raw}") from decode_exc
        # 503 VERIFICATION_UNAVAILABLE still returns a structured body.
        if "status" not in payload:
            raise RuntimeError(f"Verify API failed ({exc.code}): {payload}") from exc

    return (
        str(payload.get("status")),
        payload.get("expected_hash"),
        payload.get("actual_hash"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True, help="Path to demo JSON model")
    parser.add_argument(
        "--text",
        default="this product is excellent and wonderful",
        help="Sample text for prediction",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--offline-hash", help="Expected SHA-256 hex digest")
    mode.add_argument("--model-id", help="Registered on-chain/app model id for API verify")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    if not args.model.is_file():
        print(f"ERROR: model file not found: {args.model}", file=sys.stderr)
        return 2

    if args.offline_hash:
        ok, expected, actual = verify_offline(args.model, args.offline_hash)
        status = "VERIFIED" if ok else "INTEGRITY_MISMATCH"
        print(f"Verification status: {status}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        if not ok:
            print("Refusing to load model after integrity mismatch.")
            return 1
    else:
        status, expected, actual = verify_via_api(
            api_base=args.api_base,
            model_id=args.model_id,
            path=args.model,
        )
        print(f"Verification status: {status}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        if status != "VERIFIED":
            print("Refusing to load model — verification did not succeed.")
            return 1

    model = load_demo_model(args.model)
    label, confidence = model.predict(args.text)
    print(f"Prediction for {args.text!r}: {label} (confidence={confidence:.3f})")
    print(
        "Disclaimer: successful verification proves the bytes match the registered "
        "fingerprint only — not accuracy, safety, or ethical behavior."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
