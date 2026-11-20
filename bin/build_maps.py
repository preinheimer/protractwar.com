"""Builds the maps HTML in src/: two printable maps (1 cm grid), one file per paper size and font variant.
Side 1 has blobs, side 2 is open. Print to PDF with headless Chrome."""
import math
import os

from build_protractwar import PAPERS, SRC, VARIANTS, blob_r, dyslexic_css, variant_name

GW, GH = 19, 25            # grid size in cm
BLUE, RED = "#1f5fbf", "#c8322b"
GRID, EDGE = "#d3dae2", "#8a94a0"
BLOB_F, BLOB_S = "#e4e8ed", "#4a5260"

BLOBS_BIG = [(9.5, 12.5, 2.2, 1.0), (5, 7, 1.5, 2.3), (14, 18, 1.6, 4.1), (0, 14, 1.6, 1.7), (19, 9, 1.7, 0.6),
         (8, 0, 1.4, 3.3), (11, 25, 1.5, 5.2), (13, 6, 1.0, 2.8), (6, 17, 1.1, 4.6), (3, 11, 0.9, 0.2),
         (16, 13, 1.0, 3.9), (10, 20.5, 0.9, 1.4)]


def _extra_blobs(n=16):
    import random
    rnd = random.Random(7)
    placed = [(x, y, R / 2) for x, y, R, _ in BLOBS_BIG]
    out = []
    tries = 0
    while len(out) < n and tries < 5000:
        tries += 1
        R = rnd.uniform(0.45, 0.95)
        x, y = rnd.uniform(0, GW), rnd.uniform(0, GH)
        if math.hypot(x - 1, y - (GH - 1)) < 3.2 or math.hypot(x - (GW - 1), y - 1) < 3.2:
            continue
        if any(math.hypot(x - a, y - b) < 1.35 * (R + r) + 0.6 for a, b, r in placed):
            continue
        placed.append((x, y, R))
        out.append((x, y, R, rnd.uniform(0, 6)))
    return out


def blob(cx, cy, R, seed):
    r = blob_r(R, seed)
    n = 48
    pts = [(cx + r(t) * math.cos(t), cy + r(t) * math.sin(t)) for t in (2 * math.pi * i / n for i in range(n))]
    d = f"M {pts[0][0]:.3f} {pts[0][1]:.3f} "
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C {c1[0]:.3f} {c1[1]:.3f} {c2[0]:.3f} {c2[1]:.3f} {p2[0]:.3f} {p2[1]:.3f} "
    return f'<path d="{d}Z" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="0.045"/>'


def base(x, y, color):
    return (f'<rect x="{x}" y="{y}" width="1" height="1" fill="none" stroke="{color}" stroke-width="0.05"/>'
            f'<circle cx="{x + 0.5}" cy="{y + 0.5}" r="0.06" fill="{color}"/>')


def map_svg(with_blobs):
    g = ['<defs><clipPath id="c"><rect x="0" y="0" width="%d" height="%d"/></clipPath></defs>' % (GW, GH),
         f'<rect x="0" y="0" width="{GW}" height="{GH}" fill="#fff"/>']
    for i in range(1, GW * 2):
        g.append(f'<line x1="{i / 2}" y1="0" x2="{i / 2}" y2="{GH}" stroke="{GRID}" stroke-width="0.015"/>')
    for i in range(1, GH * 2):
        g.append(f'<line x1="0" y1="{i / 2}" x2="{GW}" y2="{i / 2}" stroke="{GRID}" stroke-width="0.015"/>')
    if with_blobs:
        g.append('<g clip-path="url(#c)">')
        g += [blob(x, y, R / 2, sd) for x, y, R, sd in BLOBS_BIG]
        g += [blob(*b) for b in _extra_blobs()]
        g.append(f'<rect x="14.9" y="21.85" width="0.8" height="0.5" rx="0.06" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="0.045"/>')
        g.append(f'<polygon points="11.2,16.9 11.8,16.05 12.15,17.05" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="0.045" stroke-linejoin="round"/>')
        g.append("</g>")
    g.append(base(0.5, GH - 1.5, BLUE))
    g.append(base(GW - 1.5, 0.5, RED))
    g.append(f'<rect x="0" y="0" width="{GW}" height="{GH}" fill="none" stroke="{EDGE}" stroke-width="0.04"/>')
    return (f'<svg viewBox="-0.05 -0.05 {GW + 0.1} {GH + 0.1}" width="{GW + 0.1}cm" height="{GH + 0.1}cm" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(g)}</svg>')


CSS = """
@page { size: letter; margin: 0; }
body { margin: 0; font-family: 'Avenir Next', Helvetica, sans-serif; }
.page { width: PAGE_W; height: PAGE_H; display: flex; flex-direction: column; align-items: center; justify-content: center;
        break-after: page; }
.page:last-child { break-after: auto; }
.foot { width: 19cm; display: flex; justify-content: space-between; font-size: 8pt; color: #9aa3ad; margin-top: 4px; }
svg { display: block; }
"""


def page(with_blobs, label):
    return (f'<div class="page">{map_svg(with_blobs)}<div class="foot"><span>Protractwar · {label}</span>'
            f'<span>1 square = 5 mm · protractwar.com</span></div></div>')


def build(paper="letter", dyslexic=False):
    size, w, h = PAPERS[paper]
    css = CSS.replace("size: letter;", f"size: {size};").replace("PAGE_W", w).replace("PAGE_H", h)
    if dyslexic:
        css += dyslexic_css()
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Protractwar Maps</title><style>{css}</style></head>'
            f'<body>{page(True, "Map with blobs")}{page(False, "Open map")}</body></html>')
    with open(os.path.join(SRC, variant_name("maps", paper, dyslexic) + ".html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    for paper, dyslexic in VARIANTS:
        build(paper, dyslexic)
