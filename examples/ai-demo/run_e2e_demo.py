#!/usr/bin/env python3
"""
End-to-end VerityAI AI demo:

1) Train/ensure a safe JSON model artifact exists
2) Register it through the live API (auth + blockchain confirmation)
3) Verify original → predict
4) Tamper a copy → verify must fail → refuse inference

Requires: backend + Hardhat node + deployed ModelProvenance (see README).
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from demo_classifier import load_demo_model, train_tiny_sentiment_model
from train_demo_model import sha256_file

DEMO_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL = DEMO_DIR / "artifacts" / "demo_sentiment.json"


def http_json(method: str, url: str, *, token: str | None = None, payload: dict | None = None):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def multipart(
    url: str,
    fields: dict[str, str],
    file_field: str,
    file_path: Path,
    *,
    token: str | None = None,
):
    boundary = "verityaie2eboundary"
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    file_bytes = file_path.read_bytes()
    chunks.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
            f"Content-Type: application/json\r\n\r\n"
        ).encode("utf-8")
    )
    chunks.append(file_bytes)
    chunks.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    body = b"".join(chunks)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"detail": raw}
        return exc.code, parsed


def ensure_model(path: Path) -> None:
    if path.is_file():
        load_demo_model(path)
        return
    model = train_tiny_sentiment_model()
    model.save(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-base", default=os.environ.get("VERITYAI_API_BASE", "http://127.0.0.1:8000"))
    parser.add_argument("--email", default="aidemo@example.com")
    parser.add_argument("--password", default="password123")
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--skip-register", action="store_true", help="Only offline hash demo")
    args = parser.parse_args()

    ensure_model(args.model)
    original_hash = sha256_file(args.model)
    print(f"[1] Demo model ready: {args.model}")
    print(f"    SHA-256: {original_hash}")

    tampered = args.model.with_name(args.model.stem + ".tampered.json")
    shutil.copyfile(args.model, tampered)
    data = bytearray(tampered.read_bytes())
    # Flip one byte inside the JSON payload (still valid-ish path for hash change).
    data[min(40, len(data) - 2)] ^= 0x01
    tampered.write_bytes(data)
    print(f"[2] Wrote tampered copy: {tampered}")
    print(f"    SHA-256: {sha256_file(tampered)}")

    if args.skip_register:
        print("[3] Offline verify original…")
        rc_ok = subprocess.call(
            [
                sys.executable,
                str(DEMO_DIR / "infer_after_verify.py"),
                "--model",
                str(args.model),
                "--offline-hash",
                original_hash,
            ]
        )
        print("[4] Offline verify tampered (expect failure)…")
        rc_bad = subprocess.call(
            [
                sys.executable,
                str(DEMO_DIR / "infer_after_verify.py"),
                "--model",
                str(tampered),
                "--offline-hash",
                original_hash,
            ]
        )
        if rc_ok != 0 or rc_bad == 0:
            print("Offline demo did not behave as expected.", file=sys.stderr)
            return 1
        print("Offline demo OK: original verified+predicted; tampered rejected.")
        return 0

    api = args.api_base.rstrip("/")
    print(f"[3] Registering account/login at {api} …")
    try:
        http_json(
            "POST",
            f"{api}/api/v1/auth/register",
            payload={
                "email": args.email,
                "password": args.password,
                "display_name": "AI Demo",
            },
        )
    except urllib.error.HTTPError as exc:
        if exc.code not in {400, 409}:
            raise
    token = http_json(
        "POST",
        f"{api}/api/v1/auth/login",
        payload={"email": args.email, "password": args.password},
    )["access_token"]

    print("[4] Registering model on-chain via API (waits for confirmation)…")
    status, registered = multipart(
        f"{api}/api/v1/models/register",
        {
            "name": "VerityAI Demo Sentiment",
            "description": "Tiny JSON linear sentiment classifier for provenance demo",
            "version": "1.0.0",
            "framework": "verityai-demo-linear",
            "framework_version": "1",
            "architecture": "bag-of-words-logistic",
        },
        "file",
        args.model,
        token=token,
    )
    if status != 200:
        print(f"Registration failed ({status}): {registered}", file=sys.stderr)
        print(
            "Ensure Hardhat is running, ModelProvenance is deployed, and "
            "BLOCKCHAIN_CONTRACT_ADDRESS / BLOCKCHAIN_PRIVATE_KEY are set.",
            file=sys.stderr,
        )
        return 1
    model_id = registered["model_id"]
    print(f"    model_id={model_id}")
    print(f"    tx={registered['transaction_hash']} block={registered['block_number']}")

    print("[5] Verify original + predict…")
    rc_ok = subprocess.call(
        [
            sys.executable,
            str(DEMO_DIR / "infer_after_verify.py"),
            "--model",
            str(args.model),
            "--model-id",
            model_id,
            "--api-base",
            api,
        ]
    )
    print("[6] Verify tampered copy (expect INTEGRITY_MISMATCH / non-zero exit)…")
    rc_bad = subprocess.call(
        [
            sys.executable,
            str(DEMO_DIR / "infer_after_verify.py"),
            "--model",
            str(tampered),
            "--model-id",
            model_id,
            "--api-base",
            api,
        ]
    )

    if rc_ok != 0:
        print("Original artifact failed verification/inference.", file=sys.stderr)
        return 1
    if rc_bad == 0:
        print("Tampered artifact was incorrectly accepted.", file=sys.stderr)
        return 1

    print("E2E demo OK.")
    print(
        "Reminder: hash verification demonstrates integrity/provenance of bytes, "
        "not correctness or safety of the model."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
