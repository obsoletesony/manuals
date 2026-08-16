"""Non-circular provenance helpers for tracked PSPMAN manual outputs."""

from __future__ import annotations

import hashlib
from pathlib import Path


def manual_input_files(repo_root: Path, manual_dir: Path) -> list[Path]:
    """Return every source input that can affect the generated manual outputs."""
    files = [repo_root / "package.json"]
    for directory in (
        repo_root / "manualkit",
        manual_dir / "content",
        manual_dir / "assets",
        manual_dir / "source",
    ):
        files.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        )
    return sorted(set(files), key=lambda path: path.relative_to(repo_root).as_posix())


def manual_input_digest(repo_root: Path, manual_dir: Path) -> tuple[str, int]:
    """Hash paths and bytes of manual inputs without depending on an enclosing commit."""
    digest = hashlib.sha256()
    files = manual_input_files(repo_root, manual_dir)
    for path in files:
        relative = path.relative_to(repo_root).as_posix().encode("utf-8")
        payload = path.read_bytes()
        digest.update(relative)
        digest.update(b"\0")
        digest.update(str(len(payload)).encode("ascii"))
        digest.update(b"\0")
        digest.update(payload)
        digest.update(b"\0")
    return digest.hexdigest(), len(files)
