"""Verify PSPMAN manual preservation with one narrow path-sensitive exception."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pypdfium2 as pdfium
from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject


TEST_DIR = Path(__file__).resolve().parent
MANUAL_DIR = TEST_DIR.parent
REPO_ROOT = MANUAL_DIR.parents[1]
REFERENCE = MANUAL_DIR / "reference" / "PSPMAN-User-Guide-approved.pdf"
GENERATED = MANUAL_DIR / "output" / "PSPMAN-User-Guide.pdf"
BUILDER = MANUAL_DIR / "source" / "build_manual.py"
RENDER_DIR = TEST_DIR / "rendered"

APPROVED_SHA256 = "1c8d586db251fbde9d96d20fc58685b3cf99dee0a129677d311431130a90201b"
APPROVED_BYTES = 227_124
RELOCATED_SHA256 = "2f2da3de2b749e99eef21461a5f85c1c1bb2d1deeeac33a8976b043f2cc501b8"
RELOCATED_BYTES = 227_120
EXPECTED_PAGES = 15
EXPECTED_PAGE_POINTS = 340.1575

APPROVED_COVER_NAME = "/FormXob.0a5a692857f3d4c7b01de761e63a0cbb"
RELOCATED_COVER_NAME = "/FormXob.0819ac937093cb9a14c6e855026d3781"
NORMALIZED_COVER_NAME = "/FormXob.PSPMAN_COVER"
EXPECTED_RAW_DIFFERING_OBJECTS = [5, 34, 68, 82]

EXPECTED_OUTPUTS = {
    "PSPMAN-User-Guide.pdf": {
        "bytes": RELOCATED_BYTES,
        "sha256": RELOCATED_SHA256,
    },
    "PSPMAN-User-Guide-Print.pdf": {
        "bytes": 229_262,
        "sha256": "829b7362087088ce580b1ce738f4c8f97642ef168bcd7b548b502be3cf218f97",
    },
    "PSPMAN-User-Guide-Spreads.pdf": {
        "bytes": 506_415,
        "sha256": "5e05244be9fa297e29d78f492b4f266c7c08570495c7d165ac691206c26d87d7",
    },
}

EXPECTED_METADATA = {
    "/Author": "ObsoleteSony",
    "/CreationDate": "D:20000101000000+00'00'",
    "/Creator": "ObsoleteSony",
    "/Keywords": "PSPMAN, ObsoleteSony, PlayStation Portable, user's guide",
    "/ModDate": "D:20000101000000+00'00'",
    "/Producer": "ReportLab PDF Library - (opensource)",
    "/Subject": "User's guide for PSPMAN",
    "/Title": "PSPMAN User's Guide",
    "/Trapped": "/False",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def object_value(value):
    return value.get_object() if hasattr(value, "get_object") else value


def normalize_text(value: str) -> str:
    return value.replace(APPROVED_COVER_NAME, NORMALIZED_COVER_NAME).replace(
        RELOCATED_COVER_NAME, NORMALIZED_COVER_NAME
    )


def canonical_object(value, *, normalize_cover: bool):
    if isinstance(value, IndirectObject):
        return ["reference", value.idnum, value.generation]
    if isinstance(value, StreamObject):
        dictionary = {
            normalize_text(str(key)) if normalize_cover else str(key): canonical_object(
                item, normalize_cover=normalize_cover
            )
            for key, item in value.items()
            if str(key) != "/Length"
        }
        payload = value.get_data()
        if normalize_cover:
            payload = payload.replace(
                APPROVED_COVER_NAME.encode("ascii"), NORMALIZED_COVER_NAME.encode("ascii")
            ).replace(
                RELOCATED_COVER_NAME.encode("ascii"), NORMALIZED_COVER_NAME.encode("ascii")
            )
        return [
            "stream",
            sorted(dictionary.items()),
            len(payload),
            sha256_bytes(payload),
        ]
    if isinstance(value, DictionaryObject):
        return [
            "dictionary",
            sorted(
                (
                    normalize_text(str(key)) if normalize_cover else str(key),
                    canonical_object(item, normalize_cover=normalize_cover),
                )
                for key, item in value.items()
            ),
        ]
    if isinstance(value, ArrayObject):
        return [
            "array",
            [canonical_object(item, normalize_cover=normalize_cover) for item in value],
        ]
    if isinstance(value, (bytes, bytearray)):
        payload = bytes(value)
        return ["bytes", len(payload), sha256_bytes(payload)]
    text = str(value)
    return [type(value).__name__, normalize_text(text) if normalize_cover else text]


def parsed_object_differences(
    approved: PdfReader, relocated: PdfReader, *, normalize_cover: bool
) -> list[int]:
    require(
        int(approved.trailer["/Size"]) == int(relocated.trailer["/Size"]),
        "PDF object counts differ",
    )
    differences: list[int] = []
    for object_id in range(1, int(approved.trailer["/Size"])):
        approved_object = approved.get_object(object_id)
        relocated_object = relocated.get_object(object_id)
        if canonical_object(
            approved_object, normalize_cover=normalize_cover
        ) != canonical_object(relocated_object, normalize_cover=normalize_cover):
            differences.append(object_id)
    return differences


def font_inventory(reader: PdfReader) -> list[dict]:
    inventory: list[dict] = []
    for page_number, page in enumerate(reader.pages, 1):
        resources = object_value(page.get("/Resources", {}))
        fonts = object_value(resources.get("/Font", {}))
        for resource_name, reference in sorted(fonts.items(), key=lambda item: str(item[0])):
            font = object_value(reference)
            embedded: list[dict] = []
            descriptor = font.get("/FontDescriptor")
            if descriptor:
                descriptor = object_value(descriptor)
                for key in ("/FontFile", "/FontFile2", "/FontFile3"):
                    if key in descriptor:
                        payload = object_value(descriptor[key]).get_data()
                        embedded.append(
                            {"kind": key, "bytes": len(payload), "sha256": sha256_bytes(payload)}
                        )
            inventory.append(
                {
                    "page": page_number,
                    "resource": str(resource_name),
                    "baseFont": str(font.get("/BaseFont", "")),
                    "subtype": str(font.get("/Subtype", "")),
                    "embedded": embedded,
                }
            )
    return inventory


def image_inventory(reader: PdfReader, *, normalize_cover: bool) -> list[dict]:
    inventory: list[dict] = []
    for page_number, page in enumerate(reader.pages, 1):
        resources = object_value(page.get("/Resources", {}))
        xobjects = object_value(resources.get("/XObject", {}))
        for resource_name, reference in sorted(xobjects.items(), key=lambda item: str(item[0])):
            image = object_value(reference)
            if image.get("/Subtype") != "/Image":
                continue
            payload = image.get_data()
            name = str(resource_name)
            if normalize_cover:
                name = normalize_text(name)
            filters = object_value(image.get("/Filter", ""))
            if isinstance(filters, list):
                filters = [str(value) for value in filters]
            else:
                filters = str(filters)
            inventory.append(
                {
                    "page": page_number,
                    "resource": name,
                    "width": int(image.get("/Width")),
                    "height": int(image.get("/Height")),
                    "bitsPerComponent": int(image.get("/BitsPerComponent")),
                    "colorSpace": str(object_value(image.get("/ColorSpace", ""))),
                    "filters": filters,
                    "decodedBytes": len(payload),
                    "decodedSha256": sha256_bytes(payload),
                }
            )
    return inventory


def render_inventory(path: Path, destination: Path) -> list[dict]:
    destination.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(str(path))
    inventory: list[dict] = []
    for index in range(len(document)):
        image = document[index].render(scale=2.5).to_pil().convert("RGB")
        output = destination / f"page-{index + 1:02d}.png"
        image.save(output, optimize=True)
        inventory.append(
            {
                "page": index + 1,
                "size": list(image.size),
                "mode": image.mode,
                "pixelSha256": sha256_bytes(image.tobytes()),
                "pngSha256": sha256_file(output),
            }
        )
    return inventory


def build_clean_outputs() -> dict[str, dict]:
    with tempfile.TemporaryDirectory(prefix="pspman-preservation-a-") as first, tempfile.TemporaryDirectory(
        prefix="pspman-preservation-b-"
    ) as second:
        for destination in (first, second):
            completed = subprocess.run(
                [sys.executable, str(BUILDER), "--output-dir", destination],
                cwd=REPO_ROOT,
                env=os.environ.copy(),
                check=False,
                capture_output=True,
                text=True,
            )
            require(
                completed.returncode == 0,
                f"Clean relocated build failed ({completed.returncode}): {completed.stderr}",
            )
        results: dict[str, dict] = {}
        for filename, expected in EXPECTED_OUTPUTS.items():
            first_path = Path(first) / filename
            second_path = Path(second) / filename
            require(first_path.read_bytes() == second_path.read_bytes(), f"Clean builds differ: {filename}")
            require(first_path.stat().st_size == expected["bytes"], f"Unexpected size: {filename}")
            digest = sha256_file(first_path)
            require(digest == expected["sha256"], f"Unexpected clean-build hash: {filename} {digest}")
            canonical = MANUAL_DIR / "output" / filename
            require(canonical.read_bytes() == first_path.read_bytes(), f"Canonical output differs: {filename}")
            results[filename] = {
                "bytes": first_path.stat().st_size,
                "sha256": digest,
                "twoCleanBuildsByteIdentical": True,
            }
        return results


def main() -> None:
    for path in (REFERENCE, GENERATED):
        require(path.is_file(), f"Required PDF is missing: {path}")

    approved_hash = sha256_file(REFERENCE)
    relocated_hash = sha256_file(GENERATED)
    require(REFERENCE.stat().st_size == APPROVED_BYTES, "Approved reference size changed")
    require(approved_hash == APPROVED_SHA256, f"Approved reference hash changed: {approved_hash}")
    require(GENERATED.stat().st_size == RELOCATED_BYTES, "Relocated output size changed")
    require(relocated_hash == RELOCATED_SHA256, f"Relocated output hash changed: {relocated_hash}")
    require(REFERENCE.read_bytes() != GENERATED.read_bytes(), "Path-sensitive exception unexpectedly absent")

    approved_reader = PdfReader(str(REFERENCE))
    relocated_reader = PdfReader(str(GENERATED))
    require(len(approved_reader.pages) == EXPECTED_PAGES, "Approved page count changed")
    require(len(relocated_reader.pages) == EXPECTED_PAGES, "Relocated page count changed")

    for label, reader in (("approved", approved_reader), ("relocated", relocated_reader)):
        for page_number, page in enumerate(reader.pages, 1):
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            require(abs(width - EXPECTED_PAGE_POINTS) <= 0.001, f"{label} page {page_number} width: {width}")
            require(abs(height - EXPECTED_PAGE_POINTS) <= 0.001, f"{label} page {page_number} height: {height}")
        metadata = {str(key): str(value) for key, value in (reader.metadata or {}).items()}
        require(metadata == EXPECTED_METADATA, f"{label} metadata mismatch: {metadata}")

    approved_text = [page.extract_text() or "" for page in approved_reader.pages]
    relocated_text = [page.extract_text() or "" for page in relocated_reader.pages]
    require(approved_text == relocated_text, "Extracted page text differs")
    all_text = "\n".join(relocated_text)
    require("OS-PSPMAN-01 (2)" not in all_text, "Visible document code remains")
    require("PSPMAN USER'S GUIDE" not in all_text, "Removed interior footer label remains")
    require("Parts and controls" not in all_text, "Removed controls page remains")
    require("OPERATING INSTRUCTIONS" not in all_text.upper(), "Obsolete title remains")

    require(font_inventory(approved_reader) == font_inventory(relocated_reader), "Embedded font inventory differs")
    require(
        image_inventory(approved_reader, normalize_cover=True)
        == image_inventory(relocated_reader, normalize_cover=True),
        "Decoded image inventory differs after the single cover-name normalization",
    )

    raw_differences = parsed_object_differences(
        approved_reader, relocated_reader, normalize_cover=False
    )
    require(
        raw_differences == EXPECTED_RAW_DIFFERING_OBJECTS,
        f"Unexpected raw PDF-object differences: {raw_differences}",
    )
    normalized_differences = parsed_object_differences(
        approved_reader, relocated_reader, normalize_cover=True
    )
    require(not normalized_differences, f"Unrelated PDF-object differences: {normalized_differences}")
    require(
        canonical_object(approved_reader.trailer, normalize_cover=False)
        == canonical_object(relocated_reader.trailer, normalize_cover=False),
        "PDF trailers differ",
    )

    require(
        REFERENCE.read_bytes().count(APPROVED_COVER_NAME.encode("ascii")) == 2,
        "Approved cover resource-name occurrence count changed",
    )
    require(
        GENERATED.read_bytes().count(RELOCATED_COVER_NAME.encode("ascii")) == 2,
        "Relocated cover resource-name occurrence count changed",
    )

    approved_renders = render_inventory(REFERENCE, RENDER_DIR / "approved")
    relocated_renders = render_inventory(GENERATED, RENDER_DIR / "relocated")
    require(approved_renders == relocated_renders, "Rendered page pixels or PNGs differ")

    clean_builds = build_clean_outputs()
    result = {
        "status": "PRESERVATION-EQUIVALENT-PATH-SENSITIVE",
        "approvedReference": {
            "bytes": APPROVED_BYTES,
            "sha256": approved_hash,
        },
        "relocatedOutput": {
            "bytes": RELOCATED_BYTES,
            "sha256": relocated_hash,
        },
        "cleanBuilds": clean_builds,
        "pages": EXPECTED_PAGES,
        "pageSizePoints": [EXPECTED_PAGE_POINTS, EXPECTED_PAGE_POINTS],
        "metadata": "identical",
        "extractedText": "identical",
        "fontInventoryAndHashes": "identical",
        "decodedImagePayloads": "identical",
        "rawDifferingObjectIds": raw_differences,
        "normalizedDifferingObjectIds": normalized_differences,
        "normalizedDifference": {
            "approved": APPROVED_COVER_NAME,
            "relocated": RELOCATED_COVER_NAME,
        },
        "pageRenders": "pixel-identical",
        "renderedPagesCompared": len(approved_renders),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

