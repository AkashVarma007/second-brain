# Device CAD v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (inline). Steps use `- [ ]`.

**Goal:** Rebuild the device model on the 3.2" tight layout as six full case designs with kickstands, and upgrade
the viewer with a design switcher, part labels with leader lines, numbered markers and an 8-step tour.

**Architecture:** `layout.py` gets the 3.2" core, outline functions and a polygon-based cavity test, and computes
each design's panel margin so the panel and front features fit its outline. `designs.py` (pure data) describes the
six designs. `build_device.py --design <name>|all` builds core + design parts in Blender, runs v1's checks plus the
stand check, exports one `.glb` per design, poses the device on its stand and renders. The viewer embeds the six
models and adds labels, markers and the tour.

**Spec:** `docs/superpowers/specs/2026-10-15-device-cad-v2-design.md` (v1 spec for everything unchanged).

**Execution note:** single inline executor with full context, user said "implement as needed". The plan gives
interfaces, algorithms and checks; routine ports of v1 code are described, not repeated.

## Global Constraints

- Blender 5.2 headless; units mm; axes as v1 (front y = 0, back y = D = 15).
- Panel: glass 77.2 × 55.0 × 2.5, active 64.8 × 48.6, active offset (3.0 left, 3.2 top), ribbon strip on the right.
- Front opening = active + 1.0 mm each side. No front logo band.
- Designs (keys): `walnut instrument arcade clear egg bomb`. Outputs `hardware/cad/out/<design>/`.
- v1 rules stay: GAP 0.05, key gap 0.3, plunger gap 0.1–0.5, stack ≤ 15.
- Stand: hinge barrel on the back, origin at the hinge axis; open angle solved so its foot meets the desk with the
  device leaning back 18° on its lowest back point.
- Budgets: each design `.glb` ≤ 1.5 MB, page ≤ 12 MB. (Ruling vs spec: one `.glb` per design instead of core +
  shell, because the internals sit at design-specific positions.)
- No new dependencies. three.js 0.169.0 via jsDelivr `+esm` (as v1 after the loader fix).
- The agent can't `git commit`; stage and ask.

## Review Focus

- A design whose rounded corners push the panel or a key into the shell: margin solver + layout test must catch it.
- Stand closed must not overhang the bottom edge or touch the body; open it must touch the desk (no floating).
- Labels on a 390 px phone: no overlap, nothing off-canvas, still readable.
- Switching design mid-tour or mid-explode must not leave stale highlights or labels.
- Stickers must sit on the flat back, not hang over a rounded edge.

---

### Task 1: Core layout v2 (pure Python, TDD)

**Files:** modify `hardware/cad/layout.py`, `hardware/cad/test_layout.py`; create `hardware/cad/designs.py`.

**Produces:**
- `outline(kind, w, h, params, inset=0.0) -> [(x, z)]` — `("rrect", r | (bl, br, tr, tl))` or `("squircle", n)`;
  `inset` shrinks w/h by 2·inset, radii by inset (≥ 0.5), shifts by inset (the cavity / flat-face outline).
- `sdist(pts, x, z) -> float` signed distance to a polygon (+ inside).
- `layout(design: dict) -> L` with `W, H, D, m (panel margin), outline, parts, keys, posts, stand, ...`. Margin solver:
  smallest m (0.1 steps from 1.8) such that panel corners have `sdist ≥ SIDE + GAP` against the outline and the
  opening corners, key caps, LED have `sdist ≥ ef + 0.3` (stay on the flat front). `W = m + 100.3 + pad_x`,
  `H = 2m + 55 + pad_z`.
- `inside_shell(L, p)`, `inside_body(L, p)` — v1's rule with `d = sdist(outline) - side`.
- Core positions (relative to panel origin `(px0, pz0) = (m, m + pad_z/2)`): column centre `cx = px0 + 82.6`;
  key sheet starts right of the panel; FPC folds straight back behind the panel's ribbon strip to a connector on
  the board under it; posts behind the panel, touching the side walls; everything else as v1, anchored as v1.
- `designs.py`: `DESIGNS = {name: {...}}` pure data — title, mood, outline kind + params, ef, eb, pad, materials
  (hex + roughness / metal / coat / kind ∈ {wood, clear, brushed}), key colours, `plate`, `back_panel`, `slots`,
  `ears`, `stickers [(png, dx_from_centre, z, width, rot)]`, `engrave`, `stand {kind, zh, width, mat, sticker}`.

**Tests first** (`test_layout.py`): for every design — panel corners inside the cavity; all INTERNAL boxes inside
the shell; no internal box overlaps (as v1); key plunger gaps; FPC lands; body within 1.5 mm of the spec table;
stickers inside the flat back (`sdist ≥ eb + 0.5`); stand closed above the bottom edge and inside the outline.
Run → fail → implement → pass.

- [ ] write tests · [ ] run (fail) · [ ] implement · [ ] run (pass) · [ ] stage

### Task 2: Stickers into the repo

Move `make_stickers.py` + PNGs from the scratchpad to `hardware/cad/stickers/`; regenerate; check 13 PNGs exist.

### Task 3: Build v2 in Blender (TDD on checks)

**Files:** `build_device.py` (shells from outline prisms; design parts: face plate, back panel, slots, ears,
stickers, engraving, stand; materials from design data), `checks.py` (cavity test via `inside_shell`; check 8 stand),
`test_blender.py` (prism + stand pivot tests).

- Port `prism()`, `decal()`, `stand()` from the concept script; stand origin at the hinge (bake the transform).
- `pose(objs, L)`: lean back 18° about the bottom-back, lift so the lowest body point is at z = 0, then bisect the
  stand angle until its lowest point is at z = 0 (±0.05). Store `open_deg` in `dims.json` and on the Stand.
- Check 8: closed stand overlaps nothing (check 4) and its lowest point ≥ body bottom; bisection converges within
  10–80°.
- CLI: `--design <name>|all`, `--no-render`, `--only`, `--samples`. Invalid design → list + exit 2.
- Parts list = v1 parts − BackLabel + Stand + per-design extras (FacePlate, BackPanel, Stickers, Engraving).

- [ ] Blender tests first (prism outline sizes; stand hinge pivot; posed foot on the desk) · [ ] implement ·
  [ ] all six build with checks 1–8 green · [ ] stage

### Task 4: Renders

Per design: `hero` (front 3/4, standing on the stand), `back` (rear 3/4), `exploded`, `front` (ortho, same scale for
all). Background run at 48 samples; eyeball all; send the key ones.

### Task 5: Viewer v2

`viewer.html` + `make_viewer.py`: embed six models; Design chips; Screen chips; View row (explode, Labels, Stand,
Dimensions); Tour button.

- Labels: parts with a label get a DOM label in a left or right column (side of the part's projected centre),
  sorted by projected y, at least one label height apart; SVG leader line from part to label. Phone: name + firmware
  chip only.
- Markers: numbered dots on the tour parts; tapping one opens that tour step.
- Tour: 8 steps from the spec; each sets explode, camera direction and distance, highlighted parts; Prev / Next /
  Close; animated camera (instant under reduced motion).
- Stand: rotates the Stand node by `open_deg` about its hinge.
- Hash: `design, screen, explode, labels, stand, step`.
- Self-test: all designs load; every tour step; labels don't overlap and stay inside the stage at 390 and 1280 wide;
  stand toggles; v1's bad-hash, tap / drag / pinch and card checks.

- [ ] self-test assertions first (fail on the v1 page) · [ ] implement · [ ] `check_viewer.py` green ·
  [ ] screenshots eyeballed · [ ] publish (same artifact URL) · [ ] stage

### Task 6: Canvas, docs, review

- `DeviceCad` board → "Case designs" gallery (hero + back per design, size, materials, stand, exploded of one);
  publish the canvas.
- `design-progress.md`, `platform-plan.md` §1/§13 (3.2" decided, six designs, pick pending).
- Final whole-branch review by a fresh reviewer; fix pass; hand-off with rulings and deferred minors.
