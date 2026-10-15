"""Fast checks of the device layout, no Blender:  python3 hardware/cad/test_layout.py"""
import itertools

from layout import D, FACE, INTERNAL, POST_R, TARGETS, inside_body, inside_cavity, layout

NOTCHED = {("Board", "USBC")}   # the receptacle sits in a notch cut into the board


def corners(p):
    return list(itertools.product(*zip(p["lo"], p["hi"])))


def boxes_overlap(a, b):
    return all(a["lo"][i] < b["hi"][i] and b["lo"][i] < a["hi"][i] for i in range(3))


def check(screen):
    L = layout(screen)
    W, H, P = L["W"], L["H"], L["parts"]
    tw, th = TARGETS[screen]
    assert abs(W - tw) <= 1.0 and abs(H - th) <= 1.0, (screen, W, H)
    assert L["D"] == 15.0
    assert L["stack_mm"] <= D, L["stack_mm"]
    assert P["Module"]["hi"][1] <= D - FACE, "module pokes into the back wall"
    for name in INTERNAL:
        for c in corners(P[name]):
            assert inside_cavity(L, c), (screen, name, c)
    for name, k in L["keys"].items():
        gap = P[k["switch"]]["lo"][1] - k["plunger_end"]
        assert 0.1 <= gap <= 0.5, (screen, name, gap)
    fpc, con = P["FPC"], P["Connector"]
    assert 0 <= con["lo"][1] - fpc["hi"][1] <= 0.5, (screen, "FPC end", fpc["hi"], con["lo"])
    assert con["lo"][0] <= fpc["hi"][0] <= con["hi"][0], (screen, "FPC misses the connector")
    posts = {"Post%d" % i: {"lo": (x - POST_R, FACE, z - POST_R), "hi": (x + POST_R, D - FACE, z + POST_R)}
             for i, (x, z) in enumerate(L["posts"])}
    boxes = dict({n: P[n] for n in INTERNAL}, **posts)
    for a, b in itertools.combinations(boxes, 2):
        if (a, b) not in NOTCHED:
            assert not boxes_overlap(boxes[a], boxes[b]), (screen, a, b)
    return L


def test_inside_cavity():
    L = layout("2.8")
    W, H = L["W"], L["H"]
    assert inside_cavity(L, (W / 2, 7.5, H / 2))
    assert inside_cavity(L, (1.6, 7.5, H / 2))            # flat side wall, mid depth
    assert not inside_cavity(L, (0.5, 7.5, H / 2))        # inside the side wall
    assert not inside_cavity(L, (W / 2, 0.5, H / 2))      # inside the front wall
    assert not inside_cavity(L, (1.6, 7.5, 1.6))          # rounded plan corner
    assert not inside_cavity(L, (1.6, 13.7, H / 2))       # rounded back edge
    assert inside_body(L, (0.5, 7.5, H / 2)) and not inside_body(L, (-0.1, 7.5, H / 2))
    assert not inside_body(L, (1.6, 14.9, H / 2))         # screw-head height at the side: outside the back round


if __name__ == "__main__":
    test_inside_cavity()
    a, b = check("2.8"), check("2.4")
    assert 8.0 <= a["W"] - b["W"] <= 10.0, a["W"] - b["W"]
    for L in (a, b):
        print('%s": body %.2f x %.2f x %.1f mm, stack %.1f mm' % (L["screen"], L["W"], L["H"], L["D"], L["stack_mm"]))
    print("layout ok")
