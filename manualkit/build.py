"""Build text-first manual projects into Reader, Print, and Spreads editions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from manualkit.document import EditionPaths, add_print_boxes, build_spreads, edition_paths
from manualkit.project import ManualProject, load_project
from manualkit.themes.plain import BLEED, PRINT_SIZE, SPREAD_SIZE, TRIM_SIZE, build_plain_edition


def sha256_file(path: Path) -> str:
    """Return the SHA-256 of one output file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_project(project: ManualProject, output_dir: Path | None = None) -> dict:
    """Build all supported editions for one validated project."""

    output_dir = (output_dir or project.output_dir).resolve()
    paths = edition_paths(output_dir, project.document["filenameStem"])
    reader_layout = build_plain_edition(paths.reader, project, print_edition=False)
    build_plain_edition(paths.print, project, print_edition=True)
    add_print_boxes(paths.print, print_size=PRINT_SIZE, bleed=BLEED, trim=TRIM_SIZE)
    build_spreads(
        paths.reader,
        paths.spreads,
        spread_size=SPREAD_SIZE,
        page_width=TRIM_SIZE[0],
        metadata={
            "/Title": f"{project.document['title']} - Reader Spreads",
            "/Subject": project.document["subject"],
            "/Author": project.document["author"],
            "/Creator": "ObsoleteSony manualkit",
        },
    )
    outputs = {
        path.name: {"bytes": path.stat().st_size, "sha256": sha256_file(path)}
        for path in (paths.reader, paths.print, paths.spreads)
    }
    report = {
        "project": project.directory.name,
        "outputs": outputs,
        "layout": reader_layout,
    }
    (output_dir / "build-report.json").write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report


def build_project_directory(project_dir: Path, output_dir: Path | None = None) -> dict:
    """Load a project directory and build all editions."""

    return build_project(load_project(project_dir), output_dir)


def project_edition_paths(project: ManualProject, output_dir: Path | None = None) -> EditionPaths:
    """Return edition paths without building them."""

    return edition_paths((output_dir or project.output_dir).resolve(), project.document["filenameStem"])
