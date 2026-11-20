"""Builds src/protractwar-protractor.html (Letter) and src/protractwar-protractor-a4.html: a page of paper
protractors to print on card stock and cut out. Print them to PDF with bin/build_pdfs.py.

Paper isn't see-through, so unlike a plastic protractor the centre point sits right on the flat bottom edge (marked
with a notch) and the bottom edge itself is the 0-180 line. Tick marks run to the curved edge, so you can make your
mark on the paper right at the rim. Two scales (big numbers from the right, small numbers from the left) let you measure a turn either way
without flipping the protractor over, since the back is blank.
"""
import math
import os

from build_protractwar import PAPERS, SRC, variant_name

R = 45            # radius, mm
PAD = 1.5         # room around the cut line for its stroke, mm
# black and white only, so it prints well on any printer
INK, OUTER, INNER, MUTED, PAPER = "#000", "#000", "#444", "#888", "#fff"
FONT = "'Avenir Next', Helvetica, sans-serif"


def pt(cx, cy, deg, r):
    a = math.radians(deg)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def protractor_svg():
    w, h = 2 * (R + PAD), R + 2 * PAD
    cx, cy = R + PAD, R + PAD          # centre point: on the bottom (flat) edge
    g = []
    # the half-disc: cut along this line
    g.append(f'<path d="M {cx - R} {cy} A {R} {R} 0 0 1 {cx + R} {cy} Z" fill="{PAPER}" stroke="{INK}" '
             f'stroke-width="0.35" stroke-linejoin="round"/>')
    # light guide lines from the centre every 30 degrees, and a stronger 90
    for d in range(30, 180, 30):
        x, y = pt(cx, cy, d, R - 13.5)
        g.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.3f}" y2="{y:.3f}" stroke="{MUTED}" '
                 f'stroke-width="{0.22 if d == 90 else 0.12}" stroke-dasharray="{"none" if d == 90 else "0.8 0.8"}"/>')
    # ticks, from the rim inward
    for d in range(0, 181):
        ln = 5.0 if d % 10 == 0 else 3.2 if d % 5 == 0 else 1.8
        x1, y1 = pt(cx, cy, d, R)
        x2, y2 = pt(cx, cy, d, R - ln)
        g.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{INK}" '
                 f'stroke-width="{0.28 if d % 10 == 0 else 0.16}"/>')
    # two scales: outer counts up from the right (black), inner counts up from the left (blue)
    for d in range(0, 181, 10):
        rot = 90 - d                     # numbers sit along the curve, upright at the top
        for r, val, col, size, weight in ((R - 8.2, d, OUTER, 2.9, 700), (R - 12.6, 180 - d, INNER, 2.3, 600)):
            x, y = pt(cx, cy, d, r)
            t = rot
            if d in (0, 180):              # end labels lie flat just above the edge, so cutting doesn't clip them
                t, y = 0, cy - size * 0.55
            g.append(f'<text x="{x:.3f}" y="{y:.3f}" transform="rotate({t} {x:.3f} {y:.3f})" font-size="{size}" '
                     f'font-weight="{weight}" fill="{col}" text-anchor="middle" dominant-baseline="central" '
                     f'font-family="{FONT}">{val}</text>')
    # the centre point, on the edge
    g.append(f'<path d="M {cx - 2.2} {cy - 3.4} L {cx} {cy} L {cx + 2.2} {cy - 3.4} Z" fill="{INK}"/>')   # points at it
    halo = f'stroke="{PAPER}" stroke-width="1.1" paint-order="stroke" stroke-linejoin="round"'   # readable over guides
    g.append(f'<text x="{cx}" y="{cy - 5.2}" font-size="2.2" font-weight="700" fill="{INK}" text-anchor="middle" '
             f'font-family="{FONT}" {halo}>put this point on your missile</text>')
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}mm" height="{h}mm" xmlns="http://www.w3.org/2000/svg">'
            f'{"".join(g)}</svg>')


CSS = """
@page { size: letter; margin: 0; }
* { box-sizing: border-box; }
body { margin: 0; font-family: 'Avenir Next', Helvetica, sans-serif; color: #000; }
.page { width: PAGE_W; height: PAGE_H; padding: 11mm 10mm 8mm; display: flex; flex-direction: column; align-items: center; }
.head { width: 186mm; margin-bottom: 5mm; }
.head h1 { font-size: 15pt; margin: 0 0 1mm; }
.head p { margin: 0; font-size: 9pt; color: #333; line-height: 1.35; }
.head b { color: #000; }
.grid { display: grid; grid-template-columns: repeat(2, auto); gap: GAP 6mm; justify-content: center; }
svg { display: block; }
"""


def build(paper_size="letter"):
    size, w, h = PAPERS[paper_size]
    gap = "9mm" if paper_size == "a4" else "6mm"
    css = (CSS.replace("size: letter;", f"size: {size};").replace("PAGE_W", w).replace("PAGE_H", h)
           .replace("GAP", gap))
    one = protractor_svg()
    html = (f'<!doctype html><html><head><meta charset="utf-8"><title>Cut-out Protractors</title>'
            f'<style>{css}</style></head><body><div class="page">'
            '<div class="head"><h1>Cut-out protractors</h1>'
            '<p><b>Print at 100% (“Actual size”)</b>, on card stock if you have it. Cut along the outside line of '
            'each protractor. The <b>point on the flat edge</b> is the centre: put it on your missile and line up '
            'the flat edge, then make your mark at the curved edge. The <b>big numbers</b> count up from the right, '
            'the small numbers count up from the left.</p></div>'
            f'<div class="grid">{one * 8}</div>'
            '</div></body></html>')
    with open(os.path.join(SRC, variant_name("protractor", paper_size, False) + ".html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    for paper_size in PAPERS:
        build(paper_size)
