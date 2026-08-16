"""Manual project discovery, manifest validation, and scaffolding."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$")
BLOCK_TYPES = {"paragraph", "subheading", "ordered-list", "unordered-list", "code", "table"}
REQUIRED_DOCUMENT_FIELDS = ("title", "author", "subject", "keywords", "filenameStem")


class ProjectError(ValueError):
    """A clear configuration or project-resolution error."""


@dataclass(frozen=True)
class ManualProject:
    """A validated project directory and its parsed manifest."""

    directory: Path
    manifest: dict

    @property
    def document(self) -> dict:
        return self.manifest["document"]

    @property
    def sections(self) -> list[dict]:
        return self.manifest["sections"]

    @property
    def output_dir(self) -> Path:
        return self.directory / "output"

    @property
    def render_dir(self) -> Path:
        return self.directory / "rendered"


def validate_slug(slug: str) -> str:
    """Return a valid lowercase kebab-case slug or raise a clear error."""

    if not SLUG_PATTERN.fullmatch(slug):
        raise ProjectError(
            "Manual slug must use lowercase letters, digits, and single hyphens "
            "between words."
        )
    return slug


def _require_text(mapping: dict, field: str, context: str) -> str:
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProjectError(f"{context} requires non-empty text for '{field}'.")
    return value


def validate_manifest(manifest: dict, source: Path) -> dict:
    """Validate the intentionally small text-manual manifest."""

    if not isinstance(manifest, dict):
        raise ProjectError(f"Manual manifest must be an object: {source}")
    document = manifest.get("document")
    if not isinstance(document, dict):
        raise ProjectError(f"Manual manifest requires a 'document' object: {source}")
    for field in REQUIRED_DOCUMENT_FIELDS:
        _require_text(document, field, "Document metadata")
    if not FILENAME_PATTERN.fullmatch(document["filenameStem"]):
        raise ProjectError(
            "Document metadata 'filenameStem' must contain only letters, digits, and hyphens."
        )
    for optional in ("subtitle", "runningName"):
        if optional in document and not isinstance(document[optional], str):
            raise ProjectError(f"Document metadata '{optional}' must be text when supplied.")

    sections = manifest.get("sections")
    if not isinstance(sections, list) or not sections:
        raise ProjectError("Manual manifest requires at least one section.")
    for section_index, section in enumerate(sections, 1):
        if not isinstance(section, dict):
            raise ProjectError(f"Section {section_index} must be an object.")
        _require_text(section, "title", f"Section {section_index}")
        blocks = section.get("blocks")
        if not isinstance(blocks, list) or not blocks:
            raise ProjectError(f"Section {section_index} requires at least one text block.")
        for block_index, block in enumerate(blocks, 1):
            if not isinstance(block, dict):
                raise ProjectError(f"Section {section_index} block {block_index} must be an object.")
            kind = block.get("type")
            if kind not in BLOCK_TYPES:
                raise ProjectError(
                    f"Section {section_index} block {block_index} has unsupported type: {kind!r}."
                )
            if kind in {"paragraph", "subheading", "code"}:
                _require_text(block, "text", f"Section {section_index} block {block_index}")
            elif kind in {"ordered-list", "unordered-list"}:
                items = block.get("items")
                if not isinstance(items, list) or not items or not all(
                    isinstance(item, str) and item.strip() for item in items
                ):
                    raise ProjectError(
                        f"Section {section_index} block {block_index} requires non-empty text items."
                    )
            elif kind == "table":
                columns = block.get("columns")
                rows = block.get("rows")
                if not isinstance(columns, list) or not columns or not all(
                    isinstance(value, str) and value.strip() for value in columns
                ):
                    raise ProjectError(
                        f"Section {section_index} block {block_index} requires table columns."
                    )
                if not isinstance(rows, list) or not rows or any(
                    not isinstance(row, list)
                    or len(row) != len(columns)
                    or not all(isinstance(value, str) for value in row)
                    for row in rows
                ):
                    raise ProjectError(
                        f"Section {section_index} block {block_index} has invalid table rows."
                    )
    return manifest


def load_project(directory: Path) -> ManualProject:
    """Load and validate a manual project from its directory."""

    directory = directory.resolve()
    manifest_path = directory / "manual.json"
    if not manifest_path.is_file():
        raise ProjectError(f"Manual manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ProjectError(f"Manual manifest is not valid JSON: {error}") from error
    return ManualProject(directory=directory, manifest=validate_manifest(manifest, manifest_path))


def resolve_project(repo_root: Path, slug: str) -> ManualProject:
    """Resolve a repository manual by slug."""

    validate_slug(slug)
    directory = repo_root.resolve() / "manuals" / slug
    if not directory.is_dir():
        raise ProjectError(f"Unknown manual slug '{slug}': {directory}")
    return load_project(directory)


def create_project(repo_root: Path, slug: str, title: str) -> ManualProject:
    """Create a minimal, deterministic, text-only manual project."""

    validate_slug(slug)
    if not isinstance(title, str) or not title.strip():
        raise ProjectError("Manual title must be non-empty text.")
    directory = repo_root.resolve() / "manuals" / slug
    if directory.exists():
        raise ProjectError(f"Refusing to overwrite existing manual directory: {directory}")
    directory.parent.mkdir(parents=True, exist_ok=True)
    directory.mkdir()

    manifest = {
        "document": {
            "title": title,
            "subtitle": "[EDIT: Add a short subtitle or remove this line.]",
            "author": "ObsoleteSony",
            "subject": title,
            "keywords": f"{slug}, user guide",
            "filenameStem": f"{slug}-user-guide",
        },
        "sections": [
            {
                "title": "Getting started",
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "[EDIT: Explain what the reader can do first.]",
                    },
                    {
                        "type": "ordered-list",
                        "items": [
                            "[EDIT: Add the first step.]",
                            "[EDIT: Add the next step.]",
                        ],
                    },
                    {
                        "type": "code",
                        "text": "[EDIT: Add a command or path only if it helps the reader.]",
                    },
                ],
            }
        ],
    }
    (directory / "manual.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    readme = f"""# {title}

Edit `manual.json`, then build and validate from the repository root:

```powershell
.\\scripts\\build-manual.ps1 -Slug "{slug}"
.\\scripts\\validate-manual.ps1 -Slug "{slug}"
```

The project begins with text only. Add a visual only when the instructions are
materially harder to understand without it.
"""
    (directory / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    return load_project(directory)
