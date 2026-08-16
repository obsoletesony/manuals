"""Deterministic, measured page-composition helpers for the PSPMAN manual."""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics

from styles import (
    CHARCOAL,
    FONT_BOLD,
    FONT_DISPLAY,
    FONT_DISPLAY_BOLD,
    FONT_REGULAR,
    INK,
    LIGHT,
    MUTED,
    ORANGE,
    PAPER,
    RULE,
    TRIM,
    WHITE,
    mm,
)


# Master grid. All values are points so the vertical rhythm is based on the
# requested 4/8/12/16/24-point scale instead of page-specific millimetres.
SPACE_4 = 4.0
SPACE_8 = 8.0
SPACE_12 = 12.0
SPACE_16 = 16.0
SPACE_24 = 24.0
PAGE_OUTER_MARGIN = mm(12)
PAGE_INNER_MARGIN = mm(15)


@lru_cache(maxsize=None)
def _monochrome_png(path_text: str) -> bytes:
    """Return a deterministic grayscale PNG while preserving source alpha."""
    with Image.open(path_text) as source:
        alpha = source.getchannel("A") if "A" in source.getbands() else None
        converted = ImageOps.grayscale(source).convert("RGB")
        if alpha is not None:
            converted.putalpha(alpha)
        stream = BytesIO()
        converted.save(stream, format="PNG", optimize=False, compress_level=9)
        return stream.getvalue()


def monochrome_image_reader(path: Path) -> ImageReader:
    """Create a fresh ReportLab reader from the cached monochrome asset."""
    return ImageReader(BytesIO(_monochrome_png(str(path.resolve()))))
HEADER_BASELINE_FROM_TOP = 25.5
HEADER_RULE_FROM_TOP = 34.0
TITLE_TOP_FROM_RULE = SPACE_8
TITLE_HEIGHT = 31.0
CONTENT_GAP = SPACE_8
# Interior pages share these editorial anchors.  Content is deliberately
# top-led; unused height remains below completed modules instead of being
# distributed around the page.
BASELINE_GRID = SPACE_4
SECONDARY_CONTENT_OFFSET = mm(45)
COMPACT_SECONDARY_CONTENT_OFFSET = mm(34)
VISUAL_SECONDARY_CONTENT_OFFSET = mm(37)
BOTTOM_CALLOUT_CLEARANCE = 9.0
SPARSE_CALLOUT_CLEARANCE = SPACE_24 + SPACE_8
RELAXED_SECONDARY_CONTENT_OFFSET = mm(48)
FOOTER_BASELINE = 22.5
FOOTER_RULE = 32.0
FOOTER_EXCLUSION_TOP = 38.0
LOWER_CONTENT_LIMIT = FOOTER_RULE + SPACE_12
TWO_COLUMN_GUTTER = SPACE_12
SCREEN_ASPECT = 480 / 272
BUTTON_SYMBOLS = frozenset({"×", "○", "□", "△"})


def wrap_lines(text: str, font: str, size: float, width: float) -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    line = words[0]
    for word in words[1:]:
        trial = f"{line} {word}"
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            line = trial
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def button_symbol_advance(size: float) -> float:
    return size * 1.4


def _inline_word_width(word: str, font: str, size: float) -> float:
    width = 0.0
    text_run = ""
    for character in word:
        if character in BUTTON_SYMBOLS:
            if text_run:
                width += pdfmetrics.stringWidth(text_run, font, size)
                text_run = ""
            width += button_symbol_advance(size)
        else:
            text_run += character
    if text_run:
        width += pdfmetrics.stringWidth(text_run, font, size)
    return width


def wrap_inline_lines(text: str, font: str, size: float, width: float) -> list[list[str]]:
    """Wrap words while treating face-button symbols as fixed-width vector objects."""
    words = text.split()
    if not words:
        return [[]]
    space_width = pdfmetrics.stringWidth(" ", font, size)
    lines: list[list[str]] = []
    line: list[str] = []
    line_width = 0.0
    for word in words:
        word_width = _inline_word_width(word, font, size)
        trial_width = line_width + (space_width if line else 0.0) + word_width
        if line and trial_width > width:
            lines.append(line)
            line = [word]
            line_width = word_width
        else:
            line.append(word)
            line_width = trial_width
    lines.append(line)
    return lines


def inline_line_width(words: list[str], font: str, size: float) -> float:
    if not words:
        return 0.0
    return sum(_inline_word_width(word, font, size) for word in words) + (
        len(words) - 1
    ) * pdfmetrics.stringWidth(" ", font, size)


def draw_button_symbol_at(
    c,
    symbol: str,
    center_x: float,
    center_y: float,
    diameter: float,
    color=INK,
    *,
    background=None,
) -> None:
    """Draw an original monochrome PSP-style face-button symbol."""
    if symbol not in BUTTON_SYMBOLS:
        raise ValueError(f"Unsupported face-button symbol: {symbol}")
    radius = diameter / 2
    inner = radius * 0.43
    line_width = max(0.42, diameter * 0.075)
    c.saveState()
    c.setStrokeColor(color)
    c.setFillColor(background if background is not None else color)
    c.setLineWidth(line_width)
    c.circle(
        center_x,
        center_y,
        radius,
        stroke=1,
        fill=1 if background is not None else 0,
    )
    if symbol == "×":
        c.line(center_x - inner, center_y - inner, center_x + inner, center_y + inner)
        c.line(center_x - inner, center_y + inner, center_x + inner, center_y - inner)
    elif symbol == "○":
        c.circle(center_x, center_y, inner * 0.78, stroke=1, fill=0)
    elif symbol == "□":
        half = inner * 0.82
        c.rect(center_x - half, center_y - half, half * 2, half * 2, stroke=1, fill=0)
    else:
        path = c.beginPath()
        path.moveTo(center_x, center_y + inner)
        path.lineTo(center_x + inner * 0.95, center_y - inner * 0.78)
        path.lineTo(center_x - inner * 0.95, center_y - inner * 0.78)
        path.close()
        c.drawPath(path, stroke=1, fill=0)
    c.restoreState()


def draw_inline_line(c, words: list[str], x: float, baseline: float, font: str, size: float, color=INK) -> float:
    """Draw one wrapped text line with vector face-button symbols inline."""
    cursor_x = x
    space_width = pdfmetrics.stringWidth(" ", font, size)
    ascent = pdfmetrics.getAscent(font, size)
    descent = pdfmetrics.getDescent(font, size)
    diameter = size * 1.15
    for word_index, word in enumerate(words):
        if word_index:
            cursor_x += space_width
        text_run = ""
        for character in word:
            if character in BUTTON_SYMBOLS:
                if text_run:
                    c.setFillColor(color)
                    c.setFont(font, size)
                    c.drawString(cursor_x, baseline, text_run)
                    cursor_x += pdfmetrics.stringWidth(text_run, font, size)
                    text_run = ""
                advance = button_symbol_advance(size)
                draw_button_symbol_at(
                    c,
                    character,
                    cursor_x + advance / 2,
                    baseline + (ascent + descent) / 2,
                    diameter,
                    color,
                )
                cursor_x += advance
            else:
                text_run += character
        if text_run:
            c.setFillColor(color)
            c.setFont(font, size)
            c.drawString(cursor_x, baseline, text_run)
            cursor_x += pdfmetrics.stringWidth(text_run, font, size)
    return cursor_x


def centered_baseline(y: float, height: float, font: str, size: float) -> float:
    """Return a baseline whose visible glyph bounds are vertically centered."""
    ascent = pdfmetrics.getAscent(font, size)
    descent = pdfmetrics.getDescent(font, size)
    return y + height / 2 - (ascent + descent) / 2


def centered_stack_baselines(
    y: float,
    height: float,
    runs: list[tuple[str, float, int, float]],
    *,
    gap: float = 0,
) -> list[float]:
    """Center one or more multiline text runs as a single visual block."""
    run_heights: list[float] = []
    for font, size, line_count, leading in runs:
        ascent = pdfmetrics.getAscent(font, size)
        descent = pdfmetrics.getDescent(font, size)
        run_heights.append(ascent - descent + max(0, line_count - 1) * leading)
    total_height = sum(run_heights) + gap * max(0, len(runs) - 1)
    visual_top = y + (height + total_height) / 2
    baselines: list[float] = []
    for index, (font, size, _line_count, _leading) in enumerate(runs):
        ascent = pdfmetrics.getAscent(font, size)
        baselines.append(visual_top - ascent)
        visual_top -= run_heights[index] + gap
    return baselines


@dataclass(frozen=True)
class Box:
    name: str
    x: float
    y: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y + self.height


@dataclass
class Cursor:
    y: float


class ManualPage:
    """One page on the shared grid with measured flow and build-time guards."""

    def __init__(self, canvas, page_number: int, title: str, *, bleed: float = 0, qa: bool = False):
        self.c = canvas
        self.page_number = page_number
        self.title = title
        self.bleed = bleed
        self.qa = qa
        self.x0 = bleed
        self.y0 = bleed
        self.trim = TRIM
        self.inside = PAGE_INNER_MARGIN
        self.outside = PAGE_OUTER_MARGIN
        self.left = self.x0 + (self.outside if page_number % 2 == 0 else self.inside)
        self.right = self.x0 + self.trim - (self.inside if page_number % 2 == 0 else self.outside)
        self.width = self.right - self.left
        self.column_width = (self.width - TWO_COLUMN_GUTTER) / 2
        self.footer_top = self.y0 + FOOTER_EXCLUSION_TOP
        self.header_rule_y = self.y0 + self.trim - HEADER_RULE_FROM_TOP
        self.title_top = self.header_rule_y - TITLE_TOP_FROM_RULE
        self.cursor = Cursor(self.title_top)
        self.boxes: list[Box] = []
        self.visuals: list[Box] = []
        self.content_top: float | None = None

    def record_visual(self, name: str, x: float, y: float, width: float, height: float) -> None:
        self.visuals.append(Box(name, x, y, width, height))

    @property
    def primary_content_y(self) -> float:
        if self.content_top is None:
            raise RuntimeError(f"Page {self.page_number} has no primary content anchor")
        return self.content_top

    @property
    def secondary_content_y(self) -> float:
        return self.primary_content_y - SECONDARY_CONTENT_OFFSET

    @property
    def compact_secondary_content_y(self) -> float:
        return self.primary_content_y - COMPACT_SECONDARY_CONTENT_OFFSET

    @property
    def visual_secondary_content_y(self) -> float:
        return self.primary_content_y - VISUAL_SECONDARY_CONTENT_OFFSET

    @property
    def relaxed_secondary_content_y(self) -> float:
        return self.primary_content_y - RELAXED_SECONDARY_CONTENT_OFFSET

    @property
    def bottom_callout_y(self) -> float:
        return self.footer_top + BOTTOM_CALLOUT_CLEARANCE

    @property
    def sparse_callout_y(self) -> float:
        return self.footer_top + SPARSE_CALLOUT_CLEARANCE

    @property
    def lower_content_limit_y(self) -> float:
        return self.y0 + LOWER_CONTENT_LIMIT

    def center_module(self, height: float, name: str) -> None:
        top = (self.primary_content_y + self.lower_content_limit_y + height) / 2
        self.align_to(top, name)

    def align_to(self, y: float, name: str) -> None:
        """Move down to a named anchor without ever pulling content upward."""
        if y > self.cursor.y + 0.25:
            raise RuntimeError(
                f"Page {self.page_number} cannot move upward to {name}: "
                f"{self.cursor.y:.2f} -> {y:.2f}"
            )
        self.cursor.y = y

    def _record(self, name: str, x: float, y: float, width: float, height: float) -> Box:
        tolerance = 0.25
        box = Box(name, x, y, width, height)
        if box.x < self.left - tolerance or box.right > self.right + tolerance:
            raise RuntimeError(f"Page {self.page_number} {name} exceeds the horizontal content frame")
        if box.y < self.footer_top - tolerance:
            raise RuntimeError(f"Page {self.page_number} {name} enters the footer exclusion zone")
        if box.top > self.title_top + tolerance:
            raise RuntimeError(f"Page {self.page_number} {name} exceeds the content top")
        for prior in self.boxes:
            separated = (
                box.right <= prior.x + tolerance
                or box.x >= prior.right - tolerance
                or box.top <= prior.y + tolerance
                or box.y >= prior.top - tolerance
            )
            if not separated:
                raise RuntimeError(f"Page {self.page_number} overlap: {prior.name} / {name}")
        self.boxes.append(box)
        return box

    def reserve(
        self,
        height: float,
        name: str,
        *,
        width: float | None = None,
        x: float | None = None,
        gap: float = SPACE_4,
    ) -> Box:
        width = self.width if width is None else width
        x = self.left if x is None else x
        top = self.cursor.y
        box = self._record(name, x, top - height, width, height)
        self.cursor.y = box.y - gap
        return box

    def spacer(self, height: float) -> None:
        """Move within the measured content frame without creating content."""
        if height < 0:
            raise ValueError("Spacer height must be non-negative")
        if self.cursor.y - height < self.footer_top:
            raise RuntimeError(f"Page {self.page_number} spacer enters the footer exclusion zone")
        self.cursor.y -= height

    def background(self, color=PAPER) -> None:
        self.c.setFillColor(color)
        self.c.rect(self.x0, self.y0, self.trim, self.trim, fill=1, stroke=0)

    def running_header(self) -> None:
        baseline = self.y0 + self.trim - HEADER_BASELINE_FROM_TOP
        self.c.setFillColor(INK)
        self.c.setFont(FONT_DISPLAY_BOLD, 5.8)
        self.c.drawString(self.left, baseline, "PSPMAN")
        self.c.setStrokeColor(ORANGE)
        self.c.setLineWidth(1.0)
        self.c.line(self.left, self.header_rule_y, self.right, self.header_rule_y)

    def section_title(self, title: str, subtitle: str | None = None) -> None:
        box = self.reserve(TITLE_HEIGHT, "title panel", gap=CONTENT_GAP)
        self.c.setFillColor(LIGHT)
        self.c.roundRect(box.x, box.y, box.width, box.height, 6.0, fill=1, stroke=0)
        self.c.setFillColor(INK)
        self.c.setFont(FONT_DISPLAY_BOLD, 12.5)
        self.c.drawString(
            box.x + SPACE_12,
            centered_baseline(box.y, box.height, FONT_DISPLAY_BOLD, 12.5),
            title,
        )
        if subtitle:
            self.text(subtitle, size=7.5, color=MUTED, leading=10.5, gap=SPACE_8)
        self.content_top = self.cursor.y

    def text(
        self,
        text: str,
        *,
        width: float | None = None,
        x: float | None = None,
        size: float = 6.9,
        font: str = FONT_REGULAR,
        color=INK,
        leading: float | None = None,
        gap: float = SPACE_4,
    ) -> float:
        width = self.width if width is None else width
        x = self.left if x is None else x
        leading = leading or size * 1.4
        lines = wrap_inline_lines(text, font, size, width)
        height = max(size, len(lines) * leading)
        box = self.reserve(height, "text", width=width, x=x, gap=gap)
        self.c.setFillColor(color)
        self.c.setFont(font, size)
        baseline = box.top - size
        for line in lines:
            if inline_line_width(line, font, size) > width + 0.25:
                raise RuntimeError(f"Page {self.page_number} text exceeds its measured box")
            draw_inline_line(self.c, line, x, baseline, font, size, color)
            baseline -= leading
        return box.y

    def heading(self, text: str, *, size: float = 8.0, gap: float = SPACE_4) -> None:
        box = self.reserve(size * 1.35, "heading", gap=gap)
        self.c.setFillColor(INK)
        self.c.setFont(FONT_BOLD, size)
        self.c.drawString(box.x, box.top - size, text)

    def bullet(self, text: str, *, color=INK, size: float = 6.45, gap: float = SPACE_4) -> None:
        text_x = self.left + SPACE_16
        width = self.right - text_x
        leading = size * 1.4
        lines = wrap_inline_lines(text, FONT_REGULAR, size, width)
        box = self.reserve(max(size, len(lines) * leading), "bullet", gap=gap)
        baseline = box.top - size
        self.c.setFillColor(ORANGE)
        self.c.circle(self.left + SPACE_4, baseline + size * 0.35, 1.8, fill=1, stroke=0)
        self.c.setFillColor(color)
        self.c.setFont(FONT_REGULAR, size)
        for line in lines:
            draw_inline_line(self.c, line, text_x, baseline, FONT_REGULAR, size, color)
            baseline -= leading

    def step(self, number: int, title: str, body: str) -> None:
        text_x = self.left + SPACE_24
        width = self.right - text_x
        body_size = 6.15
        body_leading = 7.6
        lines = wrap_lines(body, FONT_REGULAR, body_size, width)
        height = max(25.0, 10.0 + len(lines) * body_leading)
        box = self.reserve(height, f"step {number}", gap=SPACE_4)
        self.c.setFillColor(ORANGE)
        self.c.setFont(FONT_DISPLAY_BOLD, 16)
        self.c.drawString(self.left, box.top - 17.0, str(number))
        self.c.setFillColor(INK)
        self.c.setFont(FONT_BOLD, 7.1)
        self.c.drawString(text_x, box.top - 7.1, title)
        self.c.setFillColor(MUTED)
        self.c.setFont(FONT_REGULAR, body_size)
        baseline = box.top - 18.0
        for line in lines:
            self.c.drawString(text_x, baseline, line)
            baseline -= body_leading

    def callout(
        self,
        kind: str,
        text: str,
        *,
        color=ORANGE,
        bottom_anchor: float | None = None,
    ) -> None:
        label = kind.upper()
        label_x = self.left + SPACE_8
        text_x = label_x + pdfmetrics.stringWidth(label, FONT_BOLD, 5.8) + SPACE_12
        width = self.right - text_x - SPACE_8
        lines = wrap_inline_lines(text, FONT_REGULAR, 5.75, width)
        height = max(28.0, SPACE_12 + len(lines) * 7.2)
        if bottom_anchor is not None:
            target_top = bottom_anchor + height
            self.align_to(target_top, f"{label.lower()} callout anchor")
        box = self.reserve(height, f"{label.lower()} callout", gap=SPACE_4)
        self.c.setFillColor(LIGHT)
        self.c.roundRect(box.x, box.y, box.width, box.height, 5.5, fill=1, stroke=0)
        label_baseline = centered_baseline(box.y, box.height, FONT_BOLD, 5.8)
        text_baseline = centered_stack_baselines(
            box.y,
            box.height,
            [(FONT_REGULAR, 5.75, len(lines), 7.2)],
        )[0]
        self.c.setFillColor(color)
        self.c.setFont(FONT_BOLD, 5.8)
        self.c.drawString(label_x, label_baseline, label)
        self.c.setFillColor(INK)
        self.c.setFont(FONT_REGULAR, 5.75)
        baseline = text_baseline
        for line in lines:
            draw_inline_line(self.c, line, text_x, baseline, FONT_REGULAR, 5.75, INK)
            baseline -= 7.2

    def table(
        self,
        headers: list[str],
        rows: Iterable[list[str]],
        widths: list[float],
        *,
        size: float = 5.1,
        row_height: float = 16.0,
    ) -> None:
        rows = list(rows)
        if len(headers) != len(widths) or any(len(row) != len(widths) for row in rows):
            raise RuntimeError(f"Page {self.page_number} malformed table")
        if sum(widths) > self.width + 0.25:
            raise RuntimeError(f"Page {self.page_number} table exceeds the master content frame")
        row_h = row_height
        height = row_h * (len(rows) + 1)
        box = self.reserve(height, "table", width=sum(widths), gap=SPACE_12)
        x, y = box.x, box.top
        self.c.setFillColor(CHARCOAL)
        self.c.rect(x, y - row_h, box.width, row_h, fill=1, stroke=0)
        self.c.setFillColor(WHITE)
        self.c.setFont(FONT_BOLD, size)
        header_baseline = centered_baseline(y - row_h, row_h, FONT_BOLD, size)
        xx = x
        for header, width in zip(headers, widths):
            self.c.drawString(xx + SPACE_4, header_baseline, header)
            xx += width
        y -= row_h
        for index, row in enumerate(rows):
            self.c.setFillColor(PAPER if index % 2 == 0 else LIGHT)
            self.c.rect(x, y - row_h, box.width, row_h, fill=1, stroke=0)
            self.c.setFillColor(INK)
            self.c.setFont(FONT_REGULAR, size)
            row_baseline = centered_baseline(y - row_h, row_h, FONT_REGULAR, size)
            xx = x
            for value, width in zip(row, widths):
                clipped = value
                while clipped and pdfmetrics.stringWidth(clipped, FONT_REGULAR, size) > width - SPACE_8:
                    clipped = clipped[:-1]
                if clipped != value and len(clipped) > 1:
                    clipped = clipped[:-1] + "..."
                self.c.drawString(xx + SPACE_4, row_baseline, clipped)
                xx += width
            y -= row_h

    def screenshot(self, path: Path, *, width_mm: float | None = None, caption: str | None = None) -> None:
        # Screenshots stay at the native 480x272 aspect ratio. Sparse feature
        # pages may use a larger measured width so the capture can act as the
        # page's visual anchor.
        with Image.open(path) as im:
            width_px, height_px = im.size
            if (width_px, height_px) != (480, 272):
                raise RuntimeError(f"Screenshot must be native 480x272: {path}")
            if im.mode != "RGB":
                raise RuntimeError(f"Screenshot must be opaque RGB: {path}")
        width = min(mm(48 if width_mm is None else width_mm), self.width)
        height = width / SCREEN_ASPECT
        caption_height = 0 if not caption else 11.0
        box = self.reserve(height + caption_height, f"screenshot:{path.name}", gap=SPACE_8)
        image_x = self.left + (self.width - width) / 2
        image_y = box.top - height
        self.record_visual(f"visible-screenshot:{path.name}", image_x, image_y, width, height)
        print_path = path.parent / "print-2x" / path.name.replace("-480x272", "-960x544")
        source = print_path if print_path.exists() else path
        self.c.setStrokeColor(CHARCOAL)
        self.c.setLineWidth(0.8)
        self.c.rect(image_x - 1.0, image_y - 1.0, width + 2.0, height + 2.0, fill=0, stroke=1)
        self.c.drawImage(monochrome_image_reader(source), image_x, image_y, width, height, preserveAspectRatio=True, mask=None)
        if caption:
            self.c.setFillColor(MUTED)
            self.c.setFont(FONT_REGULAR, 5.7)
            self.c.drawCentredString((self.left + self.right) / 2, box.y + 1.0, caption)

    def qa_overlay(self) -> None:
        if not self.qa:
            return
        self.c.saveState()
        self.c.setLineWidth(0.35)
        self.c.setStrokeColorRGB(0.85, 0.0, 0.0, alpha=0.55)
        self.c.rect(self.left, self.footer_top, self.width, self.title_top - self.footer_top, fill=0, stroke=1)
        self.c.setStrokeColorRGB(0.0, 0.45, 0.85, alpha=0.55)
        self.c.line(self.left + self.column_width, self.footer_top, self.left + self.column_width, self.title_top)
        self.c.line(self.left + self.column_width + TWO_COLUMN_GUTTER, self.footer_top, self.left + self.column_width + TWO_COLUMN_GUTTER, self.title_top)
        self.c.setStrokeColorRGB(0.5, 0.2, 0.8, alpha=0.35)
        baseline = self.lower_content_limit_y
        while baseline <= self.primary_content_y + 0.25:
            self.c.line(self.left, baseline, self.right, baseline)
            baseline += BASELINE_GRID
        page_center = self.x0 + self.trim / 2
        self.c.setStrokeColorRGB(0.7, 0.1, 0.6, alpha=0.65)
        self.c.line(page_center, self.y0, page_center, self.y0 + self.trim)
        self.c.setFont(FONT_BOLD, 3.8)
        self.c.setFillColorRGB(0.7, 0.1, 0.6, alpha=0.8)
        self.c.drawCentredString(page_center, self.y0 + self.trim - SPACE_8, "PAGE CENTER")
        for x, label in (
            (self.left, "OUTER" if self.page_number % 2 == 0 else "INNER"),
            (self.right, "INNER" if self.page_number % 2 == 0 else "OUTER"),
        ):
            self.c.setStrokeColorRGB(0.85, 0.0, 0.0, alpha=0.65)
            self.c.line(x, self.y0, x, self.y0 + self.trim)
            self.c.setFillColorRGB(0.75, 0.0, 0.0, alpha=0.8)
            self.c.drawCentredString(x, self.y0 + SPACE_8, label)
        guides = [
            ("HEADER", self.y0 + self.trim - HEADER_BASELINE_FROM_TOP),
            ("RULE", self.header_rule_y),
            ("TITLE TOP", self.title_top),
            ("TITLE BOTTOM", self.title_top - TITLE_HEIGHT),
            ("PRIMARY", self.primary_content_y),
            ("SECONDARY COMPACT", self.compact_secondary_content_y),
            ("SECONDARY VISUAL", self.visual_secondary_content_y),
            ("SECONDARY", self.secondary_content_y),
            ("SECONDARY RELAXED", self.relaxed_secondary_content_y),
            ("CALLOUT", self.bottom_callout_y),
            ("CALLOUT SPARSE", self.sparse_callout_y),
            ("LOWER LIMIT", self.lower_content_limit_y),
            ("FOOTER RULE", self.y0 + FOOTER_RULE),
            ("FOOTER", self.y0 + FOOTER_BASELINE),
        ]
        self.c.setFont(FONT_BOLD, 3.8)
        for label, y in guides:
            self.c.setStrokeColorRGB(0.0, 0.45, 0.85, alpha=0.65)
            self.c.line(self.left, y, self.right, y)
            self.c.setFillColorRGB(0.0, 0.35, 0.75, alpha=0.8)
            self.c.drawRightString(self.right, y + 1.2, label)
        for box in self.boxes:
            self.c.setStrokeColorRGB(0.1, 0.65, 0.25, alpha=0.55)
            self.c.rect(box.x, box.y, box.width, box.height, fill=0, stroke=1)
        self.c.restoreState()

    def footer(self) -> None:
        if self.page_number in (1, 32):
            return
        rule_y = self.y0 + FOOTER_RULE
        baseline = self.y0 + FOOTER_BASELINE
        self.c.setStrokeColor(RULE)
        self.c.setLineWidth(0.5)
        self.c.line(self.left, rule_y, self.right, rule_y)
        self.c.setFillColor(MUTED)
        self.c.setFont(FONT_REGULAR, 5.3)
        if self.page_number % 2 == 0:
            self.c.drawString(self.left, baseline, str(self.page_number))
        else:
            self.c.drawRightString(self.right, baseline, str(self.page_number))


def draw_brand_wordmark(c, x: float, y: float, *, size: float = 12, color=WHITE) -> None:
    c.setFillColor(color)
    c.setFont(FONT_DISPLAY, size)
    c.drawString(x, y, "OBSOLETESONY / PSPMAN")


def draw_button(c, x: float, y: float, label: str, *, radius: float = mm(4.5)) -> None:
    c.setStrokeColor(INK)
    c.setLineWidth(1.0)
    c.circle(x, y, radius, fill=0, stroke=1)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 5.2)
    c.drawCentredString(x, centered_baseline(y - radius, radius * 2, FONT_BOLD, 5.2), label)
