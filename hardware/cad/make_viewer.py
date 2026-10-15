"""Builds docs/device-3d.html: viewer.html with the six designs' models, their dims and the screen
images inlined (one self-contained file).

    python3 hardware/cad/make_viewer.py [--cad-out DIR] [--fragment PATH]

--cad-out   where the builds are (default: hardware/cad/out)
--fragment  also write the page without its <!doctype>/<html>/<head>/<body> wrapper, for
            hosts that add their own (the claude.ai artifact)
"""
import base64
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "..", "docs", "device-3d.html")
SCREENS = ("home", "listening", "answer", "tasks", "alert")
MAX_MB = 12.0
sys.path.insert(0, HERE)
from designs import DESIGNS  # noqa: E402


def b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    cad_out = arg("--cad-out", os.path.join(HERE, "out"))
    data = {"order": list(DESIGNS), "designs": {}, "screens": {}}
    for v in DESIGNS:
        for f in ("device.glb", "dims.json"):
            p = os.path.join(cad_out, v, f)
            if not os.path.exists(p):
                sys.exit("make_viewer: missing %s — build it: blender -b -P hardware/cad/build_device.py -- --design %s" % (p, v))
        data["designs"][v] = {"dims": json.load(open(os.path.join(cad_out, v, "dims.json"))),
                              "glb": b64(os.path.join(cad_out, v, "device.glb"))}
    for s in SCREENS:
        data["screens"][s] = "data:image/png;base64," + b64(os.path.join(HERE, "screens", s + ".png"))
    tpl = open(os.path.join(HERE, "viewer.html")).read()
    if tpl.count("__DATA__") != 1:
        sys.exit("make_viewer: viewer.html must contain __DATA__ exactly once")
    html = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    with open(PAGE, "w") as f:
        f.write(html)
    mb = len(html.encode()) / 1e6
    print("wrote %s (%.2f MB)" % (os.path.relpath(PAGE), mb))
    if mb > MAX_MB:
        sys.exit("make_viewer: page is %.2f MB (max %.1f)" % (mb, MAX_MB))
    frag = arg("--fragment")
    if frag:
        body = re.sub(r"^\s*(<!doctype html>|<html[^>]*>|</?head>|</?body>|</html>)\s*$\n?", "", html, flags=re.M | re.I)
        with open(frag, "w") as f:
            f.write(body)
        print("wrote", frag)


if __name__ == "__main__":
    main()
