"""Deterministic ReportLab resource and metadata helpers."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Mapping

from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


@dataclass(frozen=True)
class PdfMetadata:
    """Metadata written in a stable order to a ReportLab canvas."""

    title: str
    author: str
    creator: str
    subject: str
    keywords: str


def invariant_canvas(path: Path, page_size: tuple[float, float]) -> canvas.Canvas:
    """Create the invariant, compressed canvas used by generated editions."""

    return canvas.Canvas(str(path), pagesize=page_size, pageCompression=1, invariant=1)


def apply_metadata(target: canvas.Canvas, metadata: PdfMetadata) -> None:
    """Apply document metadata in a deterministic order."""

    target.setTitle(metadata.title)
    target.setAuthor(metadata.author)
    target.setCreator(metadata.creator)
    target.setSubject(metadata.subject)
    target.setKeywords(metadata.keywords)


def content_image_reader(path: Path) -> ImageReader:
    """Load an explicitly supplied image with identity derived from its bytes."""

    return ImageReader(BytesIO(path.read_bytes()))


def register_font_files(definitions: Mapping[str, Path]) -> None:
    """Register explicit font files once, preserving mapping order."""

    registered = set(pdfmetrics.getRegisteredFontNames())
    for name, path in definitions.items():
        if name not in registered:
            pdfmetrics.registerFont(TTFont(name, str(path)))
            registered.add(name)
