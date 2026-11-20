"""Builds the rules HTML (rules + vector illustrations) in src/, one file per paper size and font variant.
Print them to PDF with bin/build_pdfs.py."""
import base64
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")

# paper key -> (CSS @page size, page width, page height)
PAPERS = {"letter": ("letter", "8.5in", "11in"), "a4": ("A4", "210mm", "297mm")}
VARIANTS = [(paper, dyslexic) for dyslexic in (False, True) for paper in PAPERS]
FONT_DIR = os.path.join(SRC, "fonts", "opendyslexic")


def variant_name(kind, paper, dyslexic):
    """e.g. protractwar-rules, protractwar-rules-a4, protractwar-maps-dyslexic-a4 (no extension)."""
    return f"protractwar-{kind}" + ("-dyslexic" if dyslexic else "") + ("-a4" if paper == "a4" else "")


def dyslexic_css():
    """Embeds OpenDyslexic (base64, so headless Chrome never prints before it loads) and applies it everywhere,
    including the text inside the SVG figures."""
    faces = []
    for weight in (400, 700):
        for style in ("normal", "italic"):
            with open(os.path.join(FONT_DIR, f"opendyslexic-latin-{weight}-{style}.woff2"), "rb") as f:
                data = base64.b64encode(f.read()).decode()
            faces.append(f"@font-face {{ font-family: 'OpenDyslexic'; font-weight: {weight}; font-style: {style}; "
                         f"src: url(data:font/woff2;base64,{data}) format('woff2'); }}")
    # The labels inside the figures stay in the original font: they're sized to fit their drawings and
    # OpenDyslexic's wider letters would run off the edges.
    return "\n".join(faces) + "\nbody, h1, h2, h3, .num { font-family: 'OpenDyslexic', sans-serif; }\n"

BLUE, BLUE_L = "#1f5fbf", "#dbe7fa"
RED, RED_L = "#c8322b", "#fbdedb"
INK = "#222"
GRID = "#c9d3df"
BLOB_F, BLOB_S = "#d9dee5", "#4a5260"

_fig = [0]


def rad(d):
    return math.radians(d)


def pt(x, y, d, r):
    """Point r away from (x,y) at visual angle d (CCW, 0 = right)."""
    return x + r * math.cos(rad(d)), y - r * math.sin(rad(d))


# ---------- primitives ----------
def paper(w, h, step, inner):
    _fig[0] += 1
    cid = f"clip{_fig[0]}"
    g = [f'<defs><clipPath id="{cid}"><rect x="4" y="4" width="{w-8}" height="{h-8}"/></clipPath></defs>',
         f'<rect x="4" y="4" width="{w-8}" height="{h-8}" fill="#fff"/>',
         f'<g clip-path="url(#{cid})">']
    for x in range(4, w, step):
        g.append(f'<line x1="{x}" y1="4" x2="{x}" y2="{h-4}" stroke="{GRID}" stroke-width="0.7"/>')
    for y in range(4, h, step):
        g.append(f'<line x1="4" y1="{y}" x2="{w-4}" y2="{y}" stroke="{GRID}" stroke-width="0.7"/>')
    g.append(inner)
    g.append("</g>")
    g.append(f'<rect x="4" y="4" width="{w-8}" height="{h-8}" fill="none" stroke="#555" stroke-width="1.6"/>')
    return "".join(g)


def svg(w, h, body):
    return f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" shape-rendering="geometricPrecision">{body}</svg>'


def base(x, y, s, color, fill, dot=True):
    out = f'<rect x="{x}" y="{y}" width="{s}" height="{s}" fill="{fill}" stroke="{color}" stroke-width="2.2"/>'
    if dot:
        out += f'<circle cx="{x+s/2}" cy="{y+s/2}" r="2.8" fill="{color}"/>'
    return out


def line(p, q, color=INK, w=2.2, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" '
            f'stroke="{color}" stroke-width="{w}" stroke-linecap="round"{d}/>')


def dot(p, color, r=3):
    return f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="{r}" fill="{color}"/>'


def text(x, y, s, size=10, color=INK, anchor="middle", weight="700"):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" text-anchor="{anchor}" '
            f'font-weight="{weight}" font-family="Avenir Next, Helvetica, sans-serif">{s}</text>')


def label(x, y, s, size=9.5, color=INK, anchor="middle"):
    """Text with a white halo so it reads over grid lines."""
    t = text(x, y, s, size, color, anchor)
    halo = t.replace("<text ", '<text stroke="#fff" stroke-width="3.5" stroke-linejoin="round" ')
    return halo + t


def arrow(p, q, color=INK, w=1.6):
    ang = math.atan2(q[1] - p[1], q[0] - p[0])
    a1 = (q[0] - 7 * math.cos(ang - 0.45), q[1] - 7 * math.sin(ang - 0.45))
    a2 = (q[0] - 7 * math.cos(ang + 0.45), q[1] - 7 * math.sin(ang + 0.45))
    return (line(p, q, color, w) +
            f'<polygon points="{q[0]:.1f},{q[1]:.1f} {a1[0]:.1f},{a1[1]:.1f} {a2[0]:.1f},{a2[1]:.1f}" fill="{color}"/>')


def mark(p, d, color):
    """Small tick mark across direction d at point p."""
    a = pt(*p, d + 90, 4)
    b = pt(*p, d - 90, 4)
    return line(a, b, color, 2.4)


def protractor(cx, cy, r, rot=0):
    g = [f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({-rot})">',
         f'<path d="M {-r} 0 A {r} {r} 0 0 1 {r} 0 Z" fill="#fff4b8" fill-opacity="0.82" stroke="{INK}" stroke-width="1.3"/>']
    for d in range(0, 181, 10):
        inner = r - (9 if d % 30 == 0 else 5)
        a, b = pt(0, 0, d, r), pt(0, 0, d, inner)
        g.append(line(a, b, INK, 0.9))
    for d in range(0, 181, 5):
        if d % 10:
            g.append(line(pt(0, 0, d, r), pt(0, 0, d, r - 3), INK, 0.6))
    for d in (0, 30, 60, 90, 120, 150, 180):
        x, y = pt(0, 0, d, r - 16)
        g.append(f'<text x="{x:.1f}" y="{y+2.3:.1f}" font-size="6.2" text-anchor="middle" fill="{INK}" '
                 f'font-family="Helvetica, sans-serif">{d}</text>')
    g.append(line((-5, 0), (5, 0), INK, 1))
    g.append(line((0, 0), (0, -5), INK, 1))
    g.append("</g>")
    return "".join(g)


def ruler(p, d, length, side=1):
    """Ruler lying along a line from p at angle d, offset to one side."""
    off = 1.5
    w = 13
    x0, y0 = pt(*p, d + 90 * side, off)
    a = (x0, y0)
    b = pt(*a, d, length)
    c = pt(*b, d + 90 * side, w)
    e = pt(*a, d + 90 * side, w)
    g = [f'<polygon points="{a[0]:.1f},{a[1]:.1f} {b[0]:.1f},{b[1]:.1f} {c[0]:.1f},{c[1]:.1f} {e[0]:.1f},{e[1]:.1f}" '
         f'fill="#f2d39b" fill-opacity="0.75" stroke="#8a6a2f" stroke-width="1"/>']
    i = 0
    while i * 6 < length - 2:
        s = pt(*a, d, i * 6 + 3)
        t = pt(*s, d + 90 * side, 6 if i % 5 == 0 else 3.5)
        g.append(line(s, t, "#8a6a2f", 0.8))
        i += 1
    return "".join(g)


def blob_r(R, seed):
    def r(t):
        return R * (1 + 0.16 * math.sin(3 * t + seed) + 0.09 * math.sin(5 * t + 2 * seed)
                    + 0.06 * math.cos(2 * t + seed * 0.7))
    return r


def blob(cx, cy, R, seed):
    r = blob_r(R, seed)
    n = 48
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        rr = r(t)
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f} "
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C {c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f} "
    return f'<path d="{d}Z" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="1.8"/>'


def blob_hit(start, d, cx, cy, R, seed, maxlen=400):
    r = blob_r(R, seed)
    for i in range(int(maxlen * 4)):
        q = pt(*start, d, i / 4)
        t = math.atan2(q[1] - cy, q[0] - cx)
        if math.hypot(q[0] - cx, q[1] - cy) <= r(t):
            return q
    return None


def burst(x, y, r1, r2, n=10, fill="#ffd23f", stroke=RED):
    pts = []
    for i in range(2 * n):
        rr = r1 if i % 2 == 0 else r2
        t = math.pi * i / n
        pts.append(f"{x + rr*math.cos(t):.1f},{y + rr*math.sin(t):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="1.5" stroke-linejoin="round"/>'


def face(x, y, color, fill, r=22):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{color}" stroke-width="2.2"/>'
            f'<circle cx="{x-7}" cy="{y-5}" r="2.4" fill="{INK}"/><circle cx="{x+7}" cy="{y-5}" r="2.4" fill="{INK}"/>'
            f'<path d="M {x-9} {y+5} Q {x} {y+14} {x+9} {y+5}" fill="none" stroke="{INK}" stroke-width="2" stroke-linecap="round"/>')


def bubble(x, y, w, h, tail, s, size=12):
    """Speech bubble with top-left (x,y); tail = point the tail aims at."""
    cx = x + w / 2
    tx = min(max(tail[0], x + 14), x + w - 14)
    ty = y + h if tail[1] > y + h else y
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#fff" stroke="{INK}" stroke-width="1.8"/>'
            f'<polygon points="{tx-7:.1f},{ty:.1f} {tx+7:.1f},{ty:.1f} {tail[0]:.1f},{tail[1]:.1f}" fill="#fff" stroke="{INK}" stroke-width="1.8" stroke-linejoin="round"/>'
            f'<line x1="{tx-6:.1f}" y1="{ty:.1f}" x2="{tx+6:.1f}" y2="{ty:.1f}" stroke="#fff" stroke-width="3"/>'
            + text(cx, y + h / 2 + size * 0.36, s, size))


# ---------- figures ----------
W, H = 300, 190


def fig_bases():
    inner = (base(24, 126, 40, BLUE, BLUE_L, dot=False) + base(236, 24, 40, RED, RED_L, dot=False)
             + line((24, 176), (64, 176), INK, 1) + line((24, 172), (24, 180), INK, 1) + line((64, 172), (64, 180), INK, 1)
             + label(44, 140, "2 squares", 8.5) .replace('y="140.0"', 'y="187.0"'))
    # dimension label placed under the base
    inner = (base(24, 126, 40, BLUE, BLUE_L, dot=False) + base(236, 24, 40, RED, RED_L, dot=False)
             + label(96, 150, "Blue base", 10, BLUE, "start") + label(204, 48, "Red base", 10, RED, "end")
             + arrow((84, 160), (68, 172), INK, 1.2) + label(116, 175, "2 squares wide", 8.5, INK, "start"))
    return svg(W, H, paper(W, H, 20, inner))


def fig_middle():
    s = 30
    bx, by, bs = 105, 50, 60
    inner = (base(bx, by, bs, BLUE, BLUE_L, dot=False)
             + line((bx, by), (bx + bs, by + bs), BLUE, 1.2, "4 3") + line((bx + bs, by), (bx, by + bs), BLUE, 1.2, "4 3")
             + dot((bx + bs / 2, by + bs / 2), BLUE, 4.5)
             + arrow((215, 52), (141, 77), INK, 1.4) + label(218, 48, "Start here!", 11, INK, "start")
             + label(150, 150, "Tip: draw light lines corner to corner.", 9, INK)
             + label(150, 163, "The middle is where they cross.", 9, INK))
    return svg(W, H, paper(W, H, s, inner))


BLOBS = [(150, 92, 24, 1.0), (92, 6, 22, 2.3), (214, 186, 24, 4.1), (4, 80, 18, 1.7), (296, 122, 18, 0.6),
         (60, 52, 13, 3.3), (112, 150, 13, 5.2), (196, 58, 12, 2.8), (250, 104, 13, 4.6)]


def fig_obstacles():
    inner = base(24, 126, 40, BLUE, BLUE_L) + base(236, 24, 40, RED, RED_L)
    for b in BLOBS:
        inner += blob(*b)
    inner += f'<rect x="158" y="132" width="24" height="14" rx="2" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="1.8"/>'
    inner += f'<polygon points="88,96 104,74 112,100" fill="{BLOB_F}" stroke="{BLOB_S}" stroke-width="1.8" stroke-linejoin="round"/>'
    return svg(W, H, paper(W, H, 20, inner))


def fig_first():
    body = (face(70, 140, BLUE, BLUE_L) + face(230, 140, RED, RED_L)
            + bubble(14, 22, 150, 54, (66, 114), "That's a right angle!", 11.5)
            + burst(70, 98, 0, 0)  # no-op placeholder keeps layout simple
            + label(70, 182, "Said “angle” last", 10, BLUE)
            + label(230, 182, "Waits", 10, RED))
    star = burst(108, 128, 14, 7, 5, "#ffd23f", INK) + text(108, 132, "1st", 8.5)
    return svg(W, H, '<rect width="300" height="190" fill="#fff"/>' + body + star)


def fig_guess():
    body = face(62, 120, BLUE, BLUE_L) + bubble(14, 22, 96, 50, (60, 96), "45°!", 18)
    # protractor held up to look at, but not on the paper
    px, py, pw, ph = 150, 140, 130, 40
    grid = "".join(line((x, py), (x, py + ph), GRID, 0.7) for x in range(px + 10, px + pw, 10))
    grid += "".join(line((px, y), (px + pw, y), GRID, 0.7) for y in range(py + 10, py + ph, 10))
    body += (f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#fff"/>' + grid
             + f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="none" stroke="#555" stroke-width="1.6"/>')
    body += protractor(215, 100, 52, 0)
    body += line((215, 106), (215, 132), INK, 1.4, "3 3")
    body += line((207, 112), (223, 128), RED, 4) + line((223, 112), (207, 128), RED, 4)
    body += label(212, 22, "Look, but don’t put", 15, RED) + label(212, 40, "it on the paper!", 15, RED)
    return svg(W, H, '<rect width="300" height="190" fill="#fff"/>' + body)


def fig_measure_first():
    c = (104, 144)
    inner = base(84, 124, 40, BLUE, BLUE_L)
    inner += protractor(*c, 62, 0)
    m = pt(*c, 45, 70)
    inner += mark(m, 45, BLUE) + label(m[0] - 16, m[1] - 8, "45°", 11, BLUE)
    inner += arrow((212, 160), (170, 150), INK, 1.2)
    inner += label(214, 158, "flat edge lines up", 9, INK, "start").replace('x="214.0"', 'x="214.0"')
    inner += label(214, 170, "with the paper", 9, INK, "start")
    inner += label(214, 40, "small mark", 9, BLUE, "start") + arrow((212, 44), (m[0] + 6, m[1] - 2), BLUE, 1.2)
    return svg(W, H, paper(W, H, 20, inner))


def fig_measure_later():
    s = (34, 176)
    prev = 30
    p = pt(*s, prev, 120)
    inner = base(14, 156, 40, BLUE, BLUE_L)
    inner += line(s, p, BLUE, 2.4)
    inner += dot(p, BLUE, 3.2)
    inner += line(p, pt(*p, prev, 80), BLUE, 1.2, "4 4")
    inner += protractor(*p, 58, prev)
    m = pt(*p, prev + 50, 66)
    inner += mark(m, prev + 50, BLUE) + label(m[0] - 20, m[1] - 2, "50°", 11, BLUE)
    inner += label(64, 132, "last line", 9, BLUE)
    tip = pt(*p, prev, 80)
    inner += label(tip[0] + 22, tip[1] + 16, "0° =", 8.5, INK) + label(tip[0] + 22, tip[1] + 27, "straight ahead", 8.5, INK)
    return svg(W, H, paper(W, H, 20, inner))


def fig_launch():
    c = (64, 144)
    inner = base(44, 124, 40, BLUE, BLUE_L)
    m = pt(*c, 45, 70)
    end = pt(*c, 45, 150)
    inner += ruler(c, 45, 158, side=1)
    inner += mark(m, 45, BLUE)
    inner += line(c, end, BLUE, 2.6)
    inner += dot(end, BLUE, 4)
    inner += label(end[0] + 8, end[1] + 3, "Missile is here now", 9.5, BLUE, "start")
    inner += label(m[0] + 10, m[1] + 10, "through your mark", 8.5, INK, "start")
    return svg(W, H, paper(W, H, 20, inner))


def fig_blob_hit():
    c = (44, 164)
    b = (176, 84, 34, 2.0)
    d = 32
    hit = blob_hit(c, d, *b)
    inner = base(24, 144, 40, BLUE, BLUE_L) + blob(*b)
    inner += line(hit, pt(*c, d, 250), "#9aa5b1", 1.6, "5 4")
    inner += line(c, hit, BLUE, 2.6)
    inner += burst(hit[0], hit[1], 9, 4.5, 8, "#ffd23f", BLUE) + dot(hit, BLUE, 3)
    inner += label(hit[0] - 6, hit[1] - 16, "Next turn starts here", 9.5, BLUE, "end")
    inner += label(176, 160, "Stopped by the blob!", 9.5, BLOB_S)
    inner += label(250, 30, "where it wanted to go", 8, "#7b8794", "middle")
    return svg(W, H, paper(W, H, 20, inner))


def fig_turns():
    bs = (44, 154)
    rs = (256, 36)
    bpath = [bs, pt(*bs, 40, 70)]
    bpath.append(pt(*bpath[-1], 15, 60))
    rpath = [rs, pt(*rs, 205, 70)]
    rpath.append(pt(*rpath[-1], 235, 55))
    inner = base(24, 134, 40, BLUE, BLUE_L) + base(236, 16, 40, RED, RED_L)
    n = 1
    for i in range(1, 3):
        inner += line(bpath[i - 1], bpath[i], BLUE, 2.4) + line(rpath[i - 1], rpath[i], RED, 2.4)
    for i in range(1, 3):
        for path, col, off in ((bpath, BLUE, 12), (rpath, RED, -12)):
            p = path[i]
            inner += f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="8" fill="{col}"/>'
            inner += text(p[0], p[1] + 3.5, str(n), 9.5, "#fff")
            n += 1
    inner += label(150, 180, "Blue, Red, Blue, Red…", 10, INK)
    return svg(W, H, paper(W, H, 20, inner))


def fig_hit():
    rs = (256, 36)
    p1 = pt(*rs, 210, 110)
    d2 = math.degrees(math.atan2(-(150 - p1[1]), 46 - p1[0]))
    end = pt(*p1, d2, math.hypot(46 - p1[0], 150 - p1[1]))
    inner = base(24, 134, 40, BLUE, BLUE_L) + base(236, 16, 40, RED, RED_L)
    inner += line(rs, p1, RED, 2.4) + dot(p1, RED, 3) + line(p1, end, RED, 2.6)
    inner += burst(54, 146, 24, 13, 12) + text(54, 150, "HIT!", 10.5, RED)
    inner += label(118, 110, "Crossing into the base counts!", 9.5, RED, "start")
    return svg(W, H, paper(W, H, 20, inner))


def fig_tie():
    s = 30

    def foot(c, a, b):
        """Closest point to c on the line through a and b."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        t = ((c[0] - a[0]) * dx + (c[1] - a[1]) * dy) / (dx * dx + dy * dy)
        return a[0] + t * dx, a[1] + t * dy

    inner = ""
    # left: red's line cuts through blue's base, far from the dot
    bx, by = 30, 50
    cb = (bx + 45, by + 45)
    a, b = (40, 175), (150, 70)
    inner += base(bx, by, 90, BLUE, BLUE_L, dot=False) + dot(cb, BLUE, 4)
    inner += line(a, b, RED, 2.4) + dot(b, RED, 3.5)
    inner += line(cb, foot(cb, a, b), INK, 1.2, "3 3")
    # right: blue's line cuts through red's base, close to the dot
    rx, ry = 180, 50
    cr = (rx + 45, ry + 45)
    a, b = (160, 175), (282, 57.5)
    inner += base(rx, ry, 90, RED, RED_L, dot=False) + dot(cr, RED, 4)
    inner += line(a, b, BLUE, 2.4) + dot(b, BLUE, 3.5)
    inner += line(cr, foot(cr, a, b), INK, 1.2, "3 3")
    inner += label(75, 34, "Red: far from the dot", 9.5, RED)
    inner += label(225, 34, "Blue: closer!", 9.5, BLUE)
    inner += burst(225, 166, 16, 8, 5, "#ffd23f", INK) + text(225, 169, "WIN", 7.5)
    return svg(W, H, paper(W, H, s, inner))


def fig_gg():
    body = (face(80, 130, BLUE, BLUE_L) + face(220, 130, RED, RED_L)
            + bubble(22, 40, 110, 44, (78, 106), "Good game!", 13)
            + bubble(168, 40, 110, 44, (222, 106), "You too!", 13))
    return svg(W, H, '<rect width="300" height="190" fill="#fff"/>' + body)


def fig_first_clean():
    body = (face(70, 140, BLUE, BLUE_L) + face(230, 140, RED, RED_L)
            + bubble(14, 26, 170, 50, (66, 116), "That's a right angle!", 12)
            + label(70, 182, "Said “angle” last", 10, BLUE)
            + label(230, 182, "Goes 2nd", 10, RED))
    star = burst(110, 126, 15, 8, 5, "#ffd23f", INK) + text(110, 129.5, "1st", 8.5)
    return svg(W, H, '<rect width="300" height="190" fill="#fff"/>' + body + star)


# ---------- page ----------
def step(n, title, body, figs):
    figs_html = "".join(f'<figure{" class=small" if "<rect width=" in f else ""}>{f}{"<figcaption>" + c + "</figcaption>" if c else ""}</figure>' for f, c in figs)
    return f'''<section class="step"><div class="txt"><div class="num">{n}</div><h3>{title}</h3>{body}</div>
<div class="figs{" two" if len(figs) > 1 else ""}">{figs_html}</div></section>'''


def card(n, title, body, figs, fig_w="100%", side=False):
    fh = "".join(f'<figure style="width:{fig_w if len(figs) == 1 else "49%"}">{f}{"<figcaption>" + c + "</figcaption>" if c else ""}</figure>' for f, c in figs)
    return f'''<section class="card{" side" if side else ""}"><div class="txt"><div class="num">{n}</div><h3>{title}</h3>{body}</div>
<div class="cfigs">{fh}</div></section>'''


CSS = """
@page { size: letter; margin: 0.45in 0.6in; }
* { box-sizing: border-box; }
body { font-family: 'Avenir Next', Helvetica, sans-serif; color: #1d232b; font-size: 12.5pt; line-height: 1.38; margin: 0; }
h1 { font-family: 'Arial Rounded MT Bold', 'Avenir Next', sans-serif; font-size: 30pt; margin: 0; letter-spacing: .5px; }
h1 span { color: #c8322b; }
.sub { font-size: 14pt; margin: 0 0 10px; color: #4a5260; }
h2 { font-family: 'Arial Rounded MT Bold', 'Avenir Next', sans-serif; font-size: 19pt; margin: 12px 0 4px;
     border-bottom: 3px solid #1d232b; padding-bottom: 3px; break-after: avoid; }
h3 { font-size: 14pt; margin: 0 0 4px; }
.top { display: flex; gap: 22px; }
.box { flex: 1; border: 2px solid #1d232b; border-radius: 10px; padding: 10px 14px; }
.box h2 { margin: 0 0 6px; border: 0; font-size: 15pt; padding: 0; }
.box ul { margin: 0; padding-left: 20px; }
.box li { break-inside: avoid; }
.box p { margin: 0; }
.step { display: flex; gap: 18px; align-items: flex-start; padding: 7px 0; border-bottom: 1px solid #d6dbe1;
        break-inside: avoid; }
.txt { flex: 1; position: relative; padding-left: 44px; }
.num { position: absolute; left: 0; top: 0; width: 32px; height: 32px; border-radius: 50%; background: #1d232b; color: #fff;
       font-weight: 700; text-align: center; line-height: 32px; font-size: 14pt; }
.txt p { margin: 0 0 6px; }
.txt ul { margin: 4px 0 0; padding-left: 20px; }
.txt li { margin-bottom: 4px; }
.figs { width: 2.3in; flex: none; display: flex; flex-direction: column; gap: 6px; }
.figs.two { width: 4.3in; flex-direction: row; gap: 10px; }
.figs.two figure { flex: 1; }
figure { margin: 0; }
figure.small svg { width: 62% !important; margin: 0 auto; }
figure svg { width: 100%; height: auto; display: block; }
figcaption { font-size: 9.5pt; font-weight: 700; color: #4a5260; text-align: center; margin-top: 1px; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0 22px; align-items: start; }
.card { padding: 5px 0 7px; border-bottom: 1px solid #d6dbe1; display: flex; flex-direction: column; break-inside: avoid; }
.card .txt { font-size: 11.5pt; line-height: 1.3; }
.card .txt li { margin-bottom: 2px; }
.card .txt ul { margin-top: 2px; }
.card .txt p { margin-bottom: 3px; }
.card h3 { font-size: 13pt; line-height: 1.2; min-height: 32px; display: flex; align-items: center; margin-bottom: 2px; }
.cfigs { display: flex; justify-content: center; gap: 2%; padding-top: 4px; }
.card.side { flex-direction: row; align-items: center; gap: 8px; }
.card.side .txt { flex: 1; }
.card.side .cfigs { flex: 1.1; padding: 0; }
.credits { margin-top: 14px; padding: 8px 12px; border: 1.5px solid #c3cad3; border-radius: 8px; font-size: 9.5pt; color: #4a5260; line-height: 1.45; }
.credits b { color: #1d232b; }
.pb { break-before: page; }
"""


# OpenDyslexic is much wider than Avenir, so the dyslexic rules use three pages (How to Play is split over
# pages 2 and 3) rather than shrinking the text. Step 1's picture goes under its text instead of beside it.
DYSLEXIC_RULES_CSS = """
.card:first-child.side { flex-direction: column; align-items: stretch; }
.card:first-child.side .cfigs { padding-top: 4px; }
.card:first-child.side figure { width: 60% !important; }
"""


CREDITS = ('<div class="credits"><b>Credits</b><br>Created by Alexander &amp; Paul Reinheimer<br>'
           'Website: protractwar.com</div>')


def build(paper_size="letter", dyslexic=False):
    s = []
    s.append('<h1>Protract<span>war</span> \U0001F3AF</h1><div class="sub">A game for 2 players</div>')
    s.append('''<div class="top"><div class="box"><h2>What You Need</h2><ul>
<li>Graph paper or dot paper</li><li>A sharp pencil (two different coloured pencils are even better, one for each player)</li>
<li>A protractor</li><li>A ruler</li></ul></div>
<div class="box" style="flex:.6"><h2>How to Win</h2><p>Hit the other player’s base before they hit yours!</p></div></div>''')

    s.append("<h2>Getting Ready</h2>")
    s.append(step(1, "Draw your bases.",
                  "<p>Each player draws a square in their own corner of the paper. Both squares must be the same size. "
                  "For example, each side could be 2 squares long.</p>", [(fig_bases(), "")]))
    s.append(step(2, "Mark the middle.",
                  "<p>Put a dot in the centre of each base. This is where your missile starts.</p>", [(fig_middle(), "")]))
    s.append(step(3, "Add obstacles.",
                  "<p>Take turns drawing blobs and other shapes on the paper. Make some of them touch the edge of the paper.</p>",
                  [(fig_obstacles(), "Some shapes touch the edge")]))
    s.append(step(4, "Pick who goes first.",
                  "<p>The player who said the word “angle” most recently goes first.</p>", [(fig_first_clean(), "")]))

    s.append('<h2 class="pb">How to Play</h2>')
    c = []
    c.append(card(1, "Guess an angle.",
                  "<p>On your turn, say an angle out loud, like \u201c45 degrees.\u201d You may look at the protractor, "
                  "but you may not place it on the paper.</p>", [(fig_guess(), "")], "100%", True))
    c.append(card(2, "Measure it.",
                  "<p>Put the protractor on the paper and find the angle you said. Make a small mark at that angle.</p><ul>"
                  "<li><b>First turn:</b> Line up the protractor with the edges of the paper.</li>"
                  "<li><b>Every turn after that:</b> Line up the protractor with the last line you drew.</li></ul>",
                  [(fig_measure_first(), "First turn"), (fig_measure_later(), "Every turn after that")]))
    c.append(card(3, "Launch your missile.",
                  "<p>Use the ruler to draw a straight line from where your missile is now, through your mark. You can make "
                  "the line as long or as short as you want. Where your line ends is where your missile is now.</p><ul>"
                  "<li><b>Watch out for blobs!</b> If your line runs into a blob, your missile stops right where it touched. "
                  "Your next turn starts from that spot. To stay away from a blob, stop your line before it gets there.</li></ul>",
                  [(fig_launch(), "Draw along the ruler"), (fig_blob_hit(), "Hitting a blob")]))
    c.append(card(4, "Switch turns.", "<p>Now it\u2019s the other player\u2019s turn.</p>", [(fig_turns(), "")], "80%"))
    c.append(card(5, "Keep going until someone\u2019s base gets hit.",
                  "<p>If your line crosses into the other player\u2019s base, that counts as a hit!</p><ul>"
                  "<li><b>Tie?</b> If both players hit a base in the same round, the winner is the player whose line "
                  "passed closest to the dot in the middle of the base.</li></ul>",
                  [(fig_hit(), "A hit!"), (fig_tie(), "Breaking a tie")]))
    c.append(card(6, "Say \u201cgood game\u201d", "<p>Shake hands! \U0001F642</p>", [(fig_gg(), "")], "100%", True))
    if dyslexic:
        s.append('<div class="grid"><div>' + "".join(c[:2]) + '</div><div>' + c[2] + '</div></div>'
                 '<div class="grid pb"><div>' + "".join(c[3:5]) + '</div><div>' + c[5] + CREDITS + "</div></div>")
    else:
        s.append('<div class="grid"><div>' + "".join(c[:3]) + '</div><div>' + "".join(c[3:]) + CREDITS + "</div></div>")

    css = CSS.replace("size: letter;", f"size: {PAPERS[paper_size][0]};")
    if dyslexic:
        css += dyslexic_css() + DYSLEXIC_RULES_CSS
    html = f'<!doctype html><html><head><meta charset="utf-8"><title>Protractwar Rules</title><style>{css}</style></head><body>{"".join(s)}</body></html>'
    with open(os.path.join(SRC, variant_name("rules", paper_size, dyslexic) + ".html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    for paper_size, dyslexic in VARIANTS:
        build(paper_size, dyslexic)
