"""Blender tests for the helpers the build relies on:
    ~/.local/bin/blender -b --factory-startup --python-exit-code 1 -P hardware/cad/test_blender.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402

import build_device as B  # noqa: E402
import checks  # noqa: E402


def test_overlaps_finds_intersecting_parts_only():
    B.reset()
    a = B.box("A", (0, 0, 0), (10, 10, 10))
    b = B.box("B", (9, 0, 0), (19, 10, 10))          # 1 mm into A
    assert checks.overlaps([a, b]) == [("A", "B")], checks.overlaps([a, b])
    b.location.x += 1.05                              # now a 0.05 mm gap
    bpy.context.view_layer.update()
    assert checks.overlaps([a, b]) == []


def test_overlaps_no_false_alarm_inside_a_hollow_shell():
    B.reset()                                         # board and speaker sit in the cavity, near the split face
    L = B.LY.layout("2.8")
    m = B.materials()
    sh, ins = B.shells(L, m), B.insides(L, m)
    assert checks.overlaps([sh["FrontShell"], ins["Board"], ins["Speaker"]]) == []


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


def test_pebble_front_and_back_edges():
    B.reset()
    ob = B.pebble("P", (40.0, 15.0, 30.0), (0, 0, 0), 7.0, 2.5, 4.0)
    vs = checks.world_verts(ob)
    lo, hi = checks.bounds(vs)
    front = [v.x for v in vs if v.y < lo[1] + 1e-3]
    back = [v.x for v in vs if v.y > hi[1] - 1e-3]
    assert abs(hi[0] - lo[0] - 40.0) < 0.01 and abs(hi[1] - lo[1] - 15.0) < 0.01
    assert abs(max(front) - min(front) - 35.0) < 0.15, max(front) - min(front)   # 40 - 2 x 2.5
    assert abs(max(back) - min(back) - 32.0) < 0.15, max(back) - min(back)       # 40 - 2 x 4


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
    print("blender tests ok")
