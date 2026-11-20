"""Builds the link-preview and icon images in docroot/, by rendering HTML with headless Chrome:

  og-image.png          1200x630 social card (Open Graph / Twitter), used by LinkedIn, Facebook, Slack, iMessage...
  apple-touch-icon.png  180x180 home-screen / bookmark icon
  favicon.svg           the protractor glyph, for browser tabs

Needs network access for the Google Fonts the site uses (Baloo 2, Nunito). Set CHROME=... if needed.
"""
import os
import subprocess
import tempfile

from build_pdfs import find_chrome
from build_site import DOCROOT, hero_svg

FONTS = ('<link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@700;800&family=Nunito:wght@700;800'
         '&display=block" rel="stylesheet">')
BASE_CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; overflow: hidden; }
body { color: #1d232b; background-color: #fbfcfe;
  background-image: linear-gradient(#e3e8ef 1px, transparent 1px), linear-gradient(90deg, #e3e8ef 1px, transparent 1px);
  background-size: 30px 30px; }
"""

OG_CSS = BASE_CSS + """
body { width: 1200px; height: 630px; display: grid; grid-template-columns: 470px 1fr; gap: 44px; align-items: center;
  padding: 0 60px 0 70px; font-family: 'Nunito', sans-serif; }
h1 { font-family: 'Baloo 2', sans-serif; font-weight: 800; font-size: 90px; line-height: 1; margin: 0; letter-spacing: -2px; }
h1 span, .url span { color: #c8322b; }
.tag { font-family: 'Baloo 2', sans-serif; font-weight: 700; font-size: 34px; line-height: 1.22; margin: 14px 0 22px; }
.tag b { display: block; }
.tag b:nth-child(1) { color: #1f5fbf; } .tag b:nth-child(3) { color: #c8322b; }
.lede { font-size: 23px; font-weight: 700; color: #56606c; margin: 0 0 26px; line-height: 1.35; }
.url { display: inline-block; font-family: 'Baloo 2', sans-serif; font-weight: 800; font-size: 26px; padding: 6px 18px 4px;
  background: #fff; border: 3px solid #1d232b; border-radius: 12px; box-shadow: 4px 4px 0 #1d232b; }
.art { border: 3px solid #1d232b; border-radius: 16px; overflow: hidden; background: #fff; box-shadow: 10px 10px 0 #1d232b;
  transform: rotate(1.5deg); }
.art svg { display: block; width: 100%; height: auto; }
"""

# The protractor glyph from the site, drawn bigger and bolder so it still reads at 16px
PROTRACTOR = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
              '<path d="M2 25A14 14 0 0 1 30 25Z" fill="#fff4b8" stroke="#1d232b" stroke-width="2.2" '
              'stroke-linejoin="round"/>'
              '<path d="M10 25A6 6 0 0 1 22 25" fill="none" stroke="#1d232b" stroke-width="1.8"/>'
              '<g stroke="#1d232b" stroke-width="2" stroke-linecap="round">'
              '<path d="M16 11V14.5M6.1 15.1 8.6 17.6M25.9 15.1 23.4 17.6"/></g>'
              '<circle cx="16" cy="25" r="2" fill="#1d232b"/></svg>')

ICON_CSS = BASE_CSS + """
body { width: 180px; height: 180px; display: flex; align-items: center; justify-content: center; background-size: 18px 18px; }
svg { width: 156px; height: 156px; }
"""


def screenshot(chrome, html, out, w, h):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as f:
        f.write(html)
    try:
        # virtual-time-budget lets the web fonts load before the shot
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                        "--virtual-time-budget=5000", f"--screenshot={out}", "file://" + f.name],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    finally:
        os.unlink(f.name)


def build():
    chrome = find_chrome()
    og = (f'<!doctype html><html><head><meta charset="utf-8">{FONTS}<style>{OG_CSS}</style></head><body>'
          '<div><h1>Protract<span>war</span></h1>'
          '<p class="tag"><b>Guess the angle.</b> <b>Draw the line.</b> <b>Hit the base!</b></p>'
          '<p class="lede">A free pencil-and-paper battle for two players. Print the rules and maps.</p>'
          '<div class="url">protract<span>war</span>.com</div></div>'
          f'<div class="art">{hero_svg()}</div></body></html>')
    screenshot(chrome, og, os.path.join(DOCROOT, "og-image.png"), 1200, 630)
    icon = (f'<!doctype html><html><head><meta charset="utf-8"><style>{ICON_CSS}</style></head><body>'
            f'{PROTRACTOR}</body></html>')
    screenshot(chrome, icon, os.path.join(DOCROOT, "apple-touch-icon.png"), 180, 180)
    with open(os.path.join(DOCROOT, "favicon.svg"), "w") as f:
        f.write(PROTRACTOR + "\n")


if __name__ == "__main__":
    build()
