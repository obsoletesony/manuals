#!/usr/bin/env python3
"""Structural and content preflight for the Japanese PSPMAN manual."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader

from manual_provenance import manual_input_digest
from styles import BLEED, PRINT_SIZE, SPREAD_SIZE, TRIM
from validate_manual import approved_screenshots, assert_orange_accents, close, embedded_fonts, page_size

SOURCE_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SOURCE_DIR.parent
REPO_ROOT = MANUAL_DIR.parents[1]
OUTPUT = MANUAL_DIR / "output"

STEM = "PSPMAN-User-Guide-JP"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def deterministic() -> dict[str, bool]:
    names = [f"{STEM}.pdf", f"{STEM}-Spreads.pdf", f"{STEM}-Print.pdf"]
    with tempfile.TemporaryDirectory(prefix="pspman-manual-ja-") as first, tempfile.TemporaryDirectory(
        prefix="pspman-manual-ja-"
    ) as second:
        for directory in (first, second):
            subprocess.run(
                [
                    sys.executable,
                    str(SOURCE_DIR / "build_manual.py"),
                    "--locale",
                    "ja",
                    "--output-dir",
                    directory,
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        results = {name: sha256(Path(first) / name) == sha256(Path(second) / name) for name in names}
        if not all(results.values()):
            raise AssertionError(f"Non-deterministic Japanese output: {results}")
        return results


def validate() -> dict:
    reader_path = OUTPUT / f"{STEM}.pdf"
    spread_path = OUTPUT / f"{STEM}-Spreads.pdf"
    print_path = OUTPUT / f"{STEM}-Print.pdf"
    for path in (reader_path, spread_path, print_path):
        if not path.exists():
            raise AssertionError(f"Required Japanese output missing: {path}")

    content = json.loads((MANUAL_DIR / "content" / "manual-ja.yaml").read_text(encoding="utf-8"))
    reader = PdfReader(str(reader_path))
    spreads = PdfReader(str(spread_path))
    print_pdf = PdfReader(str(print_path))
    pages = content["pages"]
    page_count = len(pages)

    assert page_count == 15, page_count
    assert len(reader.pages) == page_count, len(reader.pages)
    assert len(spreads.pages) == (page_count + 1) // 2, len(spreads.pages)
    assert len(print_pdf.pages) == page_count, len(print_pdf.pages)
    assert all(close(width, TRIM) and close(height, TRIM) for width, height in map(page_size, reader.pages))
    assert all(
        close(width, SPREAD_SIZE[0]) and close(height, SPREAD_SIZE[1])
        for width, height in map(page_size, spreads.pages)
    )
    assert all(close(width, PRINT_SIZE) and close(height, PRINT_SIZE) for width, height in map(page_size, print_pdf.pages))
    for index, page in enumerate(print_pdf.pages, 1):
        assert close(float(page.trimbox.left), BLEED) and close(float(page.trimbox.bottom), BLEED), index
        assert close(float(page.trimbox.width), TRIM) and close(float(page.trimbox.height), TRIM), index

    page_text = [page.extract_text() or "" for page in reader.pages]
    normalized_text = re.sub(r"\s+", "", "\n".join(page_text))
    textless_pages = [index for index, value in enumerate(page_text, 1) if not value.strip()]
    if textless_pages:
        raise AssertionError(f"Japanese reader PDF contains an accidental blank page: {textless_pages}")

    required = [
        "ユーザーガイド",
        "はじめに",
        "インストールと音楽の追加",
        "ライブラリ",
        "再生中画面",
        "カセット表示",
        "対応ファイルと上限",
        "PSP-1000",
        "64MBのRAM",
        "PSPStreet（E1000）",
        "メモリースティックマイクロ（M2）",
        "最大1,000曲",
        "最大12階層",
        "選んだ色はPSPMANを終了するまで保持されます",
        "obsoletesony.com/jp/pspman",
        "obsoletesony.com/jp/pspman/report-a-bug",
        "github.com/obsoletesony/PSPMAN-Issues",
        "Copyright2026ObsoleteSony.Allrightsreserved.",
    ]
    missing = [value for value in required if re.sub(r"\s+", "", value) not in normalized_text]
    if missing:
        raise AssertionError(f"Required Japanese text missing: {missing}")

    forbidden = [
        "Read this first",
        "Table of Contents",
        "Installation and adding music",
        "Supported files and limits",
        "Troubleshooting:",
        "USER'S GUIDE",
    ]
    present_forbidden = [value for value in forbidden if value.casefold() in "\n".join(page_text).casefold()]
    if present_forbidden:
        raise AssertionError(f"Untranslated guide text present: {present_forbidden}")
    if "\u2014" in "\n".join(page_text):
        raise AssertionError("Japanese manual contains an em dash")

    missing_titles = [
        f"page {record['number']}: {record['title']}"
        for record in pages
        if record.get("kind") not in {"cover", "back-cover"}
        if record["title"] not in page_text[record["number"] - 1]
    ]
    if missing_titles:
        raise AssertionError(f"Required Japanese page headings missing: {missing_titles}")

    visible_fonts: set[str] = set()
    for label, document in (("reader", reader), ("spreads", spreads), ("print", print_pdf)):
        fonts, missing_fonts = embedded_fonts(document)
        visible_fonts.update(fonts)
        if missing_fonts:
            raise AssertionError(f"Fonts not embedded in Japanese {label}: {missing_fonts}")
    if not any("NotoSansJP" in name for name in visible_fonts):
        raise AssertionError(f"Japanese font is not present: {sorted(visible_fonts)}")

    metadata = reader.metadata
    if metadata.get("/Title") != "PSPMAN ユーザーガイド":
        raise AssertionError(f"Unexpected Japanese PDF title: {metadata.get('/Title')}")
    if metadata.get("/Subject") != content["document"]["subject"]:
        raise AssertionError(f"Unexpected Japanese PDF subject: {metadata.get('/Subject')}")
    for key in ("/CreationDate", "/ModDate"):
        if metadata.get(key) != "D:20260902000000+00'00'":
            raise AssertionError(f"Unexpected Japanese reader PDF {key}: {metadata.get(key)}")

    if not reader.outline:
        raise AssertionError("Japanese reader PDF has no bookmarks")
    annotations = sum(len(page.get("/Annots", [])) for page in reader.pages)
    uris = {
        str(annotation.get_object().get("/A", {}).get("/URI"))
        for page in reader.pages
        for annotation in page.get("/Annots", [])
        if annotation.get_object().get("/A", {}).get("/URI")
    }
    expected_uris = {
        "https://obsoletesony.com/jp/pspman",
        "https://obsoletesony.com/jp/pspman/report-a-bug",
        "https://github.com/obsoletesony/PSPMAN-Issues",
    }
    if not expected_uris.issubset(uris):
        raise AssertionError(f"Required Japanese hyperlinks missing: {sorted(expected_uris - uris)}")

    checksums = json.loads((OUTPUT / "checksums-ja.json").read_text(encoding="utf-8"))
    expected_digest, expected_file_count = manual_input_digest(REPO_ROOT, MANUAL_DIR)
    provenance = checksums.get("manualProvenance", {})
    if provenance.get("inputTreeSha256") != expected_digest:
        raise AssertionError("Japanese manual output provenance is stale")
    if provenance.get("inputFileCount") != expected_file_count:
        raise AssertionError("Japanese manual output provenance input count does not match")

    approved_screenshots()
    assert_orange_accents(reader_path)
    return {
        "pages": len(reader.pages),
        "spreads": len(spreads.pages),
        "visibleFonts": sorted(visible_fonts),
        "embeddedFonts": "pass",
        "requiredText": "pass",
        "pageHeadings": "pass",
        "metadata": "pass",
        "bookmarks": "pass",
        "linkAnnotations": annotations,
        "hyperlinks": sorted(uris),
        "blankPages": "pass",
        "printBoxes": "pass",
        "screenshots": "pass",
        "orangeAccents": "pass",
        "deterministic": deterministic(),
    }


def main() -> None:
    result = validate()
    (OUTPUT / "preflight-ja.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
