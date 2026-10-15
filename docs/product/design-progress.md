# Design phase — progress and handoff

**Last updated:** 2026-10-15 (batches 3–4, flows, device CAD v2: 3.2" tight, six case designs) · Read this first when resuming the design work.

## Links

| What | Where |
|---|---|
| **Design canvas (current, source of truth)** | https://claude.ai/artifact/UQpEXSGANAde7mfd4iCWgn |
| Platform plan (users, apps, plugins, roadmap) | [`platform-plan.md`](platform-plan.md) |
| Feature roadmap doc (online, older research, INR parts) | https://claude.ai/code/artifact/25204d2c-d735-47e7-955e-d02a2b1fc2c9 |
| Old mono 128×64 mock (history only) | https://claude.ai/artifact/N4j4FnrEww5LbYWzwsV5RV |
| Device 3D viewer (six designs, labels, tour, stand, screens, explode) | https://claude.ai/artifact/MmyC2TWzQAwdWsiuALzUez · after a push also `docs/device-3d.html` on GitHub Pages |
| Device CAD v2 spec / plan | [`../superpowers/specs/2026-10-15-device-cad-v2-design.md`](../superpowers/specs/2026-10-15-device-cad-v2-design.md) · [`../superpowers/plans/2026-10-15-device-cad-v2.md`](../superpowers/plans/2026-10-15-device-cad-v2.md) (v1: [`spec`](../superpowers/specs/2026-10-15-device-cad-design.md), [`plan`](../superpowers/plans/2026-10-15-device-cad.md)) |

Canvas source files can be read back any time with the Artifact `read` action and a `path`
(for example `project/Wire.dc.html`); local scratch copies may be gone.

## Decisions (design phase)

- **Product:** a personal assistant first; apps are its skills, NOG (pixel chibi) is its face.
  Useful for office professionals first, many other user types later (34 in the plan).
- **Brain:** laptop (faster-whisper + Ollama); local and free first, cloud opt-in later.
- **Apps:** first-party first; declarative manifests drawn by built-in device widgets; logic on
  the laptop brain; phone app has the marketplace.
- **Autonomy:** internal actions automatic; anything that leaves the device (invite, email,
  message) needs one OK; never deletes or spends on its own.
- **Talk:** tap TALK to start, tap again to send (hold for a quick note); spoken + on-screen
  replies; **speaker is base hardware**. Measured ~3 s per reply on the dev laptop.
- **Device:** **3.2" 320×240 colour TFT (ILI9341)**, landscape, tight layout (the opening hugs the picture,
  no front logo band; NOG and "second brain" go on the back). Screen on the left, right column: status
  light, TALK, 5-way with OK, BACK. Speaker + USB-C on the right side, mic on the top edge, kickstand on
  the back. Six case designs modelled (see Device CAD v2), about 103 × 60 to 108 × 73 × 15 mm; the case
  is still to pick.
- **Look:** device "Night arcade" palette + pixel fonts (Silkscreen, Pixelify Sans); phone and
  laptop "Paper" palette, Manrope + pixel accent labels. Case colours and materials per design (v2).
- **NOG:** 7 moods = assistant states; career ladder Intern 0 → Associate 300 → Manager 900 →
  Director 2,000 → CEO 4,000 XP, with outfits; XP only from real outcomes, daily caps,
  missed days never cost XP.
- **UX rules:**
  - Hint bar on every screen.
  - Every visible box is reachable with the arrows.
  - In lists, OK does the main thing and ▶ opens details.
  - TALK works from anywhere; BACK goes back, hold BACK = Home.
  - Alerts pop over any screen: OK act · BACK later.
- **Laptop app:** browser dashboard (React), can be wrapped as desktop later.
- **Deferred to after the app works:** UI polish pass (motion, home scene, depth), thinner
  body (~14 mm, flat battery), pebble edges, recessed screen, clip / lanyard / stand.

## Canvas structure

| Page | Boards |
|---|---|
| 1 · Design system | `Main` (foundations: colours, type, icons, components), `NogSheet`, `Nog` (component), `Icon` (component) |
| 2 · Device | `DeviceHero` (front view + edge views, **not to scale**, see below), `DeviceScreens` (6 core screens), `Screen` (component, 20 screens), `DeviceCad` (2.8" vs 2.4" comparison: same-scale renders, dimensioned fronts, pros and costs, parts) |
| 3 · Prototype, flows & systems | `Prototype` (clickable device), `FlowDevice` (device screen map), `FlowApps` (phone + laptop maps, cross-surface handoffs), `SysArch` (architecture, built vs planned, trust zones), `SysFlows` (5 sequences + latency budget) |
| 4 · Wireframes | `WfSystem` (10 stories), `WfAssistant` (14 stories), `Story` + `Wire` (components) |
| 5 · App wireframes | One board per category, in one row: `WfProductivity` (P1–P10), `WfWork` (W1–W17), `WfLearning` (L1–L7), `WfHome` (H1–H8), `WfWellbeing` (B1–B3), `WfCreative` (R1–R3), `WfPeople` (S1–S3), `WfUtilities` (U1–U6), `WfFun` (F1), `WfAccess` (A1–A2) |
| 6 · Phone & laptop (launch page) | `WfPhone` (M1–M14), `WfLaptop` (D1–D12), `Phone`, `Web`, `PaperList` (components) |
| 7 · To discuss later | `WfLater` (X1–X12: options for open questions; each story ends with the decision needed) |

**Components**

- `Nog` — props `mood` (idle, blink, happy, listen, think, talk, sleep), `outfit` (none, intern,
  associate, manager, director, ceo), `px`.
- `Icon` — props `icon` (mic, note, check, bell, calendar, people, sun, ask, gear, speaker, wifi,
  battery, clock, up, down, left, right, plus, grid, heart, book, home, lock, star, play, coin, pin,
  drop, music, chart, flag, code, box, pill, cloud), `color`, `px`.
- `Screen` — the hand-built device screens used by the prototype (`screen`, `scale`, `sel`,
  `focus`, `t`, `scenario`, `done`, `slots`, `bookmarks`, `xp`, `toast`).
- `Wire` — draws any 320×240 frame from a `spec` object. **Use this for all new wireframes.**
- `Story` — one use-case row: `story = { id, title, who, kind, frames: [{ step, note, spec }] }`;
  `kind` = `device` (default, Wire spec), `phone` (Phone spec) or `web` (Web spec).
- `Phone` — 390×844 phone screen: `{ title, sub, back, right, tab: home|apps|inbox|memory|settings, w, sheet, toast }`.
- `Web` — 1280×800 laptop dashboard: `{ nav, url, title, sub, actions, cols: [{ span, w }], modal, toast, brain, mood }`.
- `PaperList` — the Paper widget set used by Phone and Web (`w` lists): hero, card, row, label, tiles,
  button(s), chips, seg, search, field, text, big, progress, chart, device (embeds a Wire screen),
  banner, user, reply, qr, apphead, table, log, gap.

**`Wire` spec format** (each widget mirrors a plugin-manifest widget):

```js
{ title, titleColor, right, status, statusColor, bare, toast,
  hints: [['OK', 'OPEN'], ['BACK', 'HOME']],
  w: [
    { t: 'nog', mood, outfit, px, text },          { t: 'user', text },   { t: 'reply', text },
    { t: 'card', icon, color, label, title, sub, chip, chipColor, focus },
    { t: 'row', title, sub, icon, color, box: '' | 'done', chip, chipColor, sel },
    { t: 'tiles', items: [{ icon, color, value, label, focus }] },
    { t: 'big', value, label, size, color },        { t: 'progress', pct, label, value, color },
    { t: 'chart', bars: [..], label, color },       { t: 'text', text, size, color, align },
    { t: 'label', text, color },  { t: 'wave' },    { t: 'qr', text },
    { t: 'picker', options: [..], sel },            { t: 'action', icon, color, label, text },
    { t: 'popup', icon, color, label, title, text },{ t: 'grid', items: [{ icon, color, label }], sel },
    { t: 'gap' }
  ] }
```

Storyboard artboards are 1920 wide; height = sum of story rows (device 396, phone 820, web 500) + 280.
Max 5 frames per story (3 for web).
App story IDs follow `platform-plan.md` §5, so People S1–S3 and Accessibility A1–A2 share letters
with the system/assistant stories; the board name tells them apart. Colours: amber `#FFA14A`, mint `#6EE7A8`, sky `#7CC4FF`, coral `#FF6B6B`,
lilac `#C79BFF`, dust `#A99CB8`, line `#3D3347`, cream `#F3E9DA`.

## Status

- [x] Design system, NOG sheet, device views, 20 device screens, clickable prototype.
- [x] **Wireframes batch 1** — 24 use cases, 83 frames (system S1–S10, assistant A1–A14).
  User review: "good enough" at a high level (2026-10-15).
- [x] **Wireframes batch 2 · device apps** — 60 non-core apps (core C1–C9 are covered by
  A1–A14), 238 frames on page 5 (2026-10-15). All 321 frames pass the real-layout fit check.
- [x] **Batch 3 · phone app** — 14 stories, 56 frames (M1–M14).
- [x] **Batch 4 · laptop dashboard** — 12 stories, 35 frames (D1–D12).
- [x] **Later features** — 12 option stories, 39 frames (X1–X12), each ends with the decision needed.
- [x] **Flow maps and system diagrams** — 4 boards on page 3.
- [x] **Device CAD v1** — one parametric Blender script builds the 2.8" and the 2.4" device with
  build-time checks; `.blend`, `.glb`, renders in `hardware/cad/out/`; 3D viewer and the `DeviceCad`
  comparison board (2026-10-15). All 451 storyboard frames pass the fit check.
- [x] **Device CAD v2** — 3.2" tight layout, six full case designs (walnut, instrument, arcade, clear,
  egg, sticker bomb) with kickstands; viewer with design switcher, labels, markers and an 8-step tour.
- [ ] **Pick a case design** (or mix two), then redraw the 2D `DeviceHero` front view at true scale.
- [ ] UI polish pass (after the app works).

## Checks (scratchpad `checks/`, rebuild from the canvas if wiped)

- `check.js <board>` — data-props parse, holes are plain lookups, `renderVals` runs.
- `stories.js <board>` — known widgets and icons, ≤5 frames, ≤3 hints, ≤6 widgets, text lengths.
- `fit.js <boards…>` — draws every frame (device, phone, web) with the real templates, CSS and
  fonts in headless Chrome; lists frames that overflow. `--shot out.png --only 'M4 '` saves a
  picture; `--png out.png --only 'S2 1 '` saves one frame at 2× (used for the 3D screen texture).
- `shot.js <board> <out.png>` — screenshots a whole board.
- `make_cad_board.py <repo> <viewer-url>` — rebuilds the `DeviceCad` comparison board from
  `hardware/cad/out/{28,24,shared}`; then `more_canvas.py` (keeps hand-moved board positions).
- Fonts for the checks are downloaded to scratchpad `fonts/local.css` (Manrope, Pixelify, Silkscreen).

## Calls made in batch 2 — to confirm

- **Shared Lists (P9):** sharing a list is the one OK; later items sync without asking each time.
- **Home Control (H3):** scenes run without asking (your own home); unlocking a door always asks.
- **Exports to your own laptop** (W9 timesheet, W16 count sheet) don't ask; they never leave your setup.
- **Check-in (H7):** "I'm OK" sends on one OK; "Need help" asks once, then shows 112.
- **2FA Codes (U4):** shown as device-only, never synced to the brain.
- **Maker Bench (U6):** assumes an expansion port, which the hardware layout doesn't have yet.
- **High contrast (A1):** only a switch in settings; Wire's palette is fixed, so no frame shows it.

## Calls made in batches 3–4 and the diagrams — to confirm

- **Approvals queue** sits under the phone Inbox tab ("Waiting for OK"); approving from the phone
  is marked "to discuss" on the flow map.
- **Family check-in reply** ("on my way", M14) sends on one tap, no extra sheet, because it's urgent.
- **Exports** to the phone or laptop don't ask (they stay in your setup); delete-all needs a typed word.
- **Offline queue** removes an item only after the brain confirms it (design intent).
- **New dashboard ideas** (not in the plan yet): "learn this word" for misheard words, "keep model
  warm", revocable device/phone keys with a 25 MB upload limit.
- **Dashboard URL** shows `localhost:8000/…` (brain serves it); today's dev dashboard runs on Vite :5173.

## Device CAD v2 (3.2" tight, six case designs)

Spec `docs/superpowers/specs/2026-10-15-device-cad-v2-design.md` (v1 below is history). In `hardware/cad/`:

- `designs.py` — the six designs as data (outline, edges, materials, plate, back panel, stickers, stand, keys).
- `layout.py` — the 3.2" core fitted into each outline (the panel margin grows with rounder corners);
  `python3 hardware/cad/test_layout.py`.
- `build_device.py -- --design <name>|all [--no-render] [--samples 48] [--only hero,back,exploded,front]` —
  builds, checks 1–8 (adds: nothing sticks out of the body, the stand stays above the bottom and its solved
  angle is sane), exports `out/<design>/device.glb` + `dims.json`, renders standing on the stand. All six build
  in ~20 s; renders ~6 min per design (CPU).
- `stickers/` — 13 sticker PNGs + `make_stickers.py` (HTML/SVG → PNG).
- `make_viewer.py` → `docs/device-3d.html` (~5.8 MB, six models); `check_viewer.py` — self-test of every
  design, the tour, label layout at 390 and desktop widths, stand, tap/drag/pinch, bad links, offline, 24 shots.

| Design | Body (mm) | Stand |
|---|---|---|
| Walnut & brass | 103.3 × 61.0 × 15 | brass plate, 39° |
| Field instrument | 106.1 × 62.6 × 15 | steel wire bail, 36° |
| Arcade pocket | 103.0 × 60.4 × 15 | ribbed tab, 38° |
| See-through | 104.1 × 62.6 × 15 | clear acrylic plate, 39° |
| Pet egg | 108.1 × 72.6 × 15 (+ ears) | paw plate, 39° |
| Sticker bomb | 104.1 × 62.6 × 15 | black plate, 39° |

- Matched to the approved concept sheet: domed OK and BACK keys, body-colour caps over the four back screws
  (flush with the rounded back), the concepts' sticker layout (arcade stripes run over the cosmetic grooves; the
  speaker vents through the side), instrument back reads "SB-1 FIELD UNIT 3.2″". Kept on purpose: USB-C,
  speaker slits and mic hole (the concepts had none), walnut "second brain" above the stand hinge (the concept's
  spot is under the closed stand).
- Panel outline 77.2 × 55 mm is from a supplier listing: confirm with the bare-panel drawing before buying.
- `hardware/cad/out/28`, `out/24`, `out/shared` are v1 outputs (2.8" / 2.4"), kept until you remove them.

## Device CAD v1 (2.8" vs 2.4", superseded)

Spec `docs/superpowers/specs/2026-10-15-device-cad-design.md`. Everything is in `hardware/cad/`:

- `layout.py` — every dimension and part box per size (pure Python); `python3 hardware/cad/test_layout.py`.
- `build_device.py` — `blender -b --python-exit-code 1 -P hardware/cad/build_device.py -- --screen 2.8|2.4
  [--no-render] [--samples 48] [--only …]`, and `-- --shared` for `compare.png` + `scale.png`. Runs the
  checks (body size, stack-up, every part inside the shell, no two parts overlapping, key plunger gaps,
  FPC on its connector, glb size) and stops on any failure. Build ~3 s; renders ~10 min per size (CPU).
- `test_blender.py` — Blender tests for the overlap check and mesh helpers.
- `make_viewer.py` → `docs/device-3d.html` (self-contained, three.js 0.169.0 from jsDelivr);
  `check_viewer.py` — headless self-test, bad links, offline message, 24 screenshots (phone + desktop).

| | 2.8" | 2.4" |
|---|---|---|
| Body | 109.2 × 63.5 × 15 mm | 100.26 × 56.22 × 15 mm |
| Screen (active) | 57.6 × 43.2 mm, 0.18 mm pixels | 48.96 × 36.72 mm, 0.153 mm pixels |
| Same in both | 503450 cell (~1000 mAh), ESP32-S3 module, keys, 15 mm stack | |

- **Scale finding:** the 2D `DeviceHero` front view draws a ~4" screen. Redraw it at true scale once the
  case is picked.
- Modelled as the target product (custom thin board, bare panel); not modelled: snap clips, battery
  lead, a separate speaker chamber, the expansion port (X12).

## Other open items

- Firmware on `main` (53a02ab) is the earlier 128×64 mono UI; it gets rebuilt for the colour
  TFT and the widget renderer after the design phase.
- Wokwi CI token needed only for headless screenshot runs; the VS Code extension works as is.
- Brain hardening (auth token, upload limits, timeouts) before the device talks to it over Wi-Fi.
