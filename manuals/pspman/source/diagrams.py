"""Original vector diagrams used by the PSPMAN manual."""

from __future__ import annotations

from pathlib import Path

from reportlab.pdfbase import pdfmetrics

from layout import (
    BUTTON_SYMBOLS,
    centered_baseline,
    centered_stack_baselines,
    draw_button,
    draw_button_symbol_at,
    monochrome_image_reader,
    wrap_lines,
)
from styles import CHARCOAL, FONT_BOLD, FONT_REGULAR, GOLD, INK, LIGHT, MUTED, ORANGE, PAPER, RULE, WHITE, mm


ASSET_DIR = Path(__file__).resolve().parent.parent / "assets" / "diagrams"
PSP_FRONT_ASSET = ASSET_DIR / "psp-2000-black-cc0.png"


def _label(c, number: int, x: float, y: float, text: str, target_x: float, target_y: float) -> None:
    c.setStrokeColor(ORANGE)
    c.setFillColor(ORANGE)
    c.setLineWidth(mm(0.35))
    c.line(x + mm(3), y, target_x, target_y)
    c.circle(x, y, mm(2.5), fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 5.3)
    c.drawCentredString(x, y - 1.8, str(number))
    c.setFillColor(INK)
    c.setFont(FONT_REGULAR, 5.2)
    c.drawString(x + mm(4), y - 1.8, text)


def psp_front(c, x: float, y: float, w: float, h: float, *, callouts: bool = False) -> None:
    """Simplified original front view, intentionally unbranded."""
    body_y = y + h * 0.2
    body_h = h * 0.62
    c.setFillColor(PAPER)
    c.setStrokeColor(INK)
    c.setLineWidth(mm(0.55))
    c.roundRect(x, body_y, w, body_h, mm(7), fill=1, stroke=1)
    screen_x, screen_y = x + w * 0.22, body_y + body_h * 0.14
    screen_w, screen_h = w * 0.56, body_h * 0.72
    c.setFillColor(CHARCOAL)
    c.roundRect(screen_x, screen_y, screen_w, screen_h, mm(1.7), fill=1, stroke=0)
    c.setFillColor(LIGHT)
    c.setFont(FONT_BOLD, 8)
    c.drawCentredString(screen_x + screen_w / 2, screen_y + screen_h / 2 - 3, "PSPMAN")
    # D-pad
    dx, dy = x + w * 0.12, body_y + body_h * 0.5
    c.setFillColor(INK)
    c.rect(dx - mm(1.6), dy - mm(6), mm(3.2), mm(12), fill=1, stroke=0)
    c.rect(dx - mm(6), dy - mm(1.6), mm(12), mm(3.2), fill=1, stroke=0)
    # Face buttons
    fx, fy = x + w * 0.88, dy
    for ox, oy, label in [(0, mm(5), "△"), (mm(5), 0, "○"), (0, -mm(5), "×"), (-mm(5), 0, "□")]:
        c.setStrokeColor(INK)
        c.circle(fx + ox, fy + oy, mm(2), fill=0, stroke=1)
        c.setFont(FONT_REGULAR, 4)
        c.drawCentredString(fx + ox, fy + oy - 1.4, label)
    # Analog, Start, Select, Home
    c.setStrokeColor(INK)
    c.circle(x + w * 0.12, body_y + body_h * 0.23, mm(3.2), fill=0, stroke=1)
    c.setFont(FONT_REGULAR, 4.4)
    c.drawCentredString(x + w * 0.45, body_y + mm(3), "SELECT")
    c.drawCentredString(x + w * 0.55, body_y + mm(3), "START")
    c.drawCentredString(x + w * 0.5, body_y - mm(3), "HOME")
    # Shoulder controls
    c.setFillColor(INK)
    c.roundRect(x + mm(5), body_y + body_h - mm(0.5), w * 0.16, mm(3), mm(1), fill=1, stroke=0)
    c.roundRect(x + w * 0.84 - mm(5), body_y + body_h - mm(0.5), w * 0.16, mm(3), mm(1), fill=1, stroke=0)
    if callouts:
        _label(c, 1, x, y + h * 0.92, "L / R", x + mm(12), body_y + body_h)
        _label(c, 2, x, y + h * 0.08, "D-pad", dx, dy)
        _label(c, 3, x + w * 0.78, y + h * 0.92, "Face buttons", fx, fy)
        _label(c, 4, x + w * 0.78, y + h * 0.08, "START / SELECT", x + w * 0.52, body_y + mm(3))
        _label(c, 5, x + w * 0.37, y, "HOME", x + w * 0.5, body_y - mm(3))


def psp_front(c, x: float, y: float, w: float, h: float, *, callouts: bool = False) -> None:
    """Detailed CC0 PSP-2000 front view with collision-free callouts."""
    ratio = 1280 / 555
    image_w = min(w * 0.82, h * 0.78 * ratio)
    image_h = image_w / ratio
    image_x = x + (w - image_w) / 2
    image_y = y + (h - image_h) / 2
    c.drawImage(
        monochrome_image_reader(PSP_FRONT_ASSET),
        image_x,
        image_y,
        image_w,
        image_h,
        preserveAspectRatio=True,
        mask="auto",
    )

    if not callouts:
        return

    def marker(number: int, mx: float, my: float, tx: float, ty: float) -> None:
        radius = mm(2.35)
        c.setStrokeColor(ORANGE)
        c.setLineWidth(mm(0.45))
        c.line(mx, my, tx, ty)
        c.setFillColor(ORANGE)
        c.circle(mx, my, radius, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont(FONT_BOLD, 5.3)
        c.drawCentredString(mx, my - 1.8, str(number))

    marker(1, x + mm(3), y + h - mm(3), image_x + image_w * 0.16, image_y + image_h * 0.93)
    marker(2, x + mm(3), y + h * 0.48, image_x + image_w * 0.12, image_y + image_h * 0.52)
    marker(3, x + w - mm(3), y + h - mm(3), image_x + image_w * 0.88, image_y + image_h * 0.52)
    marker(4, x + w - mm(3), y + mm(3), image_x + image_w * 0.75, image_y + image_h * 0.09)
    marker(5, x + w * 0.36, y + mm(2.5), image_x + image_w * 0.22, image_y + image_h * 0.08)


def installation(c, x: float, y: float, w: float, h: float) -> None:
    box_w = w * 0.34
    for bx, title, lines in [
        (x, "COMPUTER", ["PSP", "└ GAME", "  └ PSPMAN", "    └ EBOOT.PBP"]),
        (x + w - box_w, "PSP STORAGE", ["PSP", "└ GAME", "  └ PSPMAN", "    └ EBOOT.PBP"]),
    ]:
        c.setFillColor(LIGHT)
        c.roundRect(bx, y, box_w, h, mm(2), fill=1, stroke=0)
        title_baseline, lines_baseline = centered_stack_baselines(
            y,
            h,
            [
                (FONT_BOLD, 6.4, 1, 6.4),
                (FONT_REGULAR, 5.6, len(lines), mm(4)),
            ],
            gap=mm(2.5),
        )
        c.setFillColor(INK)
        c.setFont(FONT_BOLD, 6.4)
        c.drawString(bx + mm(3), title_baseline, title)
        c.setFont(FONT_REGULAR, 5.6)
        yy = lines_baseline
        for line in lines:
            c.drawString(bx + mm(4), yy, line)
            yy -= mm(4)
    ax1 = x + box_w + mm(3)
    ax2 = x + w - box_w - mm(3)
    ay = y + h / 2
    c.setStrokeColor(ORANGE)
    c.setLineWidth(mm(1))
    c.line(ax1, ay, ax2, ay)
    c.line(ax2, ay, ax2 - mm(4), ay + mm(3))
    c.line(ax2, ay, ax2 - mm(4), ay - mm(3))
    c.setFillColor(ORANGE)
    c.setFont(FONT_BOLD, 5.5)
    c.drawCentredString((ax1 + ax2) / 2, ay + mm(4), "COPY")


def folder_tree(c, x: float, y: float, w: float, h: float) -> None:
    rows = [
        (0, "MUSIC"),
        (1, "ObsoleteSony"),
        (2, "Digital Music Player"),
        (3, "01 - PSPMAN.flac"),
        (1, "Playlists"),
        (2, "Favorites.m3u8"),
    ]
    c.setFillColor(LIGHT)
    c.roundRect(x, y, w, h, mm(2), fill=1, stroke=0)
    yy = centered_stack_baselines(
        y,
        h,
        [(FONT_REGULAR, 5.8, len(rows), mm(5))],
    )[0]
    for level, label in rows:
        xx = x + mm(4 + level * 7)
        if level < 3 and not label.endswith((".flac", ".m3u8")):
            c.setFillColor(GOLD if level == 0 else MUTED)
            c.roundRect(xx, yy - mm(2), mm(5), mm(3.5), mm(0.5), fill=1, stroke=0)
            text_x = xx + mm(7)
        else:
            c.setStrokeColor(ORANGE)
            c.rect(xx, yy - mm(2), mm(3.5), mm(4.5), fill=0, stroke=1)
            text_x = xx + mm(5.5)
        c.setFillColor(INK)
        c.setFont(FONT_REGULAR, 5.8)
        c.drawString(text_x, yy, label)
        yy -= mm(5)


def _transport_glyph(c, kind: str, cx: float, cy: float) -> None:
    """Draw PSPMAN transport marks as vectors so print output stays crisp."""
    c.saveState()
    c.setFillColor(INK)
    c.setStrokeColor(INK)
    c.setLineWidth(mm(0.85))
    c.setLineCap(1)
    c.setLineJoin(1)

    if kind in {"previous", "next"}:
        direction = -1 if kind == "previous" else 1
        bar_x = cx + direction * mm(3.6)
        c.rect(bar_x - mm(0.55), cy - mm(2.7), mm(1.1), mm(5.4), fill=1, stroke=0)
        for offset in (-mm(0.8), mm(2.0)):
            tip_x = cx + direction * offset
            base_x = tip_x - direction * mm(3.1)
            path = c.beginPath()
            path.moveTo(tip_x, cy)
            path.lineTo(base_x, cy + mm(2.6))
            path.lineTo(base_x, cy - mm(2.6))
            path.close()
            c.drawPath(path, fill=1, stroke=0)
    elif kind == "play-pause":
        path = c.beginPath()
        path.moveTo(cx - mm(3.8), cy - mm(2.7))
        path.lineTo(cx - mm(0.2), cy)
        path.lineTo(cx - mm(3.8), cy + mm(2.7))
        path.close()
        c.drawPath(path, fill=1, stroke=0)
        c.rect(cx + mm(1.0), cy - mm(2.7), mm(0.9), mm(5.4), fill=1, stroke=0)
        c.rect(cx + mm(2.7), cy - mm(2.7), mm(0.9), mm(5.4), fill=1, stroke=0)
    elif kind == "shuffle":
        for upper in (True, False):
            sy = cy + (mm(2.1) if upper else -mm(2.1))
            ey = cy - (mm(2.1) if upper else -mm(2.1))
            path = c.beginPath()
            path.moveTo(cx - mm(4.0), sy)
            path.lineTo(cx - mm(2.3), sy)
            path.curveTo(cx - mm(0.8), sy, cx + mm(0.5), ey, cx + mm(3.0), ey)
            c.drawPath(path, fill=0, stroke=1)
            arrow = c.beginPath()
            arrow.moveTo(cx + mm(4.1), ey)
            arrow.lineTo(cx + mm(2.6), ey + mm(1.2))
            arrow.lineTo(cx + mm(2.6), ey - mm(1.2))
            arrow.close()
            c.drawPath(arrow, fill=1, stroke=0)
    elif kind == "repeat":
        p = c.beginPath()
        p.moveTo(cx - mm(3.7), cy + mm(1.5))
        p.curveTo(cx - mm(2.6), cy + mm(3.0), cx + mm(1.4), cy + mm(3.0), cx + mm(2.8), cy + mm(1.5))
        c.drawPath(p, fill=0, stroke=1)
        p = c.beginPath()
        p.moveTo(cx + mm(3.7), cy - mm(1.5))
        p.curveTo(cx + mm(2.6), cy - mm(3.0), cx - mm(1.4), cy - mm(3.0), cx - mm(2.8), cy - mm(1.5))
        c.drawPath(p, fill=0, stroke=1)
        for ax, ay, direction in ((cx + mm(3.7), cy + mm(1.5), 1), (cx - mm(3.7), cy - mm(1.5), -1)):
            arrow = c.beginPath()
            arrow.moveTo(ax, ay)
            arrow.lineTo(ax - direction * mm(1.5), ay + mm(1.1))
            arrow.lineTo(ax - direction * mm(1.5), ay - mm(1.1))
            arrow.close()
            c.drawPath(arrow, fill=1, stroke=0)
    c.restoreState()


def playback_controls(c, x: float, y: float, w: float, h: float) -> None:
    labels = [("SHUFFLE", "↝"), ("PREVIOUS", "|◀◀"), ("PLAY / PAUSE", "▶ /Ⅱ"), ("NEXT", "▶▶|"), ("REPEAT", "↻")]
    labels_text = ["SHUFFLE", "PREVIOUS", "PLAY / PAUSE", "NEXT", "REPEAT"]
    kinds = ["shuffle", "previous", "play-pause", "next", "repeat"]
    gap = w / len(labels_text)
    for i, (label, kind) in enumerate(zip(labels_text, kinds)):
        cx = x + gap * (i + 0.5)
        radius = mm(8 if i == 2 else 6)
        c.setStrokeColor(ORANGE if i == 2 else MUTED)
        c.setLineWidth(mm(0.55))
        # Optical correction: the labels occupy the lower portion of the
        # measured box, so the control row sits above the geometric midpoint.
        # This aligns its visible top with facing-page application screenshots.
        control_y = y + h * 0.72
        c.circle(cx, control_y, radius, fill=0, stroke=1)
        _transport_glyph(c, kind, cx, control_y)
        c.setFillColor(MUTED)
        c.setFont(FONT_REGULAR, 4.5)
        c.drawCentredString(cx, y + mm(2), label)


def navigation_map(c, x: float, y: float, w: float, h: float) -> None:
    nodes = {
        "LIBRARY\nHOME": (0.01, 0.61),
        "LISTS": (0.28, 0.61),
        "NOW\nPLAYING": (0.54, 0.61),
        "TRACK\nINFORMATION": (0.80, 0.75),
        "CASSETTE\nVIEW": (0.80, 0.47),
        "ABOUT": (0.01, 0.10),
        "ANY\nSCREEN": (0.37, 0.10),
        "SYSTEM\nQUIT": (0.73, 0.10),
    }
    positions = {}
    for name, (px, py) in nodes.items():
        nx, ny = x + w * px, y + h * py
        nw, nh = w * 0.18, h * 0.16
        positions[name] = (nx, ny, nw, nh)
    links = [
        ("LIBRARY\nHOME", "LISTS", "×"),
        ("LISTS", "NOW\nPLAYING", "PLAY"),
        ("NOW\nPLAYING", "TRACK\nINFORMATION", "△"),
        ("NOW\nPLAYING", "CASSETTE\nVIEW", "□"),
        ("ANY\nSCREEN", "ABOUT", "SELECT"),
        ("ANY\nSCREEN", "SYSTEM\nQUIT", "HOME"),
    ]
    c.setLineWidth(mm(0.35))
    for start, end, label in links:
        sx, sy, sw, sh = positions[start]
        ex, ey, ew, eh = positions[end]
        if ex >= sx:
            x1, y1 = sx + sw, sy + sh / 2
            x2, y2 = ex, ey + eh / 2
        else:
            x1, y1 = sx, sy + sh / 2
            x2, y2 = ex + ew, ey + eh / 2
        c.setStrokeColor(ORANGE)
        c.line(x1, y1, x2, y2)
        label_x = (x1 + x2) / 2
        label_y = (y1 + y2) / 2 + mm(1)
        if label in BUTTON_SYMBOLS:
            draw_button_symbol_at(c, label, label_x, label_y, mm(3.4), MUTED, background=PAPER)
        else:
            c.setFillColor(MUTED)
            c.setFont(FONT_REGULAR, 4.2)
            c.drawCentredString(label_x, label_y, label)

    # Draw nodes over their connectors so route lines never cross labels.
    for name, (nx, ny, nw, nh) in positions.items():
        c.setFillColor(CHARCOAL if name == "NOW\nPLAYING" else LIGHT)
        c.roundRect(nx, ny, nw, nh, mm(2), fill=1, stroke=0)
        c.setFillColor(WHITE if name == "NOW\nPLAYING" else INK)
        c.setFont(FONT_BOLD, 5.2)
        lines = name.split("\n")
        baseline = centered_stack_baselines(
            ny,
            nh,
            [(FONT_BOLD, 5.2, len(lines), 5.0)],
        )[0]
        for idx, line in enumerate(lines):
            c.drawCentredString(nx + nw / 2, baseline - idx * 5.0, line)


def quit_flow(c, x: float, y: float, w: float, h: float) -> None:
    items = [
        ("PRESS HOME", "PSP system confirmation"),
        ("CHOOSE NO", "Return to PSPMAN"),
        ("CHOOSE YES", "Save state, release audio, exit to XMB"),
    ]
    gap = mm(2)
    box_h = (h - gap * (len(items) - 1)) / len(items)
    yy = y + h - box_h
    for i, (title, detail) in enumerate(items):
        c.setFillColor(CHARCOAL if i == 0 else LIGHT)
        c.roundRect(x, yy, w, box_h, mm(2), fill=1, stroke=0)
        title_baseline = centered_baseline(yy, box_h, FONT_BOLD, 6.2)
        detail_baseline = centered_baseline(yy, box_h, FONT_REGULAR, 5.3)
        c.setFillColor(WHITE if i == 0 else INK)
        c.setFont(FONT_BOLD, 6.2)
        c.drawString(x + mm(4), title_baseline, title)
        c.setFont(FONT_REGULAR, 5.3)
        c.drawRightString(x + w - mm(4), detail_baseline, detail)
        if i < len(items) - 1:
            c.setStrokeColor(ORANGE)
            c.setLineWidth(mm(0.6))
            c.line(x + w / 2, yy, x + w / 2, yy - gap)
        yy -= box_h + gap


def about_access(c, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(LIGHT)
    c.roundRect(x, y, w * 0.35, h, mm(2), fill=1, stroke=0)
    c.setFillColor(INK)
    c.setFont(FONT_BOLD, 7)
    left_title, left_detail = centered_stack_baselines(
        y,
        h,
        [(FONT_BOLD, 7, 1, 7), (FONT_REGULAR, 5.4, 1, 5.4)],
        gap=mm(3),
    )
    c.drawCentredString(x + w * 0.175, left_title, "ANY NORMAL SCREEN")
    c.setFont(FONT_REGULAR, 5.4)
    c.drawCentredString(x + w * 0.175, left_detail, "Press SELECT")
    c.setStrokeColor(ORANGE)
    c.setLineWidth(mm(0.8))
    c.line(x + w * 0.38, y + h / 2, x + w * 0.58, y + h / 2)
    c.setFillColor(CHARCOAL)
    c.roundRect(x + w * 0.62, y, w * 0.38, h, mm(2), fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont(FONT_BOLD, 7)
    right_title, right_detail = centered_stack_baselines(
        y,
        h,
        [(FONT_BOLD, 7, 1, 7), (FONT_REGULAR, 5.2, 1, 5.2)],
        gap=mm(3),
    )
    c.drawCentredString(x + w * 0.81, right_title, "ABOUT PSPMAN")
    c.setFont(FONT_REGULAR, 5.2)
    c.drawCentredString(x + w * 0.81, right_detail, "Any button closes")


DIAGRAMS = {
    "psp-front": psp_front,
    "installation": installation,
    "folder-tree": folder_tree,
    "playback-controls": playback_controls,
    "navigation-map": navigation_map,
    "quit-flow": quit_flow,
    "about-access": about_access,
}
