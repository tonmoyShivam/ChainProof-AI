"""Safe local filesystem storage for model artifacts."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings

_SAFE_EXT_RE = re.compile(r"^\.[A-Za-z0-9]{1,16}$")


class StorageError(RuntimeError):
    """Raised when a storage operation fails safely."""


@dataclass(frozen=True)
class StoredArtifact:
    artifact_id: str
    relative_path: str
    absolute_path: Path
    size_bytes: int
    sha256_hex: str


def resolve_storage_root(settings: Settings, *, base: Path | None = None) -> Path:
    """Resolve the storage root to an absolute path and ensure it exists."""
    root = Path(settings.storage_path)
    if not root.is_absolute():
        root = (base or Path.cwd()) / root
    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_safe_filename(extension: str, *, artifact_id: str | None = None) -> str:
    """
    Build a storage filename that never incorporates untrusted path segments.

    Uses a UUID stem plus a validated extension only.
    """
    if not _SAFE_EXT_RE.match(extension):
        raise StorageError(f"Refusing unsafe extension: {extension!r}")
    stem = artifact_id or str(uuid.uuid4())
    try:
        uuid.UUID(stem)
    except ValueError as exc:
        raise StorageError("artifact_id must be a UUID") from exc
    return f"{stem}{extension.lower()}"


def assert_within_storage(root: Path, candidate: Path) -> Path:
    """Ensure candidate resolves inside the storage root (blocks path traversal)."""
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise StorageError("Resolved path escapes storage root") from exc
    return resolved


def store_bytes(
    data: bytes,
    *,
    extension: str,
    sha256_hex: str,
    settings: Settings,
    base: Path | None = None,
) -> StoredArtifact:
    """
    Persist artifact bytes under storage/artifacts using a UUID filename.

    The caller supplies the authoritative server-computed SHA-256; client hashes
    are never trusted.
    """
    root = resolve_storage_root(settings, base=base)
    artifacts_dir = root / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    artifact_id = str(uuid.uuid4())
    filename = build_safe_filename(extension, artifact_id=artifact_id)
    destination = assert_within_storage(root, artifacts_dir / filename)

    # Refuse overwrite of an existing id (UUID collision would be exceptional).
    if destination.exists():
        raise StorageError("Artifact path already exists")

    destination.write_bytes(data)

    relative = destination.relative_to(root).as_posix()
    return StoredArtifact(
        artifact_id=artifact_id,
        relative_path=relative,
        absolute_path=destination,
        size_bytes=len(data),
        sha256_hex=sha256_hex,
    )
