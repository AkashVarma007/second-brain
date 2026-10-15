"""Headless checks for docs/device-3d.html (spec checks 8-10) and screenshots of every state.

    python3 hardware/cad/check_viewer.py [--shots DIR]   (default: <tmp>/device-3d-shots)
"""
import html
import json
import os
import re
import subprocess
import sys
import tempfile

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = "file://" + os.path.abspath(os.path.join(HERE, "..", "..", "docs", "device-3d.html"))
CHROME = ["google-chrome", "--headless=new", "--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader",
          "--hide-scrollbars", "--virtual-time-budget=60000"]
DEFAULTS = {"size": "28", "compare": "0", "finish": "graphite", "screen": "home", "explode": "0", "dims": "0", "pick": ""}
PARTS = sorted("FrontShell BackShell BackLabel Lens Panel FPC Connector Foam Battery Board Module Amp Charger USBC Mic "
               "Speaker KeySheet TALK Ring OK BACK SwTalk Sw5Way SwBack LightPipe Screws".split())
STATES = [("default", ""), ("size24", "size=24"), ("compare", "compare=1"), ("chalk", "finish=chalk"),
          ("amber", "finish=amber"), ("listening", "screen=listening"), ("answer", "screen=answer"),
          ("tasks", "screen=tasks"), ("alert", "screen=alert"), ("exploded", "explode=1"),
          ("picked", "explode=1&pick=Battery"), ("dims", "compare=1&dims=1")]


def chrome(url, *extra):
    return subprocess.run(CHROME + list(extra) + [url], capture_output=True, text=True, timeout=300).stdout


def shot(hash_, w, h, out):
    """Screenshot at w x h. Headless Chrome won't make a window narrower than 500 px and its
    viewport isn't the window height, so the page goes in an iframe of exactly w x h and the
    shot is cropped to it.
    Retried while the model hasn't appeared (no TALK-key coral pixels yet)."""
    url = PAGE + ("#" + hash_ if hash_ else "")
    frame = os.path.join(tempfile.gettempdir(), "device-3d-frame.html")
    with open(frame, "w") as f:
        f.write('<!doctype html><style>html,body{margin:0}</style><iframe src="%s" style="display:block;width:%dpx;height:%dpx;border:0"></iframe>' % (url, w, h))
    url = "file://" + frame
    for _ in range(3):
        chrome(url, "--screenshot=" + out, "--window-size=%d,%d" % (max(w, 500), h + 120))
        im = Image.open(out).convert("RGB").crop((0, 0, w, h))
        im.save(out)
        coral = sum(1 for r, g, b in im.getdata() if r > 180 and g < 130 and b < 130 and r - g > 80)
        if coral >= 40:                      # the TALK key is on screen in every state: the model loaded
            return
    sys.exit("9 screenshot never left the loading state: " + out)


def selftest(extra=""):
    for _ in range(2):                       # three.js comes from the CDN; one retry for a slow first fetch
        dom = chrome(PAGE + "#selftest=1" + extra, "--dump-dom")
        m = re.search(r'<pre id="result"[^>]*>(.*?)</pre>', dom, re.S)
        if m and m.group(1).strip():
            return json.loads(html.unescape(m.group(1)))
    sys.exit("check_viewer: no self-test result — the page did not finish loading")


def main():
    shots = sys.argv[sys.argv.index("--shots") + 1] if "--shots" in sys.argv else os.path.join(tempfile.gettempdir(), "device-3d-shots")
    r = selftest()
    assert not r["errors"], "8 page errors: %s" % r["errors"]
    assert r["states"] == len(STATES), r["states"]
    assert r["parts"] == PARTS, "parts differ: %s" % sorted(set(r["parts"]) ^ set(PARTS))
    c = r["compare"]
    assert 8.0 <= c["expect_mm"] <= 10.0 and abs(c["diff_mm"] - c["expect_mm"]) <= 1.0, "10 compare widths: %s" % c
    assert r["tap"]["drag"] == "" and r["tap"]["pinch"] == "" and r["tap"]["tap"] != "", "tap vs drag / pinch: %s" % r["tap"]
    assert r["cards"]["28"].startswith('2.8"') and r["cards"]["24"].startswith('2.4"'), "card shows the other size: %s" % r["cards"]
    bad = selftest("&size=99&finish=pink&screen=nope&explode=abc&pick=Nothing")
    assert bad["start"] == DEFAULTS and not bad["errors"], "bad hash: %s" % bad
    off = chrome(PAGE, "--dump-dom", "--host-resolver-rules=MAP cdn.jsdelivr.net 127.0.0.1:9")
    assert re.search(r'<div id="msg"[^>]*>[^<]*needs internet', off), "offline: no message"
    os.makedirs(shots, exist_ok=True)
    for w, h, tag in ((390, 844, "phone"), (1280, 800, "desktop")):
        for name, hs in STATES:
            shot(hs, w, h, os.path.join(shots, "%s-%s.png" % (tag, name)))
    print("viewer ok: %d states, compare %.2f mm (want %.2f), tap picks %s, %d screenshots in %s"
          % (r["states"], c["diff_mm"], c["expect_mm"], r["tap"]["tap"], 2 * len(STATES), shots))


if __name__ == "__main__":
    main()
