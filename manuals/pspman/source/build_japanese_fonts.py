#!/usr/bin/env python3
"""Build deterministic Noto Sans JP subsets for the Japanese PSPMAN guide."""

from __future__ import annotations

import argparse
import json
import string
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

SOURCE_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SOURCE_DIR.parent
DEFAULT_CONTENT = MANUAL_DIR / "content" / "manual-ja.yaml"
DEFAULT_OUTPUT = MANUAL_DIR / "assets" / "fonts" / "ja"


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)


def corpus(content_path: Path) -> str:
    content = json.loads(content_path.read_text(encoding="utf-8"))
    fixed_builder_text = "PSPMAN PUBLIC ALPHA Reader Spreads 0123456789"
    return "\n".join([*strings(content), string.printable, fixed_builder_text])


def build_subset(source_path: Path, output_path: Path, text: str, weight: int) -> None:
    font = TTFont(source_path, recalcTimestamp=False)
    instantiateVariableFont(font, {"wght": weight}, inplace=True, optimize=True)

    subfamily = "Bold" if weight >= 700 else "Regular"
    postscript_name = f"NotoSansJP-{subfamily}"
    for platform_id, encoding_id, language_id in ((3, 1, 0x409), (3, 1, 0x411)):
        font["name"].setName("Noto Sans JP", 1, platform_id, encoding_id, language_id)
        font["name"].setName(subfamily, 2, platform_id, encoding_id, language_id)
        font["name"].setName(f"Noto Sans JP {subfamily}", 4, platform_id, encoding_id, language_id)
        font["name"].setName(postscript_name, 6, platform_id, encoding_id, language_id)
        font["name"].setName("Noto Sans JP", 16, platform_id, encoding_id, language_id)
        font["name"].setName(subfamily, 17, platform_id, encoding_id, language_id)

    options = subset.Options()
    options.name_IDs = [0, 1, 2, 3, 4, 5, 6, 16, 17]
    options.name_legacy = True
    options.name_languages = [0x409, 0x411]
    options.recalc_average_width = True
    options.recalc_bounds = True
    options.recalc_timestamp = False
    options.layout_features = ["*"]
    options.notdef_glyph = True
    options.notdef_outline = True
    options.recommended_glyphs = True

    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text=text)
    subsetter.subset(font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    font.save(output_path, reorderTables=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_font", type=Path)
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    text = corpus(args.content)
    build_subset(
        args.source_font,
        args.output_dir / "NotoSansJP-Regular-subset.ttf",
        text,
        400,
    )
    build_subset(
        args.source_font,
        args.output_dir / "NotoSansJP-Bold-subset.ttf",
        text,
        700,
    )


if __name__ == "__main__":
    main()
