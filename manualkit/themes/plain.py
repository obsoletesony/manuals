"""A deliberately quiet, text-first manual theme."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics

from manualkit.deterministic import PdfMetadata, apply_metadata, invariant_canvas
from manualkit.project import ManualProject, ProjectError


MM = 72.0 / 25.4
TRIM_SIZE = (148 * MM, 210 * MM)
BLEED = 3 * MM
PRINT_SIZE = (TRIM_SIZE[0] + 2 * BLEED, TRIM_SIZE[1] + 2 * BLEED)
SPREAD_SIZE = (TRIM_SIZE[0] * 2, TRIM_SIZE[1])

INK = HexColor("#171717")
MUTED = HexColor("#666666")
RULE = HexColor("#b8b8b8")
PAPER = HexColor("#ffffff")

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_MONO = "Courier"

SIDE_MARGIN = 48.0
TOP_MARGIN = 48.0
BOTTOM_MARGIN = 44.0


class LayoutError(ProjectError):
    """Text cannot fit within the neutral theme's page geometry."""


@dataclass(frozen=True)
class DrawRecord:
    page: int
    kind: str
    x0: float
    y0: float
    x1: float
    y1: float


def _split_long_word(word: str, font: str, size: float, width: float) -> list[str]:
    pieces: list[str] = []
    current = ""
    for character in word:
        candidate = current + character
        if current and pdfmetrics.stringWidth(candidate, font, size) > width:
            pieces.append(current)
            current = character
        else:
            current = candidate
    if current:
        pieces.append(current)
    return pieces or [""]


def wrap_text(text: str, font: str, size: float, width: float) -> list[str]:
    """Wrap text by rendered width without introducing changing inputs."""

    words: list[str] = []
    for word in text.split():
        if pdfmetrics.stringWidth(word, font, size) <= width:
            words.append(word)
        else:
            words.extend(_split_long_word(word, font, size, width))
    if not words:
        return [""]
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if pdfmetrics.stringWidth(candidate, font, size) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


class PlainDocument:
    """Render the small text-manual manifest without inferred decoration."""

    def __init__(self, path: Path, project: ManualProject, *, print_edition: bool):
        self.project = project
        self.document = project.document
        self.print_edition = print_edition
        self.origin = BLEED if print_edition else 0.0
        self.page_size = PRINT_SIZE if print_edition else TRIM_SIZE
        self.canvas = invariant_canvas(path, self.page_size)
        apply_metadata(
            self.canvas,
            PdfMetadata(
                title=self.document["title"],
                author=self.document["author"],
                creator="ObsoleteSony manualkit",
                subject=self.document["subject"],
                keywords=self.document["keywords"],
            ),
        )
        self.left = self.origin + SIDE_MARGIN
        self.right = self.origin + TRIM_SIZE[0] - SIDE_MARGIN
        self.top = self.origin + TRIM_SIZE[1] - TOP_MARGIN
        self.bottom = self.origin + BOTTOM_MARGIN
        self.width = self.right - self.left
        self.page = 0
        self.y = self.top
        self.interior = False
        self.records: list[DrawRecord] = []

    def _record(self, kind: str, x0: float, y0: float, x1: float, y1: float) -> None:
        self.records.append(DrawRecord(self.page, kind, x0, y0, x1, y1))

    def _finish_page(self) -> None:
        if not self.interior:
            return
        label = str(self.page)
        font_size = 8.0
        self.canvas.setFillColor(MUTED)
        self.canvas.setFont(FONT_REGULAR, font_size)
        baseline = self.origin + 20.0
        if self.page % 2:
            self.canvas.drawRightString(self.origin + TRIM_SIZE[0] - 24.0, baseline, label)
            x0 = self.origin + TRIM_SIZE[0] - 36.0
            x1 = self.origin + TRIM_SIZE[0] - 24.0
        else:
            self.canvas.drawString(self.origin + 24.0, baseline, label)
            x0 = self.origin + 24.0
            x1 = self.origin + 36.0
        self._record("page-number", x0, baseline - 2.0, x1, baseline + font_size)

    def _start_page(self, *, interior: bool) -> None:
        if self.page:
            self._finish_page()
            self.canvas.showPage()
        self.page += 1
        self.interior = interior
        self.y = self.top
        self.canvas.setFillColor(PAPER)
        self.canvas.rect(0, 0, self.page_size[0], self.page_size[1], fill=1, stroke=0)
        running_name = self.document.get("runningName", "").strip()
        if interior and running_name:
            self.canvas.setFillColor(MUTED)
            self.canvas.setFont(FONT_REGULAR, 8.0)
            self.canvas.drawString(self.left, self.y, running_name)
            self._record("running-name", self.left, self.y - 2.0, self.right, self.y + 8.0)
            self.y -= 18.0

    def _ensure(self, height: float) -> None:
        if height > self.top - self.bottom:
            raise LayoutError(f"A text block is taller than a page: {height:.2f} points")
        if self.y - height < self.bottom:
            self._start_page(interior=True)

    def _draw_lines(
        self,
        lines: list[str],
        *,
        x: float,
        font: str,
        size: float,
        leading: float,
        kind: str,
        color=INK,
    ) -> None:
        height = max(size, len(lines) * leading)
        self._ensure(height)
        top = self.y
        self.canvas.setFillColor(color)
        self.canvas.setFont(font, size)
        baseline = self.y - size
        for line in lines:
            self.canvas.drawString(x, baseline, line)
            baseline -= leading
        self.y -= height
        self._record(kind, x, self.y, self.right, top)

    def draw_cover(self) -> None:
        self._start_page(interior=False)
        title_lines = wrap_text(self.document["title"], FONT_BOLD, 24.0, self.width)
        self.y -= 54.0
        self._draw_lines(
            title_lines,
            x=self.left,
            font=FONT_BOLD,
            size=24.0,
            leading=29.0,
            kind="document-title",
        )
        self.y -= 12.0
        self.canvas.setStrokeColor(RULE)
        self.canvas.setLineWidth(0.8)
        self.canvas.line(self.left, self.y, self.right, self.y)
        self._record("title-rule", self.left, self.y - 0.4, self.right, self.y + 0.4)
        self.y -= 22.0
        subtitle = self.document.get("subtitle", "").strip()
        if subtitle:
            lines = wrap_text(subtitle, FONT_REGULAR, 11.0, self.width)
            self._draw_lines(
                lines,
                x=self.left,
                font=FONT_REGULAR,
                size=11.0,
                leading=15.0,
                kind="subtitle",
                color=MUTED,
            )

    def draw_section(self, section: dict) -> None:
        if not self.interior:
            self._start_page(interior=True)
        title_lines = wrap_text(section["title"], FONT_BOLD, 17.0, self.width)
        required = len(title_lines) * 21.0 + 18.0
        self._ensure(required)
        if self.y < self.top - 1.0:
            self.y -= 14.0
        self._draw_lines(
            title_lines,
            x=self.left,
            font=FONT_BOLD,
            size=17.0,
            leading=21.0,
            kind="section-heading",
        )
        self.y -= 14.0
        for block in section["blocks"]:
            self.draw_block(block)

    def draw_block(self, block: dict) -> None:
        kind = block["type"]
        if kind == "paragraph":
            lines = wrap_text(block["text"], FONT_REGULAR, 10.0, self.width)
            self._draw_lines(
                lines,
                x=self.left,
                font=FONT_REGULAR,
                size=10.0,
                leading=14.0,
                kind=kind,
            )
            self.y -= 11.0
        elif kind == "subheading":
            self.y -= 4.0
            lines = wrap_text(block["text"], FONT_BOLD, 12.0, self.width)
            self._draw_lines(
                lines,
                x=self.left,
                font=FONT_BOLD,
                size=12.0,
                leading=16.0,
                kind=kind,
            )
            self.y -= 7.0
        elif kind in {"ordered-list", "unordered-list"}:
            self._draw_list(block["items"], ordered=kind == "ordered-list")
            self.y -= 8.0
        elif kind == "code":
            self._draw_code(block["text"])
            self.y -= 11.0
        elif kind == "table":
            self._draw_table(block["columns"], block["rows"])
            self.y -= 11.0
        else:
            raise LayoutError(f"Unsupported text block: {kind}")

    def _draw_list(self, items: list[str], *, ordered: bool) -> None:
        indent = 20.0
        text_width = self.width - indent
        for index, item in enumerate(items, 1):
            lines = wrap_text(item, FONT_REGULAR, 10.0, text_width)
            height = len(lines) * 14.0
            self._ensure(height)
            top = self.y
            self.canvas.setFillColor(INK)
            self.canvas.setFont(FONT_REGULAR, 10.0)
            label = f"{index}." if ordered else "-"
            baseline = self.y - 10.0
            self.canvas.drawRightString(self.left + 13.0, baseline, label)
            for line in lines:
                self.canvas.drawString(self.left + indent, baseline, line)
                baseline -= 14.0
            self.y -= height
            self._record("ordered-list" if ordered else "unordered-list", self.left, self.y, self.right, top)
            self.y -= 4.0

    def _draw_code(self, text: str) -> None:
        inset = 12.0
        width = self.width - inset * 2
        lines: list[str] = []
        for source_line in text.splitlines() or [""]:
            lines.extend(wrap_text(source_line, FONT_MONO, 8.5, width))
        height = len(lines) * 12.0 + 12.0
        self._ensure(height)
        top = self.y
        self.canvas.setStrokeColor(RULE)
        self.canvas.setLineWidth(0.5)
        self.canvas.line(self.left, top, self.right, top)
        baseline = top - 14.0
        self.canvas.setFillColor(INK)
        self.canvas.setFont(FONT_MONO, 8.5)
        for line in lines:
            self.canvas.drawString(self.left + inset, baseline, line)
            baseline -= 12.0
        self.y -= height
        self.canvas.line(self.left, self.y, self.right, self.y)
        self._record("code", self.left, self.y, self.right, top)

    def _draw_table(self, columns: list[str], rows: list[list[str]]) -> None:
        column_width = self.width / len(columns)
        cell_padding = 5.0
        font_size = 8.5
        leading = 11.0
        prepared: list[tuple[list[list[str]], float]] = []
        for row in [columns, *rows]:
            cells = [
                wrap_text(value, FONT_BOLD if row is columns else FONT_REGULAR, font_size, column_width - 2 * cell_padding)
                for value in row
            ]
            height = max(len(lines) for lines in cells) * leading + 2 * cell_padding
            prepared.append((cells, height))
        total_height = sum(height for _, height in prepared)
        self._ensure(total_height)
        top = self.y
        self.canvas.setStrokeColor(RULE)
        self.canvas.setLineWidth(0.5)
        y = top
        for row_index, (cells, height) in enumerate(prepared):
            self.canvas.line(self.left, y, self.right, y)
            self.canvas.setFont(FONT_BOLD if row_index == 0 else FONT_REGULAR, font_size)
            self.canvas.setFillColor(INK)
            for column_index, lines in enumerate(cells):
                x = self.left + column_index * column_width
                baseline = y - cell_padding - font_size
                for line in lines:
                    self.canvas.drawString(x + cell_padding, baseline, line)
                    baseline -= leading
            y -= height
        self.canvas.line(self.left, y, self.right, y)
        for index in range(len(columns) + 1):
            x = self.left + index * column_width
            self.canvas.line(x, top, x, y)
        self.y = y
        self._record("table", self.left, y, self.right, top)

    def finish(self) -> dict:
        self._finish_page()
        self.canvas.save()
        return {
            "pages": self.page,
            "pageSizePoints": [self.page_size[0], self.page_size[1]],
            "trimSizePoints": [TRIM_SIZE[0], TRIM_SIZE[1]],
            "records": [asdict(record) for record in self.records],
        }


def build_plain_edition(path: Path, project: ManualProject, *, print_edition: bool) -> dict:
    """Build one Reader or Print edition with the neutral theme."""

    renderer = PlainDocument(path, project, print_edition=print_edition)
    renderer.draw_cover()
    for section in project.sections:
        renderer.draw_section(section)
    return renderer.finish()
