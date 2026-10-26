"""
Lightweight VerityAI demo classifier — safe JSON weights only.

Format: verityai-demo-linear-v1 (bag-of-words logistic regression).
Never uses pickle / joblib / unsafe deserialization.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORMAT_ID = "verityai-demo-linear-v1"
TOKEN_RE = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass
class DemoModel:
    vocabulary: dict[str, int]
    weights: list[float]
    bias: float
    labels: list[str]
    task: str = "text_binary_sentiment"

    def vectorize(self, text: str) -> list[float]:
        vec = [0.0] * len(self.vocabulary)
        for token in tokenize(text):
            idx = self.vocabulary.get(token)
            if idx is not None:
                vec[idx] += 1.0
        return vec

    def predict_proba(self, text: str) -> float:
        vec = self.vectorize(text)
        z = self.bias + sum(w * x for w, x in zip(self.weights, vec, strict=True))
        # Numerically stable sigmoid
        if z >= 0:
            ez = math.exp(-z)
            return 1.0 / (1.0 + ez)
        ez = math.exp(z)
        return ez / (1.0 + ez)

    def predict(self, text: str) -> tuple[str, float]:
        prob_positive = self.predict_proba(text)
        if prob_positive >= 0.5:
            return self.labels[1], prob_positive
        return self.labels[0], 1.0 - prob_positive

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": FORMAT_ID,
            "task": self.task,
            "vocabulary": self.vocabulary,
            "weights": self.weights,
            "bias": self.bias,
            "labels": self.labels,
            "notes": (
                "Demo-only artifact for VerityAI provenance. "
                "A matching hash does not prove model accuracy or safety."
            ),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_demo_model(path: Path) -> DemoModel:
    """Load only the known-safe VerityAI demo JSON format."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("format") != FORMAT_ID:
        raise ValueError(
            f"Refusing to load model: expected format {FORMAT_ID!r}, "
            f"got {raw.get('format')!r}. Unsafe formats (e.g. pickle) are not supported."
        )
    vocabulary = raw["vocabulary"]
    weights = raw["weights"]
    labels = raw["labels"]
    if not isinstance(vocabulary, dict) or not isinstance(weights, list):
        raise ValueError("Invalid demo model payload")
    if len(weights) != len(vocabulary):
        raise ValueError("weights length must match vocabulary size")
    if not isinstance(labels, list) or len(labels) != 2:
        raise ValueError("labels must be a 2-item list")
    return DemoModel(
        vocabulary={str(k): int(v) for k, v in vocabulary.items()},
        weights=[float(w) for w in weights],
        bias=float(raw["bias"]),
        labels=[str(labels[0]), str(labels[1])],
        task=str(raw.get("task", "text_binary_sentiment")),
    )


def _sigmoid(z: float) -> float:
    if z >= 0:
        ez = math.exp(-z)
        return 1.0 / (1.0 + ez)
    ez = math.exp(z)
    return ez / (1.0 + ez)


def train_tiny_sentiment_model(epochs: int = 80, lr: float = 0.35) -> DemoModel:
    """Train a tiny binary sentiment classifier on a fixed toy corpus (CPU-only)."""
    positives = [
        "this movie was great and wonderful",
        "i love the excellent product quality",
        "fantastic experience happy with results",
        "amazing service and delightful support",
        "good food and pleasant atmosphere",
        "wonderful day with beautiful weather",
        "excellent work superb outcome",
        "i enjoy this awesome feature",
    ]
    negatives = [
        "this movie was terrible and awful",
        "i hate the poor product quality",
        "horrible experience angry with results",
        "bad service and disappointing support",
        "poor food and unpleasant atmosphere",
        "awful day with miserable weather",
        "terrible work disappointing outcome",
        "i dislike this horrible feature",
    ]
    texts = positives + negatives
    labels = [1] * len(positives) + [0] * len(negatives)

    vocab: dict[str, int] = {}
    for text in texts:
        for token in tokenize(text):
            if token not in vocab:
                vocab[token] = len(vocab)

    n = len(vocab)
    weights = [0.0] * n
    bias = 0.0

    def vectorize(text: str) -> list[float]:
        vec = [0.0] * n
        for token in tokenize(text):
            idx = vocab.get(token)
            if idx is not None:
                vec[idx] += 1.0
        return vec

    for _ in range(epochs):
        for text, y in zip(texts, labels, strict=True):
            x = vectorize(text)
            z = bias + sum(w * xi for w, xi in zip(weights, x, strict=True))
            p = _sigmoid(z)
            err = p - y
            for i in range(n):
                weights[i] -= lr * err * x[i]
            bias -= lr * err

    return DemoModel(
        vocabulary=vocab,
        weights=weights,
        bias=bias,
        labels=["negative", "positive"],
    )
