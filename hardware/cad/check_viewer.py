"""Headless checks for docs/device-3d.html (v2: six designs, labels, tour, stand) and screenshots
of every state at phone and desktop size.

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
DESIGNS = ["walnut", "instrument", "arcade", "clear", "egg", "bomb"]
CORE = set("FrontShell BackShell Lens Panel FPC Connector Foam Battery Board Module Amp Charger USBC Mic Speaker KeySheet "
           "TALK Ring OK BACK SwTalk Sw5Way SwBack LightPipe Screws Caps Stand".split())
EXTRAS = {"walnut": {"BackPanel", "Engraving"}, "instrument": {"FacePlate", "Engraving"}, "arcade": {"Stickers"},
          "clear": {"Stickers"}, "egg": {"Stickers", "Cheeks"}, "bomb": {"Stickers"}}
DEFAULTS = {"design": "walnut", "screen": "home", "explode": "0", "labels": "0", "stand": "0", "dims": "0", "pick": "", "step": "0"}
STATES = [("walnut", ""), ("instrument", "design=instrument"), ("arcade", "design=arcade"), ("clear", "design=clear"),
          ("egg", "design=egg"), ("bomb", "design=bomb"), ("labels", "explode=1&labels=1"), ("egg-labels", "design=egg&explode=1&labels=1"),
          ("stand", "design=arcade&stand=1"), ("tour3", "step=3"), ("tour8", "design=egg&step=8"), ("picked", "explode=1&pick=Battery")]


def chrome(url, *extra):
    return subprocess.run(CHROME + list(extra) + [url], capture_output=True, text=True, timeout=300).stdout


def shown(im, w, h):
    """The model is on screen: at least 20 % of the stage's rows hold a pixel that differs clearly
    from the page background. The loading or error message is a few lines (<= 9 % of rows); a dark
    model on the dark page can cover as little pixel area as that message, so area alone can't tell."""
    stage = im.crop((0, int(h * 0.07), w, int(h * 0.62)))
    bg = stage.getpixel((2, 2))
    px, sw = list(stage.getdata()), stage.width
    rows = sum(1 for y in range(stage.height)
               if any(max(abs(a - b) for a, b in zip(p, bg)) > 40 for p in px[y * sw:(y + 1) * sw]))
    return rows / stage.height >= 0.2


def shot(hash_, w, h, out):
    """Screenshot at w x h. Headless Chrome won't make a window narrower than 500 px and its viewport
    isn't the window height, so the page goes in an iframe of exactly w x h and the shot is cropped
    to it. Retried while the model hasn't appeared."""
    url = PAGE + ("#" + hash_ if hash_ else "")
    frame = os.path.join(tempfile.gettempdir(), "device-3d-frame.html")
    with open(frame, "w") as f:
        f.write('<!doctype html><style>html,body{margin:0}</style><iframe src="%s" style="display:block;width:%dpx;height:%dpx;border:0"></iframe>' % (url, w, h))
    for _ in range(3):
        chrome("file://" + frame, "--screenshot=" + out, "--window-size=%d,%d" % (max(w, 500), h + 120))
        im = Image.open(out).convert("RGB").crop((0, 0, w, h))
        im.save(out)
        if shown(im, w, h):
            return
    sys.exit("9 screenshot never showed the model: " + out)


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
    assert sorted(r["designs"]) == sorted(DESIGNS), r["designs"].keys()
    for d, parts in r["designs"].items():
        missing = (CORE | EXTRAS[d]) - set(parts)
        assert not missing, "%s is missing %s" % (d, sorted(missing))
    assert r["tour"] == 8, "tour ran %s of 8 steps" % r["tour"]
    for size, lab in r["labels"].items():
        assert lab["n"] >= (10 if size == "desktop" else 5) and lab["overlaps"] == 0 and lab["outside"] == 0, "labels at %s: %s" % (size, lab)
    assert r["tap"]["drag"] == "" and r["tap"]["pinch"] == "" and r["tap"]["tap"] != "", "tap vs drag / pinch: %s" % r["tap"]
    for d, card in r["cards"].items():
        assert r["titles"][d] in card, "card for %s shows: %s" % (d, card)
    assert abs(r["stand"]["applied"] - r["stand"]["open_deg"]) < 0.5, "stand: %s" % r["stand"]
    assert r["helpers"]["after_switch"] == r["helpers"]["expected"], "stale highlight boxes: %s" % r["helpers"]
    for size, mk in r["markers"].items():
        assert mk["outside"] == 0 and mk["stacked"] == 0, "markers at %s: %s" % (size, mk)
    assert r["chips"]["phone"] > 0 and r["chips"]["hidden"] == 0, "firmware chips on a phone: %s" % r["chips"]
    assert r["deeplink"] == {"explode": "0.55", "stand": "0"} and r["deeplink8"]["stand"] == "1", "tour deep link: %s %s" % (r["deeplink"], r["deeplink8"])
    for size, band in r["band"].items():
        assert band["inside"], "model under the labels at %s: %s" % (size, band)
    bad = selftest("&design=pebble&screen=constructor&explode=abc&step=99&pick=__proto__&labels=toString")
    assert bad["start"] == DEFAULTS and not bad["errors"], "bad hash: %s" % bad
    off = chrome(PAGE, "--dump-dom", "--host-resolver-rules=MAP cdn.jsdelivr.net 127.0.0.1:9")
    assert re.search(r'<div id="msg"[^>]*>[^<]*needs internet', off), "offline: no message"
    os.makedirs(shots, exist_ok=True)
    for w, h, tag in ((390, 844, "phone"), (1280, 800, "desktop")):
        for name, hs in STATES:
            shot(hs, w, h, os.path.join(shots, "%s-%s.png" % (tag, name)))
    assert "planned" in r["fwtext"], "firmware not marked planned: %s" % r["fwtext"]
    assert "planned" in r["pickfw"], "tapped part's firmware not marked planned: %s" % r["pickfw"]
    print("viewer ok: %d designs, 8 tour steps, labels %s, tap picks %s, %d screenshots in %s"
          % (len(r["designs"]), {k: v["n"] for k, v in r["labels"].items()}, r["tap"]["tap"], 2 * len(STATES), shots))


if __name__ == "__main__":
    main()
