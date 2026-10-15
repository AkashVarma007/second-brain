"""The six case designs, as pure data (no bpy): layout.py fits the core into each outline and
build_device.py turns the rest into meshes and materials. Colours are sRGB hex.

pad = (extra width, extra bottom, extra top) in mm on top of the fitted panel margin.
Sticker positions: (png, dx, z, width, rot) — dx from the body's centre line (world x, so on the
back a positive dx appears on the left), z from the bottom, width in mm, rot in radians.
Front stickers: (png, side -1 | 1, mm below the screen opening, width, rot), near that lower corner.
"""


def M(color, rough=0.5, metal=0.0, coat=0.0, kind=None, emit=0.0):
    return dict(color=color, rough=rough, metal=metal, coat=coat, kind=kind, emit=emit)


BRASS = M("#C9A45C", 0.22, 1.0)
STEEL = M("#9DA3A8", 0.25, 1.0)
INK = M("#1D1823", 0.6)

DESIGNS = {
    "walnut": dict(
        title="Walnut & brass", mood="classy",
        blurb="Anodised graphite body, walnut back panel, brass keys and a brass kickstand.",
        outline=("rrect", 6.0), ef=1.2, eb=2.5,
        body=M("#2E2E33", 0.32, 0.7),
        keys=dict(talk=BRASS, icon=M("#2A1A10", 0.6), ring=M("#3A3A40", 0.3, 0.7), arrow=BRASS, ok=BRASS,
                  back=BRASS, led=M("#FFD9A0", emit=5.0)),
        back_panel=dict(inset=6.0, proud=0.9, mat=M("#7A4E2D", 0.45, coat=0.3, kind="wood")),
        engrave=dict(text="second brain", size=4.2, z=-9.5, mat=M("#2A1A10", 0.6)),   # z < 0: from the top, above the stand hinge
        stand=dict(kind="plate", zh=0.74, width=26.0, mat=BRASS)),
    "instrument": dict(
        title="Field instrument", mood="classy-tech",
        blurb="Brushed aluminium face plate with hex screws and dial ticks, dark body, steel wire stand.",
        outline=("rrect", 3.0), ef=0.8, eb=1.5, pad=(4.0, 2.0, 2.0),
        body=M("#2B2D31", 0.5),
        plate=dict(inset=0.6, thick=0.8, mat=M("#C8CCD0", 0.3, 1.0, kind="brushed"), screws=STEEL, ticks=M("#2B2D31", 0.5)),
        keys=dict(talk=M("#FF5A1F", 0.35, coat=0.3), icon=M("#2B2D31", 0.5), ring=M("#2B2D31", 0.5),
                  arrow=M("#C8CCD0", 0.3, 1.0), ok=M("#C8CCD0", 0.3, 1.0), back=M("#2B2D31", 0.5), led=M("#FF7A2E", emit=6.0)),
        engrave=dict(text='SB-1  FIELD UNIT  3.2"', size=3.0, z=14.0, mat=M("#C8CCD0", 0.3, 1.0)),
        stand=dict(kind="wire", zh=0.74, width=60.0, mat=STEEL)),
    "arcade": dict(
        title="Arcade pocket", mood="funky",
        blurb="Cream two-tone body with one big corner, slot grille, PLAYER 1 stickers and a ribbed tab stand.",
        outline=("rrect", (4.0, 16.0, 4.0, 4.0)), ef=2.0, eb=2.5, usb_up=True,
        body=M("#EDE4D3", 0.45, coat=0.2),
        keys=dict(talk=M("#FF4F7B", 0.35, coat=0.3), icon=INK, ring=M("#4B3B8F", 0.4), arrow=M("#EDE4D3", 0.45),
                  ok=M("#FFD23F", 0.35, coat=0.3), back=M("#4B3B8F", 0.4), led=M("#2EC4B6", emit=6.0)),
        slots=dict(n=6, depth=0.6),
        stickers=[("player1", 22.0, 38.0, 22.0, 0.12), ("nog", -31.0, 36.0, 24.0, -0.08), ("stripes", 26.0, 14.0, 36.0, 0.0),
                  ("bolt", -38.0, 20.0, 9.0, 0.3)],                         # stripes run over the (cosmetic) grooves
        stand=dict(kind="tab", zh=0.74, width=28.0, mat=M("#4B3B8F", 0.4), sticker=("press", 22.0, 0.55))),
    "clear": dict(
        title="See-through", mood="funky",
        blurb="Tinted clear shell showing the board, battery and wiring, neon keys, clear acrylic stand.",
        outline=("rrect", 7.0), ef=2.5, eb=4.0,
        body=M("#7FD6CC", 0.1, kind="clear"),
        keys=dict(talk=M("#FF3EA5", 0.35, coat=0.3), icon=INK, ring=M("#2EC4B6", 0.35, coat=0.3), arrow=M("#FFFFFF", 0.4),
                  ok=M("#FFD23F", 0.35, coat=0.3), back=M("#2EC4B6", 0.35, coat=0.3), led=M("#FFFFFF", emit=6.0)),
        stickers=[("barcode", 26.0, 14.0, 16.0, 0.0), ("holo", -22.0, 50.0, 22.0, -0.06)],
        stand=dict(kind="plate", zh=0.74, width=26.0, mat=M("#E8F7F5", 0.05, kind="clear"))),
    "egg": dict(
        title="Pet egg", mood="funny",
        blurb="Squircle body with little ears, blush cheeks, a big NOG sticker and a paw-print stand.",
        outline=("squircle", 5.0), ef=3.0, eb=5.0, pad=(0.0, 2.0, 0.0),
        body=M("#F6C9A8", 0.5, coat=0.2),
        keys=dict(talk=M("#FF6B6B", 0.35, coat=0.3), icon=INK, ring=M("#8FD9B6", 0.4, coat=0.3), arrow=M("#FFFFFF", 0.4),
                  ok=M("#FFD23F", 0.35, coat=0.3), back=M("#8FD9B6", 0.4, coat=0.3), led=M("#FF8FC8", emit=6.0)),
        ears=dict(r=7.5, inset=0.27),
        front_stickers=[("cheek", -1, 3.5, 10.0, 0.0), ("cheek", 1, 3.5, 10.0, 0.0)],
        stickers=[("nog", 30.0, 40.0, 30.0, 0.0), ("talk", -30.0, 18.0, 22.0, -0.1)],
        stand=dict(kind="plate", zh=0.72, width=30.0, mat=M("#8FD9B6", 0.4, coat=0.3), sticker=("paw", 14.0, 0.6))),
    "bomb": dict(
        title="Sticker bomb", mood="funny",
        blurb="Matte black body covered in stickers, neon keys, a black stand with a bolt.",
        outline=("rrect", 7.0), ef=2.5, eb=4.0,
        body=M("#17161A", 0.75),
        keys=dict(talk=M("#E6FF3A", 0.35, coat=0.3), icon=M("#17161A", 0.75), ring=M("#17161A", 0.75), arrow=M("#FFFFFF", 0.4),
                  ok=M("#FF3EA5", 0.35, coat=0.3), back=M("#2A292E", 0.6), led=M("#E6FF3A", emit=6.0)),
        stickers=[("holo", 21.0, 49.0, 24.0, -0.08), ("talk", -23.0, 47.0, 20.0, 0.12), ("fragile", 7.0, 31.0, 26.0, 0.05),
                  ("hundred", -29.0, 23.0, 17.0, -0.2), ("barcode", 29.0, 14.0, 18.0, 0.1), ("smiley", -5.0, 13.0, 13.0, 0.25),
                  ("bolt", 37.0, 34.0, 8.0, -0.3), ("nog", -10.0, 33.0, 14.0, -0.15), ("player1", -40.0, 43.0, 11.0, 0.2)],
        stand=dict(kind="plate", zh=0.74, width=26.0, mat=M("#17161A", 0.75), sticker=("bolt", 8.0, 0.55))),
}
