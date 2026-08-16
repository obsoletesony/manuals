"""Product-neutral tools for deterministic user-guide PDFs."""

from .deterministic import PdfMetadata, apply_metadata, content_image_reader, invariant_canvas
from .document import EditionPaths, add_print_boxes, build_spreads, edition_paths
from .project import ManualProject, ProjectError, create_project, load_project, resolve_project

__all__ = [
    "EditionPaths",
    "PdfMetadata",
    "ManualProject",
    "ProjectError",
    "add_print_boxes",
    "apply_metadata",
    "build_spreads",
    "content_image_reader",
    "create_project",
    "edition_paths",
    "invariant_canvas",
    "load_project",
    "resolve_project",
]
