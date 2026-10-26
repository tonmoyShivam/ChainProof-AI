"""Unit tests for the Milestone 7 safe JSON demo classifier."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

DEMO_DIR = Path(__file__).resolve().parents[2] / "examples" / "ai-demo"
ARTIFACT = DEMO_DIR / "artifacts" / "demo_sentiment.json"


@pytest.fixture(scope="module")
def demo_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    import sys

    sys.path.insert(0, str(DEMO_DIR))
    from demo_classifier import train_tiny_sentiment_model

    out = tmp_path_factory.mktemp("demo") / "model.json"
    train_tiny_sentiment_model().save(out)
    return out


def test_round_trip_and_prediction(demo_path: Path) -> None:
    import sys

    sys.path.insert(0, str(DEMO_DIR))
    from demo_classifier import load_demo_model

    model = load_demo_model(demo_path)
    label, confidence = model.predict("this is a great and wonderful product")
    assert label == "positive"
    assert confidence > 0.5


def test_loader_rejects_unknown_format(tmp_path: Path) -> None:
    import sys

    sys.path.insert(0, str(DEMO_DIR))
    from demo_classifier import load_demo_model

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"format": "pickle-not-allowed", "weights": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Refusing to load model"):
        load_demo_model(bad)


def test_checked_in_artifact_loads_if_present() -> None:
    if not ARTIFACT.is_file():
        pytest.skip("checked-in demo artifact missing")
    import sys

    sys.path.insert(0, str(DEMO_DIR))
    from demo_classifier import FORMAT_ID, load_demo_model

    model = load_demo_model(ARTIFACT)
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert payload["format"] == FORMAT_ID
    assert model.labels == ["negative", "positive"]


def test_tamper_changes_hash(demo_path: Path) -> None:
    import hashlib

    original = demo_path.read_bytes()
    digest_a = hashlib.sha256(original).hexdigest()
    tampered = bytearray(original)
    tampered[10] ^= 0x01
    digest_b = hashlib.sha256(bytes(tampered)).hexdigest()
    assert digest_a != digest_b
