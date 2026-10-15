"""Layout of the pocket device (v2: 3.2" tight layout) for one case design, in mm.

Pure Python (no bpy): build_device.py turns it into meshes and test_layout.py checks it in a
second. Axes: x = width (left to right), z = height (bottom to top), y = depth (front face y = 0,
back face y = D). Parts are axis-aligned boxes (lo / hi corners); the body's plan shape comes from
the design's outline. The panel margin is the smallest that fits the panel and the front controls
inside that outline (rounder corners push it in).
"""
import math

from designs import DESIGNS

PANEL = {"glass": (77.2, 55.0, 2.5), "active": (64.8, 48.6), "off": (3.0, 3.2)}   # 3.2" ILI9341; ribbon strip on the right
OPEN_MARGIN = 1.0                                          # screen opening = active area + this
D, FACE, SIDE = 15.0, 1.2, 1.5                             # depth, front/back wall, side wall
GAP = 0.05                                                 # between parts that touch by design
SPLIT = D - 2.6                                            # front tub | back cover
STACK = (("lens", FACE), ("panel", 2.5), ("foam", 0.3), ("battery", 5.0), ("board", 1.0), ("module", 3.1))
KEY_GAP, KEY_LIFT = 0.3, 0.6                               # key-to-opening clearance, key height above the face
SW_H, SW_GAP = 3.5, 0.3                                    # tact switch height, plunger-to-switch gap
POST_R, BORE_R = 1.7, 0.8                                  # screw posts, screw bores
CX_FROM_PANEL = 77.2 + 0.3 + 5.1                           # key column centre: the 5-way's tube clears the ribbon strip
TILT = 18.0                                                # stand angle, degrees from upright

# parts that must sit inside the shell cavity; CLIPPED ones are cut to the cavity outline in Blender
INTERNAL = ("Panel", "Foam", "Battery", "Board", "Module", "Amp", "Charger", "USBC", "Connector", "FPC",
            "Mic", "Speaker", "SwTalk", "Sw5Way", "SwBack", "KeySheet")
CLIPPED = ("Board", "KeySheet")


# --- outlines -----------------------------------------------------------------------
def _rrect(w, h, r, seg=14):
    pts = []
    for (cx, cz, a0), rr in zip(((r[0], r[0], 180), (w - r[1], r[1], 270), (w - r[2], h - r[2], 0), (r[3], h - r[3], 90)), r):
        for i in range(seg + 1):
            a = math.radians(a0 + 90 * i / seg)
            pts.append((cx + rr * math.cos(a), cz + rr * math.sin(a)))
    return pts


def _squircle(w, h, n, k=160):
    pts = []
    for i in range(k):
        t = 2 * math.pi * i / k
        c, s = math.cos(t), math.sin(t)
        pts.append((w / 2 * (1 + math.copysign(abs(c) ** (2 / n), c)), h / 2 * (1 + math.copysign(abs(s) ** (2 / n), s))))
    return pts


def offset(pts, d):
    """Move every vertex of a counter-clockwise outline d inwards along its normal (true parallel
    offset for smooth convex outlines: walls keep their thickness on squircles too)."""
    out, n = [], len(pts)
    for i in range(n):
        (x0, z0), (x1, z1), (x2, z2) = pts[i - 1], pts[i], pts[(i + 1) % n]
        na = (-(z1 - z0), x1 - x0)
        nb = (-(z2 - z1), x2 - x1)
        la, lb = math.hypot(*na) or 1e-12, math.hypot(*nb) or 1e-12
        na, nb = (na[0] / la, na[1] / la), (nb[0] / lb, nb[1] / lb)
        mx, mz = na[0] + nb[0], na[1] + nb[1]
        ml = math.hypot(mx, mz) or 1e-12
        k = d / max((mx * na[0] + mz * na[1]) / ml, 0.3)       # keep the distance at a corner (miter)
        out.append((x1 + mx / ml * k, z1 + mz / ml * k))
    return out


def outline(spec, w, h, inset=0.0):
    """Plan outline [(x, z)] counter-clockwise from the front; inset shrinks it by a parallel offset
    (cavity, flat face, back panel)."""
    kind, p = spec
    if kind == "rrect":
        pts = _rrect(w, h, p if isinstance(p, (tuple, list)) else (p,) * 4)
    else:
        pts = _squircle(w, h, p)
    return offset(pts, inset) if inset else pts


def sdist(pts, x, z):
    """Signed distance from (x, z) to the polygon: + inside, - outside."""
    inside, best = False, float("inf")
    for i in range(len(pts)):
        (x1, z1), (x2, z2) = pts[i], pts[(i + 1) % len(pts)]
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            inside = not inside
        dx, dz = x2 - x1, z2 - z1
        t = max(0.0, min(1.0, ((x - x1) * dx + (z - z1) * dz) / ((dx * dx + dz * dz) or 1e-12)))
        best = min(best, math.hypot(x - x1 - t * dx, z - z1 - t * dz))
    return best if inside else -best


def _inside(L, p, side, face):
    x, y, z = p
    d = sdist(L["outline"], x, z) - side
    if d < 0 or not face <= y <= D - face:
        return False
    for t, re in ((y - face, L["ef"] - face), (D - face - y, L["eb"] - face)):
        re = max(re, 0.4)
        if d < re and t < re and math.hypot(re - d, re - t) > re:
            return False
    return True


def inside_shell(L, p):
    """Point inside the shell's inner space (the outline less the walls, edges rounded like the outside)."""
    return _inside(L, p, SIDE, FACE)


def inside_body(L, p):
    """Point inside the outer body shape (nothing may stick out of it)."""
    return _inside(L, p, 0.0, 0.0)


def edge_clear(t, re):
    """How far from the wall a point t behind the inner face must be to clear an edge round of radius re."""
    return re - math.sqrt(max(2 * re * t - t * t, 0.0)) if t < re else 0.0


def x_right(pts, z0, z1, margin, w):
    """Largest x where the span z0..z1 is at least margin inside the outline (parts against the right wall)."""
    x = w
    while x > 0 and any(sdist(pts, x, z0 + (z1 - z0) * i / 4) < margin for i in range(5)):
        x -= 0.05
    return x


def z_top(pts, x, margin, h):
    """Highest z at column x that is at least margin inside the outline."""
    z = h
    while z > 0 and sdist(pts, x, z) < margin:
        z -= 0.05
    return z


# --- the layout ---------------------------------------------------------------------
def _place(d, m):
    gw, gh, gt = PANEL["glass"]
    aw, ah = PANEL["active"]
    padx, padb, padt = d.get("pad", (0.0, 0.0, 0.0))
    W, H = m + padx + 100.3, 2 * m + gh + padb + padt
    px0, pz0 = m + padx / 2, m + padb                        # panel glass bottom-left
    ol = outline(d["outline"], W, H)
    plate = d.get("plate", {}).get("thick", 0.0)
    lift = KEY_LIFT + (plate + GAP if plate else 0.0)
    parts = {}

    def part(name, lo, hi, label, size, explode, fw=None, **extra):
        parts[name] = dict(lo=tuple(lo), hi=tuple(hi), label=label, size=size, explode=float(explode), fw=fw, **extra)

    Y, y = {}, 0.0
    for name, t in STACK:
        Y[name] = (y, y + t)
        y += t + GAP

    gx0, gz0, gx1, gz1 = px0, pz0, px0 + gw, pz0 + gh
    ax0, az1 = gx0 + PANEL["off"][0], gz1 - PANEL["off"][1]
    active = (ax0, az1 - ah, ax0 + aw, az1)
    o = OPEN_MARGIN
    opening = (active[0] - o, active[1] - o, active[2] + o, active[3] + o)
    gcx, gcz = (gx0 + gx1) / 2, (gz0 + gz1) / 2
    part("Lens", (opening[0], 0.0, opening[1]), (opening[2], FACE, opening[3]), "Cover glass", "clear acrylic over the screen", 62)
    part("Panel", (gx0, Y["panel"][0], gz0), (gx1, Y["panel"][1], gz1), '3.2" ILI9341 TFT, 320 x 240',
         "active %g x %g mm, SPI" % (aw, ah), 18, fw="display", active=active)
    bw, bh = 50.0, 34.0
    part("Foam", (gcx - bw / 2, Y["foam"][0], gcz - bh / 2), (gcx + bw / 2, Y["foam"][1], gcz + bh / 2), "Foam pad", "0.3 thick", 8)
    part("Battery", (gcx - bw / 2, Y["battery"][0], gcz - bh / 2), (gcx + bw / 2, Y["battery"][1], gcz + bh / 2),
         "503450 LiPo, about 1000 mAh", "50 x 34 x 5", 0, fw="power")

    # key column: TALK, 5-way ring + OK, BACK spread over the panel's height; status light top-right
    cx = px0 + CX_FROM_PANEL
    top, bottom = gz0 + 51.0, gz0 + 4.0
    g = (top - bottom - (7.5 + 18.0 + 8.5)) / 2
    talk_z, ring_z, back_z = top - 3.75, top - 7.5 - g - 9.0, bottom + 4.25
    sw = (Y["board"][0] - GAP - SW_H, Y["board"][0] - GAP)
    pe = sw[0] - SW_GAP
    keys = {
        "TALK": dict(shape="pill", x=cx, z=talk_z, w=20.0, h=7.5, front=-lift, plunger_r=1.5, switch="SwTalk"),
        "Ring": dict(shape="ring", x=cx, z=ring_z, r=9.0, r_in=4.6, front=-lift, tube=(4.4, 5.0), switch="Sw5Way"),
        "OK": dict(shape="disc", x=cx, z=ring_z, r=4.0, front=-lift - 0.4, plunger_r=2.0, switch="Sw5Way"),
        "BACK": dict(shape="disc", x=cx, z=back_z, r=4.25, front=-lift - 0.4, plunger_r=1.5, switch="SwBack"),
    }
    names = {"TALK": ("TALK key", "hold to talk"), "Ring": ("5-way ring", "up / down / left / right"),
             "OK": ("OK key", "centre of the 5-way"), "BACK": ("BACK key", "go back")}
    for name, k in keys.items():
        hw = k["w"] / 2 if k["shape"] == "pill" else k["r"]
        hh = k["h"] / 2 if k["shape"] == "pill" else k["r"]
        k["plunger_end"] = pe
        part(name, (k["x"] - hw, k["front"], k["z"] - hh), (k["x"] + hw, pe, k["z"] + hh), *names[name], 80, fw="input", key=k)
    for name, z, s in (("SwTalk", talk_z, 6.0), ("Sw5Way", ring_z, 10.0), ("SwBack", back_z, 6.0)):
        part(name, (cx - s / 2, sw[0], z - s / 2), (cx + s / 2, sw[1], z + s / 2),
             "5-way switch" if s == 10.0 else "Tact switch", "%g x %g x %g" % (s, s, SW_H), -12, fw="input")
    led = (cx + 8.7, gz0 + 53.5)
    part("LightPipe", (led[0] - 0.9, -lift + 0.5, led[1] - 0.9), (led[0] + 0.9, Y["board"][0] - 2 * GAP - 0.8, led[1] + 0.9),
         "Status light", "light pipe over an LED", 80, fw="ui", r=0.9)
    ref, reb = max(d["ef"] - FACE, 0.4), max(d["eb"] - FACE, 0.4)
    spk_c, slit_y = H / 2 - 4.0, 7.3
    sx1 = x_right(ol, spk_c - 7.5, spk_c + 7.5, SIDE + max(edge_clear(slit_y - 5.5 - FACE, ref), edge_clear(D - FACE - slit_y - 5.5, reb)) + 0.1, W)
    part("KeySheet", (gx1 + GAP, FACE + GAP, gz0 + 2.0), (min(W - 6.0, sx1 - 3.5 - GAP), FACE + GAP + 0.8, top + 1.0), "Rubber key sheet", "0.8 thick", 30,
         holes=[(cx, talk_z, 1.5 + GAP), (cx, ring_z, 5.0 + GAP), (cx, back_z, 1.5 + GAP)])

    # board and what sits on it
    by = (Y["board"][0] + Y["board"][1]) / 2
    uz = H / 2 + 15.5 if d.get("usb_up") else H / 2 - 16.5
    ux1 = x_right(ol, uz - 4.47, uz + 4.47, SIDE + edge_clear(D - FACE - (by + 1.63), reb) + 0.15, W)
    usb = (ux1 - 7.4, uz - 4.47, ux1, uz + 4.47)
    part("USBC", (usb[0], by - 1.63, usb[1]), (usb[2], by + 1.63, usb[3]), "USB-C", "charging and data", -12, fw="power")
    part("Board", (5.2, Y["board"][0], 2.0), (min(W - 5.9, sx1 - 3.5 - GAP), Y["board"][1], H - 2.0), "Main board", "1.0 thick, black", -12,
         notch=(usb[0] - GAP, usb[1] - GAP, W, usb[3] + GAP))
    mnear = SIDE + edge_clear(D - FACE - Y["module"][1], max(d["eb"] - FACE, 0.4)) + 0.2      # module's back face is near the back round
    mz1 = min(z_top(ol, x, mnear, H) for x in (gcx - 9.0, gcx, gcx + 9.0)) - 0.5
    part("Module", (gcx - 9.0, Y["module"][0], mz1 - 25.5), (gcx + 9.0, Y["module"][1], mz1), "ESP32-S3 module",
         "16 MB flash, 8 MB PSRAM, Wi-Fi", -12, fw="runtime")
    part("Amp", (gcx + 14.0, Y["module"][0], gz0 + 5.0), (gcx + 17.0, Y["module"][0] + 0.9, gz0 + 8.0), "MAX98357A amp", "I2S audio out", -12, fw="audio out")
    part("Charger", (W - 15.5, Y["module"][0], gz0 + 7.0), (W - 12.5, Y["module"][0] + 0.9, gz0 + 10.0), "Charger + protection", "USB-C to LiPo", -12, fw="power")
    cy = (Y["board"][0] - GAP - 0.8, Y["board"][0] - GAP)
    part("Connector", (gx1 - 7.7, cy[0], gcz - 7.0), (gx1 - 4.7, cy[1], gcz + 7.0), "Screen connector", "FPC, 0.5 mm pitch", -12, fw="display")
    part("FPC", (gx1 - 6.6, Y["panel"][1] + GAP, gcz - 6.0), (gx1 - 6.3, cy[0] - GAP, gcz + 6.0), "Screen ribbon", "folds behind the panel", 18, fw="display")
    mic_y = 7.28
    mic_top = min(z_top(ol, x, SIDE + GAP, H) for x in (cx - 2.36, cx, cx + 2.36))
    part("Mic", (cx - 2.36, mic_y - 1.88, mic_top - 1.0), (cx + 2.36, mic_y + 1.88, mic_top), "INMP441 mic", "I2S, port in the top edge", -12, fw="audio in")
    part("Speaker", (sx1 - 3.5, slit_y - 5.5, spk_c - 7.5), (sx1, slit_y + 5.5, spk_c + 7.5), "Speaker", "15 x 11 mm, fires out the right side", -12, fw="audio out")

    def post_at(sx, sz):
        x, z = sx, sz
        n = math.hypot(W / 2 - sx, H / 2 - sz)
        while sdist(ol, x, z) < SIDE + POST_R - 0.3:        # slide toward the middle until it sits against the wall
            x, z = x + 0.2 * (W / 2 - sx) / n, z + 0.2 * (H / 2 - sz) / n
        return x, z

    posts = []
    for seeds in (((3.2, 7.0),), ((3.2, H - 7.0),), ((W - 3.5, 7.0),), tuple((W - 3.5, H - 7.0 - k) for k in range(0, 14, 2))):
        for sx, sz in seeds:                                 # first spot that keeps clear of the status-light pipe
            x, z = post_at(sx, sz)
            if math.hypot(x - led[0], z - led[1]) >= POST_R + 0.9 + 0.3:
                break
        posts.append((round(x, 2), round(z, 2)))
    # sink the screw heads (r 1.9) until they clear the rounded back edge at every post
    sink = 1.2
    while sink < 3.0 and min(sdist(ol, x, z) for x, z in posts) - 1.9 - 0.1 < edge_clear(sink, d["eb"]):
        sink += 0.1
    part("Screws", (min(x for x, _ in posts) - 1.9, 6.5, min(z for _, z in posts) - 1.9),
         (max(x for x, _ in posts) + 1.9, D - sink, max(z for _, z in posts) + 1.9), "4 x M2 screws", "from the back into the front tub", -46)
    part("Caps", (min(x for x, _ in posts) - 2.0, D - sink + 0.1, min(z for _, z in posts) - 2.0),
         (max(x for x, _ in posts) + 2.0, D, max(z for _, z in posts) + 2.0), "4 screw caps", "press-fit, body colour, flush with the back", -53)
    part("FrontShell", (0, 0, 0), (W, SPLIT, H), "Front shell", d["title"], 44)
    part("BackShell", (0, SPLIT + GAP, 0), (W, D, H), "Back cover", "%s, 4 screw bosses" % d["title"], -28)

    back = D + GAP + (0.15 if d.get("stickers") else 0.0)    # the closed stand rests on the stickers
    if d.get("back_panel"):
        bp = d["back_panel"]
        part("BackPanel", (bp["inset"], back, bp["inset"]), (W - bp["inset"], back + bp["proud"], H - bp["inset"]), "Back panel", "walnut veneer", -32)
        back += bp["proud"] + GAP
    if d.get("plate"):
        pl = d["plate"]
        part("FacePlate", (pl["inset"], -plate - GAP, pl["inset"]), (W - pl["inset"], -GAP, H - pl["inset"]), "Face plate", "brushed aluminium", 52)

    st = d["stand"]
    zh = st["zh"] * H
    s = dict(kind=st["kind"], x=W / 2, zh=zh, width=st["width"], barrel=1.0, thick=1.4, y=back,
             length=zh * math.cos(math.radians(TILT)) + 1.5)
    part("Stand", (s["x"] - s["width"] / 2, back, zh - s["length"]), (s["x"] + s["width"] / 2, back + 2.0, zh + s["barrel"]),
         "Kickstand", "opens to stand the device at %g deg" % TILT, -60, stand=s)

    grille = []                                              # cosmetic diagonal grooves on the back (arcade): 1.4 x 13 at 45 deg
    if d.get("slots"):                                       # (the speaker vents through the side; stickers may run over them)
        grille = [(W - 30 + i * 3.4, 13 + i * 1.2) for i in range(d["slots"]["n"])]
    fronts = []
    for png, side, below, w, rot in d.get("front_stickers", []):
        fronts.append((png, (opening[0] + 12.0 if side < 0 else opening[2] - 12.0, opening[1] - below, w)))
    ears = [(W * e, H - 3.0) for e in ((d["ears"]["inset"], 1 - d["ears"]["inset"]) if d.get("ears") else ())]
    return dict(design=d, W=W, H=H, D=D, m=m, outline=ol, ef=d["ef"], eb=d["eb"], parts=parts, keys=keys,
                posts=posts, Y=Y, stack_mm=sum(t for _, t in STACK) + FACE, opening=opening, cx=cx, led=led,
                slits=[spk_c - 5.5 + i * 2.75 for i in range(5)], slit_y=slit_y, mic=(cx, mic_y), stand=s, screw_sink=round(sink, 2),
                front_stickers=fronts, ears=ears, lift=lift, grooves=grille)


def _fits(L):
    d, ol, P = L["design"], L["outline"], L["parts"]
    # the panel's front face sits GAP behind the front wall, inside the cavity's rounded front edge
    need = SIDE + edge_clear(P["Panel"]["lo"][1] - FACE, max(d["ef"] - FACE, 0.4)) + 1e-3
    pts = [(x, z) for x in (P["Panel"]["lo"][0], P["Panel"]["hi"][0]) for z in (P["Panel"]["lo"][2], P["Panel"]["hi"][2])]
    if any(sdist(ol, x, z) < need for x, z in pts):
        return False
    o = L["opening"]
    front = [(x, z) for x in (o[0], o[2]) for z in (o[1], o[3])]
    for k in L["keys"].values():
        r = (k["w"] / 2 if k["shape"] == "pill" else k["r"]) + KEY_GAP
        rz = (k["h"] / 2 + KEY_GAP) if k["shape"] == "pill" else r
        front += [(k["x"] + r * math.cos(a), k["z"] + rz * math.sin(a)) for a in (i * math.pi / 8 for i in range(16))]
    front += [(L["led"][0] + 1.1 * math.cos(a), L["led"][1] + 1.1 * math.sin(a)) for a in (i * math.pi / 4 for i in range(8))]
    return all(sdist(ol, x, z) >= d["ef"] + 0.3 for x, z in front)


def layout(name):
    d = DESIGNS[name]
    for i in range(300):
        L = _place(d, 1.8 + 0.1 * i)
        if _fits(L):
            L["name"] = name
            return L
    raise ValueError("layout: the core does not fit design %s" % name)
