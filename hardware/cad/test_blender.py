"""Blender tests for the helpers the build relies on:
    ~/.local/bin/blender -b --factory-startup --python-exit-code 1 -P hardware/cad/test_blender.py"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import build_device as B  # noqa: E402
import checks  # noqa: E402
import layout as LY  # noqa: E402


def test_overlaps_finds_intersecting_parts_only():
    B.reset()
    a = B.box("A", (0, 0, 0), (10, 10, 10))
    b = B.box("B", (9, 0, 0), (19, 10, 10))          # 1 mm into A
    assert checks.overlaps([a, b]) == [("A", "B")], checks.overlaps([a, b])
    b.location.x += 1.05                              # now a 0.05 mm gap
    bpy.context.view_layer.update()
    assert checks.overlaps([a, b]) == []


def test_join_keeps_name_and_materials():
    B.reset()
    a = B.box("Key", (0, 0, 0), (1, 1, 1), B.mat("t1", "#FF0000"))
    t = B.text("Lbl", "OK", 1.0, (0.5, -0.5, 0.5), B.mat("t2", "#00FF00"))
    B.join(a, [t])
    assert a.name == "Key" and a.type == "MESH"
    assert {s.material.name for s in a.material_slots} == {"t1", "t2"}
    assert "Lbl" not in bpy.data.objects


def test_to_mesh_keeps_world_place():
    B.reset()
    t = B.text("Lbl", "OK", 2.0, (30.0, -1.0, 20.0), B.mat("t2", "#00FF00"))   # rotated to face the front
    lo, hi = checks.bounds(checks.world_verts(B.to_mesh(t)))
    assert 27.0 < lo[0] < hi[0] < 33.0 and 18.0 < lo[2] < hi[2] < 22.0 and hi[1] - lo[1] < 0.5, (lo, hi)


def test_prism_outline_and_edge_rounds():
    B.reset()
    ob = B.prism("P", LY.outline(("rrect", 6.0), 40.0, 30.0), 15.0, 2.5, 4.0)
    vs = checks.world_verts(ob)
    lo, hi = checks.bounds(vs)
    assert max(abs(hi[0] - lo[0] - 40.0), abs(hi[1] - lo[1] - 15.0), abs(hi[2] - lo[2] - 30.0)) < 0.01, (lo, hi)
    front = [v.x for v in vs if v.y < lo[1] + 1e-3]
    back = [v.x for v in vs if v.y > hi[1] - 1e-3]
    assert abs(max(front) - min(front) - 35.0) < 0.15, max(front) - min(front)   # 40 - 2 x 2.5
    assert abs(max(back) - min(back) - 32.0) < 0.15, max(back) - min(back)       # 40 - 2 x 4


def test_stand_pivots_on_its_hinge():
    B.reset()
    s = dict(kind="plate", x=10.0, zh=40.0, width=20.0, barrel=1.0, thick=1.4, y=15.05, length=38.0)
    ob = B.stand(s, B.mat("m", "#888888"))
    assert (ob.location - Vector((10.0, 16.05, 40.0))).length < 1e-6, ob.location        # origin on the hinge axis
    lo, hi = checks.bounds(checks.world_verts(ob))
    assert abs(lo[2] - 2.0) < 0.05 and lo[1] >= 15.05 - 1e-6, (lo, hi)                    # closed: hangs to zh - length
    ob.rotation_euler.x = math.radians(90)
    bpy.context.view_layer.update()
    lo, hi = checks.bounds(checks.world_verts(ob))
    assert abs(hi[1] - (16.05 + 38.0)) < 0.5 and lo[2] > 38.0, (lo, hi)                   # swung straight back


def test_stand_sticker_renders():
    B.reset()                                          # the decal's UVs must be the stand's render UV map
    s = dict(kind="plate", x=0.0, zh=40.0, width=20.0, barrel=1.0, thick=1.4, y=15.05, length=38.0)
    ob = B.stand(s, B.mat("m", "#888888"), ("paw", 10.0, 0.5))
    assert ob.data.uv_layers.active_render and ob.data.uv_layers.active_render.name == "UVMap", [l.name for l in ob.data.uv_layers]


def test_wire_stand_hinge_reaches_its_rods():
    B.reset()
    s = dict(kind="wire", x=0.0, zh=40.0, width=60.0, barrel=1.0, thick=1.4, y=15.05, length=38.0)
    ob = B.stand(s, B.mat("m", "#888888"))
    barrel = [v for v in checks.world_verts(ob) if v.z > 40.5]                    # above the rod tops: only the barrel
    assert max(v.x for v in barrel) >= 29.5 and min(v.x for v in barrel) <= -29.5, (min(v.x for v in barrel), max(v.x for v in barrel))


def test_open_angle_puts_the_foot_on_the_desk():
    B.reset()
    body = B.box("Body", (0, 0, 0), (60, 15, 50))
    s = dict(kind="plate", x=30.0, zh=36.0, width=20.0, barrel=1.0, thick=1.4, y=15.05,
             length=36.0 * math.cos(math.radians(LY.TILT)) + 1.5)
    st = B.stand(s, B.mat("m", "#888888"))
    P = B.pose_matrix(checks.world_verts(body))
    a = B.open_angle(P, st)
    assert 10 < math.degrees(a) < 80, math.degrees(a)
    st.rotation_euler.x = a
    bpy.context.view_layer.update()
    low_stand = min((P @ v).z for v in checks.world_verts(st))
    low_body = min((P @ v).z for v in checks.world_verts(body))
    assert abs(low_stand) < 0.05 and abs(low_body) < 1e-6, (low_stand, low_body)


def test_dome_key_is_a_closed_round_cap():
    B.reset()
    ob = B.dome("OK", 4.0, -1.0, 1.2, 0.7, (10.0, 20.0), B.mat("m", "#888888"))
    vs = checks.world_verts(ob)
    lo, hi = checks.bounds(vs)
    assert abs(lo[1] + 1.0) < 1e-6 and abs(hi[1] - 1.2) < 1e-6, (lo, hi)                        # front at the centre, back flat
    assert abs(hi[0] - lo[0] - 8.0) < 0.02 and abs((lo[2] + hi[2]) / 2 - 20.0) < 1e-6, (lo, hi)
    rim = [v.y for v in vs if abs((v.x - 10.0) ** 2 + (v.z - 20.0) ** 2 - 16.0) < 1e-3]
    assert abs(min(rim) - (-1.0 + 0.7)) < 1e-6, min(rim)                                            # the dome is 0.7 high
    edges = {}
    for p in ob.data.polygons:
        for e in p.edge_keys:
            edges[e] = edges.get(e, 0) + 1
    assert set(edges.values()) == {2}, "not closed"


def test_caps_close_the_screw_counterbores_flush():
    from mathutils.bvhtree import BVHTree
    B.reset()
    L = LY.layout("egg")                                   # biggest back round: the caps sit under the curve
    m = B.materials(L["design"])
    sh = B.shells(L, m)
    caps = B.caps(L, m)
    assert caps.name == "Caps" and checks.overlaps([caps, sh["BackShell"]]) == []

    def first_hit(ob, x, z):
        vs, polys = checks._mesh(ob)
        return BVHTree.FromPolygons(vs, polys).ray_cast(Vector((x, L["D"] + 10.0, z)), Vector((0, -1, 0)))[0]
    for x, z in L["posts"]:
        hit = first_hit(caps, x, z)
        assert hit is not None and hit.y > L["D"] - L["screw_sink"], (x, z, hit)                 # in front of the screw head
        s = 1 if x < L["W"] / 2 else -1                                                          # inboard: cap edge vs back just past the hole
        edge, skin = first_hit(caps, x + 1.9 * s, z), first_hit(sh["BackShell"], x + 2.2 * s, z)
        assert abs(edge.y - skin.y) < 0.1, (x, z, edge.y, skin.y)                                # flush with the rounded back


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("blender tests ok")
