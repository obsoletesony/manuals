"""Structural, rendering, and determinism checks for text-first manuals."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import tempfile

from PIL import Image, ImageDraw
from pypdf import PdfReader
import pypdfium2 as pdfium

from manualkit.build import build_project, project_edition_paths, sha256_file
from manualkit.project import ManualProject, load_project
from manualkit.themes.plain import BLEED, PRINT_SIZE, SPREAD_SIZE, TRIM_SIZE


def _close(left: float, right: float, tolerance: float = 0.01) -> bool:
    return abs(left - right) <= tolerance


def _page_size(page) -> tuple[float, float]:
    return float(page.mediabox.width), float(page.mediabox.height)


def _image_xobjects(reader: PdfReader) -> list[str]:
    images: list[str] = []
    for page_number, page in enumerate(reader.pages, 1):
        resources = page.get("/Resources", {})
        resources = resources.get_object() if hasattr(resources, "get_object") else resources
        xobjects = resources.get("/XObject", {})
        xobjects = xobjects.get_object() if hasattr(xobjects, "get_object") else xobjects
        for name, reference in xobjects.items():
            value = reference.get_object()
            if value.get("/Subtype") == "/Image":
                images.append(f"page {page_number}: {name}")
    return images


def _render_pdf(path: Path, destination: Path, prefix: str) -> list[Path]:
    destination.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(path))
    rendered: list[Path] = []
    try:
        for index in range(len(document)):
            image = document[index].render(scale=1.5).to_pil().convert("RGB")
            output = destination / f"{prefix}-{index + 1:02d}.png"
            image.save(output, optimize=True)
            image.close()
            rendered.append(output)
    finally:
        document.close()
    return rendered


def _contact_sheet(paths: list[Path], destination: Path) -> None:
    images: list[Image.Image] = []
    for path in paths:
        with Image.open(path) as source:
            images.append(source.convert("RGB"))
    columns = 3
    cell_width, cell_height = 310, 460
    rows = (len(images) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * cell_width, rows * cell_height), "#dddddd")
    draw = ImageDraw.Draw(sheet)
    for index, image in enumerate(images):
        image.thumbnail((290, 420))
        column, row = index % columns, index // columns
        x = column * cell_width + (cell_width - image.width) // 2
        y = row * cell_height + 8
        sheet.paste(image, (x, y))
        draw.text((column * cell_width + 8, row * cell_height + 432), str(index + 1), fill="#111111")
        image.close()
    sheet.save(destination, optimize=True)


def render_project(project: ManualProject, output_dir: Path, render_dir: Path) -> dict:
    """Render every page in all editions and create a Reader contact sheet."""

    paths = project_edition_paths(project, output_dir)
    render_dir.mkdir(parents=True, exist_ok=True)
    reader_pages = _render_pdf(paths.reader, render_dir / "reader", "page")
    print_pages = _render_pdf(paths.print, render_dir / "print", "page")
    spread_pages = _render_pdf(paths.spreads, render_dir / "spreads", "spread")
    contact = render_dir / "contact-sheet.png"
    _contact_sheet(reader_pages, contact)
    return {
        "readerPages": len(reader_pages),
        "printPages": len(print_pages),
        "spreadPages": len(spread_pages),
        "contactSheet": str(contact),
    }


def deterministic_build(project: ManualProject) -> dict[str, dict]:
    """Build twice in one process environment and compare raw edition bytes."""

    with tempfile.TemporaryDirectory(prefix="manualkit-determinism-") as temporary:
        root = Path(temporary)
        first = root / "first"
        second = root / "second"
        build_project(project, first)
        build_project(project, second)
        first_paths = project_edition_paths(project, first)
        second_paths = project_edition_paths(project, second)
        result: dict[str, dict] = {}
        for left, right in zip(
            (first_paths.reader, first_paths.print, first_paths.spreads),
            (second_paths.reader, second_paths.print, second_paths.spreads),
            strict=True,
        ):
            if left.read_bytes() != right.read_bytes():
                raise AssertionError(f"Repeated builds differ: {left.name}")
            result[left.name] = {
                "bytes": left.stat().st_size,
                "sha256": sha256_file(left),
                "byteIdentical": True,
            }
        return result


def cross_root_determinism(project_dir: Path) -> dict[str, dict]:
    """Build twice from each of two copied project roots and compare raw bytes."""

    with tempfile.TemporaryDirectory(prefix="manualkit-cross-root-") as temporary:
        root = Path(temporary)
        project_roots = {
            "rootA": root / "project-a",
            "rootB": root / "different" / "nested" / "project-b",
        }
        built: dict[str, dict[str, Path]] = {}
        for label, destination in project_roots.items():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(
                project_dir,
                destination,
                ignore=shutil.ignore_patterns("output", "rendered", "__pycache__", "*.pyc"),
            )
            project = load_project(destination)
            first_output = root / "outputs" / label / "first"
            second_output = root / "outputs" / label / "second"
            build_project(project, first_output)
            build_project(project, second_output)
            first_paths = project_edition_paths(project, first_output)
            second_paths = project_edition_paths(project, second_output)
            editions = {}
            for first, second in zip(
                (first_paths.reader, first_paths.print, first_paths.spreads),
                (second_paths.reader, second_paths.print, second_paths.spreads),
                strict=True,
            ):
                if first.read_bytes() != second.read_bytes():
                    raise AssertionError(f"Same-root builds differ in {label}: {first.name}")
                editions[first.name] = first
            built[label] = editions

        result: dict[str, dict] = {}
        for filename, left in built["rootA"].items():
            right = built["rootB"][filename]
            if left.read_bytes() != right.read_bytes():
                raise AssertionError(f"Cross-root builds differ: {filename}")
            result[filename] = {
                "bytes": left.stat().st_size,
                "sha256": sha256_file(left),
                "sameRootBuildsPerPath": 2,
                "crossRootByteIdentical": True,
            }
        return result


def validate_project(
    project: ManualProject,
    output_dir: Path | None = None,
    *,
    render_dir: Path | None = None,
    check_determinism: bool = True,
) -> dict:
    """Validate structure, bounds, metadata, rendering, and determinism."""

    output_dir = (output_dir or project.output_dir).resolve()
    paths = project_edition_paths(project, output_dir)
    for path in (paths.reader, paths.print, paths.spreads):
        if not path.is_file():
            raise AssertionError(f"Required edition is missing: {path}")
    report_path = output_dir / "build-report.json"
    if not report_path.is_file():
        raise AssertionError(f"Build report is missing: {report_path}")
    build_report = json.loads(report_path.read_text(encoding="utf-8"))

    reader = PdfReader(BytesIO(paths.reader.read_bytes()))
    print_pdf = PdfReader(BytesIO(paths.print.read_bytes()))
    spreads = PdfReader(BytesIO(paths.spreads.read_bytes()))
    page_count = build_report["layout"]["pages"]
    if len(reader.pages) != page_count or len(print_pdf.pages) != page_count:
        raise AssertionError("Reader and Print page counts do not match the layout report.")
    if len(spreads.pages) != (page_count + 1) // 2:
        raise AssertionError("Spread page count is incorrect.")
    if not all(
        _close(width, TRIM_SIZE[0]) and _close(height, TRIM_SIZE[1])
        for width, height in map(_page_size, reader.pages)
    ):
        raise AssertionError("Reader page dimensions are incorrect.")
    if not all(
        _close(width, PRINT_SIZE[0]) and _close(height, PRINT_SIZE[1])
        for width, height in map(_page_size, print_pdf.pages)
    ):
        raise AssertionError("Print page dimensions are incorrect.")
    if not all(
        _close(width, SPREAD_SIZE[0]) and _close(height, SPREAD_SIZE[1])
        for width, height in map(_page_size, spreads.pages)
    ):
        raise AssertionError("Spread page dimensions are incorrect.")

    for page in print_pdf.pages:
        if not (
            _close(float(page.trimbox.left), BLEED)
            and _close(float(page.trimbox.bottom), BLEED)
            and _close(float(page.trimbox.width), TRIM_SIZE[0])
            and _close(float(page.trimbox.height), TRIM_SIZE[1])
        ):
            raise AssertionError("Print trim or bleed boxes are incorrect.")

    metadata = reader.metadata or {}
    expected_metadata = {
        "/Title": project.document["title"],
        "/Author": project.document["author"],
        "/Creator": "ObsoleteSony manualkit",
        "/Subject": project.document["subject"],
        "/Keywords": project.document["keywords"],
    }
    for key, expected in expected_metadata.items():
        if str(metadata.get(key, "")) != expected:
            raise AssertionError(f"Reader metadata mismatch for {key}: {metadata.get(key)!r}")

    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    normalized_text = re.sub(r"\s+", " ", text).strip()
    required_text = [project.document["title"], *(section["title"] for section in project.sections)]
    missing = [
        value
        for value in required_text
        if re.sub(r"\s+", " ", value).strip() not in normalized_text
    ]
    if missing:
        raise AssertionError(f"Required manual text is missing: {missing}")
    blank_pages = [index for index, page in enumerate(reader.pages, 1) if not (page.extract_text() or "").strip()]
    if blank_pages:
        raise AssertionError(f"Reader contains blank pages: {blank_pages}")

    images = _image_xobjects(reader) + _image_xobjects(print_pdf) + _image_xobjects(spreads)
    if images:
        raise AssertionError(f"Text-first output contains raster image XObjects: {images}")

    for record in build_report["layout"]["records"]:
        if not (
            0 <= record["x0"] <= record["x1"] <= TRIM_SIZE[0]
            and 0 <= record["y0"] <= record["y1"] <= TRIM_SIZE[1]
        ):
            raise AssertionError(f"Layout record clips or overflows the page: {record}")

    result = {
        "pages": page_count,
        "spreads": len(spreads.pages),
        "metadata": "pass",
        "clippingAndOverflow": "pass",
        "rasterImageXObjects": 0,
        "outputs": build_report["outputs"],
    }
    if check_determinism:
        result["deterministic"] = deterministic_build(project)
    if render_dir is not None:
        result["render"] = render_project(project, output_dir, render_dir.resolve())
    return result
