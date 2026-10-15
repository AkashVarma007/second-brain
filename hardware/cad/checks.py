"""Build-time checks on the real meshes (spec checks 1-7). Runs inside Blender.
Each check returns messages naming the part and the numbers; an empty list is a pass."""
import itertools
import json
import os

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import layout as LY


def _mesh(ob):
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    vs = [ev.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    return vs, polys


def world_verts(ob):
    return _mesh(ob)[0]


def bounds(vs):
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]


RAYS = [Vector(d).normalized() for d in ((0.5431, 0.6127, 0.5743), (-0.6211, -0.4973, 0.6057), (0.4877, -0.5519, -0.6767))]


def _odd(tree, p, d):
    hits, o = 0, Vector(p)
    for _ in range(1000):
        loc = tree.ray_cast(o, d)[0]
        if loc is None:
            break
        hits += 1
        o = loc + d * 1e-4
    return hits % 2 == 1


def _inside(tree, p):
    """Point inside a closed mesh: rays from p cross its surface an odd number of times.
    Majority of three skewed rays, since one ray can graze a faceted wall and miscount.
    (The nearest face's normal is not enough: near a concave edge it can point the wrong way.)"""
    return sum(_odd(tree, p, d) for d in RAYS) >= 2


def overlaps(objs, n=8):
    """Name pairs that share volume (world space). Surfaces that cross are caught by the BVH
    triangle test; overlaps whose faces are coplanar (flush boxes) by an n^3 grid of points
    in the bounding-box intersection that lie inside both meshes."""
    data = {}
    for ob in objs:
        vs, polys = _mesh(ob)
        data[ob.name] = (BVHTree.FromPolygons(vs, polys), bounds(vs))
    bad = []
    for a, b in itertools.combinations(sorted(data), 2):
        (ta, (alo, ahi)), (tb, (blo, bhi)) = data[a], data[b]
        lo = [max(alo[i], blo[i]) for i in range(3)]
        hi = [min(ahi[i], bhi[i]) for i in range(3)]
        if any(hi[i] - lo[i] <= 1e-4 for i in range(3)):
            continue
        axes = [[lo[i] + (hi[i] - lo[i]) * (k + 0.5) / n for k in range(n)] for i in range(3)]
        if ta.overlap(tb) or any(_inside(ta, p) and _inside(tb, p) for p in map(Vector, itertools.product(*axes))):
            bad.append((a, b))
    return bad


def run(L, objs):
    """Checks 1-6. objs = {part name: object}."""
    err = []
    W, H, D = L["W"], L["H"], L["D"]
    tw, th = LY.TARGETS[L["screen"]]
    shell = world_verts(objs["FrontShell"]) + world_verts(objs["BackShell"])
    lo, hi = bounds(shell)
    mw, md, mh = (hi[i] - lo[i] for i in range(3))
    if max(abs(mw - W), abs(mh - H), abs(md - D)) > 0.05:
        err.append("1 body mesh %.2f x %.2f x %.2f, layout %.2f x %.2f x %.2f" % (mw, mh, md, W, H, D))
    if abs(W - tw) > 1.0 or abs(H - th) > 1.0 or D != 15.0:
        err.append("1 body %.2f x %.2f x %.1f is not within 1 mm of %g x %g x 15" % (W, H, D, tw, th))
    for tag, ys, e in (("front", lo[1], LY.EDGE_FRONT), ("back", hi[1], LY.EDGE_BACK)):
        xs = [v.x for v in shell if abs(v.y - ys) < 1e-3]
        if abs(max(xs) - min(xs) - (W - 2 * e)) > 0.15:
            err.append("1 %s edge round: flat face %.2f wide, want %.2f" % (tag, max(xs) - min(xs), W - 2 * e))
    if L["stack_mm"] > D:
        err.append("2 stack-up %.2f mm > %.1f" % (L["stack_mm"], D))
    for name in LY.INTERNAL:
        out = [v for v in world_verts(objs[name]) if not LY.inside_cavity(L, v)]
        if out:
            err.append("3 %s: %d vertices outside the cavity, e.g. (%.2f, %.2f, %.2f)" % ((name, len(out)) + tuple(out[0])))
    out = [v for v in world_verts(objs["Screws"]) if not LY.inside_body(L, v)]
    if out:
        err.append("3 Screws: %d vertices stick out of the body, e.g. (%.2f, %.2f, %.2f)" % ((len(out),) + tuple(out[0])))
    for a, b in overlaps(list(objs.values())):
        err.append("4 %s intersects %s" % (a, b))
    for name, k in L["keys"].items():
        gap = bounds(world_verts(objs[k["switch"]]))[0][1] - bounds(world_verts(objs[name]))[1][1]
        if not 0.1 <= gap <= 0.5:
            err.append("5 %s: plunger-to-switch gap %.2f mm (want 0.1-0.5)" % (name, gap))
    f_hi = bounds(world_verts(objs["FPC"]))[1]
    c_lo, c_hi = bounds(world_verts(objs["Connector"]))
    if not (0 <= c_lo[1] - f_hi[1] <= 0.5 and c_lo[0] <= f_hi[0] <= c_hi[0]):
        err.append("6 FPC end (%.2f, %.2f) misses the connector (y %.2f, x %.2f-%.2f)" % (f_hi[0], f_hi[1], c_lo[1], c_lo[0], c_hi[0]))
    return err


def outputs(L, out):
    """Check 7: glb size and dims.json against the layout."""
    err = []
    mb = os.path.getsize(os.path.join(out, "device.glb")) / 1e6
    if mb > 2.5:
        err.append("7 device.glb is %.2f MB (max 2.5)" % mb)
    d = json.load(open(os.path.join(out, "dims.json")))
    want = [round(L["W"], 2), round(L["H"], 2), L["D"]]
    if d["body_mm"] != want or d["screen"] != L["screen"]:
        err.append("7 dims.json says %s %s, layout %s %s" % (d["screen"], d["body_mm"], L["screen"], want))
    return err
