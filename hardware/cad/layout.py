"""Layout of the pocket device for one screen size, in mm.

Pure Python (no bpy): build_device.py turns it into meshes and test_layout.py checks it in
a second. Axes: x = width (left to right), z = height (bottom to top), y = depth (front
face y = 0, back face y = D). Every part is an axis-aligned box given by lo / hi corners;
Blender rounds the look and the build-time checks then test the real meshes.
"""
import math

PANELS = {  # glass (w, h, t), active (w, h), active-area offset from the glass top-left (FPC end right)
    "2.8": {"glass": (69.2, 50.0, 2.5), "active": (57.6, 43.2), "off": (3.2, 3.4)},
    "2.4": {"glass": (60.26, 42.72, 2.5), "active": (48.96, 36.72), "off": (3.0, 3.0)},
}
TARGETS = {"2.8": (109.0, 64.0), "2.4": (100.0, 56.0)}   # approved body W x H

FRAME, GAP_COL, COL_W, BAND = 5.5, 5.0, 24.0, 8.0         # front layout
D, FACE, SIDE = 15.0, 1.2, 1.5                             # depth, front/back wall, side wall
GAP = 0.05                                                 # between parts that touch by design
R_CORNER, EDGE_FRONT, EDGE_BACK = 7.0, 2.5, 4.0            # plan corners, pebble edges
SPLIT = D - 2.6                                            # front tub | back cover
STACK = (("lens", FACE), ("panel", 2.5), ("foam", 0.3), ("battery", 5.0), ("board", 1.0), ("module", 3.1))
KEY_GAP, KEY_LIFT = 0.3, 0.6                               # key-to-opening clearance, key height above the face
SW_H, SW_GAP = 3.5, 0.3                                    # tact switch height, plunger-to-switch gap
POST_R, BORE_R = 1.7, 0.8                                  # screw posts, screw bores
LENS_BOTTOM = 3.0                                          # lens covers the screen and the logo band

# parts that must sit inside the shell cavity (shells, lens, keys, light pipe and screws pass through openings)
INTERNAL = ("Panel", "Foam", "Battery", "Board", "Module", "Amp", "Charger", "USBC", "Connector", "FPC",
            "Mic", "Speaker", "SwTalk", "Sw5Way", "SwBack", "KeySheet")


def layout(screen):
    p = PANELS[screen]
    gw, gh, gt = p["glass"]
    aw, ah = p["active"]
    W = FRAME + gw + GAP_COL + COL_W + FRAME
    H = FRAME + gh + BAND
    parts = {}

    def part(name, lo, hi, label, size, explode, **extra):
        parts[name] = dict(lo=tuple(lo), hi=tuple(hi), label=label, size=size, explode=float(explode), **extra)

    Y, y = {}, 0.0
    for name, t in STACK:                                   # depth stack, front to back, GAP apart
        Y[name] = (y, y + t)
        y += t + GAP

    gx0, gz1 = FRAME, H - FRAME                             # glass top-left
    gx1, gz0 = gx0 + gw, gz1 - gh
    gcx, gcz = (gx0 + gx1) / 2, (gz0 + gz1) / 2
    ax0, az1 = gx0 + p["off"][0], gz1 - p["off"][1]
    active = (ax0, az1 - ah, ax0 + aw, az1)
    part("Lens", (gx0, 0.0, LENS_BOTTOM), (gx1, FACE, gz1), "Front lens", "dark acrylic, %.1f thick" % FACE, 62, window=active)
    part("Panel", (gx0, Y["panel"][0], gz0), (gx1, Y["panel"][1], gz1), '%s" ILI9341 TFT, 320 x 240' % screen,
         "glass %g x %g x %g, active %g x %g" % (gw, gh, gt, aw, ah), 18, active=active)

    bw, bh = 50.0, 34.0                                     # 503450 cell behind the panel
    part("Foam", (gcx - bw / 2, Y["foam"][0], gcz - bh / 2), (gcx + bw / 2, Y["foam"][1], gcz + bh / 2), "Foam pad", "0.3 thick", 8)
    part("Battery", (gcx - bw / 2, Y["battery"][0], gcz - bh / 2), (gcx + bw / 2, Y["battery"][1], gcz + bh / 2),
         "503450 LiPo, about 1000 mAh", "50 x 34 x 5", 0)

    # control column: TALK, 5-way ring + OK, BACK spread evenly; status light top-right
    cx0 = gx1 + GAP_COL
    cx = cx0 + COL_W / 2
    top, bottom = H - 9.0, 6.0
    g = (top - bottom - (7.5 + 18.0 + 8.5)) / 2
    talk_z, ring_z, back_z = top - 3.75, top - 7.5 - g - 9.0, bottom + 4.25
    sw = (Y["board"][0] - GAP - SW_H, Y["board"][0] - GAP)  # switch body; actuator faces the front
    pe = sw[0] - SW_GAP                                     # plunger end
    keys = {
        "TALK": dict(shape="pill", x=cx, z=talk_z, w=20.0, h=7.5, front=-KEY_LIFT, plunger_r=1.5, switch="SwTalk"),
        "Ring": dict(shape="ring", x=cx, z=ring_z, r=9.0, r_in=4.6, front=-KEY_LIFT, tube=(4.4, 5.0), switch="Sw5Way"),
        "OK": dict(shape="disc", x=cx, z=ring_z, r=4.0, front=-1.0, plunger_r=2.0, switch="Sw5Way"),
        "BACK": dict(shape="disc", x=cx, z=back_z, r=4.25, front=-KEY_LIFT, plunger_r=1.5, switch="SwBack"),
    }
    names = {"TALK": ("TALK key", "20 x 7.5 pill, hold to talk"), "Ring": ("5-way ring", "18 across, up / down / left / right"),
             "OK": ("OK key", "8 across, centre of the 5-way"), "BACK": ("BACK key", "8.5 across")}
    for name, k in keys.items():
        hw = k["w"] / 2 if k["shape"] == "pill" else k["r"]
        hh = k["h"] / 2 if k["shape"] == "pill" else k["r"]
        k["plunger_end"] = pe
        part(name, (k["x"] - hw, k["front"], k["z"] - hh), (k["x"] + hw, pe, k["z"] + hh), *names[name], 78, key=k)
    for name, z, s in (("SwTalk", talk_z, 6.0), ("Sw5Way", ring_z, 10.0), ("SwBack", back_z, 6.0)):
        part(name, (cx - s / 2, sw[0], z - s / 2), (cx + s / 2, sw[1], z + s / 2),
             "5-way switch" if s == 10.0 else "Tact switch", "%g x %g x %g" % (s, s, SW_H), -12)
    led = (W - 9.0, H - 5.0)
    part("LightPipe", (led[0] - 0.9, -0.1, led[1] - 0.9), (led[0] + 0.9, Y["board"][0] - 2 * GAP - 0.8, led[1] + 0.9),
         "Status light pipe", "1.8 across, clear", 78, r=0.9)
    part("KeySheet", (cx0 + 0.5, FACE + GAP, 4.0), (W - 6.0, FACE + GAP + 0.8, H - 7.5), "Rubber key sheet", "0.8 thick", 30,
         holes=[(cx, talk_z, 1.5 + GAP), (cx, ring_z, 5.0 + GAP), (cx, back_z, 1.5 + GAP)])

    # main board and what sits on it
    by = (Y["board"][0] + Y["board"][1]) / 2
    usb = (W - 9.05, 14.0 - 4.47, W - 1.65, 14.0 + 4.47)    # x0, z0, x1, z1
    part("USBC", (usb[0], by - 1.63, usb[1]), (usb[2], by + 1.63, usb[3]), "USB-C receptacle", "8.94 x 7.35 x 3.26, mid-mount", -12)
    part("Board", (FRAME, Y["board"][0], 2.0), (W - 5.9, Y["board"][1], H - 2.0), "Main board",
         "%.1f x %.1f x 1.0, black" % (W - 5.9 - FRAME, H - 4.0), -12, notch=(usb[0] - GAP, usb[1] - GAP, W, usb[3] + GAP))
    mz1 = H - 3.5                                           # antenna end at the top edge
    part("Module", (gcx - 9.0, Y["module"][0], mz1 - 25.5), (gcx + 9.0, Y["module"][1], mz1), "ESP32-S3-WROOM-1 N16R8",
         "18 x 25.5 x 3.1, antenna at the top edge", -12)
    part("Amp", (gcx + 14.0, Y["module"][0], 8.0), (gcx + 17.0, Y["module"][0] + 0.9, 11.0), "MAX98357A amp", "3 x 3", -12)
    part("Charger", (W - 15.5, Y["module"][0], 10.0), (W - 12.5, Y["module"][0] + 0.9, 13.0), "Charger + protection", "TP4056 + DW01 class", -12)
    cy = (Y["board"][0] - GAP - 0.8, Y["board"][0] - GAP)
    part("Connector", (gx1 + 0.5, cy[0], gcz - 7.0), (gx1 + 3.5, cy[1], gcz + 7.0), "FPC connector", "0.5 mm pitch", -12)
    fx = gx1 + 1.5
    segs = [((gx1 + GAP, Y["panel"][1] - 0.3, gcz - 6.0), (fx + 0.3, Y["panel"][1], gcz + 6.0)),
            ((fx, Y["panel"][1], gcz - 6.0), (fx + 0.3, cy[0] - GAP, gcz + 6.0))]
    part("FPC", segs[0][0], segs[1][1], "Display FPC", "12 wide, folds back to the board", 18, segs=segs)
    mic_y = 7.28
    part("Mic", (cx - 2.36, mic_y - 1.88, H - SIDE - GAP - 1.0), (cx + 2.36, mic_y + 1.88, H - SIDE - GAP),
         "INMP441 mic", "4.72 x 3.76, port in the top edge", -12)
    slit_y = 7.3
    part("Speaker", (W - 5.85, slit_y - 5.5, 20.5), (W - 2.35, slit_y + 5.5, 35.5), "Micro speaker",
         "15 x 11 x 3.5, fires out of the right side", -12)

    posts = [(3.5, 7.0), (3.5, H - 7.0), (W - 3.5, 7.0), (W - 3.5, H - 7.0)]
    part("Screws", (1.6, 6.5, 5.1), (W - 1.6, D - 1.2, H - 5.1), "4 x M2 screws", "from the back into the front tub", -46)
    part("FrontShell", (0, 0, 0), (W, SPLIT, H), "Front shell", "matte plastic, %.1f side walls" % SIDE, 44)
    part("BackShell", (0, SPLIT + GAP, 0), (W, D, H), "Back cover", "2.6 deep, 4 screw bosses", -28)
    part("BackLabel", (W / 2 - 22, D + 0.11, 10.5), (W / 2 + 22, D + 0.23, 13.5), "Back label", "second brain · SB-1 · 5V 1A", -28)

    return dict(screen=screen, W=W, H=H, D=D, parts=parts, keys=keys, posts=posts, Y=Y,
                stack_mm=sum(t for _, t in STACK) + FACE, slits=[22.0 + i * 2.75 for i in range(5)], slit_y=slit_y,
                mic=(cx, mic_y), band_z=(LENS_BOTTOM + gz0) / 2)


def _inside_pebble(L, p, side, face):
    """Point inside the body shape shrunk by side (plan) and face (front / back): a rounded
    rectangle in plan whose front and back edges are rounded EDGE_FRONT / EDGE_BACK, less the wall."""
    x, y, z = p
    W, H = L["W"], L["H"]
    r = R_CORNER - side
    qx = abs(x - W / 2) - ((W - 2 * side) / 2 - r)
    qz = abs(z - H / 2) - ((H - 2 * side) / 2 - r)
    d = r - math.hypot(max(qx, 0.0), max(qz, 0.0)) - min(max(qx, qz), 0.0)   # distance to the plan outline, + inside
    if d < 0 or not face <= y <= D - face:
        return False
    for t, re in ((y - face, EDGE_FRONT - face), (D - face - y, EDGE_BACK - face)):
        if d < re and t < re and math.hypot(re - d, re - t) > re:
            return False
    return True


def inside_cavity(L, p):
    """True if point p = (x, y, z) is inside the shell's inner space."""
    return _inside_pebble(L, p, SIDE, FACE)


def inside_body(L, p):
    """True if point p is inside the outer body shape (nothing may stick out of it)."""
    return _inside_pebble(L, p, 0.0, 0.0)
