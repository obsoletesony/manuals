"""Common edition paths and PDF assembly mechanics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject


@dataclass(frozen=True)
class EditionPaths:
    """Canonical paths for the three supported manual editions."""

    reader: Path
    print: Path
    spreads: Path


def edition_paths(output_dir: Path, filename_stem: str) -> EditionPaths:
    """Resolve stable edition filenames and create their output directory."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return EditionPaths(
        reader=output_dir / f"{filename_stem}.pdf",
        print=output_dir / f"{filename_stem}-Print.pdf",
        spreads=output_dir / f"{filename_stem}-Spreads.pdf",
    )


def _dimensions(value: float | tuple[float, float]) -> tuple[float, float]:
    return value if isinstance(value, tuple) else (value, value)


def add_print_boxes(
    path: Path,
    *,
    print_size: float | tuple[float, float],
    bleed: float | tuple[float, float],
    trim: float | tuple[float, float],
) -> None:
    """Apply media, bleed, trim, and crop boxes to a print edition."""

    print_width, print_height = _dimensions(print_size)
    bleed_x, bleed_y = _dimensions(bleed)
    trim_width, trim_height = _dimensions(trim)
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (print_width, print_height)
        page.bleedbox.lower_left = (0, 0)
        page.bleedbox.upper_right = (print_width, print_height)
        page.trimbox.lower_left = (bleed_x, bleed_y)
        page.trimbox.upper_right = (bleed_x + trim_width, bleed_y + trim_height)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (print_width, print_height)
        writer.add_page(page)
    writer.add_metadata(reader.metadata or {})
    with path.open("wb") as handle:
        writer.write(handle)


def build_spreads(
    reader_path: Path,
    spread_path: Path,
    *,
    spread_size: tuple[float, float],
    page_width: float,
    metadata: Mapping[str, str],
) -> None:
    """Assemble reader pages into deterministic two-page spreads."""

    reader = PdfReader(str(reader_path))
    total_pages = len(reader.pages)
    pairs: list[tuple[int | None, int]] = (
        [(None, 1)] if total_pages % 2 else [(total_pages, 1)]
    ) + [(left, left + 1) for left in range(2, total_pages, 2)]
    writer = PdfWriter()
    for left_number, right_number in pairs:
        spread = PageObject.create_blank_page(width=spread_size[0], height=spread_size[1])
        if left_number is not None:
            spread.merge_transformed_page(
                reader.pages[left_number - 1], Transformation().translate(0, 0)
            )
        spread.merge_transformed_page(
            reader.pages[right_number - 1], Transformation().translate(page_width, 0)
        )
        writer.add_page(spread)
    writer.add_metadata(dict(metadata))
    with spread_path.open("wb") as handle:
        writer.write(handle)
