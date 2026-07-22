# Second Brain — Design Spec (Phases 1–3, software side)

**Date:** 2026-07-21
**Status:** Design — pending external hardware review + user approval
**Scope:** Phases 1–3 (laptop brain + monitoring UI, simulated device UI, sim↔server
round-trip). Phases 4–5 (real mic, SD, soldering, enclosure) deferred until hardware is bought.

## 1. Goal

A voice-driven wearable "second brain": press a button, speak, get back a cleaned-up **note**
or a parsed **task with priority**. The device is a thin client; a local laptop server (the
"brain") does transcription + AI. Everything runs locally and free.

**Design model:** store-and-forward — device records audio to SD, uploads to the brain when
Wi-Fi is available, displays the AI result.

**Build strategy:** software + simulator first (zero cost, ~80% of risk), hardware last.

## 2. Locked decisions

| Area | Decision | Rationale |
|------|----------|-----------|
| Device board (sim + HW) | ESP32-S3 + PSRAM, ILI9341 TFT, 3 buttons | RAM headroom for LVGL + future audio/SD/Wi-Fi |
| Device language | C++ (Arduino/PlatformIO) | Microcontroller; only real option |
| Firmware architecture | **Portable core + HAL + ports** (Approach B) | Hardware swap is a stated plan; keeps logic reusable + headless-testable |
| Brain language | **Python (FastAPI)** | faster-whisper is native + frictionless; Ollama is HTTP anyway |
| Monitoring UI | **React + Vite + TypeScript** (`web/`) | User wants a dashboard; talks to brain over HTTP/JSON |
| Transcription | faster-whisper `small.en` | Better than `base` on short speech; fast on CPU |
| AI | Ollama `llama3.2:3b` | Local, free; trivial for note-cleanup / task-parse |
| Device ↔ brain link | cloudflared free tunnel (primary); wokwigw (alt) | Wokwi cloud sim can't reach laptop `localhost`; Wokwi Private Gateway is paid |
| Sim audio | Hardcoded sample WAV + placeholder transcript | No microphone in the Wokwi simulator |

## 3. Core principle: protocol-first

The single most durable part of this system is **the protocol** — the HTTP endpoints + JSON
shapes between device and brain (§5). It is language- and hardware-neutral. Everything else
plugs into it as a swappable edge:

```
   SWAPPABLE EDGE               STABLE CORE                    SWAPPABLE EDGE
 ┌────────────────┐        ┌──────────────────┐        ┌──────────────────────┐
 │ device drivers │        │  PROTOCOL         │        │ brain implementation │
 │ ESP32 / Pi /   │──HAL──▶│  (HTTP + JSON)    │◀─HTTP─▶│ Python now; could be  │
 │ phone (C++...) │        │  the contract     │        │ TS later — same wire  │
 └────────────────┘        └──────────────────┘        └──────────────────────┘
        ▲                                                          ▲
   React monitoring UI (TS) also talks to the brain over the same protocol.
```

Consequences:
- Swap the **device hardware** → only its HAL/port changes; brain + protocol untouched.
- Swap the **brain language** (Python → TS) later → device + protocol untouched.
- The **React UI** is just another protocol client. Backend language is irrelevant to it.

## 4. Architecture

```
[ ESP32-S3 device (Wokwi sim) ]              [ Laptop brain (Python) ]
   C++: LVGL UI, 3-btn nav          HTTP/     FastAPI
   core/ (portable logic)           JSON      faster-whisper (small.en)
   hal/  + ports/esp32s3            ◀──────▶  Ollama (llama3.2:3b)
                                              SQLite (notes, tasks)
                                                  ▲
                                                  │ HTTP/JSON
                                     [ React + Vite + TS monitoring UI ]
                                       lists notes/tasks, watches pipeline
```

Three independent parts, all joined only by the JSON protocol:
- **Brain** (Python) — hardware-agnostic; the AI heavy lifting.
- **Device firmware** (C++) — layered so only the HAL/port changes per board (§7).
- **Monitoring UI** (React/TS) — read-only dashboard over the brain's API.

## 5. The protocol contract (language-neutral seam)

Both the device (C++) and the React UI (TS) code against these. Kept in one place and
documented so any client can implement it.

| Method + path | Body / query | Returns |
|---|---|---|
| `POST /process` | multipart `audio` file + `mode=note\|task` | `{ transcript, result }` |
| `POST /process-sample` | `?mode=note\|task` (runs bundled sample; for sim) | `{ transcript, result }` |
| `GET /notes` | — | `[ { id, text, created_at } ]` |
| `GET /tasks` | — | `[ { id, title, priority, created_at } ]` |
| `GET /health` | — | `{ status: "ok" }` |

Result shapes:
- `mode=note` → `result = { text: <cleaned note> }`
- `mode=task` → `result = { title: str, priority: "high"\|"medium"\|"low" }`

## 6. Phase 1 — Brain + monitoring UI (Python + React, no device hardware)

```
brain/
  main.py            FastAPI app + endpoints (§5)
  transcribe.py      faster-whisper wrapper (loads small.en once)
  ai.py              Ollama: note-cleanup + task-parse (JSON output)
  storage.py         SQLite: notes + tasks
  models.py          Pydantic schemas (mirror the protocol)
  requirements.txt
  test_pipeline.py   posts sample.wav, asserts JSON shape, prints result
  samples/note.wav   short spoken sample (TTS-generated or recorded)
web/                 React + Vite + TypeScript
  src/               dashboard: notes list, tasks list, "send sample" test button
  src/protocol.ts    TS types mirroring §5 (the shared contract, TS side)
```

**Brain behavior:** whisper transcribe → ollama(mode) → persist → return per §5. Task mode
requests Ollama JSON output, validates, defaults `medium` if unclear.

**Error boundaries:** non-audio/empty upload → 400; Ollama unreachable → 503; whisper failure
→ 500; invalid `mode` → 400.

**Verification:**
- `python test_pipeline.py` → posts `samples/note.wav`, asserts 200 + non-empty transcript +
  well-formed `result`, prints both. Whole pipeline proven with no device.
- `web/` runs (`vite dev`), lists notes/tasks from the brain, "send sample" shows a live result.

## 7. Firmware architecture — portable core + HAL + ports (Approach B)

```
firmware/
  core/              framework-free C++ — NO Arduino/chip/LVGL headers
    domain.*         Note, Task, Priority types
    menu.*           menu model + cursor position
    nav.*            button-event state machine (UP/DOWN/SELECT/BACK)
    sync.*           store-and-forward state machine
    protocol.*       build/parse the §5 JSON
  hal/               abstract interfaces (pure virtual)
    IDisplay.h IInput.h IMic.h IStorage.h INet.h
  app/
    ui/              LVGL screens (home/notes/tasks), driven by core state
    main.cpp         wires core → hal for the target
  ports/
    esp32s3/         TFT_eSPI, WiFi, GPIO buttons impls + config.h (pins)
    native/          laptop stubs (for host tests)
  test/              Unity tests: run core on the laptop, no board
  platformio.ini     envs: esp32s3 (sim+hw), native (host tests)
  wokwi.toml, diagram.json
```

Key split:
- **`core/`** = pure logic, zero hardware deps → compiles + unit-tested on the laptop
  (`pio test -e native`). This is the "test the logic without a board" win.
- **`app/ui/`** = LVGL screen construction, driven by `core` state (LVGL kept out of `core`).
- **`hal/` + `ports/`** = the only hardware-specific code. New board = new `ports/<board>/`.

**Swap cost:** component swap → one HAL impl. New ESP32 variant → `config.h` pins + PlatformIO
`board`. New chip family → new `ports/` folder. `core/` + `app/ui/` + brain + protocol untouched.

**YAGNI note:** HAL wraps only what actually changes (display/input/mic/storage/net). No
speculative abstraction.

## 8. Phase 2 — Simulated device UI (Wokwi, no hardware)

Target `esp32s3` env with `ports/esp32s3` + `native` stubs for mic/storage.

**Screens (LVGL, in `app/ui/`):**
- **Home:** list `[ Notes, Tasks ]`, visible cursor.
- **Notes flow:** Notes → "Record" → (SELECT simulates record) → hardcoded transcript →
  `[ Save / Discard ]`.
- **Tasks flow:** Tasks → "New task" → placeholder record → task title + priority (hardcoded) →
  task list.

**Nav (`core/nav`):** DOWN = move, SELECT = enter/confirm, BACK = up. Pure logic, unit-tested
headless in Phase 1's spirit.

**Mic stand-in:** `IMic` native stub returns a fixed sample string — full UI testable with no mic.

**Verification:** Wokwi boots; click through both flows via the 3 buttons; `pio test -e native`
passes for nav/menu logic.

## 9. Phase 3 — Sim ↔ brain round-trip

- ESP32-S3 connects Wi-Fi (`Wokwi-GUEST`).
- User runs the brain, then `cloudflared tunnel --url http://localhost:8000` → public HTTPS URL.
- `ports/esp32s3` `INet` POSTs to `POST /process-sample?mode=note` (server runs the bundled
  sample through whisper + ollama; sim has no mic).
- Returned AI text displays on the TFT.
- **Proves the full chain:** device → brain → Whisper → Ollama → back → screen. React UI shows
  the same new note/task appear.

**Error handling:** Wi-Fi timeout → "No Wi-Fi"; non-200 → "Server error"; retry on SELECT.

**Verification:** with brain + tunnel running, trigger sync from the sim, confirm AI text on the
simulated display and the new item in the React UI.

## 10. Eventual hardware (Phases 4–5, out of current scope)

Full BOM, wiring, and open questions live in `HARDWARE_BRIEF.md` (shared for external hardware
review). Summary: ESP32-S3 + ILI9341 TFT + 3 buttons + INMP441 I2S mic + microSD (SPI) + LiPo +
TP4056, targeting sub-$20. Phase 4 adds real mic + SD + sync (implement `IMic`/`IStorage` in
`ports/esp32s3`); Phase 5 adds battery, protoboard layout, cardboard enclosure.

## 11. Out of scope (v1)

Cloud sync, phone app, wake-word / always-listening, on-device AI, multi-user, OTA updates.

## 12. Risks / watch-items

1. **Wokwi → localhost** needs a tunnel (cloudflared) or paid Private Gateway — budget ~1hr.
2. **Sub-$20** is tight and sourcing-dependent (AliExpress yes, retail no).
3. **Whisper `small.en`** accuracy on short/noisy clips — revisit model size if transcripts poor.
4. **SPI bus sharing** (TFT + SD) under store-and-forward load — validate in Phase 4.
5. **Brain hardening before the Phase 3 tunnel.** The Phase 1 brain is built for localhost/single
   trusted user: `POST /process` has no upload-size cap, transcription has no timeout, and no
   endpoint has authentication. Before exposing it via cloudflared in Phase 3, add an upload size
   limit, a transcription timeout, and at least a shared-secret/token check — otherwise the public
   URL is an unauthenticated, unbounded compute endpoint.
