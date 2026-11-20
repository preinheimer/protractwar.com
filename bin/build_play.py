"""Builds docroot/play.html, the online two-player game (not linked from the main page), from
src/play.template.html. Fills in the printed map's geometry so the online "Printed map" matches the PDF."""
import json
import os

from build_protractwar import ROOT, SRC
from build_maps import BLOBS_BIG, BLUE_BASE, GH, GW, RECT, RED_BASE, TRIANGLE, _extra_blobs

DOCROOT = os.path.join(ROOT, "docroot")


def printed_map():
    # map_svg draws BLOBS_BIG at half their listed radius and the extra blobs as-is
    blobs = [(x, y, R / 2, sd) for x, y, R, sd in BLOBS_BIG] + _extra_blobs()
    rx, ry, rw, rh = RECT
    return {
        "w": GW, "h": GH,
        "blue": list(BLUE_BASE), "red": list(RED_BASE),
        "blobs": [[round(v, 4) for v in b] for b in blobs],
        "polys": [[[rx, ry], [rx + rw, ry], [rx + rw, ry + rh], [rx, ry + rh]], [list(p) for p in TRIANGLE]],
    }


def build():
    with open(os.path.join(SRC, "play.template.html")) as f:
        html = f.read()
    assert html.count("__PRINTED_MAP__") == 1
    html = html.replace("__PRINTED_MAP__", json.dumps(printed_map(), separators=(",", ":")))
    with open(os.path.join(DOCROOT, "play.html"), "w") as f:
        f.write(html)


if __name__ == "__main__":
    build()
