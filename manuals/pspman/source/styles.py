"""Shared visual constants for the PSPMAN operating instructions."""

from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

MM = 72.0 / 25.4
TRIM = 120 * MM
BLEED = 3 * MM
PRINT_SIZE = TRIM + 2 * BLEED
SPREAD_SIZE = (TRIM * 2, TRIM)

INK = HexColor("#171717")
MUTED = HexColor("#686868")
LIGHT = HexColor("#ececec")
PAPER = HexColor("#fafafa")
ORANGE = HexColor("#111111")
CHARCOAL = HexColor("#222222")
GOLD = HexColor("#555555")
WHITE = HexColor("#ffffff")
RULE = HexColor("#b7b7b7")

FONT_REGULAR = "Inter"
FONT_BOLD = "Inter-Bold"
FONT_DISPLAY = "InterDisplay"
FONT_DISPLAY_BOLD = "InterDisplay-Bold"


def register_fonts(repo_root: Path) -> None:
    font_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    definitions = {
        FONT_REGULAR: font_dir / "Inter-Regular.ttf",
        FONT_BOLD: font_dir / "Inter-Bold.ttf",
        FONT_DISPLAY: font_dir / "InterDisplay-Regular.ttf",
        FONT_DISPLAY_BOLD: font_dir / "InterDisplay-Bold.ttf",
    }
    for name, path in definitions.items():
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(path)))


def mm(value: float) -> float:
    return value * MM
