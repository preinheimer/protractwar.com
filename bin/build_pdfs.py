"""Prints every src/protractwar-*.html to a PDF next to it with headless Chrome, then checks page counts.

Set CHROME to the browser binary if it isn't in a standard location.
"""
import glob
import os
import re
import shutil
import subprocess
import sys

from build_protractwar import SRC

CHROME_CANDIDATES = [
    os.environ.get("CHROME", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    shutil.which("google-chrome") or "",
    shutil.which("chromium") or "",
    shutil.which("chromium-browser") or "",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and os.path.exists(c):
            return c
    sys.exit("Chrome not found; set CHROME=/path/to/chrome")


def expected_pages(name):
    """Everything is two pages, except the dyslexic rules, which need a third for the wider font."""
    return 3 if name.startswith("protractwar-rules-dyslexic") else 2


def page_count(pdf_path):
    with open(pdf_path, "rb") as f:
        return len(re.findall(rb"/Type\s*/Page[^s]", f.read()))


def main():
    chrome = find_chrome()
    ok = True
    for html in sorted(glob.glob(os.path.join(SRC, "protractwar-*.html"))):
        pdf = html[:-len(".html")] + ".pdf"
        subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", "file://" + html],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        n, want = page_count(pdf), expected_pages(os.path.basename(pdf))
        flag = "" if n == want else f"  <-- expected {want} pages"
        ok &= n == want
        print(f"{os.path.basename(pdf):40} {n} pages{flag}")
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
