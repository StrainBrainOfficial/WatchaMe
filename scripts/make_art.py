#!/usr/bin/env python3
"""Generate the repo/addon artwork once, so the CI build needs no image library."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
BG, PANEL, ACCENT, ACCENT2, INK = (20, 22, 26), (28, 31, 38), (122, 162, 255), (94, 234, 212), (230, 233, 239)


def rounded(draw, box, radius, fill):
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def mark(img, cx, cy, size, thick):
    """A stylised toolbox: lid handle over a body, split by an accent seam."""
    d = ImageDraw.Draw(img)
    w, h = size, int(size * 0.66)
    left, top = cx - w // 2, cy - h // 2 + int(size * 0.08)
    rounded(d, (left, top, left + w, top + h), radius=int(size * 0.10), fill=ACCENT)
    seam = top + int(h * 0.34)
    d.rectangle((left, seam, left + w, seam + thick), fill=BG)
    hw, hh = int(w * 0.38), int(size * 0.22)
    hx, hy = cx - hw // 2, top - hh + thick
    d.rounded_rectangle((hx, hy, hx + hw, hy + hh), radius=int(size * 0.06), fill=ACCENT2)
    d.rounded_rectangle((hx + thick, hy + thick, hx + hw - thick, hy + hh), radius=int(size * 0.04), fill=BG)
    latch = int(size * 0.13)
    d.rounded_rectangle((cx - latch // 2, seam - latch // 2, cx + latch // 2, seam + latch // 2 + thick),
                        radius=int(size * 0.03), fill=ACCENT2)


def make_icon(path, side=512):
    img = Image.new("RGB", (side, side), BG)
    d = ImageDraw.Draw(img)
    rounded(d, (int(side * 0.06),) * 2 + (int(side * 0.94),) * 2, int(side * 0.20), PANEL)
    mark(img, side // 2, side // 2, int(side * 0.52), max(3, side // 90))
    img.save(path)


def make_fanart(path, w=1920, h=1080):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    for i in range(h):  # subtle vertical wash
        t = i / h
        d.line((0, i, w, i), fill=(int(20 + 14 * t), int(22 + 16 * t), int(26 + 22 * t)))
    for i, x in enumerate(range(-200, w + 200, 190)):  # faint diagonal ribs
        d.line((x, h + 100, x + 460, -100), fill=(34, 38, 47), width=2 if i % 3 else 5)
    mark(img, w // 2, h // 2, 300, 5)
    img.save(path)


if __name__ == "__main__":
    (ROOT / "assets").mkdir(exist_ok=True)
    make_icon(ROOT / "assets" / "icon.png")
    make_fanart(ROOT / "assets" / "fanart.png")
    tb = ROOT / "src" / "script.kodikit.toolbox"
    if tb.is_dir():
        make_icon(tb / "icon.png")
        make_fanart(tb / "fanart.png")
    print("artwork written")
