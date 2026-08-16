"""Product-neutral tools for deterministic user-guide PDFs."""

from .deterministic import PdfMetadata, apply_metadata, content_image_reader, invariant_canvas
from .document import EditionPaths, add_print_boxes, build_spreads, edition_paths

__all__ = [
    "EditionPaths",
    "PdfMetadata",
    "add_print_boxes",
    "apply_metadata",
    "build_spreads",
    "content_image_reader",
    "edition_paths",
    "invariant_canvas",
]
