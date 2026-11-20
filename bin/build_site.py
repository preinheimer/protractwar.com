"""Builds docroot/index.html (single-page promo site) and copies the PDFs next to it."""
import os
import shutil

from build_protractwar import (ROOT, SRC, VARIANTS, variant_name, BLUE, BLUE_L, RED, RED_L, INK, base, blob, blob_hit, burst, dot, line, paper, pt, svg,
                               fig_bases, fig_middle, fig_obstacles, fig_first_clean, fig_guess, fig_measure_first,
                               fig_measure_later, fig_launch, fig_blob_hit, fig_turns, fig_hit, fig_tie, fig_gg)

RULES_PDF = variant_name("rules", "letter", False) + ".pdf"
MAPS_PDF = variant_name("maps", "letter", False) + ".pdf"
PROTRACTOR_PDF = variant_name("protractor", "letter", False) + ".pdf"

# Letter/A4 toggle. Links carry data-pdf (rules|maps) and data-dys (0|1); the default hrefs are Letter so the page
# works without JavaScript. The choice is remembered per browser; first visits guess from the browser's locale.
PAPER_JS = """<script>
(function () {
  var LETTER = ["US", "CA", "MX", "PH", "CL", "CO", "VE", "CR", "GT", "PA", "PR", "DO", "SV"];
  function guess() {
    var m = (navigator.language || "").match(/-([A-Za-z]{2})\\b/);
    return m && LETTER.indexOf(m[1].toUpperCase()) === -1 ? "a4" : "letter";
  }
  function saved() { try { return localStorage.getItem("paper"); } catch (e) { return null; } }
  function set(paper, remember) {
    if (remember) { try { localStorage.setItem("paper", paper); } catch (e) {} }
    document.querySelectorAll("a[data-pdf]").forEach(function (a) {
      a.href = "protractwar-" + a.dataset.pdf + (a.dataset.dys === "1" ? "-dyslexic" : "") +
               (paper === "a4" ? "-a4" : "") + ".pdf";
    });
    document.querySelectorAll(".paper button").forEach(function (b) {
      b.setAttribute("aria-pressed", b.dataset.paper === paper ? "true" : "false");
    });
  }
  var toggle = document.querySelector(".paper");
  toggle.hidden = false;
  toggle.addEventListener("click", function (e) {
    var b = e.target.closest("button");
    if (b) set(b.dataset.paper, true);
  });
  var p = saved();
  set(p === "a4" || p === "letter" ? p : guess(), false);
})();
</script>"""
DOCROOT = os.path.join(ROOT, "docroot")


def protractor_icon():
    """Inline protractor glyph sized like an emoji (1em). Unicode has no protractor emoji."""
    ticks = "".join(
        f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>'
        for x1, y1, x2, y2 in (
            (*pt(16, 22, d, 14), *pt(16, 22, d, 14 - (3.2 if d % 90 == 0 else 2.2))) for d in range(0, 181, 15)))
    return ('<svg class="emoji-svg" viewBox="0 0 32 24" aria-hidden="true">'
            '<path d="M2 22A14 14 0 0 1 30 22Z" fill="#fff4b8" stroke="#222" stroke-width="1.6" stroke-linejoin="round"/>'
            '<path d="M9 22A7 7 0 0 1 23 22" fill="none" stroke="#222" stroke-width="1.2"/>'
            f'<g stroke="#222" stroke-width="1.1" stroke-linecap="round">{ticks}</g>'
            '<circle cx="16" cy="22" r="1.4" fill="#222"/></svg>')


def hero_svg():
    W, H = 600, 380
    blobs = [(205, 245, 38, 1.0), (330, 140, 44, 2.3), (472, 248, 36, 4.1), (120, 92, 28, 3.3),
             (300, 384, 34, 5.2), (604, 160, 30, 0.6), (250, -4, 28, 2.8)]
    inner = "".join(blob(*b) for b in blobs)
    inner += base(24, 324, 40, BLUE, BLUE_L) + base(544, 24, 40, RED, RED_L)   # on the grid (4 + 20k)
    # three turns each. Red's missile: the third move is stopped by a blob
    r0 = (564, 44)
    r1 = pt(*r0, 200, 90)
    r2 = pt(*r1, 240, 70)
    hit = blob_hit(r2, 185, *blobs[1])
    inner += line(r0, r1, RED, 3) + dot(r1, RED, 4) + line(r1, r2, RED, 3) + dot(r2, RED, 4) + line(r2, hit, RED, 3)
    inner += burst(hit[0], hit[1], 10, 5, 8, "#ffd23f", RED) + dot(hit, RED, 3.5)
    # blue's missile: three moves, the last one hits red's base
    b = [(44, 344), (260, 300), (420, 170), (564, 44)]
    for i in range(1, len(b)):
        inner += line(b[i - 1], b[i], BLUE, 3)
    for p in b[1:-1]:
        inner += dot(p, BLUE, 4)
    inner += burst(564, 44, 30, 15, 12) + (
        f'<text x="564" y="49" font-size="13" font-weight="800" text-anchor="middle" fill="{RED}" '
        f'font-family="Avenir Next, Helvetica, sans-serif">HIT!</text>')
    return svg(W, H, paper(W, H, 20, inner))


def card(n, title, body, figs):
    fh = "".join(f'<figure>{f}{"<figcaption>" + c + "</figcaption>" if c else ""}</figure>' for f, c in figs)
    cls = "figs two" if len(figs) > 1 else "figs"
    return (f'<article class="step"><div class="step-head"><span class="num">{n}</span><h3>{title}</h3></div>'
            f'<div class="step-body">{body}</div><div class="{cls}">{fh}</div></article>')


SETUP = [
    ("Draw your bases.", "<p>Each player draws a square in their own corner of the paper. Both squares must be the same "
     "size. For example, each side could be 2 squares long.</p>", [(fig_bases(), "")]),
    ("Mark the middle.", "<p>Put a dot in the centre of each base. This is where your missile starts.</p>",
     [(fig_middle(), "")]),
    ("Add obstacles.", "<p>Take turns drawing blobs and other shapes on the paper. Make some of them touch the edge of "
     "the paper.</p>", [(fig_obstacles(), "")]),
    ("Pick who goes first.", "<p>The player who said the word “angle” most recently goes first.</p>",
     [(fig_first_clean(), "")]),
]

PLAY = [
    ("Guess an angle.", "<p>On your turn, say an angle out loud, like “45 degrees.” You may look at the "
     "protractor, but you may not place it on the paper.</p>", [(fig_guess(), "")]),
    ("Measure it.", "<p>Put the protractor on the paper and find the angle you said. Make a small mark at that "
     "angle.</p><ul><li><b>First turn:</b> Line up the protractor with the edges of the paper.</li>"
     "<li><b>Every turn after that:</b> Line up the protractor with the last line you drew.</li></ul>",
     [(fig_measure_first(), "First turn"), (fig_measure_later(), "Every turn after that")]),
    ("Launch your missile.", "<p>Use the ruler to draw a straight line from your missile through your mark, as "
     "long or as short as you want. Your missile is now at the end of the line.</p><ul><li><b>Watch out for "
     "blobs!</b> If your line touches a blob, your missile stops right there. To avoid a blob, stop your line "
     "before it.</li><li><b>Crossing lines is fine.</b> Your line can cross any line on the paper, yours or the "
     "other player’s.</li></ul>", [(fig_launch(), "Draw along the ruler"), (fig_blob_hit(), "Hitting a blob")]),
    ("Switch turns.", "<p>Now it’s the other player’s turn.</p>", [(fig_turns(), "")]),
    ("Keep going until someone’s base gets hit.", "<p>If your line crosses into the other player’s base, "
     "that counts as a hit!</p><ul><li><b>Tie?</b> If both players hit a base in the same round, the winner is the "
     "player whose line passed closest to the dot in the middle of the base.</li></ul>",
     [(fig_hit(), "A hit!"), (fig_tie(), "Breaking a tie")]),
    ("Say “good game”", "<p>Shake hands! \U0001F642</p>", [(fig_gg(), "")]),
]

DL_ICON = ('<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 3v12m0 0-5-5m5 5 5-5M4 '
           '19h16" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" '
           'stroke-linejoin="round"/></svg>')

CSS = """
:root { --ink:#1d232b; --muted:#56606c; --blue:#1f5fbf; --blue-l:#dbe7fa; --red:#c8322b; --red-l:#fbdedb;
  --paper:#fbfcfe; --grid:#e3e8ef; --card:#ffffff; --line:#d6dbe1; --sun:#ffd23f; color-scheme: light; }
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; color: var(--ink); font-family: 'Nunito', 'Avenir Next', Helvetica, sans-serif; font-size: 18px;
  line-height: 1.55; background-color: var(--paper);
  background-image: linear-gradient(var(--grid) 1px, transparent 1px), linear-gradient(90deg, var(--grid) 1px, transparent 1px);
  background-size: 24px 24px; }
h1, h2, h3 { font-family: 'Baloo 2', 'Arial Rounded MT Bold', sans-serif; line-height: 1.1; margin: 0; }
a { color: var(--blue); }
.wrap { max-width: 1100px; margin: 0 auto; padding: 0 20px; }
header.top { position: sticky; top: 0; z-index: 5; background: rgba(251,252,254,.92); backdrop-filter: blur(6px);
  border-bottom: 2px solid var(--ink); }
header.top .wrap { display: flex; align-items: center; justify-content: space-between; height: 60px; gap: 16px; }
.logo { font-family: 'Baloo 2', sans-serif; font-weight: 800; font-size: 26px; text-decoration: none; color: var(--ink); }
.logo span, h1 span { color: var(--red); }
nav a { margin-left: 22px; font-weight: 700; text-decoration: none; color: var(--ink); white-space: nowrap; }
nav a:hover { color: var(--blue); }
.hero { padding: 56px 0 40px; }
.hero .wrap { display: grid; grid-template-columns: 1fr 1.15fr; gap: 44px; align-items: center; }
.hero h1 { font-size: clamp(54px, 8vw, 92px); font-weight: 800; letter-spacing: -1px; }
.tag { font-family: 'Baloo 2', sans-serif; font-size: clamp(21px, 2.3vw, 27px); font-weight: 700; margin: 6px 0 14px; line-height: 1.3; }
.tag b { white-space: nowrap; }
.tag b:nth-child(1) { color: var(--blue); } .tag b:nth-child(2) { color: var(--ink); } .tag b:nth-child(3) { color: var(--red); }
.lede { font-size: 19px; color: var(--muted); margin: 0 0 26px; max-width: 30em; }
.btns { display: flex; flex-wrap: wrap; gap: 12px; }
.btn { display: inline-flex; align-items: center; gap: 10px; padding: 13px 22px; border-radius: 12px; font-weight: 800;
  text-decoration: none; border: 2.5px solid var(--ink); box-shadow: 4px 4px 0 var(--ink); transition: transform .1s, box-shadow .1s; }
.btn:hover { transform: translate(-2px,-2px); box-shadow: 6px 6px 0 var(--ink); }
.btn:active { transform: translate(2px,2px); box-shadow: 2px 2px 0 var(--ink); }
.btn.primary { background: var(--blue); color: #fff; }
.btn.secondary { background: #fff; color: var(--ink); }
.hero-art { border: 2.5px solid var(--ink); border-radius: 14px; overflow: hidden; background: #fff; box-shadow: 8px 8px 0 var(--ink);
  transform: rotate(1.2deg); }
.hero-art svg { display: block; width: 100%; height: auto; }
section.band { padding: 54px 0; }
section.band.white { background: #fff; border-top: 2px solid var(--ink); border-bottom: 2px solid var(--ink); }
.band h2 { font-size: clamp(34px, 4.5vw, 46px); font-weight: 800; margin-bottom: 8px; }
.band .intro { color: var(--muted); margin: 0 0 28px; }
.why { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.why div { background: var(--card); border: 2px solid var(--ink); border-radius: 14px; padding: 18px 20px; }
.why h3 { font-size: 22px; margin-bottom: 4px; }
.why p { margin: 0; color: var(--muted); }
.need { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px; }
.need div { background: var(--card); border: 2px solid var(--ink); border-radius: 14px; padding: 16px; text-align: center; font-weight: 700; }
.need .ic { font-size: 34px; display: block; margin-bottom: 4px; }
.emoji-svg { width: 1.25em; height: 1em; vertical-align: -0.1em; }
.need small { display: block; font-weight: 600; color: var(--muted); font-size: 14px; line-height: 1.35; margin-top: 4px; }
.win { background: var(--sun); border: 2.5px solid var(--ink); border-radius: 14px; padding: 16px 22px; font-size: 21px;
  font-weight: 800; box-shadow: 4px 4px 0 var(--ink); }
.win span { font-family: 'Baloo 2', sans-serif; margin-right: 8px; }
.steps { display: grid; grid-template-columns: repeat(2, 1fr); gap: 22px; }
.step { background: var(--card); border: 2px solid var(--ink); border-radius: 16px; padding: 20px 22px; display: flex;
  flex-direction: column; }
.step-head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.num { flex: none; width: 38px; height: 38px; border-radius: 50%; background: var(--ink); color: #fff; font-weight: 800;
  display: grid; place-items: center; font-size: 19px; }
.step h3 { font-size: 24px; font-weight: 700; }
.step-body p { margin: 0 0 8px; }
.step-body ul { margin: 0 0 8px; padding-left: 22px; }
.step-body li { margin-bottom: 4px; }
.figs { margin-top: auto; padding-top: 10px; display: grid; gap: 12px; }
.figs.two { grid-template-columns: 1fr 1fr; }
figure { margin: 0; }
figure svg { width: 100%; height: auto; display: block; border-radius: 6px; }
figcaption { text-align: center; font-weight: 800; font-size: 14px; color: var(--muted); margin-top: 4px; }
.dl { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.dl article { background: var(--card); border: 2.5px solid var(--ink); border-radius: 16px; padding: 24px; box-shadow: 6px 6px 0 var(--ink);
  display: flex; flex-direction: column; gap: 10px; }
.dl h3 { font-size: 28px; }
.dl p { margin: 0; color: var(--muted); }
.dl ul { margin: 0; padding-left: 20px; color: var(--muted); }
.dl .btn { align-self: flex-start; margin-top: auto; }
.dl article.wide { grid-column: 1 / -1; display: grid; grid-template-columns: 1fr auto; gap: 10px 24px; align-items: center; }
.dl article.wide .btn { margin-top: 0; }
.paper { display: inline-flex; align-items: center; gap: 12px; margin: -10px 0 26px; flex-wrap: wrap; }
.paper > span { font-weight: 800; }
.paper .seg { display: inline-flex; border: 2.5px solid var(--ink); border-radius: 12px; overflow: hidden; }
.paper button { font: inherit; font-weight: 800; padding: 8px 18px; border: 0; background: var(--card); color: var(--ink);
  cursor: pointer; }
.paper button + button { border-left: 2.5px solid var(--ink); }
.paper button[aria-pressed="true"] { background: var(--ink); color: #fff; }
.paper button:focus-visible { outline: 3px solid var(--sun); outline-offset: -5px; }
.dys { margin-top: 2px; font-size: 16px; font-weight: 700; }
.dys a { color: var(--blue); }
.dys small { display: block; font-weight: 600; color: var(--muted); font-size: 14px; }
.tip { font-size: 15px; background: var(--blue-l); border-radius: 10px; padding: 10px 14px; color: var(--ink); }
footer { padding: 34px 0 44px; text-align: center; color: var(--muted); font-size: 16px; }
footer b { color: var(--ink); }
.hits { margin: 14px 0 0; display: flex; align-items: center; justify-content: center; gap: 10px; font-size: 15px; }
.hits img { display: block; height: 32px; width: auto; }
@media (max-width: 860px) {
  .hero .wrap { grid-template-columns: 1fr; gap: 32px; }
  .hero { padding-top: 34px; }
  .why, .steps, .dl, .dl article.wide { grid-template-columns: 1fr; }
  .need { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 520px) {
  body { font-size: 17px; }
  .wrap { padding: 0 16px; }
  nav a { margin-left: 12px; font-size: 15px; }
  .logo { font-size: 22px; }
  nav a.hide-s { display: none; }
  .figs.two { grid-template-columns: 1fr; }
  .hero-art { transform: none; box-shadow: 5px 5px 0 var(--ink); }
}
"""


def build():
    setup = "".join(card(i + 1, *s) for i, s in enumerate(SETUP))
    play = "".join(card(i + 1, *s) for i, s in enumerate(PLAY))
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Protractwar – a pencil-and-paper angle game</title>
<meta name="description" content="Protractwar is a free pencil-and-paper game for two players. Guess an angle, measure it with a protractor, and launch your missile at the other player's base.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="logo" href="#">Protract<span>war</span></a>
  <nav><a class="hide-s" href="#setup">Getting ready</a><a href="#play">How to play</a><a href="#downloads">Downloads</a></nav>
</div></header>

<section class="hero"><div class="wrap">
  <div>
    <h1>Protract<span>war</span></h1>
    <p class="tag"><b>Guess the angle.</b> <b>Draw the line.</b> <b>Hit the base!</b></p>
    <p class="lede">A free pencil-and-paper battle for two players. All you need is graph paper, a protractor, a ruler
      and a sharp eye for angles.</p>
    <div class="btns">
      <a class="btn primary" href="{RULES_PDF}" data-pdf="rules" data-dys="0" download>{DL_ICON} Get the rules (PDF)</a>
      <a class="btn secondary" href="{MAPS_PDF}" data-pdf="maps" data-dys="0" download>{DL_ICON} Get the maps (PDF)</a>
    </div>
  </div>
  <div class="hero-art" role="img" aria-label="A Protractwar map: blue's missile zig-zags around blobs and hits red's base">{hero_svg()}</div>
</div></section>

<section class="band white"><div class="wrap">
  <div class="why">
    <div><h3>{protractor_icon()} Angle practice</h3><p>Every turn, players guess an angle, then check it with a real protractor.</p></div>
    <div><h3>✏️ Just paper</h3><p>No screens, no batteries. Print a map or draw your own on graph paper.</p></div>
    <div><h3>\U0001F3AF Easy to learn</h3><p>Ten short steps, each with a picture. Kids can teach it to each other.</p></div>
  </div>
</div></section>

<section class="band" id="need"><div class="wrap">
  <h2>What you need</h2>
  <p class="intro">Two players and a few things from your pencil case.</p>
  <div class="need">
    <div><span class="ic">\U0001F4C4</span>Graph or dot paper<small>or print one of our maps</small></div>
    <div><span class="ic">✏️</span>A sharp pencil<small>two coloured pencils are even better, one for each player</small></div>
    <div><span class="ic">{protractor_icon()}</span>A protractor<small>or <a href="#downloads">print our cut-out ones</a></small></div>
    <div><span class="ic">\U0001F4CF</span>A ruler</div>
  </div>
  <div class="win"><span>How to win:</span> Hit the other player’s base before they hit yours!</div>
</div></section>

<section class="band white" id="setup"><div class="wrap">
  <h2>Getting ready</h2>
  <p class="intro">Set up the paper before the first missile flies.</p>
  <div class="steps">{setup}</div>
</div></section>

<section class="band" id="play"><div class="wrap">
  <h2>How to play</h2>
  <p class="intro">Take turns. Each turn, your missile moves one straight line.</p>
  <div class="steps">{play}</div>
</div></section>

<section class="band white" id="downloads"><div class="wrap">
  <h2>Print and play</h2>
  <p class="intro">Free PDFs for Letter or A4 paper.</p>
  <div class="paper" role="group" aria-label="Paper size" hidden><span>Paper size:</span><div class="seg">
    <button type="button" data-paper="letter" aria-pressed="true">Letter</button><button type="button" data-paper="a4" aria-pressed="false">A4</button>
  </div></div>
  <noscript><p class="intro">A4 versions: <a href="protractwar-rules-a4.pdf">rules</a>, <a href="protractwar-maps-a4.pdf">maps</a>,
  <a href="protractwar-rules-dyslexic-a4.pdf">dyslexia-friendly rules</a>, <a href="protractwar-maps-dyslexic-a4.pdf">dyslexia-friendly maps</a>,
  <a href="protractwar-protractor-a4.pdf">cut-out protractors</a>.</p></noscript>
  <div class="dl">
    <article>
      <h3>\U0001F4D6 The rules</h3>
      <p>All the instructions on this page, with pictures, on two pages.</p>
      <ul><li>Page 1: what you need and getting ready</li><li>Page 2: how to play</li></ul>
      <a class="btn primary" href="{RULES_PDF}" data-pdf="rules" data-dys="0" download>{DL_ICON} Download rules</a>
      <p class="dys">\U0001F524 <a href="protractwar-rules-dyslexic.pdf" data-pdf="rules" data-dys="1" download>Dyslexia-friendly rules</a>
        <small>Set in the OpenDyslexic font, on three pages.</small></p>
    </article>
    <article>
      <h3>\U0001F5FA️ The maps</h3>
      <p>A ready-to-play sheet with bases already drawn. Print it double-sided.</p>
      <ul><li>Side 1: a map full of blobs</li><li>Side 2: an open map to add your own</li></ul>
      <p class="tip">Print at 100% (“Actual size”) so each grid square is exactly 5 mm.</p>
      <a class="btn secondary" href="{MAPS_PDF}" data-pdf="maps" data-dys="0" download>{DL_ICON} Download maps</a>
      <p class="dys">\U0001F524 <a href="protractwar-maps-dyslexic.pdf" data-pdf="maps" data-dys="1" download>Dyslexia-friendly maps</a>
        <small>The map labels in the OpenDyslexic font.</small></p>
    </article>
    <article class="wide">
      <div>
        <h3>{protractor_icon()} Cut-out protractors</h3>
        <p>No protractor? Print a page of eight and cut them out. Card stock works best.</p>
        <ul><li>The centre point is right on the flat edge, so you don’t need to see through it</li>
          <li>Two scales, so you can measure a turn to the left or the right</li></ul>
      </div>
      <a class="btn secondary" href="{PROTRACTOR_PDF}" data-pdf="protractor" data-dys="0" download>{DL_ICON} Download protractors</a>
    </article>
  </div>
</div></section>

<footer><div class="wrap">
  Created by <b>Alexander &amp; Paul Reinheimer</b> · <a href="https://protractwar.com">protractwar.com</a>
  <p class="hits">You are visitor <img src="counter.php" alt="(visitor counter)" height="32"></p>
</div></footer>
{PAPER_JS}
</body>
</html>"""
    os.makedirs(DOCROOT, exist_ok=True)
    with open(os.path.join(DOCROOT, "index.html"), "w") as f:
        f.write(html)
    names = [variant_name(kind, paper, dyslexic) for kind in ("rules", "maps") for paper, dyslexic in VARIANTS]
    names += [variant_name("protractor", paper, False) for paper in ("letter", "a4")]
    for name in names:
        shutil.copy(os.path.join(SRC, name + ".pdf"), os.path.join(DOCROOT, name + ".pdf"))


if __name__ == "__main__":
    build()
