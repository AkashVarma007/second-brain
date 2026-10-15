# Device CAD v2 — 3.2" tight layout, six case designs, stand, explainer (design)

**Date:** 2026-10-15 · **Status:** approved ("Implement as needed, provided designs are great") · **Builds on:** `2026-10-15-device-cad-design.md` (v1,
committed). v1's checks, file layout and viewer pattern carry over; this spec lists what changes.

User's words: "3.2 tight it is"; "can you improve the exploding view, like with firmware design, markers and
labels, and an interactive things explaining overall design"; "creative designs … classy, funky, funny … add
stickers"; "add a small stand behind"; "Designs are great, can you create 3d models and everything properly."

## Decisions

| Area | Decision |
|---|---|
| Screen | **3.2" ILI9341, 320 × 240** (same UI and driver as before). Active 64.8 × 48.6 mm. Glass assumed 77.2 × 55.0 × 2.5 mm with the ribbon (dead) strip on the right (~9.4 mm) — from a supplier listing, to confirm against the bare-panel drawing before buying. 2.8" / 2.4" variants retired. |
| Layout ("tight") | The front opening is the active area + 1 mm. The panel's dead border hides under the body plastic; its ribbon strip hides under the key column. No logo band on the front. Panel corners must sit inside the shell cavity, so the panel margin grows with the corner radius (computed per design, checked). |
| Designs | All six concepts become full models: **Walnut & brass, Field instrument, Arcade pocket, See-through, Pet egg, Sticker bomb.** Same core (panel, battery, board, keys, mic, speaker, USB-C) in every design; each design defines its outline, edges, materials, face plate, back details, stickers, stand and key colours. |
| Branding | NOG mark and "second brain" move to the back (engraving, sticker or label per design). |
| Stand | Every design gets a kickstand on the back: hinged, closed flat against the back, opens so the device leans back 18° on the desk. Plate, tab, wire bail or paw plate per design. |
| Stickers | Vinyl decals (PNG artwork with die-cut border) generated from HTML/SVG, committed under `hardware/cad/stickers/`. |
| Viewer | Design switcher replaces the finish chips. New: **labels** (leader lines from each part to a label with name, spec and firmware piece), **numbered markers**, a **guided tour** (8 steps), stand open/closed. Screen chips, explode, dimensions stay. |
| Firmware in the explainer | Each part names the firmware piece that drives it (display, input, audio in, audio out, power, network, UI/apps). These are the *planned* modules for sub-project B and are labelled as planned. |

## Bodies (as built; the build checks the mesh against the layout, not against this table)

| Design | Plan shape | Body W × H × D (mm) | Stand |
|---|---|---|---|
| Walnut & brass | rounded R6 | 103.3 × 61.0 × 15 | brass plate, opens 39° |
| Field instrument | rounded R3 + aluminium face plate (+2 mm frame for the screws) | 106.1 × 62.6 × 15 | steel wire bail, 36° |
| Arcade pocket | R4 with one R16 corner | 103.0 × 60.4 × 15 | ribbed tab, 38° |
| See-through | rounded R7, clear shell | 104.1 × 62.6 × 15 | clear acrylic plate, 39° |
| Pet egg | squircle (n = 5) with ears | 108.1 × 72.6 × 15 (+ 4.5 ears) | paw plate, 39° |
| Sticker bomb | rounded R7 | 104.1 × 62.6 × 15 | black plate, 39° |

(First estimates were ≈ 103–104 × 60–62 and the egg ≈ 112 × 72; the fitted numbers above replace them.)

Stands add ~1.4 mm at the back where they sit when closed.

## Explainer content

Tour steps (each moves the camera, sets the explode amount, highlights the parts, shows a short card):

1. **The device** — pocket size, 3.2" screen, keys, 15 mm.
2. **Screen** — 3.2" ILI9341 over SPI. Firmware: display driver + UI (NOG-OS screens).
3. **Keys** — TALK, 5-way + OK, BACK on tact switches. Firmware: input (debounce, hold-to-talk).
4. **Brain chip** — ESP32-S3, 16 MB flash, 8 MB PSRAM. Firmware: app runtime, screen router, apps from manifests.
5. **Voice** — INMP441 mic (I2S in), MAX98357A amp + speaker (I2S out). Firmware: audio capture and playback.
6. **Power** — 503450 cell ~1000 mAh, USB-C charger. Firmware: battery gauge, sleep.
7. **Link to the laptop brain** — Wi-Fi to the brain API (`/process`, `/notes`, `/tasks`). Firmware: network client, offline queue.
8. **Case & stand** — this design's materials, the screws, the 18° stand.

Labels show for the main parts in the exploded view; they are laid out in two columns beside the model so they never overlap, with a leader line to each part.

## Files (changes from v1)

```
hardware/cad/
  layout.py        3.2" tight core; design-dependent body size and panel margin
  designs.py       the six designs: outline, edges, materials, plate, back details, stickers, stand, keys
  stickers/        sticker PNGs + make_stickers.py (HTML/SVG -> PNG)
  build_device.py  --design <name>|all ; builds core + design, checks, exports, renders
  out/<design>/    device.blend, dims.json, renders (hero, back, front, exploded)
  out/core.glb     internals shared by all designs; out/<design>/shell.glb per design
  viewer.html, make_viewer.py, check_viewer.py   updated for designs, labels, tour, stand
docs/device-3d.html
```

## Verification

- v1 checks 1–7 for every design (body size within 1.5 mm of the table, stack-up, inside the cavity, nothing
  sticking out of the body, no overlaps, plunger gaps, FPC landing, glb sizes).
- **New 8 — stand:** closed, it touches nothing but its hinge; open, its foot is within 0.5 mm of the desk when
  the device leans back 18° on its bottom-back edge.
- **New 9 — panel fit:** panel corners inside the cavity for every outline (point-in-outline test in
  `test_layout.py`).
- Viewer self-test: every design loads, every tour step runs, labels don't overlap each other or leave the canvas
  (phone and desktop), stand toggles, plus v1's checks (bad hash, offline message, tap vs drag/pinch, cards).
- Size budget: `core.glb` ≤ 1.5 MB, each `shell.glb` ≤ 1 MB, page ≤ 12 MB.
- Eyeball every render and the screenshots; send the key ones to the user's phone.

## Out of scope

Firmware itself (sub-project B), STEP export, moulding detail, PCB layout, a real hinge mechanism (the stand
hinge is a modelled barrel, not a spring), touch panel.
