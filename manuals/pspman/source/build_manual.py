#!/usr/bin/env python3
"""Build all PSPMAN User's Guide PDF editions."""

from __future__ import annotations

import argparse
import hashlib
import json
from io import BytesIO
import subprocess
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf._page import PageObject
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from diagrams import DIAGRAMS, psp_front
from layout import (
    FOOTER_RULE,
    LOWER_CONTENT_LIMIT,
    ManualPage,
    SPACE_4,
    SPACE_8,
    SPACE_12,
    SPACE_16,
    centered_baseline,
    centered_stack_baselines,
    draw_button_symbol_at,
    draw_inline_line,
    draw_brand_wordmark,
    wrap_inline_lines,
    wrap_lines,
)
from styles import (
    BLEED,
    CHARCOAL,
    FONT_BOLD,
    FONT_DISPLAY,
    FONT_DISPLAY_BOLD,
    FONT_REGULAR,
    GOLD,
    INK,
    LIGHT,
    MUTED,
    ORANGE,
    PAPER,
    PRINT_SIZE,
    SPREAD_SIZE,
    TRIM,
    WHITE,
    mm,
    register_fonts,
)
from manual_provenance import manual_input_digest

SOURCE_DIR = Path(__file__).resolve().parent
MANUAL_DIR = SOURCE_DIR.parent
REPO_ROOT = MANUAL_DIR.parents[1]
CONTENT_DIR = MANUAL_DIR / "content"
ASSET_DIR = MANUAL_DIR / "assets"
SCREENSHOT_DIR = ASSET_DIR / "screenshots"
PSPMAN3_COVER_LOGO = ASSET_DIR / "branding" / "pspman3-cover-white.png"
BRAND_DIR = ASSET_DIR / "branding"
DEFAULT_OUTPUT = MANUAL_DIR / "output"
COVER_FOOTER_LABEL = "USER'S GUIDE"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def app_version() -> str:
    return load_json(REPO_ROOT / "package.json")["version"]


def canonical_origin() -> str:
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=REPO_ROOT, text=True).strip()
    return remote.removesuffix(".git").replace("https://github.com/ObsoleteSony/", "https://github.com/obsoletesony/")


def metadata(c: canvas.Canvas) -> None:
    c.setTitle("PSPMAN User's Guide")
    c.setAuthor("ObsoleteSony")
    c.setCreator("ObsoleteSony")
    c.setSubject("User's guide for PSPMAN")
    c.setKeywords("PSPMAN, ObsoleteSony, PlayStation Portable, user's guide")


def cover(c, page: ManualPage, *, back: bool = False) -> None:
    c.setFillColor(CHARCOAL)
    c.rect(0, 0, c._pagesize[0], c._pagesize[1], fill=1, stroke=0)
    x0, y0 = page.x0, page.y0
    cover_logo = ImageReader(BytesIO(PSPMAN3_COVER_LOGO.read_bytes()))
    if back:
        logo_width = TRIM - mm(30)
        logo_height = logo_width * 356 / 2400
        c.drawImage(
            cover_logo,
            x0 + mm(15),
            y0 + TRIM - mm(42),
            logo_width,
            logo_height,
            preserveAspectRatio=True,
            mask="auto",
        )
        c.linkURL(
            "https://www.obsoletesony.com/pspman",
            (
                x0 + mm(15),
                y0 + TRIM - mm(42),
                x0 + mm(15) + logo_width,
                y0 + TRIM - mm(42) + logo_height,
            ),
            relative=0,
        )
        return
    logo_width = TRIM - mm(30)
    logo_height = logo_width * 356 / 2400
    c.drawImage(
        cover_logo,
        x0 + mm(15),
        y0 + TRIM - mm(42),
        logo_width,
        logo_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    c.setFillColor(MUTED)
    c.setFont(FONT_DISPLAY, 14)
    c.drawRightString(x0 + TRIM - mm(15), y0 + mm(17), COVER_FOOTER_LABEL)


TOC = [
    ("Read this first", 2), ("Install and add music", 4),
    ("Library", 5), ("Playback", 6),
    ("Now Playing", 7), ("Queue, Favorites, and Track Information", 8),
    ("Cassette View", 9), ("About, diagnostics, and safe exit", 10),
    ("Supported files and limits", 11), ("Troubleshooting", 12),
    ("Credits, support, and legal", 14),
]


def draw_contents(page: ManualPage) -> None:
    page.section_title("Table of Contents")
    c = page.c
    entries_box = page.reserve(mm(66), "table of contents entries", gap=0)
    row_pitch = (entries_box.height - SPACE_16) / (len(TOC) - 1)
    for index, (label, number) in enumerate(TOC):
        left = page.left
        right = page.right
        label_baseline = entries_box.top - SPACE_8 - index * row_pitch
        label_width = c.stringWidth(label, FONT_BOLD, 7)
        number_text = str(number)
        number_width = c.stringWidth(number_text, FONT_DISPLAY_BOLD, 8)
        leader_start = left + label_width + SPACE_8
        leader_end = right - number_width - SPACE_8
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 7)
        c.drawString(left, label_baseline, label)
        if leader_end > leader_start:
            c.setFillColor(MUTED)
            dot_x = leader_start
            while dot_x <= leader_end:
                c.circle(dot_x, label_baseline + 1.2, 0.45, stroke=0, fill=1)
                dot_x += 2.4
        c.setFillColor(INK)
        c.setFont(FONT_DISPLAY_BOLD, 8)
        c.drawRightString(right, label_baseline, number_text)
        hit_top = label_baseline + SPACE_8
        hit_bottom = label_baseline - row_pitch + SPACE_8 if index < len(TOC) - 1 else entries_box.y
        page.c.linkRect("", f"page-{number}", (left, hit_bottom, right, hit_top), relative=0, thickness=0)
def draw_grid(
    page: ManualPage,
    items: list[list[str]],
    *,
    row_height_mm: float = 9,
    detail_line_limit: int = 2,
    row_gap_mm: float = 0,
    centered: bool = False,
    aligned_content: bool = False,
) -> None:
    c = page.c
    cell_w = (page.width - mm(4)) / 2
    cell_h = mm(row_height_mm)
    row_gap = mm(row_gap_mm)
    rows = (len(items) + 1) // 2
    total_height = rows * cell_h + max(0, rows - 1) * row_gap
    if centered:
        page.center_module(total_height, "centered category grid")
    box = page.reserve(total_height, "category grid", gap=mm(3))
    page.record_visual("category grid", box.x, box.y, box.width, box.height)
    for i, (title, detail) in enumerate(items):
        col, row = i % 2, i // 2
        x = page.left + col * (cell_w + mm(4))
        y = box.top - (row + 1) * cell_h - row * row_gap
        card_y = y + mm(0.5)
        card_h = cell_h - mm(1)
        c.setFillColor(LIGHT)
        c.roundRect(x, card_y, cell_w, card_h, mm(1.5), fill=1, stroke=0)
        detail_lines = wrap_inline_lines(detail, FONT_REGULAR, 4.4, cell_w - mm(6))[:detail_line_limit]
        if aligned_content:
            title_baseline = card_y + card_h - SPACE_16
            detail_baseline = title_baseline - SPACE_12
        else:
            title_baseline, detail_baseline = centered_stack_baselines(
                card_y,
                card_h,
                [
                    (FONT_BOLD, 6.1, 1, 6.1),
                    (FONT_REGULAR, 4.4, len(detail_lines), 5.0),
                ],
                gap=2.2,
            )
        c.setFillColor(ORANGE)
        c.setFont(FONT_BOLD, 6.1)
        c.drawString(x + mm(3), title_baseline, title.upper())
        c.setFillColor(MUTED)
        c.setFont(FONT_REGULAR, 4.4)
        for line_index, line in enumerate(detail_lines[:detail_line_limit]):
            draw_inline_line(
                c,
                line,
                x + mm(3),
                detail_baseline - line_index * 5.0,
                FONT_REGULAR,
                4.4,
                MUTED,
            )


def draw_control_grid(page: ManualPage, items: list[list[str]]) -> None:
    c = page.c
    face_button_symbols = {"×", "○", "□", "△"}
    column_gap = mm(5)
    column_width = (page.width - column_gap) / 2
    row_height = mm(7.75)
    rows = (len(items) + 1) // 2
    box = page.reserve(rows * row_height, "control grid", gap=mm(2))
    for index, (label, detail) in enumerate(items):
        column, row = index % 2, index // 2
        x = page.left + column * (column_width + column_gap)
        row_y = box.top - (row + 1) * row_height
        symbol_label = label in face_button_symbols
        label_font = FONT_BOLD
        label_size = 5.8
        baseline = centered_baseline(row_y, row_height, label_font, label_size)
        c.setFillColor(ORANGE)
        if symbol_label:
            draw_button_symbol_at(c, label, x + mm(2.3), row_y + row_height / 2, mm(4.6), ORANGE)
        else:
            c.setFont(label_font, label_size)
            c.drawString(x, baseline, label.upper())
        c.setFillColor(INK)
        c.setFont(FONT_REGULAR, 5.3)
        c.drawString(x + mm(18), centered_baseline(row_y, row_height, FONT_REGULAR, 5.3), detail)


def draw_facts(page: ManualPage, items: list[list[str]], *, row_height_mm: float = 11) -> None:
    c = page.c
    column_gap = mm(5)
    column_width = (page.width - column_gap) / 2
    row_height = mm(row_height_mm)
    rows = (len(items) + 1) // 2
    box = page.reserve(rows * row_height, "facts grid", gap=mm(2))
    for index, (label, value) in enumerate(items):
        column, row = index % 2, index // 2
        x = page.left + column * (column_width + column_gap)
        row_y = box.top - (row + 1) * row_height
        lines = wrap_lines(value, FONT_REGULAR, 5.3, column_width)[:2]
        label_baseline, value_baseline = centered_stack_baselines(
            row_y,
            row_height,
            [
                (FONT_BOLD, 5.7, 1, 5.7),
                (FONT_REGULAR, 5.3, len(lines), 6.4),
            ],
            gap=2.4,
        )
        c.setFillColor(MUTED)
        c.setFont(FONT_BOLD, 5.7)
        c.drawString(x, label_baseline, label.upper())
        c.setFillColor(INK)
        c.setFont(FONT_REGULAR, 5.3)
        for line_index, line in enumerate(lines[:2]):
            c.drawString(x, value_baseline - line_index * 6.4, line)


def draw_numbered_list(page: ManualPage, items: list[str]) -> None:
    c = page.c
    gap = mm(5)
    width = (page.width - gap) / 2
    row_height = mm(11.5)
    rows = (len(items) + 1) // 2
    box = page.reserve(rows * row_height, "numbered legend", gap=mm(2))
    for index, text in enumerate(items):
        title, _, body = text.partition(":")
        column, row = index % 2, index // 2
        x = page.left + column * (width + gap)
        row_y = box.top - (row + 1) * row_height
        center_y = row_y + row_height / 2
        body_lines = wrap_lines(body.strip(), FONT_REGULAR, 4.8, width - mm(6))[:3]
        runs = [(FONT_BOLD, 5.6, 1, 5.6)]
        if body_lines:
            runs.append((FONT_REGULAR, 4.8, len(body_lines), 5.8))
        baselines = centered_stack_baselines(row_y, row_height, runs, gap=2.6)
        c.setFillColor(ORANGE)
        c.circle(x + mm(2), center_y, mm(2), fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 4.7)
        c.drawCentredString(x + mm(2), centered_baseline(row_y, row_height, FONT_BOLD, 4.7), str(index + 1))
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 5.6)
        c.drawString(x + mm(6), baselines[0], title)
        c.setFillColor(MUTED)
        c.setFont(FONT_REGULAR, 4.8)
        if body_lines:
            for line_index, line in enumerate(body_lines):
                c.drawString(x + mm(6), baselines[1] - line_index * 5.8, line)


def draw_callout_labels(page: ManualPage, labels: list[list[str]]) -> None:
    c = page.c
    x = page.left
    rows = (len(labels) + 1) // 2
    row_height = mm(7)
    box = page.reserve(rows * row_height, "screenshot legend", gap=mm(3))
    for i, (number, label) in enumerate(labels):
        col, row = i % 2, i // 2
        xx = x + col * page.width / 2
        row_y = box.top - (row + 1) * row_height
        center_y = row_y + row_height / 2
        c.setFillColor(ORANGE)
        c.circle(xx + mm(2), center_y, mm(2), fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 4.7)
        c.drawCentredString(xx + mm(2), centered_baseline(row_y, row_height, FONT_BOLD, 4.7), number)
        c.setFillColor(INK)
        c.setFont(FONT_REGULAR, 5.7)
        c.drawString(xx + mm(6), centered_baseline(row_y, row_height, FONT_REGULAR, 5.7), label)


def draw_controls_by_screen(page: ManualPage, controls: dict) -> None:
    page.section_title("Controls by screen")
    c = page.c
    rows = controls["screens"]
    screen_width = mm(29)
    action_width = page.width - screen_width
    header_height = 18.0
    row_height = 31.0
    box = page.reserve(header_height + row_height * len(rows), "screen controls table", gap=SPACE_8)
    c.setFillColor(CHARCOAL)
    c.rect(box.x, box.top - header_height, box.width, header_height, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 5.3)
    header_baseline = centered_baseline(box.top - header_height, header_height, FONT_BOLD, 5.3)
    c.drawString(box.x + SPACE_4, header_baseline, "SCREEN")
    c.drawString(box.x + screen_width + SPACE_4, header_baseline, "CONTROLS")
    y = box.top - header_height
    for index, (screen, action) in enumerate(rows):
        c.setFillColor(PAPER if index % 2 == 0 else LIGHT)
        c.rect(box.x, y - row_height, box.width, row_height, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 5.25)
        c.drawString(
            box.x + SPACE_4,
            centered_baseline(y - row_height, row_height, FONT_BOLD, 5.25),
            screen,
        )
        c.setFont(FONT_REGULAR, 4.75)
        lines = wrap_inline_lines(action, FONT_REGULAR, 4.75, action_width - SPACE_8)
        action_baseline = centered_stack_baselines(
            y - row_height,
            row_height,
            [(FONT_REGULAR, 4.75, len(lines[:3]), 6.1)],
        )[0]
        for line_index, line in enumerate(lines[:3]):
            draw_inline_line(
                c,
                line,
                box.x + screen_width + SPACE_4,
                action_baseline - line_index * 6.1,
                FONT_REGULAR,
                4.75,
                INK,
            )
        y -= row_height


PAGE_TEMPLATES = {
    "standard-text",
    "visual",
    "reference",
    "dense",
}
BULLET_GAPS = {"standard": SPACE_4, "compact": 1.8, "relaxed": 6.0}
BEFORE_GAPS = {"section": SPACE_8, "section-large": SPACE_16}


def draw_blocks(
    page: ManualPage,
    blocks: list[dict],
) -> None:
    for block in blocks:
        before = block.get("before")
        if before:
            if before not in BEFORE_GAPS:
                raise RuntimeError(f"Unknown before-spacing token: {before}")
            page.spacer(BEFORE_GAPS[before])
        anchor = block.get("anchor")
        if anchor == "secondary-compact":
            page.align_to(page.compact_secondary_content_y, "compact secondary content")
        elif anchor == "secondary-visual":
            page.align_to(page.visual_secondary_content_y, "visual secondary content")
        elif anchor == "secondary":
            page.align_to(page.secondary_content_y, "secondary content")
        elif anchor == "secondary-relaxed":
            page.align_to(page.relaxed_secondary_content_y, "relaxed secondary content")
        kind = block["type"]
        if kind == "text": page.text(block["text"])
        elif kind == "heading": page.heading(block["text"])
        elif kind == "bullet":
            spacing = block.get("spacing", "standard")
            if spacing not in BULLET_GAPS:
                raise RuntimeError(f"Unknown bullet spacing token: {spacing}")
            page.bullet(block["text"], gap=BULLET_GAPS[spacing])
        elif kind == "step": page.step(block["number"], block["title"], block["text"])
        elif kind == "callout":
            page.callout(
                block["kind"],
                block["text"],
                color=ORANGE if block["kind"].lower() != "technical note" else GOLD,
                bottom_anchor=(
                    page.bottom_callout_y
                    if anchor == "bottom-callout"
                    else page.sparse_callout_y if anchor == "sparse-callout" else None
                ),
            )
        elif kind == "screenshot": page.screenshot(SCREENSHOT_DIR / block["file"], width_mm=block.get("width", 74), caption=block.get("caption"))
        elif kind == "grid":
            draw_grid(
                page,
                block["items"],
                row_height_mm=block.get("row_height", 9),
                detail_line_limit=block.get("detail_lines", 2),
                row_gap_mm=block.get("row_gap", 0),
                centered=block.get("centered", False),
                aligned_content=block.get("aligned_content", False),
            )
        elif kind == "control-grid": draw_control_grid(page, block["items"])
        elif kind == "facts": draw_facts(page, block["items"], row_height_mm=block.get("row_height", 11))
        elif kind == "numbered-list": draw_numbered_list(page, block["items"])
        elif kind == "callout-diagram": draw_callout_labels(page, block["labels"])
        elif kind == "diagram":
            height = mm(block["height"])
            box = page.reserve(height, f"diagram:{block['id']}", gap=mm(4))
            page.record_visual(f"diagram:{block['id']}", box.x, box.y, box.width, box.height)
            if block["id"] == "psp-controls":
                psp_front(page.c, page.left, box.y, page.width, height, callouts=True)
            else:
                DIAGRAMS[block["id"]](page.c, page.left, box.y, page.width, height)
        else:
            raise ValueError(f"Unknown block type: {kind}")


def layout_review(
    page: ManualPage,
    density: str,
    template: str,
    intentional_exception: str | None = None,
) -> dict:
    # Limit the review to the usable region.  A few bespoke pages reserve
    # subtitle boxes before setting content_top; counting those made their
    # occupancy exceed 100% even though the rendered page was valid.
    content_boxes = [
        box
        for box in page.boxes
        if box.name != "title panel"
        and page.content_top is not None
        and box.top <= page.content_top + 0.25
    ]
    if not content_boxes or page.content_top is None:
        return {"page": page.page_number, "density": density, "candidates": []}
    # The reviewable frame ends 12 pt above the visible footer rule.  The
    # builder itself keeps the stricter footer exclusion zone, while the
    # diagnostic measures what a reader actually sees on the finished page.
    content_bottom = page.y0 + FOOTER_RULE + SPACE_12
    usable_height = page.content_top - content_bottom
    lowest = min(box.y for box in content_boxes)
    highest = max(box.top for box in content_boxes)
    occupancy = (highest - lowest) / usable_height if usable_height else 1.0
    footer_clear = lowest - (page.y0 + FOOTER_RULE)
    top_clear = page.content_top - highest
    bottom_clear = lowest - content_bottom
    ordered = sorted(content_boxes, key=lambda box: box.top, reverse=True)
    major_gaps: list[dict] = []
    for first, second in zip(ordered, ordered[1:]):
        coupled = (
            (first.name == "heading" and second.name in {"text", "bullet"})
            or (first.name == second.name and first.name in {"bullet", "step"})
            or (first.name.startswith("screenshot:") and second.name == "screenshot legend")
            or (first.name.startswith("diagram:") and second.name == "numbered legend")
        )
        if not coupled:
            major_gaps.append({
                "after": first.name,
                "before": second.name,
                "gapPt": round(max(0.0, first.y - second.top), 2),
            })
    screenshots = [box for box in content_boxes if box.name.startswith("screenshot:")]
    visual_boxes = list(page.visuals) + [
        box for box in content_boxes if box.name in {"table", "screen controls table"}
    ]
    candidates: list[str] = []
    if footer_clear < SPACE_12:
        candidates.append("footer clear area below 12 pt")
    if abs(top_clear) > 0.5 and not intentional_exception:
        candidates.append("first meaningful content misses the primary anchor")
    minimum_major_gap = min((gap["gapPt"] for gap in major_gaps), default=None)
    if minimum_major_gap is not None and minimum_major_gap < SPACE_4:
        candidates.append("major content groups are separated by less than 4 pt")
    if screenshots and any(box.width < page.width * 0.63 for box in screenshots) and footer_clear > mm(8):
        candidates.append("screenshot may be enlarged within the content frame")
    return {
        "page": page.page_number,
        "density": density,
        "template": template,
        "frameX0Pt": round(page.left, 4),
        "frameX1Pt": round(page.right, 4),
        "frameWidthPt": round(page.width, 4),
        "firstContentTopFromTopPt": round(page.y0 + page.trim - highest, 2),
        "lastContentBottomFromBottomPt": round(lowest - page.y0, 2),
        "lowerClearanceToFooterRulePt": round(footer_clear, 2),
        "occupancy": round(occupancy, 3),
        "topClearPt": round(top_clear, 2),
        "bottomClearPt": round(bottom_clear, 2),
        "primaryAnchorPt": round(page.primary_content_y, 2),
        "secondaryAnchorPt": round(page.secondary_content_y, 2),
        "compactSecondaryAnchorPt": round(page.compact_secondary_content_y, 2),
        "visualSecondaryAnchorPt": round(page.visual_secondary_content_y, 2),
        "bottomCalloutAnchorPt": round(page.bottom_callout_y, 2),
        "footerClearPt": round(footer_clear, 2),
        "minimumMajorGapPt": minimum_major_gap,
        "majorGaps": major_gaps,
        "principalVisuals": [
            {
                "name": box.name,
                "xPt": round(box.x, 2),
                "topFromTopPt": round(page.y0 + page.trim - box.top, 2),
                "widthPt": round(box.width, 2),
                "heightPt": round(box.height, 2),
            }
            for box in visual_boxes
        ],
        "intentionalException": intentional_exception,
        "candidates": candidates,
    }


def build_pages(
    path: Path,
    *,
    print_edition: bool,
    content: dict,
    controls: dict,
    compatibility: dict,
    qa: bool = False,
) -> list[dict]:
    page_size = (PRINT_SIZE, PRINT_SIZE) if print_edition else (TRIM, TRIM)
    bleed = BLEED if print_edition else 0
    c = canvas.Canvas(str(path), pagesize=page_size, pageCompression=1, invariant=1)
    metadata(c)
    reviews: list[dict] = []
    outline_pages = {1, len(content["pages"]), *(number for _, number in TOC)}
    for record in content["pages"]:
        number = record["number"]
        page = ManualPage(c, number, record["title"], bleed=bleed, qa=qa)
        c.bookmarkPage(f"page-{number}")
        if number in outline_pages:
            c.addOutlineEntry(record["title"], f"page-{number}", level=0, closed=False)
        if record.get("kind") == "cover":
            cover(c, page)
        elif record.get("kind") == "back-cover":
            cover(c, page, back=True)
        else:
            template = record.get("template", "standard-text")
            if template not in PAGE_TEMPLATES:
                raise RuntimeError(f"Page {number} has unknown template: {template}")
            c.setFillColor(PAPER)
            c.rect(0, 0, page_size[0], page_size[1], fill=1, stroke=0)
            page.background()
            page.running_header()
            kind = record.get("kind", "blocks")
            if kind == "contents": draw_contents(page)
            elif kind == "controls-by-screen": draw_controls_by_screen(page, controls)
            else:
                page.section_title(record["title"])
                blocks = record.get("blocks", [])
                draw_blocks(page, blocks)
            reviews.append(layout_review(
                page,
                record.get("density", "dense" if kind == "controls-by-screen" else "standard"),
                template,
                record.get("measurementException"),
            ))
            page.footer()
            page.qa_overlay()
        c.showPage()
    c.save()
    return reviews


def add_print_boxes(path: Path) -> None:
    reader = PdfReader(str(path))
    writer = PdfWriter()
    for page in reader.pages:
        page.mediabox.lower_left = (0, 0)
        page.mediabox.upper_right = (PRINT_SIZE, PRINT_SIZE)
        page.bleedbox.lower_left = (0, 0)
        page.bleedbox.upper_right = (PRINT_SIZE, PRINT_SIZE)
        page.trimbox.lower_left = (BLEED, BLEED)
        page.trimbox.upper_right = (BLEED + TRIM, BLEED + TRIM)
        page.cropbox.lower_left = (0, 0)
        page.cropbox.upper_right = (PRINT_SIZE, PRINT_SIZE)
        writer.add_page(page)
    writer.add_metadata(reader.metadata or {})
    with path.open("wb") as handle:
        writer.write(handle)


def build_spreads(reader_path: Path, spread_path: Path) -> None:
    reader = PdfReader(str(reader_path))
    total_pages = len(reader.pages)
    pairs: list[tuple[int | None, int]] = (
        [(None, 1)] if total_pages % 2 else [(total_pages, 1)]
    ) + [(left, left + 1) for left in range(2, total_pages, 2)]
    writer = PdfWriter()
    for left_number, right_number in pairs:
        spread = PageObject.create_blank_page(width=SPREAD_SIZE[0], height=SPREAD_SIZE[1])
        if left_number is not None:
            spread.merge_transformed_page(reader.pages[left_number - 1], Transformation().translate(0, 0))
        spread.merge_transformed_page(reader.pages[right_number - 1], Transformation().translate(TRIM, 0))
        writer.add_page(spread)
    writer.add_metadata({
        "/Title": "PSPMAN User's Guide - Reader Spreads",
        "/Subject": "User's guide for PSPMAN",
        "/Author": "ObsoleteSony",
        "/Creator": "PSPMAN deterministic manual builder",
    })
    with spread_path.open("wb") as handle:
        writer.write(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--qa-output", type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    register_fonts(REPO_ROOT)
    content = load_json(CONTENT_DIR / "manual.yaml")
    controls = load_json(CONTENT_DIR / "controls.json")
    compatibility = load_json(CONTENT_DIR / "compatibility.json")
    version = app_version()
    input_digest, input_file_count = manual_input_digest(REPO_ROOT, MANUAL_DIR)
    if canonical_origin().lower() != content["document"]["repository"].lower():
        raise RuntimeError(f"Repository URL mismatch: {canonical_origin()}")
    page_count = len(content["pages"])
    if page_count != 15 or [p["number"] for p in content["pages"]] != list(range(1, page_count + 1)):
        raise RuntimeError("Manual content must define pages 1 through 15 exactly")
    reader = args.output_dir / "PSPMAN-User-Guide.pdf"
    spreads = args.output_dir / "PSPMAN-User-Guide-Spreads.pdf"
    print_pdf = args.output_dir / "PSPMAN-User-Guide-Print.pdf"
    layout_reviews = build_pages(reader, print_edition=False, content=content, controls=controls, compatibility=compatibility)
    build_pages(print_pdf, print_edition=True, content=content, controls=controls, compatibility=compatibility)
    add_print_boxes(print_pdf)
    build_spreads(reader, spreads)
    if args.qa_output:
        args.qa_output.parent.mkdir(parents=True, exist_ok=True)
        build_pages(
            args.qa_output,
            print_edition=False,
            content=content,
            controls=controls,
            compatibility=compatibility,
            qa=True,
        )
    manifest = {
        "version": version,
        "manualProvenance": {
            "scope": "user-guide-output",
            "schemaVersion": 1,
            "inputDigestAlgorithm": "sha256",
            "inputTreeSha256": input_digest,
            "inputFileCount": input_file_count,
            "definition": "Paths and bytes of package.json plus docs/manual content, assets, and source",
        },
        "documentCode": content["document"]["code"],
        "outputs": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in [reader, spreads, print_pdf]},
    }
    (args.output_dir / "checksums.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    review_report = {
        "checks": {
            "minimumMajorGroupGapPt": SPACE_4,
            "minimumFooterClearPt": SPACE_12,
            "primaryContentAnchorTolerancePt": 0.5,
            "screenshotWidthReviewThreshold": 0.63,
        },
        "pages": layout_reviews,
        "visualReviewCandidates": [
            {"page": review["page"], "reasons": review["candidates"]}
            for review in layout_reviews
            if review["candidates"]
        ],
    }
    (args.output_dir / "layout-review.json").write_text(
        json.dumps(review_report, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    measurement_report = {
        "pageSizePt": [round(TRIM, 4), round(TRIM, 4)],
        "coordinateSystem": "PDF points; X from left, first-content from top, last-content from bottom",
        "pages": layout_reviews,
    }
    (args.output_dir / "measurement-report.json").write_text(
        json.dumps(measurement_report, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
