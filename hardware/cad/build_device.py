"""Parametric 3D model of the Second Brain pocket device (v2: 3.2" tight layout, six case designs).

Builds the shared core (panel, battery, board, keys, mic, speaker, USB-C) and one case design from
layout.py + designs.py, runs the build-time checks (checks.py), saves out/<design>/device.blend +
device.glb + dims.json and renders the views (the device standing on its kickstand).

    blender -b --python-exit-code 1 -P hardware/cad/build_device.py -- --design walnut|...|all
            [--samples 48] [--only hero,back,exploded,front] [--no-render]

Axes: X = width (left to right), Z = height (bottom to top), Y = depth (front face at
y = 0, back at y = D). Units are millimetres (1 BU = 1 mm).
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import checks  # noqa: E402  (needs HERE on sys.path)
import layout as LY  # noqa: E402
from designs import DESIGNS  # noqa: E402

COLORS = {   # the shared core; the case colours come from designs.py
    "glass": "#17131C", "black": "#141216", "rubber": "#3A3540", "foam": "#3B3742", "metal": "#B9BDC2",
    "battery": "#C9CCD1", "fpc": "#B8621C", "screw": "#9DA3A8",
}
SCREEN_IMG = os.path.join(HERE, "screens", "home.png")
STICKERS = os.path.join(HERE, "stickers")
ORTHO_FRONT = 150.0                            # one scale for every design, so the front renders compare


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


def dmat(name, spec):
    """Material from a designs.py spec: plain, clear (transmission), brushed (anisotropic) or wood."""
    m = mat(name, spec["color"], rough=spec["rough"], metal=spec["metal"], emit=spec["emit"], coat=spec["coat"])
    b = m.node_tree.nodes["Principled BSDF"]
    if spec["kind"] == "clear":
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["IOR"].default_value = 1.49
    elif spec["kind"] == "brushed":
        b.inputs["Anisotropic"].default_value = 0.7
    elif spec["kind"] == "wood" and not m.node_tree.nodes.get("Wave Texture"):
        nt = m.node_tree                       # base colour stays the mid tone for the .glb (no procedural export)
        tc, mp = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.08, 0.6, 0.08)
        wave, ramp = nt.nodes.new("ShaderNodeTexWave"), nt.nodes.new("ShaderNodeValToRGB")
        wave.inputs["Scale"].default_value, wave.inputs["Distortion"].default_value, wave.inputs["Detail"].default_value = 3.0, 7.0, 6.0
        ramp.color_ramp.elements[0].color, ramp.color_ramp.elements[1].color = hex_rgba("#3B2416"), hex_rgba("#8A5A35")
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], wave.inputs["Vector"])
        nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
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


def dome(name, r, front, back, h, loc, material=None, coll=None, verts=48, rings=8):
    """Round key cap along Y: a spherical cap h high (its centre at y = front), then a straight side
    back to y = back. loc = (x, z) of the axis."""
    R = (r * r + h * h) / (2 * h)
    prof = [(r * i / rings, front + R - math.sqrt(R * R - (r * i / rings) ** 2)) for i in range(1, rings + 1)] + [(r, back)]
    bm = bmesh.new()
    rs = [[bm.verts.new((p * math.cos(2 * math.pi * j / verts), y, p * math.sin(2 * math.pi * j / verts))) for j in range(verts)]
          for p, y in prof]
    tip, tail = bm.verts.new((0, front, 0)), bm.verts.new((0, back, 0))
    for j in range(verts):
        k = (j + 1) % verts
        bm.faces.new((tip, rs[0][j], rs[0][k]))
        bm.faces.new((tail, rs[-1][k], rs[-1][j]))
        for a, b in zip(rs, rs[1:]):
            bm.faces.new((a[j], b[j], b[k], a[k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me), coll)
    ob.location = (loc[0], 0.0, loc[1])
    if material:
        me.materials.append(material)
    for p in me.polygons:
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


def boolean(target, others, op):
    for o in others:
        m = target.modifiers.new(op + "_" + o.name, "BOOLEAN")
        m.operation, m.solver, m.object = op, "EXACT", o
    bake(target)
    for o in others:
        bpy.data.objects.remove(o)
    return target


def cut(target, cutters):
    """Boolean-subtract cutters from target, then delete the cutters."""
    return boolean(target, cutters, "DIFFERENCE")


def unite(target, others):
    """Boolean-add others into target, then delete them."""
    return boolean(target, others, "UNION")


def box(name, lo, hi, material=None, corner=0.0, edge=0.0, axis="Y", segs=12):
    """Box from lo / hi corners (layout.py parts), optionally rounded (and then baked)."""
    size = tuple(h - l for l, h in zip(lo, hi))
    ob = rbox(name, size, tuple((l + h) / 2 for l, h in zip(lo, hi)), corner, edge, material, segs=segs, axis=axis)
    return bake(ob) if corner or edge else ob


def prism(name, pts, depth, ef, eb, material=None, y0=0.0, segs=6):
    """Extrude a plan outline [(x, z)] along +Y from y0 and round its front / back perimeter
    edges by ef / eb (one bevel, width scaled per edge by its bevel weight)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    fr = [bm.verts.new((x, y0, z)) for x, z in pts]
    bk = [bm.verts.new((x, y0 + depth, z)) for x, z in pts]
    bm.faces.new(fr)
    bm.faces.new(list(reversed(bk)))
    for i in range(len(pts)):
        j = (i + 1) % len(pts)
        bm.faces.new((fr[i], fr[j], bk[j], bk[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    ob = link(bpy.data.objects.new(name, me))
    if material:
        me.materials.append(material)
    big = max(ef, eb)
    if big > 0:
        w = me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
        for e in me.edges:
            ys = [me.vertices[i].co.y for i in e.vertices]
            w.data[e.index].value = (ef / big if all(abs(y - y0) < 1e-4 for y in ys)
                                     else eb / big if all(abs(y - y0 - depth) < 1e-4 for y in ys) else 0.0)
        m = ob.modifiers.new("edges", "BEVEL")
        m.limit_method, m.width, m.segments = "WEIGHT", big, segs
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
    if part.get("fw"):
        ob["fw"] = part["fw"]
    return ob


def decal(png, cx, cz, width, y, back=True, rot=0.0, gloss=0.35, max_px=512):
    """Vinyl sticker: a flat plane with the PNG (alpha cut-out), on the back (+Y) or the front."""
    img = bpy.data.images.load(os.path.join(STICKERS, png + ".png"), check_existing=True)
    w, h = width, width * img.size[1] / img.size[0]
    if max(img.size) > max_px:                         # small on the device: keep the .glb light
        k = max_px / max(img.size)
        img.scale(round(img.size[0] * k), round(img.size[1] * k))
    m = bpy.data.materials.get("st_" + png)
    if not m:
        m = bpy.data.materials.new("st_" + png)
        m.use_nodes = True
        nt = m.node_tree
        bsdf, tex = nt.nodes["Principled BSDF"], nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        bsdf.inputs["Roughness"].default_value = gloss
    ob = link(bpy.data.objects.new("st_" + png, bpy.data.meshes.new("st_" + png)))
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    uv = bm.loops.layers.uv.new("UVMap")
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x + 0.5, lp.vert.co.y + 0.5)
    c, s = math.cos(rot), math.sin(rot)
    for v in bm.verts:
        x, z = v.co.x * w, v.co.y * h
        v.co.x, v.co.y = x * c - z * s, x * s + z * c
    bm.to_mesh(ob.data)
    bm.free()
    ob.location = (cx, y, cz)
    ob.rotation_euler = (math.radians(90), 0, math.radians(180) if back else 0)
    ob.data.materials.append(m)
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


def materials(d):
    m = {"body": dmat("body", d["body"]),
         "screen": mat("screen", COLORS["glass"], rough=0.15, emit=0.3, image=SCREEN_IMG),
         "lens": mat("lens_window", "#0E0C12", rough=0.03, alpha=0.0),   # clear: any tint made Cycles blotch the screen
         "glass": mat("glass", COLORS["glass"], rough=0.2),
         "black": mat("black", COLORS["black"], rough=0.6),
         "rubber": mat("rubber", COLORS["rubber"], rough=0.8),
         "foam": mat("foam", COLORS["foam"], rough=0.9),
         "metal": mat("metal", COLORS["metal"], rough=0.3, metal=1.0),
         "battery": mat("battery", COLORS["battery"], rough=0.35, metal=0.6),
         "fpc": mat("fpc", COLORS["fpc"], rough=0.4),
         "screw": mat("screw", COLORS["screw"], rough=0.25, metal=1.0)}
    for k, spec in d["keys"].items():
        m["key_" + k] = dmat("key_" + k, spec)
    return m


def front_cutters(L, y0, y1):
    """Openings through a front layer (shell front wall or face plate): screen, keys, status light."""
    o, G, g = L["opening"], LY.GAP, LY.KEY_GAP
    cs = [box("c_open", (o[0] - G, y0, o[1] - G), (o[2] + G, y1, o[3] + G), corner=1.5 + G)]
    for name, k in L["keys"].items():
        if k["shape"] == "pill":
            cs.append(box("c_talk", (k["x"] - k["w"] / 2 - g, y0, k["z"] - k["h"] / 2 - g),
                          (k["x"] + k["w"] / 2 + g, y1, k["z"] + k["h"] / 2 + g), corner=k["h"] / 2 + g - 0.01, segs=16))
        elif name != "OK":                                     # OK sits inside the ring's opening
            cs.append(cyl("c_" + name, k["r"] + g, y1 - y0, (k["x"], (y0 + y1) / 2, k["z"])))
    cs.append(cyl("c_led", 0.9 + 0.2, y1 - y0, (L["led"][0], (y0 + y1) / 2, L["led"][1])))
    return cs


def shells(L, m):
    """Body from the design outline (+ ears), hollowed, every opening cut, split into front tub
    + back cover, posts and bosses, screw holes, back grooves."""
    W, H, D, P, d = L["W"], L["H"], L["D"], L["parts"], L["design"]
    S, F, G = LY.SIDE, LY.FACE, LY.GAP
    body = prism("Body", L["outline"], D, d["ef"], d["eb"], m["body"])
    if L["ears"]:
        ears = []
        for x, z in L["ears"]:
            e = cyl("ear", d["ears"]["r"], D - 3.0, (x, D / 2, z), m["body"])
            bv = e.modifiers.new("r", "BEVEL")
            bv.width, bv.segments, bv.limit_method = 2.0, 5, "ANGLE"
            ears.append(bake(e))
        unite(body, ears)
    cavity = prism("c_cavity", LY.outline(d["outline"], W, H, inset=S), D - 2 * F, max(d["ef"] - F, 0.4), max(d["eb"] - F, 0.4), y0=F)
    cutters = [cavity] + front_cutters(L, -1.0, F + 0.01)
    u, sp = P["USBC"], P["Speaker"]
    cutters.append(box("c_usb", (u["hi"][0] - 0.5, u["lo"][1] - 0.2, u["lo"][2] - 0.2), (W + 1.0, u["hi"][1] + 0.2, u["hi"][2] + 0.2),
                       corner=1.6, axis="X"))
    for z in L["slits"]:
        cutters.append(box("c_slit", (sp["hi"][0] - 0.5, L["slit_y"] - 3.5, z - 0.55), (W + 1.0, L["slit_y"] + 3.5, z + 0.55), corner=0.5, axis="X"))
    mic = P["Mic"]
    cutters.append(cyl("c_mic", 0.6, H + 2.0 - mic["hi"][2], (L["mic"][0], L["mic"][1], (mic["hi"][2] - 0.5 + H + 1.5) / 2), axis="Z"))
    cut(body, cutters)

    out = {}
    for name, y0, y1 in (("FrontShell", -1.0, LY.SPLIT), ("BackShell", LY.SPLIT + G, D + 1.0)):
        sh = body.copy()
        sh.data = body.data.copy()
        link(sh)
        sh.name = name
        keep = box("k_" + name, (-2.0, y0, -2.0), (W + 2.0, y1, H + 12.0))
        mod = sh.modifiers.new("keep", "BOOLEAN")
        mod.operation, mod.solver, mod.object = "INTERSECT", "EXACT", keep
        bake(sh)
        bpy.data.objects.remove(keep)
        out[name] = sh
    bpy.data.objects.remove(body)

    r, py0 = LY.POST_R, P["Panel"]["hi"][1] + G                   # posts start behind the panel, against the side walls
    unite(out["FrontShell"], [cyl("post", r, LY.SPLIT - py0, (x, (py0 + LY.SPLIT) / 2, z)) for x, z in L["posts"]])
    unite(out["BackShell"], [cyl("boss", r, D - F + 0.3 - (LY.SPLIT + G), (x, (LY.SPLIT + G + D - F + 0.3) / 2, z)) for x, z in L["posts"]])

    def screw_holes():
        hs = []
        for x, z in L["posts"]:
            hs.append(cyl("bore", LY.BORE_R, D + 1.0 - 6.0, (x, (6.0 + D + 1.0) / 2, z)))
            cb = L["screw_sink"] + 0.75                            # the head sits below the back round
            hs.append(cyl("cbore", 2.1, cb + 1.0, (x, D - cb + (cb + 1.0) / 2, z)))
        return hs
    cut(out["FrontShell"], screw_holes())
    cut(out["BackShell"], screw_holes())
    if d.get("slots"):                                            # diagonal grille grooves, bottom-right of the back
        gs = []
        for x, z in L["grooves"]:
            c = rbox("slot", (1.4, 2 * d["slots"]["depth"], 13.0), (x, D, z), 0.6)
            c.rotation_euler = (0, math.radians(45), 0)
            gs.append(bake(c))
        cut(out["BackShell"], gs)
    return out


def lens(L, m):
    o = L["opening"]
    return box("Lens", (o[0], 0.0, o[1]), (o[2], LY.FACE, o[3]), m["lens"], corner=1.5)


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
    """TALK pill (mic icon), 5-way ring (arrows) + domed OK, domed BACK (return glyph), each with its plunger; light pipe."""
    out, F = {}, LY.FACE
    for name, k in L["keys"].items():
        x, z, f, pe = k["x"], k["z"], k["front"], k["plunger_end"]
        d, yc, ys = F - f, (f + F) / 2, (F + pe) / 2
        if k["shape"] == "pill":
            ob = unite(bake(rbox(name, (k["w"], d, k["h"]), (x, yc, z), k["h"] / 2 - 0.01, 0.4, m["key_talk"], segs=16)),
                       [cyl("stem", k["plunger_r"], pe - F, (x, ys, z), m["key_talk"])])
            bits = [rbox("ic", (1.3, 0.1, 2.4), (x, f - 0.05, z + 0.45), 0.64, 0, m["key_icon"]),
                    rbox("ic", (0.3, 0.1, 0.9), (x, f - 0.05, z - 1.15), material=m["key_icon"]),
                    rbox("ic", (1.5, 0.1, 0.3), (x, f - 0.05, z - 1.65), material=m["key_icon"])]
        elif k["shape"] == "ring":
            ob = unite(ring(name, k["r"], k["r_in"], d, (x, yc, z), m["key_ring"]),
                       [ring("tube", k["tube"][1], k["tube"][0], pe - F, (x, ys, z), m["key_ring"])])
            r = (k["r"] + k["r_in"]) / 2
            bits = [arrow("arw", 1.8, (x + dx * r, f - 0.1, z + dz * r), math.atan2(dx, dz), m["key_arrow"])
                    for dx, dz in ((0, 1), (0, -1), (-1, 0), (1, 0))]
        else:
            mt = m["key_ok"] if name == "OK" else m["key_back"]
            ob = unite(dome(name, k["r"], f, F, min(0.7, -0.75 * f), (x, z), mt), [cyl("stem", k["plunger_r"], pe - F, (x, ys, z), mt)])
            bits = []
            if name == "BACK":
                arc = cut(ring("arc", 1.5, 1.05, 0.1, (x + 0.3, f + 0.02, z - 0.3), m["key_arrow"]),   # sits on the dome
                          [box("c_arc", (x - 2.0, f - 1.0, z - 2.5), (x + 2.5, f + 1.0, z - 0.3))])
                bits += [arc, arrow("arw", 1.1, (x - 0.95, f - 0.02, z - 0.6), math.pi, m["key_arrow"])]
        out[name] = join(ob, bits) if bits else ob
    lp = L["parts"]["LightPipe"]
    c = [(a + b) / 2 for a, b in zip(lp["lo"], lp["hi"])]
    out["LightPipe"] = cyl("LightPipe", lp["r"], lp["hi"][1] - lp["lo"][1], c, m["key_led"])
    return out


def clipped(name, p, inset, material, corner=1.0):
    """Part box cut to the cavity outline (board, key sheet follow rounded and odd-shaped bodies)."""
    L = clipped.L
    ob = box(name, p["lo"], p["hi"], material, corner=corner)
    inner = prism("c_clip", LY.outline(L["design"]["outline"], L["W"], L["H"], inset=inset), L["D"] + 2, 0, 0, y0=-1.0)
    return boolean(ob, [inner], "INTERSECT")


def insides(L, m):
    """Board and everything on it, battery, foam, FPC, speaker, mic, key sheet, screws."""
    P, out, G = L["parts"], {}, LY.GAP
    clipped.L = L
    simple = {"Foam": ("foam", 0, 0, "Y"), "Amp": ("black", 0, 0, "Y"), "Charger": ("black", 0, 0, "Y"),
              "Connector": ("black", 0, 0, "Y"), "Mic": ("black", 0, 0, "Y"), "SwTalk": ("black", 0.4, 0, "Y"),
              "Sw5Way": ("black", 0.6, 0, "Y"), "SwBack": ("black", 0.4, 0, "Y"), "Battery": ("battery", 1.2, 0.8, "Y"),
              "USBC": ("metal", 1.2, 0, "X"), "Speaker": ("black", 2.0, 0, "X"), "FPC": ("fpc", 0, 0, "Y")}
    for name, (mt, corner, edge, axis) in simple.items():
        out[name] = box(name, P[name]["lo"], P[name]["hi"], m[mt], corner, edge, axis)
    b, n = P["Board"], P["Board"]["notch"]
    out["Board"] = cut(clipped("Board", b, LY.SIDE + 0.4, m["black"], corner=2.0),
                       [box("c_notch", (n[0], b["lo"][1] - 1.0, n[1]), (n[2] + 1.0, b["hi"][1] + 1.0, n[3]))] +
                       [cyl("c_post", LY.POST_R + 0.3, 4.0, (x, (b["lo"][1] + b["hi"][1]) / 2, z)) for x, z in L["posts"]])
    md = P["Module"]
    ant = md["hi"][2] - 6.5
    out["Module"] = unite(box("Module", md["lo"], (md["hi"][0], md["hi"][1], ant), m["metal"]),
                          [box("ant", (md["lo"][0], md["lo"][1], ant), (md["hi"][0], md["lo"][1] + 0.8, md["hi"][2]), m["black"])])
    k = P["KeySheet"]
    yc, dk = (k["lo"][1] + k["hi"][1]) / 2, k["hi"][1] - k["lo"][1] + 2.0
    sheet_in = LY.SIDE + LY.edge_clear(k["lo"][1] - LY.FACE, max(L["ef"] - LY.FACE, 0.4)) + 0.15   # clears the front edge round
    out["KeySheet"] = cut(clipped("KeySheet", k, sheet_in, m["rubber"]),
                          [cyl("c_hole", r, dk, (x, yc, z)) for x, z, r in k["holes"]])
    D = L["D"]
    top = D - L["screw_sink"]                                                    # head y top-0.7 .. top
    parts = [unite(cyl("head", 1.9, 0.7, (x, top - 0.35, z), m["screw"]),
                   [cyl("shank", 0.7, top - 0.7 - 6.5, (x, (6.5 + top - 0.7) / 2, z), m["screw"])]) for x, z in L["posts"]]
    out["Screws"] = join(parts[0], parts[1:])
    out["Screws"].name = "Screws"
    return out


def caps(L, m):
    """Body-colour caps pressed into the screw counterbores, cut flush with the (rounded) back."""
    D, d, y0 = L["D"], L["design"], L["D"] - L["screw_sink"] + 0.1          # 0.1 in front of the screw heads
    cs = [cyl("cap", 2.0, D + 1.0 - y0, (x, (y0 + D + 1.0) / 2, z), m["body"]) for x, z in L["posts"]]
    ob = join(cs[0], cs[1:])
    ob.name = "Caps"
    return boolean(ob, [prism("c_skin", L["outline"], D, d["ef"], d["eb"])], "INTERSECT")


def stand(s, material, sticker=None):
    """Kickstand, closed flat against the back. Its origin is the hinge axis, so rotating it about
    local X opens it (positive angle swings the foot backwards)."""
    length, w, G = s["length"], s["width"], LY.GAP
    yc = -s["barrel"] + s["thick"] / 2                      # plate rests on the back (hinge axis is barrel above it)
    parts = []
    if s["kind"] == "wire":
        r = 0.9
        for sx in (-1, 1):                                   # the bottom bar's underside is the tip
            parts.append(cyl("rod", r, length - r, (sx * w / 2, -s["barrel"] + r, -(length - r) / 2), material, axis="Z"))
        parts.append(cyl("bar", r, w + 2 * r, (0, -s["barrel"] + r, -length + r), material, axis="X"))
    else:
        parts.append(bake(rbox("plate", (w, s["thick"], length), (0, yc, -length / 2), min(5.0, w / 2 - 0.1), 0.5, material, segs=10)))
        if s["kind"] == "tab":
            for i in range(4):
                parts.append(rbox("rib", (w * 0.6, 0.5, 1.0), (0, yc + s["thick"] / 2 + 0.25 - G, -length + 4 + i * 2.6), 0.3, 0, material))
    parts.append(cyl("hinge", s["barrel"], w + 1.8 if s["kind"] == "wire" else w * 0.8, (0, 0, 0), material, axis="X"))  # the bail's rods hang from its ends
    ob = join(parts[0], parts[1:])
    ob.data.transform(ob.matrix_basis)                    # vertices in hinge space, origin on the hinge axis
    ob.matrix_basis.identity()
    if sticker:
        st = to_mesh(decal(sticker[0], 0, -length * sticker[2], sticker[1], yc + s["thick"] / 2 + 0.02))
        ob.data.uv_layers.new(name="UVMap")              # same name on both, so join keeps it the render UV map
        ob = join(ob, [st])
    ob.name = "Stand"
    ob.location = (s["x"], s["y"] + s["barrel"], s["zh"])
    return ob


def extras(L, m):
    """Per-design parts: face plate, back panel, engraving, stickers, front stickers, kickstand."""
    d, W, H, D, P, G = L["design"], L["W"], L["H"], L["D"], L["parts"], LY.GAP
    out, back_y = {}, D
    if d.get("plate"):
        pl, fp = d["plate"], P["FacePlate"]
        plate = prism("FacePlate", LY.outline(d["outline"], W, H, inset=pl["inset"]), pl["thick"], 0.25, 0.25,
                      dmat("plate", pl["mat"]), y0=fp["lo"][1])
        cut(plate, front_cutters(L, fp["lo"][1] - 1.0, fp["hi"][1] + 0.5))
        bits = []
        o = L["opening"]
        for x, z in ((o[0] - 1.9, o[1] - 1.9), (o[0] - 1.9, o[3] + 1.9), (W - 3.4, 3.4), (W - 3.4, H - 3.4)):
            sc = cyl("screw", 1.1, 0.4, (x, fp["lo"][1] - 0.2, z), dmat("plate_screw", pl["screws"]))
            bits.append(cut(sc, [cyl("hex", 0.5, 1.0, (x, fp["lo"][1] - 0.4, z), verts=6)]))
        ring_k = L["keys"]["Ring"]
        for i in range(16):
            a = 2 * math.pi * i / 16
            t = rbox("tick", (0.35, 0.12, 1.4 if i % 4 else 2.2),
                     (ring_k["x"] + 10.9 * math.sin(a), fp["lo"][1] - 0.06, ring_k["z"] + 10.9 * math.cos(a)), material=dmat("plate_tick", pl["ticks"]))
            t.rotation_euler = (0, a, 0)
            bits.append(t)
        out["FacePlate"] = join(plate, bits)
    if d.get("back_panel"):
        bp = P["BackPanel"]
        out["BackPanel"] = prism("BackPanel", LY.outline(d["outline"], W, H, inset=d["back_panel"]["inset"]),
                                 d["back_panel"]["proud"], 0.3, 0.3, dmat("back_panel", d["back_panel"]["mat"]), y0=bp["lo"][1])
        back_y = bp["hi"][1]
    if d.get("engrave"):
        e = d["engrave"]
        t = text("Engraving", e["text"], e["size"], (W / 2, back_y + 0.06 + G, e["z"] if e["z"] >= 0 else H + e["z"]), dmat("engrave", e["mat"]), extrude=0.05)
        t.rotation_euler = (math.radians(90), 0, math.radians(180))
        out["Engraving"] = to_mesh(t)
    if d.get("stickers"):
        st = [decal(png, W / 2 + dx, z, w, back_y + G + 0.01 * i, rot=rot) for i, (png, dx, z, w, rot) in enumerate(d["stickers"])]
        out["Stickers"] = join(st[0], st[1:])
        out["Stickers"].name = "Stickers"
    if L["front_stickers"]:
        fs = [decal(png, x, z, w, -G, back=False) for png, (x, z, w) in L["front_stickers"]]
        out["Cheeks"] = join(fs[0], fs[1:])
        out["Cheeks"].name = "Cheeks"
    sd = d["stand"]
    out["Stand"] = stand(L["stand"], dmat("stand", sd["mat"]), sd.get("sticker"))
    return out


EXTRA_PARTS = {"Engraving": ("Engraving", "on the back", -28), "Stickers": ("Stickers", "vinyl, die-cut", -36),
               "Cheeks": ("Blush stickers", "vinyl", 50)}


def build(L):
    """Every part of one design, tagged with label / size / explode / firmware piece. Returns {part name: object}."""
    m = materials(L["design"])
    objs = {}
    objs.update(shells(L, m))
    objs["Lens"] = lens(L, m)
    objs["Panel"] = panel(L, m)
    objs.update(keys(L, m))
    objs.update(insides(L, m))
    objs["Caps"] = caps(L, m)
    objs.update(extras(L, m))
    for name, ob in objs.items():
        p = L["parts"].get(name) or dict(zip(("label", "size", "explode"), EXTRA_PARTS[name]))
        tag(ob, p)
    return objs


# --- Standing on the kickstand ------------------------------------------------
def pose_matrix(body_verts):
    """Lean the device back by TILT about its back-bottom edge and lift it so its lowest point is on the desk."""
    piv = Vector((0.0, LY.D, 0.0))
    M = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(-LY.TILT), 4, "X") @ Matrix.Translation(-piv)
    return Matrix.Translation((0.0, 0.0, -min((M @ v).z for v in body_verts))) @ M


def open_angle(P, stand_ob):
    """Stand angle (radians) that puts its lowest point on the desk in pose P (bisection between
    straight down and nearly flat behind)."""
    vs = [v.co.copy() for v in stand_ob.data.vertices]
    T = Matrix.Translation(stand_ob.location)

    def low(a):
        Ms = P @ T @ Matrix.Rotation(a, 4, "X")
        return min((Ms @ v).z for v in vs)
    lo, hi = math.radians(LY.TILT), math.radians(85.0)
    if not (low(lo) < 0 < low(hi)):
        raise ValueError("stand cannot reach the desk: %.2f .. %.2f" % (low(lo), low(hi)))
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if low(mid) < 0 else (lo, mid)
    return (lo + hi) / 2


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


def render(scene, L, objs, out, samples, only, P, alpha):
    W, H, D = L["W"], L["H"], L["D"]
    ground = stage(scene, W, D)
    scene.cycles.samples = samples * (2 if L["design"]["body"]["kind"] == "clear" else 1)
    want = lambda v: not only or v in only

    def shot(name):
        scene.render.filepath = os.path.join(out, name + ".png")
        bpy.ops.render.render(write_still=True)
        print("rendered", name)
    if want("front"):
        camera(scene, "Cam_front", (W / 2, -500, H / 2), (W / 2, D / 2, H / 2), ortho=ORTHO_FRONT)
        shot("front")
    if want("exploded"):
        for name, ob in objs.items():
            ob.location.y -= ob["explode"]
        camera(scene, "Cam_exploded", (W / 2 - 400, -140, H / 2 + 180), (W / 2 - 4, -8, H / 2 - 6), lens=60)
        shot("exploded")
        for name, ob in objs.items():
            ob.location.y += ob["explode"]
    if want("hero") or want("back"):                     # stand on the desk
        piv = link(bpy.data.objects.new("Pose", None))
        piv.matrix_world = P
        bpy.context.view_layer.update()
        for ob in objs.values():
            ob.parent = piv
        objs["Stand"].rotation_euler.x = alpha
        zc = H / 2 * math.cos(math.radians(LY.TILT))
        if want("hero"):
            camera(scene, "Cam_hero", (W / 2 - 150, -270, zc + 125), (W / 2 + 4, 6, zc - 2), lens=62)
            shot("hero")
        if want("back"):
            camera(scene, "Cam_back", (W / 2 + 200, 310, zc + 100), (W / 2 - 4, 30, zc - 8), lens=62)
            shot("back")


def export_glb(objs, path):
    keep = {ob.name for ob in objs.values()}
    for ob in bpy.context.scene.objects:
        ob.select_set(ob.name in keep)
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_extras=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)


def write_dims(L, out, alpha):
    d, P = L["design"], L["parts"]
    s = L["stand"]
    dims = {"design": L["name"], "title": d["title"], "mood": d["mood"], "blurb": d["blurb"],
            "body_mm": [round(L["W"], 2), round(L["H"], 2), L["D"]], "panel_margin": round(L["m"], 2),
            "active_mm": list(LY.PANEL["active"]), "active_rect": [round(v, 2) for v in P["Panel"]["active"]],
            "stack_mm": round(L["stack_mm"], 2),
            "stand": {"open_deg": round(math.degrees(alpha), 2), "tilt_deg": LY.TILT, "kind": s["kind"],
                      "hinge": [round(s["x"], 2), round(s["y"] + s["barrel"], 2), round(s["zh"], 2)]},
            "views": {"front": {"px_per_mm": 1600 / ORTHO_FRONT, "centre_px": [800, 500]}},
            "parts": {n: {"label": p["label"], "size": p["size"], "explode": p["explode"], "fw": p.get("fw")} for n, p in P.items()}}
    with open(os.path.join(out, "dims.json"), "w") as f:
        json.dump(dims, f, indent=2, ensure_ascii=False)


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    get = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    only = set(get("--only", "").split(",")) - {""} or None
    return argv, get, only


def build_design(name, argv, samples, only):
    L = LY.layout(name)
    out = os.path.join(HERE, "out", name)
    os.makedirs(out, exist_ok=True)
    scene = reset()
    objs = build(L)
    body = [v for n in ("FrontShell", "BackShell", "BackPanel", "FacePlate") if n in objs for v in checks.world_verts(objs[n])]
    P = pose_matrix(body)
    alpha = open_angle(P, objs["Stand"])
    objs["Stand"]["open_deg"] = math.degrees(alpha)
    errors = checks.run(L, objs) + checks.stand(L, objs, alpha)
    if errors:
        print("CHECKS FAILED (%s):\n  %s" % (name, "\n  ".join(errors)))
        sys.exit(1)
    print("checks 1-6, 8 passed (%s)" % name)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, "device.blend"))
    export_glb(objs, os.path.join(out, "device.glb"))
    write_dims(L, out, alpha)
    errors = checks.outputs(L, out)
    if errors:
        print("CHECKS FAILED (%s):\n  %s" % (name, "\n  ".join(errors)))
        sys.exit(1)
    print("check 7 passed (%s)" % name)
    if "--no-render" not in argv:
        render(scene, L, objs, out, samples, only, P, alpha)


def main():
    argv, get, only = args()
    try:
        samples = int(get("--samples", 48))
    except ValueError:
        print("build_device: --samples must be a whole number")
        sys.exit(2)
    which = get("--design", "walnut")
    names = list(DESIGNS) if which == "all" else [which]
    if any(n not in DESIGNS for n in names):
        print('build_device: --design must be one of %s or all (got "%s")' % (", ".join(DESIGNS), which))
        sys.exit(2)
    for n in names:
        build_design(n, argv, samples, only)


if __name__ == "__main__":
    main()
