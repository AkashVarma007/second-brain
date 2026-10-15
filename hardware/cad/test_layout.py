"""Fast checks of the v2 layout for every design, no Blender:  python3 hardware/cad/test_layout.py"""
import itertools
import math
import os

from PIL import Image

from designs import DESIGNS
from layout import CLIPPED, D, FACE, GAP, INTERNAL, POST_R, SIDE, inside_shell, layout, outline, sdist

HERE = os.path.dirname(os.path.abspath(__file__))
HOLED = {"Board"}                       # the board has a notch for the USB-C and clearance holes for the posts


def corners(p):
    return list(itertools.product(*zip(p["lo"], p["hi"])))


def boxes_overlap(a, b):
    return all(a["lo"][i] < b["hi"][i] and b["lo"][i] < a["hi"][i] for i in range(3))


def footprint(cx, cz, w, h, rot):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + x * c - z * s, cz + x * s + z * c) for x, z in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]


def check(name):
    d, L = DESIGNS[name], layout(name)
    W, H, P, ol = L["W"], L["H"], L["parts"], L["outline"]
    assert 95 <= W <= 118 and 55 <= H <= 80, (name, "not pocket-sized", W, H)
    assert L["stack_mm"] <= D
    for x in (P["Panel"]["lo"][0], P["Panel"]["hi"][0]):                       # panel corners inside the cavity
        for z in (P["Panel"]["lo"][2], P["Panel"]["hi"][2]):
            assert sdist(ol, x, z) >= SIDE + GAP - 1e-9, (name, "panel corner in the wall", x, z)
    for n in INTERNAL:
        if n not in CLIPPED:
            for c in corners(P[n]):
                assert inside_shell(L, c), (name, n, "outside the cavity", c)
    for k in L["keys"].values():
        gap = P[k["switch"]]["lo"][1] - k["plunger_end"]
        assert 0.1 <= gap <= 0.5, (name, k["switch"], gap)
    fpc, con = P["FPC"], P["Connector"]
    assert 0 <= con["lo"][1] - fpc["hi"][1] <= 0.5 and con["lo"][0] <= fpc["hi"][0] <= con["hi"][0], (name, "FPC misses the connector")
    posts = {"Post%d" % i: {"lo": (x - POST_R, P["Panel"]["hi"][1] + GAP, z - POST_R), "hi": (x + POST_R, D - FACE, z + POST_R)}
             for i, (x, z) in enumerate(L["posts"])}
    for x, z in L["posts"]:
        assert sdist(ol, x, z) >= SIDE + POST_R - 0.35, (name, "post outside the wall", x, z)
    boxes = dict({n: P[n] for n in INTERNAL}, **posts)
    lp = P["LightPipe"]                                   # posts run front-to-back past the status-light pipe
    for post, pb in posts.items():
        assert not all(lp["lo"][i] < pb["hi"][i] and pb["lo"][i] < lp["hi"][i] for i in (0, 2)), (name, post, "post hits the light pipe")
    for a, b in itertools.combinations(boxes, 2):
        if not ({a, b} & HOLED and ({a, b} - HOLED).pop() in ("USBC", *posts)):
            assert not boxes_overlap(boxes[a], boxes[b]), (name, a, b)
    for png, dx, z, w, rot in d.get("stickers", []):    # stickers on the flat back (a back decal is mirrored: -rot in world)
        iw, ih = Image.open(os.path.join(HERE, "stickers", png + ".png")).size
        fp = footprint(W / 2 + dx, z, w, w * ih / iw, -rot)
        for x, zz in fp:
            assert sdist(ol, x, zz) >= d["eb"] + 0.5, (name, png, "off the flat back")
    o = L["opening"]
    for png, (x, z, w) in L["front_stickers"]:
        iw, ih = Image.open(os.path.join(HERE, "stickers", png + ".png")).size
        for xx, zz in footprint(x, z, w, w * ih / iw, 0):
            assert sdist(ol, xx, zz) >= d["ef"] + 0.3, (name, png, "off the flat front")
            assert not (o[0] - 0.3 < xx < o[2] + 0.3 and o[1] - 0.3 < zz < o[3] + 0.3), (name, png, "on the screen opening")
    s = L["stand"]          # stand closed: hinge end on the flat back; its tip (~95 % of the hinge height) stays above the bottom
    for x in (s["x"] - s["width"] / 2, s["x"] + s["width"] / 2):
        assert sdist(ol, x, s["zh"] + s["barrel"]) >= d["eb"] + 0.3, (name, "stand hinge off the flat back", x)
    assert s["zh"] - s["length"] >= 0.5 and s["length"] >= s["zh"] * math.cos(math.radians(18)), (name, "stand can't reach", s)
    return L


def test_sdist_and_outline():
    sq = outline(("rrect", 0.5), 10.0, 10.0)
    assert abs(sdist(sq, 5, 5) - 5) < 0.05 and sdist(sq, -1, 5) < 0 and abs(sdist(sq, 5, 0)) < 1e-6
    inner = outline(("rrect", 7.0), 100.0, 60.0, inset=1.5)
    assert abs(min(x for x, _ in inner) - 1.5) < 1e-6 and abs(max(x for x, _ in inner) - 98.5) < 1e-6
    sq4 = outline(("squircle", 4.0), 100.0, 60.0)
    assert abs(max(x for x, _ in sq4) - 100.0) < 1e-6 and sdist(sq4, 1.0, 1.0) < 0     # squircle corners are cut away


if __name__ == "__main__":
    test_sdist_and_outline()
    for name in DESIGNS:
        L = check(name)
        print("%-11s body %.1f x %.1f x %.0f mm, panel margin %.1f" % (name, L["W"], L["H"], L["D"], L["m"]))
    print("layout ok")
