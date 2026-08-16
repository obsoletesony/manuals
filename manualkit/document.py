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


def add_print_boxes(path: Path, *, print_size: float, bleed: float, trim: float) -> None:
    """Apply media, bleed, trim, and crop boxes to a print edition."""

    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (print_size, print_size)
        page.bleedbox.lower_left = (0, 0)
        page.bleedbox.upper_right = (print_size, print_size)
        page.trimbox.lower_left = (bleed, bleed)
        page.trimbox.upper_right = (bleed + trim, bleed + trim)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (print_size, print_size)
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
