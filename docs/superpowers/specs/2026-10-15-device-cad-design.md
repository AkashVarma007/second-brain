# Device 3D CAD — 2.8" and 2.4" (design)

**Date:** 2026-10-15 · **Status:** design sections 1–4 approved in chat; spec awaiting review ·
**Scope:** sub-project A of the device + firmware phase (B = full colour firmware in Wokwi, next)

## Goal

Proper 3D models of the pocket device, good enough to judge the look and to choose between a
2.8" and a 2.4" screen. Pocketable, cheap to build, as sleek as possible. Blender only: one
parametric script builds either size and outputs a model, a web model and renders; an
interactive viewer and a canvas board put the two sizes side by side.

User's words: "proper 3D CAD models properly"; "start with 2.8, once that is done, lets build
2.4 also, then we can compare and choose".

## Decisions

| Area | Decision | Why |
|---|---|---|
| Tool | Blender 5.2 (`~/.local/bin/blender`), Python script, headless | User choice; already used by the concept model |
| What the model shows | The target product: custom thin board, bare panel, flat cell | The 18–20 mm module prototype is not the product |
| Variants | `--screen 2.8` and `--screen 2.4` from one script | Same layout rules, so the comparison is fair |
| Formats | `.blend`, `.glb` (web), PNG renders | No STEP / CadQuery / STL now; STL later if a print is wanted |
| Viewer | `docs/device-3d.html`, one self-contained file (models + screen images embedded) | Same pattern as `docs/wiring-3d.html`; works on GitHub Pages, as an artifact, from disk |
| Viewer library | three.js `0.169.0` (core, `GLTFLoader`, `OrbitControls`) from jsDelivr via import map, exact version | Loading glTF by hand is not worth it. **New dependency — needs the user's OK** |
| Old concept outputs | `hardware/cad/renders/`, `device.blend`, `dims.json`, `screen_home.png` (uncommitted) are replaced by `out/` | Same script, new layout |

## Product layout (both sizes)

Front, left to right: screen, 5 mm gap, control column. Below the screen: an 8 mm logo band that
replaces the bottom frame.

- Frame 5.5 mm (top, left, right of the body). Control column 24 mm wide.
- Control column, top to bottom: status light, TALK pill 20 × 7.5, 5-way ring Ø18 with OK cap,
  BACK Ø8.5.
- Width = 5.5 + glass W + 5 + 24 + 5.5. Height = 5.5 + glass H + 8. Depth = 15.0.

| | 2.8" ILI9341 | 2.4" ILI9341 |
|---|---|---|
| Panel glass | 69.2 × 50.0 × 2.5 | 60.26 × 42.72 × 2.5 |
| Active area | 57.6 × 43.2 | 48.96 × 36.72 |
| Body (derived) | ≈ 109.2 × 63.5 × 15 | ≈ 100.3 × 56.2 × 15 |
| Weight (estimate) | ≈ 90–95 g | ≈ 85–90 g |

Active areas follow the pixel pitch: 0.18 mm (2.8") and 0.153 mm (2.4") × 320 × 240.

Stack-up, front to back (mm): lens 1.2 + panel 2.5 + foam 0.3 + battery 5.0 + board 1.0 +
ESP32-S3 module 3.1 + back wall 1.2 + clearance 0.7 = **15.0**.

Shape: plan corners R7; pebble edge bevels 2.5 front, 4 back; flush lens. Side walls 1.5.
Right side: USB-C (chamfered opening) and slot speaker grille. Top edge: mic pinhole above the
control column.

## Parts

Outside:
- Front shell (deep tub) and back cover, matte textured plastic; split line 2.6 mm from the back;
  4 × M2 screws from the back.
- Flush dark acrylic lens over the screen and logo band. Black mask, white NOG pixel mark and
  "second brain" in the band.
- TALK: soft coral pill with mic icon. 5-way ring with arrows and an amber OK cap. BACK: round
  with ↩. Clear light pipe for the status light. Real gaps (0.3 mm) and lift on the keys.

Inside:
- ILI9341 panel with FPC folding back to a board connector.
- Main board 1.0 mm, black: ESP32-S3-WROOM-1 module on the back side (antenna end at the top
  edge, copper keep-out), MAX98357A amp, charger + protection, USB-C, tact switches under the keys.
- INMP441 mic at the top edge; micro speaker 15 × 11 against the right-side grille (no separate
  chamber in this model).
- 503450 LiPo (50 × 34 × 5, ≈ 1000 mAh) behind the panel (its lead is not modelled).
- Screw posts in the front tub meeting bosses in the back cover; rubber key sheet behind the keys;
  each key has a plunger down to its switch. Snap clips are not modelled.

Finishes: Graphite (default), Chalk, Amber. Hex values live in the script's `COLORS`.

Screen states (textures): home, listening, answer, tasks, alert — rendered from the device
wireframes at 320 × 240 (2×) with the existing headless fit tool, saved to `hardware/cad/screens/`.

Scale reference: a credit card (85.6 × 54) and a typical phone outline (72 × 147).

## Files

```
hardware/cad/
  build_device.py      --screen 2.8|2.4 [--samples N] [--only views] [--no-render]
                       builds, runs the checks, exports, renders
  make_viewer.py       embeds both .glb + screen images into viewer.html -> docs/device-3d.html
  viewer.html          viewer template (three.js, UI, placeholders for data)
  screens/             home, listening, answer, tasks, alert .png
  out/28/  out/24/     device.blend, device.glb, dims.json,
                       hero, front, right, top, back, exploded .png
  out/shared/          compare.png (both sizes, same scale), scale.png (card + phone)
docs/device-3d.html    generated viewer
```

Parts are separate named objects (`FrontShell`, `BackShell`, `Lens`, `Panel`, `FPC`, `Battery`,
`Board`, `Module`, `Amp`, `USBC`, `Mic`, `Speaker`, `KeySheet`, `TALK`, `Ring`, `OK`, `BACK`,
`LightPipe`, `Screws`). Each carries custom properties exported as glTF extras: `label`,
`size` (mm text) and `explode` (mm offset along depth). Text and curve objects are converted to
meshes before export. The `.glb` uses fewer bevel segments than the renders and contains parts
only (no lights, camera, shadow catcher).

## Viewer (`docs/device-3d.html`)

- Drag to rotate, pinch / scroll to zoom, reset view.
- Size toggle 2.8 ⇄ 2.4, and Compare: both models side by side at the same scale.
- Finish chips recolour the shell and key materials. Screen chips swap the panel texture.
- Explode slider moves each part by its `explode` extra. Tap a part: its label and size.
- Dimension overlay toggle (W × H × D from `dims.json`).
- State is kept in the URL hash (e.g. `#size=24&finish=chalk&screen=tasks&explode=1`), so a view
  can be linked and the checks can open any state directly.
- Works at phone width (390 px) and desktop. Models ≈ 2 MB each; the page ≤ 7 MB after base64.
- Needs internet for three.js (CDN).

## Canvas

The DeviceCad board (page 2) becomes a comparison board: both sizes at the same scale,
dimensions, part list, pros and cons, and the viewer link. `make_cad_board.py` (scratchpad
`checks/`) reads `out/28`, `out/24` and `out/shared`. After the user picks a size, the 2D
DeviceHero front view is redrawn to true scale.

## Verification

Build-time checks inside `build_device.py`, every run, both sizes. A failed check stops the
build with a message naming the part and the numbers.

1. Body: W and H equal the layout formula, within 1 mm of the approved targets (2.8: 109 × 64,
   2.4: 100 × 56); D = 15.0.
2. Stack-up sums to ≤ 15.0.
3. Every inside part lies within the shell cavity.
4. No two parts intersect (BVH triangle overlap on evaluated meshes). Parts that touch by design
   are modelled with a 0.05 mm gap so the test can stay strict.
5. Each key plunger ends 0.1–0.5 mm above its switch actuator (travel room, no preload).
6. The FPC end lands on the board connector (within 0.5 mm).
7. `.glb` ≤ 2.5 MB each; `dims.json` matches the script constants.

Viewer checks (headless Chrome, `--use-angle=swiftshader` for WebGL):

8. Loads both models with no errors (`window.onerror` / unhandled rejections collected into a
   result block read with `--dump-dom`).
9. Screenshots at 390 px and 1280 px for every toggle state via URL hash: size, compare, each
   finish, each screen, exploded, part picked.
10. Compare view: the 2.8 model is ≈ 9 mm wider than the 2.4 on screen (measured from projected
    bounding boxes).

Then: canvas lint (`check.js`) and publish; eyeball every render and screenshot; send the key
ones to the user's phone.

**Done when** checks 1–10 pass, both sizes are built and rendered, the viewer is live, and the
user has seen both. The user then picks a size.

## Out of scope

Firmware (sub-project B), STEP export, injection-moulding detail (draft angles, ribs, gate
marks), PCB layout and routing, real part sourcing, the expansion port (X12), STL / 3D print.
