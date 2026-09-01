#!/usr/bin/env python3
"""Focused structural and content preflight for the PSPMAN manual."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw
from pypdf import PdfReader
import pypdfium2 as pdfium

from styles import BLEED, PRINT_SIZE, SPREAD_SIZE, TRIM, mm
from manual_provenance import manual_input_digest

SOURCE_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SOURCE_DIR.parent
REPO_ROOT = MANUAL_DIR.parents[1]
OUTPUT = MANUAL_DIR / "output"
RENDER = MANUAL_DIR / "rendered"


def close(a: float, b: float, tolerance: float = 0.5) -> bool:
    return abs(a - b) <= tolerance


def page_size(page) -> tuple[float, float]:
    return float(page.mediabox.width), float(page.mediabox.height)


def embedded_fonts(reader: PdfReader) -> tuple[set[str], list[str]]:
    names: set[str] = set()
    missing: list[str] = []
    for index, page in enumerate(reader.pages, 1):
        fonts = page.get("/Resources", {}).get("/Font", {})
        fonts = fonts.get_object() if hasattr(fonts, "get_object") else fonts
        content = page.get_contents()
        stream = content.get_data().decode("latin1", "ignore") if content is not None else ""
        # ReportLab initializes every page with an unused Helvetica text state.
        # Validate only fonts followed by a text-showing operator before another
        # font selection, so an unused Base-14 resource is not mistaken for
        # visible typography.
        used_keys = {
            "/" + match.group(1)
            for match in re.finditer(
                r"/(F\S+)\s+[\d.]+\s+Tf(?:(?!\s/F\S+\s+[\d.]+\s+Tf).)*?(?:Tj|TJ)",
                stream,
                re.DOTALL,
            )
        }
        for key, ref in fonts.items():
            if str(key) not in used_keys:
                continue
            font = ref.get_object()
            name = str(font.get("/BaseFont", "unknown"))
            names.add(name)
            descriptor = font.get("/FontDescriptor")
            if not descriptor:
                missing.append(f"page {index}: {name} has no embedded font descriptor")
                continue
            descriptor = descriptor.get_object()
            if not any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                missing.append(f"page {index}: {name}")
    return names, missing


def approved_screenshots() -> None:
    required = {
        "library-home-480x272.png", "all-songs-480x272.png",
        "now-playing-480x272.png", "cassette-480x272.png", "about-480x272.png",
    }
    paths = sorted((MANUAL_DIR / "assets" / "screenshots").glob("*.png"))
    names = {path.name for path in paths}
    if names != required:
        raise AssertionError(f"Screenshot set mismatch: expected {sorted(required)}, got {sorted(names)}")
    for path in paths:
        image = Image.open(path)
        if image.size != (480, 272):
            raise AssertionError(f"Screenshot must be native 480x272: {path.name} {image.size}")
        lowered = path.name.lower()
        if any(term in lowered for term in ("shiver", "brightside", "weeknd", "oasis", "coldplay", "gorillaz")):
            raise AssertionError(f"Unapproved screenshot filename: {path.name}")


def assert_monochrome(path: Path) -> None:
    """Require every rendered production page to contain neutral RGB values."""
    document = pdfium.PdfDocument(str(path))
    for page_number in range(len(document)):
        image = document[page_number].render(scale=0.75).to_pil().convert("RGB")
        red, green, blue = image.split()
        if ImageChops.difference(red, green).getbbox() or ImageChops.difference(red, blue).getbbox():
            raise AssertionError(f"Production PDF contains color on page {page_number + 1}")


def validate() -> dict:
    reader_path = OUTPUT / "PSPMAN-User-Guide.pdf"
    spread_path = OUTPUT / "PSPMAN-User-Guide-Spreads.pdf"
    print_path = OUTPUT / "PSPMAN-User-Guide-Print.pdf"
    for path in (reader_path, spread_path, print_path):
        if not path.exists():
            raise AssertionError(f"Required output missing: {path}")
    reader = PdfReader(str(reader_path))
    spreads = PdfReader(str(spread_path))
    print_pdf = PdfReader(str(print_path))
    expected_titles = json.loads((MANUAL_DIR / "content" / "manual.yaml").read_text(encoding="utf-8"))["pages"]
    page_count = len(expected_titles)
    assert page_count == 15, page_count
    assert len(reader.pages) == page_count, len(reader.pages)
    assert len(spreads.pages) == (page_count + 1) // 2, len(spreads.pages)
    assert len(print_pdf.pages) == page_count, len(print_pdf.pages)
    assert all(close(w, TRIM) and close(h, TRIM) for w, h in map(page_size, reader.pages))
    assert all(close(w, SPREAD_SIZE[0]) and close(h, SPREAD_SIZE[1]) for w, h in map(page_size, spreads.pages))
    assert all(close(w, PRINT_SIZE) and close(h, PRINT_SIZE) for w, h in map(page_size, print_pdf.pages))
    for index, page in enumerate(print_pdf.pages, 1):
        assert close(float(page.trimbox.left), BLEED) and close(float(page.trimbox.bottom), BLEED), index
        assert close(float(page.trimbox.width), TRIM) and close(float(page.trimbox.height), TRIM), index
        assert close(float(page.bleedbox.width), PRINT_SIZE) and close(float(page.bleedbox.height), PRINT_SIZE), index
    page_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(page_text)
    normalized_text = re.sub(r"\s+", " ", text).strip()
    textless_pages = [index for index, value in enumerate(page_text, 1) if not value.strip()]
    if textless_pages != [page_count] or expected_titles[-1].get("kind") != "back-cover":
        raise AssertionError(f"Reader PDF contains an accidental blank page: {textless_pages}")
    package_version = json.loads((REPO_ROOT / "package.json").read_text(encoding="utf-8"))["version"]
    required = [
        "PSPMAN", "User's Guide",
        "obsoletesony.com/pspman", "obsoletesony.com/pspman/report-a-bug", "github.com/obsoletesony/PSPMAN-Issues",
        "0.1.0-alpha.2", "stereo 16-bit / 44.1 kHz FLAC", "Cassette View", "Track Information",
        "Supported files and limits", "PSP-1000", "64 MB of RAM", "PSP Street (E1000)",
        "Custom firmware or another working homebrew environment", "1,000 tracks", "12 folder levels",
        "embedded JPEG and PNG cover art", "No Cover", "Some Japanese characters may not display correctly",
        "Copyright 2026 ObsoleteSony. All rights reserved.", "PSPMAN is built with PocketJS.",
    ]
    missing_text = [value for value in required if value.casefold() not in normalized_text.casefold()]
    if missing_text:
        raise AssertionError(f"Required text missing: {missing_text}")
    checksums = json.loads((OUTPUT / "checksums.json").read_text(encoding="utf-8"))
    provenance = checksums.get("manualProvenance", {})
    expected_digest, expected_file_count = manual_input_digest(REPO_ROOT, MANUAL_DIR)
    if provenance.get("scope") != "user-guide-output":
        raise AssertionError("Manual checksums have the wrong provenance scope")
    if provenance.get("schemaVersion") != 1:
        raise AssertionError("Manual checksums have an unsupported provenance schema")
    if provenance.get("inputTreeSha256") != expected_digest:
        raise AssertionError("Manual output provenance is stale for the current manual inputs")
    if provenance.get("inputFileCount") != expected_file_count:
        raise AssertionError("Manual output provenance input count does not match current inputs")
    forbidden = [
        "modern", "LLC.", "Sony Walkman", "28960401M",
        "current build", "canonical build", "primary verified",
        "not yet broadly verified", "needs broader verification", "verified real-time",
        "centralized quit", "bounded diagnostics", "native resources",
        "recorded in the PDF metadata", "rights-clean", "Vita backend",
        "Frequently asked questions", "Navigation map", "Hi-Res processing",
        "Performance and file guidance", "Expanded information",
        "Basic operation gives the shortest path to a result",
        "Technical notes explain source formats", "Notes clarify behavior",
        "identifies accepted source files", "ultimately submitted as",
        "direct playback-screen shortcut", "has a contextual purpose",
        "preserves the storage hierarchy", "complete original values",
        "when the current screen permits it", "content is probed",
        "display versus stored data",
        "bounded", "collision-safe", "best effort", "safe No Cover fallback",
        "reusable artwork cache entries", "bounded native decode path",
        "qualified Japanese characters", "packaging and interaction preflight",
        "rendered title width", "truly exceeds the space", "decoded samples",
        "bounded buffers", "native audio path", "PPSSPP",
        "Button names",
        "These instructions use CROSS, CIRCLE, SQUARE, TRIANGLE, L, R, START, SELECT, and HOME as labeled on the PSP.",
        "Safe listening", "Set a comfortable volume",
        "Real-hardware testing currently covers", "PSP-2001", "5.00 M33-4",
    ]
    present_forbidden = [value for value in forbidden if re.search(re.escape(value), text, re.IGNORECASE)]
    if present_forbidden:
        raise AssertionError(f"Forbidden wording present: {present_forbidden}")
    if "\u2014" in text:
        raise AssertionError("Manual contains an em dash")
    if "Parts and controls" in normalized_text:
        raise AssertionError("The removed Parts and controls page remains in the manual")
    if "OPERATING INSTRUCTIONS" in text.upper():
        raise AssertionError("The obsolete Operating Instructions title remains in the manual")
    if page_text[0].count("USER'S GUIDE") != 1 or "USER'S GUIDE" in page_text[-1]:
        raise AssertionError("USER'S GUIDE must appear on the front cover only")
    if "PSPMAN USER'S GUIDE" in normalized_text:
        raise AssertionError("The removed interior footer label remains in the manual")
    if "OS-PSPMAN-01 (2)" in normalized_text:
        raise AssertionError("The removed document code remains on a manual page")
    wrong_titles = [
        f"page {record['number']}: {record['title']}"
        for record in expected_titles
        if record.get("kind") not in {"cover", "back-cover"}
        if record["title"] not in page_text[record["number"] - 1]
    ]
    if wrong_titles:
        raise AssertionError(f"Required page headings missing: {wrong_titles}")
    all_fonts: set[str] = set()
    for label, document in (("reader", reader), ("spreads", spreads), ("print", print_pdf)):
        fonts, missing_fonts = embedded_fonts(document)
        all_fonts.update(fonts)
        if missing_fonts:
            raise AssertionError(f"Fonts not embedded in {label}: {missing_fonts}")
    if not all("Inter" in name for name in all_fonts):
        raise AssertionError(f"Unexpected visible font: {sorted(all_fonts)}")
    metadata = reader.metadata
    for key in ("/Title", "/Author", "/Subject", "/Keywords"):
        if not metadata.get(key):
            raise AssertionError(f"PDF metadata missing {key}")
    if metadata.get("/Title") != "PSPMAN User's Guide":
        raise AssertionError(f"Unexpected PDF title: {metadata.get('/Title')}")
    if metadata.get("/Subject") != "User's guide for PSPMAN":
        raise AssertionError(f"Unexpected PDF subject: {metadata.get('/Subject')}")
    if spreads.metadata.get("/Subject") != "User's guide for PSPMAN":
        raise AssertionError(f"Unexpected spread PDF subject: {spreads.metadata.get('/Subject')}")
    if print_pdf.metadata.get("/Subject") != "User's guide for PSPMAN":
        raise AssertionError(f"Unexpected print PDF subject: {print_pdf.metadata.get('/Subject')}")
    if package_version in str(metadata):
        raise AssertionError("PDF metadata exposes a development version")
    development_terms = re.compile(r"\b(?:fixture|QA|backend)\b", re.IGNORECASE)
    if development_terms.search(text):
        raise AssertionError(f"Development terminology present: {development_terms.search(text).group(0)}")
    independence = "PSPMAN is an independent homebrew project and is not affiliated with or endorsed by Sony Group Corporation or Sony Interactive Entertainment."
    independence_count = normalized_text.count(independence)
    if independence_count != 1:
        raise AssertionError(f"Independence statement must appear exactly once as text, found {independence_count}")
    compatibility_statement = "PSPMAN accepts stereo 16-bit / 44.1 kHz FLAC."
    compatibility_count = normalized_text.count(compatibility_statement)
    if compatibility_count != 1:
        raise AssertionError(f"Definitive compatibility statement must appear exactly once, found {compatibility_count}")
    if not reader.outline:
        raise AssertionError("Reader PDF has no bookmarks")
    annotations = sum(len(page.get("/Annots", [])) for page in reader.pages)
    if annotations == 0:
        raise AssertionError("Reader PDF has no link annotations")
    uris = {
        str(annotation.get_object().get("/A", {}).get("/URI"))
        for page in reader.pages
        for annotation in page.get("/Annots", [])
        if annotation.get_object().get("/A", {}).get("/URI")
    }
    expected_uris = {"https://www.obsoletesony.com/pspman"}
    if not expected_uris.issubset(uris):
        raise AssertionError(f"Required hyperlinks missing: {sorted(expected_uris - uris)}")
    pairs: list[tuple[int | None, int]] = (
        [(None, 1)] if page_count % 2 else [(page_count, 1)]
    ) + [(page, page + 1) for page in range(2, page_count, 2)]
    spread_text = [page.extract_text() or "" for page in spreads.pages]
    for index, (left, right) in enumerate(pairs):
        for page_number in (left, right):
            if page_number is None:
                continue
            record = expected_titles[page_number - 1]
            if record.get("kind") in {"cover", "back-cover"}:
                continue
            marker = record["title"]
            if marker not in spread_text[index]:
                raise AssertionError(f"Spread {index + 1} is missing paired page {page_number}: {marker}")
    approved_screenshots()
    assert_monochrome(reader_path)
    measurement_path = OUTPUT / "measurement-report.json"
    if not measurement_path.exists():
        raise AssertionError("Measurement report is missing")
    measurements = json.loads(measurement_path.read_text(encoding="utf-8"))["pages"]
    by_page = {entry["page"]: entry for entry in measurements}
    for page_number, entry in by_page.items():
        if page_number % 2 == 0:
            expected_x0, expected_x1 = mm(12), TRIM - mm(15)
        else:
            expected_x0, expected_x1 = mm(15), TRIM - mm(12)
        if not close(entry["frameX0Pt"], expected_x0) or not close(entry["frameX1Pt"], expected_x1):
            raise AssertionError(f"Page {page_number} frame is not mirrored correctly: {entry}")
    if any(entry["lowerClearanceToFooterRulePt"] < 12 for entry in measurements):
        raise AssertionError("Manual content enters the footer clear area")
    for entry in measurements:
        unexplained = [gap for gap in entry["majorGaps"] if gap["gapPt"] > 24.5]
        if unexplained and not entry.get("intentionalException"):
            raise AssertionError(f"Page {entry['page']} has an unexplained internal gap: {unexplained}")
    if any(
        visual["name"].startswith("diagram:")
        for entry in measurements
        for visual in entry["principalVisuals"]
    ):
        raise AssertionError("A diagram remains in the manual")
    return {
        "pages": len(reader.pages), "spreads": len(spreads.pages),
        "visibleFonts": sorted(all_fonts), "embeddedFonts": "pass",
        "requiredText": "pass", "pageHeadings": "pass", "metadata": "pass",
        "bookmarks": "pass", "linkAnnotations": annotations,
        "hyperlinks": sorted(uris), "spreadPairing": "pass", "blankPages": "pass",
        "printBoxes": "pass", "screenshots": "pass", "monochrome": "pass", "measurementReport": "pass",
    }


def contact_sheet(images: list[Image.Image], path: Path, *, labels: list[str]) -> Path:
    columns = 4
    rows = (len(images) + columns - 1) // columns
    cell_w, cell_h = 260, 245
    contact = Image.new("RGB", (cell_w * columns, cell_h * rows), "#d6d6d6")
    draw = ImageDraw.Draw(contact)
    for index, image in enumerate(images):
        thumb = image.copy()
        thumb.thumbnail((250, 220))
        x = (index % columns) * cell_w + (cell_w - thumb.width) // 2
        y = (index // columns) * cell_h
        contact.paste(thumb, (x, y))
        draw.text((index % columns * cell_w + 5, y + 222), labels[index], fill="#111111")
    contact.save(path, optimize=True)
    return path


def render() -> dict[str, str]:
    RENDER.mkdir(parents=True, exist_ok=True)
    for path in RENDER.glob("page-*.png"):
        path.unlink()
    for path in RENDER.glob("print-scale-page-*.png"):
        path.unlink()
    for pattern in ("spread-*.png", "grid-page-*.png"):
        for path in RENDER.glob(pattern):
            path.unlink()
    pdf = pdfium.PdfDocument(str(OUTPUT / "PSPMAN-User-Guide.pdf"))
    pages: list[Image.Image] = []
    for index in range(len(pdf)):
        bitmap = pdf[index].render(scale=2.5)
        image = bitmap.to_pil().convert("RGB")
        page_path = RENDER / f"page-{index + 1:02d}.png"
        image.save(page_path, optimize=True)
        pages.append(image)
    contact_path = RENDER / "contact-sheet.png"
    contact_sheet(pages, contact_path, labels=[f"{index:02d}" for index in range(1, len(pdf) + 1)])
    spread_pdf = pdfium.PdfDocument(str(OUTPUT / "PSPMAN-User-Guide-Spreads.pdf"))
    spread_paths: list[str] = []
    for spread_index, left_page in enumerate(range(2, len(pdf), 2), 1):
        spread_image = spread_pdf[spread_index].render(scale=2.5).to_pil().convert("RGB")
        spread_path = RENDER / f"spread-{left_page:02d}-{left_page + 1:02d}.png"
        spread_image.save(spread_path, optimize=True)
        spread_paths.append(str(spread_path))
    grid_contact = None
    grid_pdf_path = RENDER / "diagnostic-grid.pdf"
    if grid_pdf_path.exists():
        grid_pdf = pdfium.PdfDocument(str(grid_pdf_path))
        grid_pages: list[Image.Image] = []
        for index in range(len(grid_pdf)):
            grid_image = grid_pdf[index].render(scale=2.5).to_pil().convert("RGB")
            grid_path = RENDER / f"grid-page-{index + 1:02d}.png"
            grid_image.save(grid_path, optimize=True)
            grid_pages.append(grid_image)
        grid_contact = RENDER / "diagnostic-grid-contact-sheet.png"
        contact_sheet(grid_pages, grid_contact, labels=[f"{index:02d}" for index in range(1, len(grid_pages) + 1)])
    # Representative pages at 96 dpi, corresponding to the real 120 mm trim
    # size on a standard-density display or printer.
    for page_number in (3, 5, 7, 9, 11, 14):
        bitmap = pdf[page_number - 1].render(scale=96 / 72)
        bitmap.to_pil().convert("RGB").save(
            RENDER / f"print-scale-page-{page_number:02d}.png", optimize=True
        )
    return {
        "contactSheet": str(contact_path),
        "spreadRenders": str(RENDER / "spread-02-03.png") + " ... " + str(RENDER / f"spread-{2 * ((len(pdf) - 1) // 2):02d}-{2 * ((len(pdf) - 1) // 2) + 1:02d}.png"),
        "diagnosticGridContactSheet": str(grid_contact) if grid_contact else "not generated",
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic() -> dict:
    with tempfile.TemporaryDirectory(prefix="pspman-manual-") as first, tempfile.TemporaryDirectory(prefix="pspman-manual-") as second:
        python = Path(__import__("sys").executable)
        for directory in (first, second):
            subprocess.run([str(python), str(SOURCE_DIR / "build_manual.py"), "--output-dir", directory], cwd=REPO_ROOT, check=True, capture_output=True, text=True)
        names = ["PSPMAN-User-Guide.pdf", "PSPMAN-User-Guide-Spreads.pdf", "PSPMAN-User-Guide-Print.pdf"]
        if any(" " in name or "'" in name for name in names):
            raise AssertionError("Generated PDF filenames must not contain spaces or apostrophes")
        results = {name: sha256(Path(first) / name) == sha256(Path(second) / name) for name in names}
        if not all(results.values()):
            raise AssertionError(f"Non-deterministic output: {results}")
        return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--determinism", action="store_true")
    args = parser.parse_args()
    result = validate()
    if args.render:
        result.update(render())
    if args.determinism:
        result["deterministic"] = deterministic()
    (OUTPUT / "preflight.json").write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
