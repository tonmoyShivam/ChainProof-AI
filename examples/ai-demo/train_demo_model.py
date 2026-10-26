#!/usr/bin/env python3
"""Train the tiny VerityAI demo sentiment classifier and write a JSON artifact."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from demo_classifier import load_demo_model, train_tiny_sentiment_model


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "artifacts" / "demo_sentiment.json",
        help="Output path for the JSON model artifact",
    )
    args = parser.parse_args()

    model = train_tiny_sentiment_model()
    model.save(args.out)
    # Round-trip load to ensure the safe loader accepts the file.
    loaded = load_demo_model(args.out)
    label, confidence = loaded.predict("this is a great and wonderful product")
    digest = sha256_file(args.out)

    print(f"Wrote {args.out}")
    print(f"SHA-256: {digest}")
    print(f"Smoke prediction: {label} (confidence={confidence:.3f})")
    print(
        "Note: a matching fingerprint proves byte integrity only — "
        "not model accuracy, safety, or creator real-world identity."
    )


if __name__ == "__main__":
    main()
