"""Parametric 3D model of the Second Brain pocket device (v1: 2.8" and 2.4" screens).

Builds every part at real size from layout.py, runs the build-time checks (checks.py),
saves out/<28|24>/device.blend + device.glb + dims.json and renders the views.

    blender -b --python-exit-code 1 -P hardware/cad/build_device.py -- --screen 2.8
            [--samples 48] [--only hero,front,right,top,back,exploded] [--no-render]
    blender -b --python-exit-code 1 -P hardware/cad/build_device.py -- --shared [--samples 48]
            (out/shared/compare.png + scale.png: both sizes, a credit card and a phone)

Axes: X = width (left to right), Z = height (bottom to top), Y = depth (front face at
y = 0, back at y = D). Units are millimetres (1 BU = 1 mm).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import checks  # noqa: E402  (needs HERE on sys.path)
import layout as LY  # noqa: E402

FINISHES = {   # the viewer recolours the "body" and "ring" materials; renders use graphite
    "graphite": {"body": "#2B2731", "ring": "#3A3540"},
    "chalk": {"body": "#E8E3DA", "ring": "#CFC8BD"},
    "amber": {"body": "#E0913A", "ring": "#2B2731"},
}
COLORS = {
    "talk": "#FF6B6B", "ok": "#FFA14A", "mint": "#6EE7A8", "label": "#F3E9DA", "cream": "#F3E9DA",
    "mask": "#0E0C12", "glass": "#17131C", "black": "#141216", "rubber": "#3A3540", "foam": "#3B3742",
    "metal": "#B9BDC2", "battery": "#C9CCD1", "fpc": "#B8621C", "card": "#D8D2C8", "phone": "#3A3A40",
}
SCREEN_IMG = os.path.join(HERE, "screens", "home.png")
ORTHO_FRONT, ORTHO_SIDE = 150.0, 90.0          # one scale for both sizes, so the renders compare

# NOG (happy) pixel rows from the design system's Nog component
NOG = [".......########.......", ".....##hh......##.....", "....#..ff.ff.ff..#....", "...#..f..f..f..f..#...",
       "..#.h..............#..", "..#................#..", ".#..................#.", ".#....e........e....#.",
       ".#...e.e......e.e...#.", ".#..cc..........cc..#.", ".#.......eeee.......#.", ".#........ee........#.",
       "..#................#..", "..#................#..", "...##............##...", ".....############.....",
       "......##......##......", "......##......##......"]


# --- Helpers -----------------------------------------------------------------
def hex_rgba(h, a=1.0):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, a)


_mats = {}


def mat(name, color, rough=0.5, metal=0.0, emit=0.0, coat=0.0, image=None, alpha=1.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = hex_rgba(color)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    if emit:
        bsdf.inputs["Emission Color"].default_value = hex_rgba(color)
        bsdf.inputs["Emission Strength"].default_value = emit
    if image and os.path.exists(image):
        tex = m.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(image)
        tex.interpolation = "Closest"          # keep pixels crisp
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        m.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.2
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    _mats[name] = m
    return m


def link(ob, coll=None):
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def box_mesh(name, sx, sy, sz):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= sx
        v.co.y *= sy
        v.co.z *= sz
    bm.to_mesh(me)
    bm.free()
    return me


def rbox(name, size, loc, r_corner=0.0, r_edge=0.0, material=None, coll=None, segs=12, axis="Y"):
    """Box centred at loc; r_corner rounds the edges running along `axis` (Y = plan corners
    seen from the front, X = corners seen from the side), r_edge rounds the rest."""
    k = "xyz".index(axis.lower())
    others = [i for i in range(3) if i != k]
    me = box_mesh(name, *size)
    ob = link(bpy.data.objects.new(name, me), coll)
    ob.location = loc
    if r_corner:
        attr = me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
        for e in me.edges:
            a, b = me.vertices[e.vertices[0]].co, me.vertices[e.vertices[1]].co
            attr.data[e.index].value = 1.0 if all(abs(a[i] - b[i]) < 1e-6 for i in others) else 0.0
        m = ob.modifiers.new("corners", "BEVEL")
        m.limit_method = "WEIGHT"
        m.width = min(r_corner, size[others[0]] / 2 - 1e-3, size[others[1]] / 2 - 1e-3)
        m.segments = segs
    if r_edge:
        m = ob.modifiers.new("edges", "BEVEL")
        m.limit_method = "ANGLE"
        m.angle_limit = math.radians(60)
        m.width = r_edge
        m.segments = 4
    if material:
        ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def cyl(name, r, depth, loc, material=None, coll=None, axis="Y", verts=48):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts, radius1=r, radius2=r, depth=depth)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me), coll)
    ob.location = loc
    if axis == "Y":
        ob.rotation_euler = (math.radians(90), 0, 0)
    elif axis == "X":
        ob.rotation_euler = (0, math.radians(90), 0)
    if material:
        ob.data.materials.append(material)
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def ring(name, r_out, r_in, depth, loc, material, coll=None):
    outer = cyl(name, r_out, depth, loc, material, coll)
    inner = cyl(name + "_hole", r_in, depth + 2, loc, coll=coll)
    m = outer.modifiers.new("hole", "BOOLEAN")
    m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", inner
    bake(outer)
    bpy.data.objects.remove(inner)
    return outer


def text(name, body, size, loc, material, coll=None, extrude=0.12, align="CENTER", rot_z=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    cu.align_y = "CENTER"
    ob = link(bpy.data.objects.new(name, cu), coll)
    ob.location = loc
    ob.rotation_euler = (math.radians(90), 0, rot_z)   # face -Y (the front)
    ob.data.materials.append(material)
    return ob


def arrow(name, size, loc, angle, material, coll=None):
    """Small triangular key arrow on the front face, pointing up when angle = 0."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    pts = [(0, size * 0.5), (-size * 0.55, -size * 0.35), (size * 0.55, -size * 0.35)]
    for y in (-0.1, 0.1):
        for px, pz in pts:
            bm.verts.new((px, y, pz))
    bm.verts.ensure_lookup_table()
    v = bm.verts
    for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
        bm.faces.new([v[i] for i in f])
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me), coll)
    ob.location = loc
    ob.rotation_euler = (0, angle, 0)   # rotate within the front plane
    ob.data.materials.append(material)
    return ob


def bake(ob):
    """Apply all modifiers (works headless, no operator context needed)."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    old = ob.data
    ob.modifiers.clear()
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    me.shade_smooth()
    me.set_sharp_from_angle(angle=math.radians(35))
    return ob


def cut(target, cutters):
    """Boolean-subtract cutters from target, then delete the cutters."""
    for c in cutters:
        m = target.modifiers.new("cut_" + c.name, "BOOLEAN")
        m.operation, m.solver, m.object = "DIFFERENCE", "EXACT", c
    bake(target)
    for c in cutters:
        bpy.data.objects.remove(c)
    return target


def unite(target, others):
    """Boolean-add others into target, then delete them."""
    for o in others:
        m = target.modifiers.new("add_" + o.name, "BOOLEAN")
        m.operation, m.solver, m.object = "UNION", "EXACT", o
    bake(target)
    for o in others:
        bpy.data.objects.remove(o)
    return target


def box(name, lo, hi, material=None, corner=0.0, edge=0.0, axis="Y", segs=12):
    """Box from lo / hi corners (layout.py parts), optionally rounded (and then baked)."""
    size = tuple(h - l for l, h in zip(lo, hi))
    ob = rbox(name, size, tuple((l + h) / 2 for l, h in zip(lo, hi)), corner, edge, material, segs=segs, axis=axis)
    return bake(ob) if corner or edge else ob


def pebble(name, size, loc, r_corner, edge_front, edge_back, material=None):
    """Plan corners r_corner, then the front-face edge rounded edge_front and the back-face
    edge edge_back: one bevel whose width is scaled per edge by its bevel weight."""
    ob = bake(rbox(name, size, loc, r_corner, 0, material, segs=16))
    me, half, big = ob.data, size[1] / 2, max(edge_front, edge_back)
    w = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    for e in me.edges:
        ys = [me.vertices[i].co.y for i in e.vertices]
        w.data[e.index].value = (edge_front / big if all(abs(y + half) < 1e-4 for y in ys)
                                 else edge_back / big if all(abs(y - half) < 1e-4 for y in ys) else 0.0)
    m = ob.modifiers.new("edges", "BEVEL")
    m.limit_method, m.width, m.segments = "WEIGHT", big, 6
    return bake(ob)


def to_mesh(ob):
    """Text / curve object -> mesh object with the same name, place and materials."""
    if ob.type == "MESH":
        return ob
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())   # matrix_world is stale until evaluated
    name, mw = ob.name, ev.matrix_world.copy()
    me = bpy.data.meshes.new_from_object(ev)
    bpy.data.objects.remove(ob)
    new = link(bpy.data.objects.new(name, me))
    new.matrix_world = mw
    return new


def join(target, others):
    """Merge others into target: one object, materials kept. Works headless."""
    others = [to_mesh(o) for o in others]
    sel = [target] + others
    with bpy.context.temp_override(active_object=target, object=target, selected_objects=sel, selected_editable_objects=sel):
        bpy.ops.object.join()
    return target


def tag(ob, part):
    """Custom properties -> glTF extras the viewer reads."""
    ob["label"], ob["size"], ob["explode"] = part["label"], part["size"], float(part["explode"])
    return ob


# --- Scene -------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()                                          # the old file's materials are gone
    bpy.context.preferences.filepaths.save_version = 0     # no device.blend1 backups
    s = bpy.context.scene
    s.unit_settings.system = "METRIC"
    s.unit_settings.scale_length = 0.001
    s.unit_settings.length_unit = "MILLIMETERS"
    return s


def materials():
    fin = FINISHES["graphite"]
    return {
        "body": mat("body", fin["body"], rough=0.55, coat=0.15),
        "ring": mat("ring", fin["ring"], rough=0.45),
        "talk": mat("talk", COLORS["talk"], rough=0.35, coat=0.4),
        "ok": mat("ok", COLORS["ok"], rough=0.35, coat=0.4),
        "mask": mat("mask", COLORS["mask"], rough=0.08, coat=1.0),
        "window": mat("lens_window", COLORS["mask"], rough=0.03, alpha=0.0),   # clear: any tint made Cycles blotch the screen
        "label": mat("label", COLORS["label"], rough=0.6),
        "cream": mat("cream", COLORS["cream"], rough=0.5),
        "screen": mat("screen", COLORS["glass"], rough=0.15, emit=0.3, image=SCREEN_IMG),
        "glass": mat("glass", COLORS["glass"], rough=0.2),
        "black": mat("black", COLORS["black"], rough=0.6),
        "rubber": mat("rubber", COLORS["rubber"], rough=0.8),
        "foam": mat("foam", COLORS["foam"], rough=0.9),
        "metal": mat("metal", COLORS["metal"], rough=0.3, metal=1.0),
        "battery": mat("battery", COLORS["battery"], rough=0.35, metal=0.6),
        "fpc": mat("fpc", COLORS["fpc"], rough=0.4),
        "led": mat("led", COLORS["mint"], emit=6.0),
    }


def shells(L, m):
    """Pebble body, hollowed, every opening cut, split into front tub + back cover, posts and bosses."""
    W, H, D, P = L["W"], L["H"], L["D"], L["parts"]
    S, F, G = LY.SIDE, LY.FACE, LY.GAP
    body = pebble("Body", (W, D, H), (W / 2, D / 2, H / 2), LY.R_CORNER, LY.EDGE_FRONT, LY.EDGE_BACK, m["body"])
    cutters = [pebble("c_cavity", (W - 2 * S, D - 2 * F, H - 2 * S), (W / 2, D / 2, H / 2),
                      LY.R_CORNER - S, LY.EDGE_FRONT - F, LY.EDGE_BACK - F)]
    lo, hi = P["Lens"]["lo"], P["Lens"]["hi"]
    cutters.append(box("c_lens", (lo[0] - G, -1.0, lo[2] - G), (hi[0] + G, F + 0.01, hi[2] + G), corner=2.0 + G))
    front_cut = lambda name, r, x, z: cyl(name, r, F + 1.01, (x, (F - 0.99) / 2, z))   # through the front wall only
    for name, k in L["keys"].items():
        if k["shape"] == "pill":
            g = LY.KEY_GAP
            cutters.append(box("c_talk", (k["x"] - k["w"] / 2 - g, -1.0, k["z"] - k["h"] / 2 - g),
                               (k["x"] + k["w"] / 2 + g, F + 0.01, k["z"] + k["h"] / 2 + g), corner=k["h"] / 2 + g - 0.01, segs=16))
        elif name != "OK":                                     # OK sits inside the ring's opening
            cutters.append(front_cut("c_" + name, k["r"] + LY.KEY_GAP, k["x"], k["z"]))
    lp = P["LightPipe"]
    cutters.append(front_cut("c_led", lp["r"] + 0.2, (lp["lo"][0] + lp["hi"][0]) / 2, (lp["lo"][2] + lp["hi"][2]) / 2))
    u = P["USBC"]
    cutters.append(box("c_usb", (W - S - 1.0, u["lo"][1] - 0.2, u["lo"][2] - 0.2), (W + 1.0, u["hi"][1] + 0.2, u["hi"][2] + 0.2),
                       corner=1.6, axis="X"))
    for z in L["slits"]:
        cutters.append(box("c_slit", (W - S - 1.0, L["slit_y"] - 3.5, z - 0.55), (W + 1.0, L["slit_y"] + 3.5, z + 0.55),
                           corner=0.5, axis="X"))
    cutters.append(cyl("c_mic", 0.6, 2 * S + 2.0, (L["mic"][0], L["mic"][1], H), axis="Z"))
    cut(body, cutters)

    out = {}
    for name, y0, y1 in (("FrontShell", -1.0, LY.SPLIT), ("BackShell", LY.SPLIT + G, D + 1.0)):
        sh = body.copy()
        sh.data = body.data.copy()
        link(sh)
        sh.name = name
        keep = box("k_" + name, (-2.0, y0, -2.0), (W + 2.0, y1, H + 2.0))
        mod = sh.modifiers.new("keep", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "INTERSECT", "EXACT", keep
        bake(sh)
        bpy.data.objects.remove(keep)
        out[name] = sh
    bpy.data.objects.remove(body)

    r = LY.POST_R
    unite(out["FrontShell"], [cyl("post", r, LY.SPLIT - (F - 0.3), (x, (F - 0.3 + LY.SPLIT) / 2, z)) for x, z in L["posts"]])
    unite(out["BackShell"], [cyl("boss", r, D - F + 0.3 - (LY.SPLIT + G), (x, (LY.SPLIT + G + D - F + 0.3) / 2, z))
                             for x, z in L["posts"]])

    def screw_holes():
        hs = []
        for x, z in L["posts"]:
            hs.append(cyl("bore", LY.BORE_R, D + 1.0 - 6.0, (x, (6.0 + D + 1.0) / 2, z)))
            hs.append(cyl("cbore", 2.1, 2.95, (x, D - 1.95 + 1.475, z)))   # counterbore y D-1.95 .. D+1: the head sits below the back round
        return hs
    cut(out["FrontShell"], screw_holes())
    cut(out["BackShell"], screw_holes())

    bl = P["BackLabel"]
    t = text("BackLabel", "second brain  ·  SB-1  ·  5V 1A", 2.4,
             (W / 2, (bl["lo"][1] + bl["hi"][1]) / 2, (bl["lo"][2] + bl["hi"][2]) / 2), m["label"], extrude=0.06)
    t.rotation_euler = (math.radians(90), 0, math.radians(180))           # face +Y (the back)
    out["BackLabel"] = to_mesh(t)
    return out


def lens(L, m):
    """Flush dark lens: black mask, clear window over the active area, NOG mark + name in the band."""
    p = L["parts"]["Lens"]
    ob = box("Lens", p["lo"], p["hi"], m["mask"], corner=2.0)
    x0, z0, x1, z1 = p["window"]
    cut(ob, [box("c_win", (x0, -1.0, z0), (x1, LY.FACE + 1.0, z1))])
    bits = [box("pane", (x0 + 0.01, 0.0, z0 + 0.01), (x1 - 0.01, LY.FACE, z1 - 0.01), m["window"])]
    px, bz = 0.24, L["band_z"]
    lx, top = p["lo"][0] + 2.0, bz + len(NOG) * px / 2
    for r, row in enumerate(NOG):
        for c, ch in enumerate(row):
            if ch in "#e":
                bits.append(rbox("nog_px", (px, 0.12, px), (lx + c * px + px / 2, -0.05, top - r * px - px / 2), material=m["label"]))
    bits.append(text("Name", "second brain", 2.6, (lx + len(NOG[0]) * px + 1.5, -0.05, bz), m["label"], extrude=0.1, align="LEFT"))
    return join(ob, bits)


def panel(L, m):
    """Bare ILI9341: dark glass plus the textured screen plane over the active area."""
    p = L["parts"]["Panel"]
    ob = box("Panel", p["lo"], p["hi"], m["glass"], corner=0.6)
    x0, z0, x1, z1 = p["active"]
    w, h = x1 - x0, z1 - z0
    scr = link(bpy.data.objects.new("scr", bpy.data.meshes.new("scr")))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in bm.verts:
        v.co.x, v.co.y = v.co.x * w, v.co.y * h
    uv = bm.loops.layers.uv.new("UVMap")     # same name on both meshes, so join keeps it the active UV map
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x / w + 0.5, lp.vert.co.y / h + 0.5)
    bm.to_mesh(scr.data)
    bm.free()
    scr.location = ((x0 + x1) / 2, p["lo"][1] - 0.01, (z0 + z1) / 2)
    scr.rotation_euler = (math.radians(90), 0, 0)
    scr.data.materials.append(m["screen"])
    ob.data.uv_layers.new(name="UVMap")
    return join(ob, [scr])


def keys(L, m):
    """TALK pill (mic icon), 5-way ring (arrows) + OK, BACK (return glyph), each with its plunger; light pipe."""
    out, F = {}, LY.FACE
    for name, k in L["keys"].items():
        x, z, f, pe = k["x"], k["z"], k["front"], k["plunger_end"]
        d, yc, ys = F - f, (f + F) / 2, (F + pe) / 2
        if k["shape"] == "pill":
            ob = unite(bake(rbox(name, (k["w"], d, k["h"]), (x, yc, z), k["h"] / 2 - 0.01, 0.4, m["talk"], segs=16)),
                       [cyl("stem", k["plunger_r"], pe - F, (x, ys, z), m["talk"])])
            bits = [rbox("ic", (1.3, 0.1, 2.4), (x, f - 0.05, z + 0.45), 0.64, 0, m["black"]),
                    rbox("ic", (0.3, 0.1, 0.9), (x, f - 0.05, z - 1.15), material=m["black"]),
                    rbox("ic", (1.5, 0.1, 0.3), (x, f - 0.05, z - 1.65), material=m["black"])]
        elif k["shape"] == "ring":
            ob = unite(ring(name, k["r"], k["r_in"], d, (x, yc, z), m["ring"]),
                       [ring("tube", k["tube"][1], k["tube"][0], pe - F, (x, ys, z), m["ring"])])
            r = (k["r"] + k["r_in"]) / 2
            bits = [arrow("arw", 1.8, (x + dx * r, f - 0.1, z + dz * r), math.atan2(dx, dz), m["cream"])
                     for dx, dz in ((0, 1), (0, -1), (-1, 0), (1, 0))]
        else:
            mt = m["ok"] if name == "OK" else m["ring"]
            ob = unite(cyl(name, k["r"], d, (x, yc, z), mt), [cyl("stem", k["plunger_r"], pe - F, (x, ys, z), mt)])
            bits = []
            if name == "BACK":
                arc = cut(ring("arc", 1.5, 1.05, 0.1, (x + 0.3, f - 0.05, z - 0.3), m["cream"]),
                          [box("c_arc", (x - 2.0, f - 1.0, z - 2.5), (x + 2.5, f + 1.0, z - 0.3))])
                bits += [arc, arrow("arw", 1.1, (x - 0.95, f - 0.1, z - 0.6), math.pi, m["cream"])]
        out[name] = join(ob, bits)
    lp = L["parts"]["LightPipe"]
    c = [(a + b) / 2 for a, b in zip(lp["lo"], lp["hi"])]
    out["LightPipe"] = cyl("LightPipe", lp["r"], lp["hi"][1] - lp["lo"][1], c, m["led"])
    return out


def insides(L, m):
    """Board and everything on it, battery, foam, FPC, speaker, mic, key sheet, screws."""
    P, out = L["parts"], {}
    simple = {"Foam": ("foam", 0, 0, "Y"), "Amp": ("black", 0, 0, "Y"), "Charger": ("black", 0, 0, "Y"),
              "Connector": ("black", 0, 0, "Y"), "Mic": ("black", 0, 0, "Y"), "SwTalk": ("black", 0.4, 0, "Y"),
              "Sw5Way": ("black", 0.6, 0, "Y"), "SwBack": ("black", 0.4, 0, "Y"), "Battery": ("battery", 1.2, 0.8, "Y"),
              "USBC": ("metal", 1.2, 0, "X"), "Speaker": ("black", 2.0, 0, "X")}
    for name, (mt, corner, edge, axis) in simple.items():
        out[name] = box(name, P[name]["lo"], P[name]["hi"], m[mt], corner, edge, axis)
    b, n = P["Board"], P["Board"]["notch"]
    out["Board"] = cut(box("Board", b["lo"], b["hi"], m["black"], corner=2.0),
                       [box("c_notch", (n[0], b["lo"][1] - 1.0, n[1]), (n[2] + 1.0, b["hi"][1] + 1.0, n[3]))])
    md = P["Module"]
    ant = md["hi"][2] - 6.5
    out["Module"] = unite(box("Module", md["lo"], (md["hi"][0], md["hi"][1], ant), m["metal"]),
                         [box("ant", (md["lo"][0], md["lo"][1], ant), (md["hi"][0], md["lo"][1] + 0.8, md["hi"][2]), m["black"])])
    s0, s1 = P["FPC"]["segs"]
    out["FPC"] = unite(box("FPC", *s0, m["fpc"]), [box("seg", *s1, m["fpc"])])
    k = P["KeySheet"]
    yc, dk = (k["lo"][1] + k["hi"][1]) / 2, k["hi"][1] - k["lo"][1] + 2.0
    out["KeySheet"] = cut(box("KeySheet", k["lo"], k["hi"], m["rubber"], corner=1.0),
                          [cyl("c_hole", r, dk, (x, yc, z)) for x, z, r in k["holes"]])
    D = L["D"]
    parts = [unite(cyl("head", 1.9, 0.7, (x, D - 1.55, z), m["metal"]),          # head y D-1.9 .. D-1.2
                   [cyl("shank", 0.7, D - 1.9 - 6.5, (x, (6.5 + D - 1.9) / 2, z), m["metal"])]) for x, z in L["posts"]]
    out["Screws"] = join(parts[0], parts[1:])
    out["Screws"].name = "Screws"
    return out


def build(L):
    """Every part of one variant, tagged with label / size / explode. Returns {part name: object}."""
    m = materials()
    objs = {}
    objs.update(shells(L, m))
    objs["Lens"] = lens(L, m)
    objs["Panel"] = panel(L, m)
    objs.update(keys(L, m))
    objs.update(insides(L, m))
    for name, ob in objs.items():
        tag(ob, L["parts"][name])
    return objs


# --- Lights, cameras, render -------------------------------------------------
def stage(scene, width, depth):
    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = hex_rgba("#EFE9E0")
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    scene.world = world
    for name, rot, energy in (("Key", (52, 0, -38), 3.2), ("Fill", (65, 0, 55), 1.2), ("Rim", (-60, 0, 160), 1.5)):
        sun = bpy.data.lights.new(name, "SUN")
        sun.energy = energy
        sun.angle = math.radians(12)
        ob = link(bpy.data.objects.new(name, sun))
        ob.rotation_euler = tuple(math.radians(a) for a in rot)
    ground = rbox("Ground", (4000, 4000, 1), (width / 2, depth / 2, -0.5))
    ground.is_shadow_catcher = True
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.use_denoising = True
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1000
    return ground


def camera(scene, name, loc, target, ortho=None, lens=70.0, roll=0.0):
    cam = bpy.data.cameras.new(name)
    cam.clip_start, cam.clip_end = 1.0, 20000.0
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    ob = link(bpy.data.objects.new(name, cam))
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    ob.rotation_euler.rotate_axis("Z", math.radians(roll))
    scene.camera = ob
    return ob


def render(scene, L, objs, out, samples, only):
    W, H, D = L["W"], L["H"], L["D"]
    ground = stage(scene, W, D)
    scene.cycles.samples = samples
    c = (W / 2, D / 2, H / 2)
    views = {
        "hero": dict(loc=(W / 2 - 200, -340, H / 2 + 150), target=(W / 2 + 12, D / 2, H / 2 - 2), lens=70),
        "front": dict(loc=(W / 2, -500, H / 2), target=c, ortho=ORTHO_FRONT),
        "top": dict(loc=(W / 2, D / 2, H + 500), target=c, ortho=ORTHO_FRONT),
        "right": dict(loc=(W + 500, D / 2, H / 2), target=c, ortho=ORTHO_SIDE, roll=90),
        "back": dict(loc=(W / 2, D + 500, H / 2), target=c, ortho=ORTHO_FRONT),
    }
    for name, v in views.items():
        if only and name not in only:
            continue
        camera(scene, "Cam_" + name, v["loc"], v["target"], v.get("ortho"), v.get("lens", 70), v.get("roll", 0))
        ground.hide_render = name == "top"        # looking down, the ground shadow would swamp the thin edge
        scene.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", name)
    if not only or "exploded" in only:
        ground.hide_render = False
        for name, ob in objs.items():
            ob.location.y -= L["parts"][name]["explode"]
        camera(scene, "Cam_exploded", (W / 2 - 380, -170, H / 2 + 170), (W / 2, -10, H / 2 - 6), lens=55)
        scene.render.filepath = os.path.join(out, "exploded.png")
        bpy.ops.render.render(write_still=True)
        print("rendered exploded")


def shared(samples, only):
    """Both sizes side by side (compare.png) and next to a credit card and a phone (scale.png)."""
    out = os.path.join(HERE, "out", "shared")
    os.makedirs(out, exist_ok=True)
    scene = reset()
    a, b = LY.layout("2.8"), LY.layout("2.4")
    build(a)
    dx = a["W"] + 20.0
    for ob in build(b).values():
        ob.location.x += dx
    x = dx + b["W"] + 20.0
    props = [box("Card", (x, 7.1, 0.0), (x + 85.6, 7.9, 54.0), mat("card", COLORS["card"], rough=0.5), corner=3.2)]
    x += 85.6 + 20.0
    props.append(box("Phone", (x, 3.5, 0.0), (x + 72.0, 11.5, 147.0), mat("phone", COLORS["phone"], rough=0.3), corner=9.0, edge=1.5))
    x += 72.0
    stage(scene, x, LY.D)
    scene.cycles.samples = samples
    if not only or "scale" in only:
        camera(scene, "Cam_scale", (x / 2, -800, 75), (x / 2, 7.5, 75), ortho=x * 1.08)
        scene.render.filepath = os.path.join(out, "scale.png")
        bpy.ops.render.render(write_still=True)
        print("rendered scale")
    if not only or "compare" in only:
        for ob in props:
            ob.hide_render = True                  # just the two devices
        t = ((dx + b["W"]) / 2, 7.5, 28.0)
        camera(scene, "Cam_compare", (t[0], -480, t[2] + 170), t, lens=70)   # centre line: off to one side the nearer device looks bigger
        scene.render.filepath = os.path.join(out, "compare.png")
        bpy.ops.render.render(write_still=True)
        print("rendered compare")


def export_glb(objs, path):
    keep = {ob.name for ob in objs.values()}
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in keep)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_extras=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)


def write_dims(L, out):
    P, pan = L["parts"], LY.PANELS[L["screen"]]
    d = {"screen": L["screen"], "body_mm": [round(L["W"], 2), round(L["H"], 2), L["D"]],
         "glass_mm": list(pan["glass"]), "active_mm": list(pan["active"]),
         "active_rect": [round(v, 2) for v in P["Panel"]["active"]], "stack_mm": round(L["stack_mm"], 2),
         "finishes": FINISHES,
         "views": {n: {"px_per_mm": 1600 / o, "centre_px": [800, 500]}
                   for n, o in (("front", ORTHO_FRONT), ("top", ORTHO_FRONT), ("back", ORTHO_FRONT), ("right", ORTHO_SIDE))},
         "parts": {n: {"label": p["label"], "size": p["size"], "explode": p["explode"]} for n, p in P.items()}}
    with open(os.path.join(out, "dims.json"), "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    only = set(get("--only").split(",")) if "--only" in argv else None
    return argv, get, only


def main():
    argv, get, only = args()
    samples = int(get("--samples", 48))
    if "--shared" in argv:
        return shared(samples, only)
    screen = get("--screen", "2.8")
    if screen not in LY.PANELS:
        print('build_device: --screen must be one of %s (got "%s")' % (", ".join(LY.PANELS), screen))
        sys.exit(2)
    L = LY.layout(screen)
    out = os.path.join(HERE, "out", screen.replace(".", ""))
    os.makedirs(out, exist_ok=True)
    scene = reset()
    objs = build(L)
    errors = checks.run(L, objs)
    if errors:
        print("CHECKS FAILED (%s\"):\n  %s" % (screen, "\n  ".join(errors)))
        sys.exit(1)
    print('checks 1-6 passed (%s")' % screen)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "device.blend"))
    export_glb(objs, os.path.join(out, "device.glb"))
    write_dims(L, out)
    errors = checks.outputs(L, out)
    if errors:
        print("CHECKS FAILED (%s\"):\n  %s" % (screen, "\n  ".join(errors)))
        sys.exit(1)
    print('check 7 passed (%s")' % screen)
    if "--no-render" not in argv:
        render(scene, L, objs, out, samples, only)


if __name__ == "__main__":
    main()
