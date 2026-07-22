# Second Brain

> 🚧 **Work in progress — early development.** Personal project under active construction.
> Phase 1 (the laptop brain + dashboard) runs today; Phase 2 (the simulated ESP32-S3 UI) compiles
> clean with its navigation logic host-tested and Wokwi project files ready — see **Status** below.
> Later phases (device↔brain networking, hardware) are still ahead. Structure and details will change.

A voice-driven wearable "second brain." Press a button, speak, and get back a cleaned-up
**note** or a parsed **task with a priority** — all processed locally, free, no cloud.

> **Status:** 🟢 Phase 1 complete — the laptop brain and monitoring dashboard work end to end.
> 🟢 Phase 2 complete — the ESP32-S3 UI (LVGL, 3-button nav) compiles for the Wokwi simulator,
> with its navigation logic unit-tested on the host; Wokwi project files are included to run it.
> Phase 3 (device↔brain round-trip over Wi-Fi) is next; hardware comes after.
> See [`docs/superpowers/specs/2026-07-21-second-brain-design.md`](docs/superpowers/specs/2026-07-21-second-brain-design.md).

## What it is

A tiny wearable device records a short voice clip. The clip syncs over Wi-Fi to a local
"brain" running on your laptop, which transcribes the speech and turns it into a note or a
task. Results show on the device screen and in a web dashboard. Everything runs on your own
machine — no subscriptions, no cloud.

**Design model:** *store-and-forward* — the device records to an SD card and uploads to the
brain whenever Wi-Fi is available.

## Architecture (protocol-first)

Three parts, joined only by a language-neutral **HTTP + JSON protocol** — so any part can be
swapped without touching the others:

```
  DEVICE (C++)            PROTOCOL (HTTP+JSON)           BRAIN (Python)
  ESP32-S3          ◀───────── the stable seam ─────────▶ FastAPI
  screen, buttons,                                         faster-whisper (speech→text)
  record, display                                          Ollama llama3.2:3b (AI)
                                                           SQLite (notes, tasks)
                                                              ▲
                                          MONITORING UI (React + Vite + TS)
                                          lists notes/tasks, watches the pipeline
```

- **Device** and **brain** language are each swappable behind the protocol.
- Firmware is layered (portable `core/` + `hal/` + per-board `ports/`) so new hardware only
  needs a new port — see the spec.

## Repository layout

| Path | What | Status |
|------|------|--------|
| `docs/` | Design spec + notes | ✅ done |
| `HARDWARE_BRIEF.md` | Full hardware BOM + open questions (for hardware review) | ✅ done |
| `brain/` | Python FastAPI server — Whisper + Ollama + SQLite | ✅ Phase 1 |
| `web/` | React + Vite + TypeScript monitoring dashboard | ✅ Phase 1 |
| `firmware/` | ESP32-S3 firmware (LVGL UI), runs in Wokwi simulator | ✅ Phase 2 (sim UI) |

## Build phases

1. **Phase 1** — Laptop brain (Python) + React dashboard. *No hardware.*
2. **Phase 2** — Simulated device UI in Wokwi (LVGL, 3 buttons). *No hardware.*
3. **Phase 3** — Simulated device ↔ brain round-trip over Wi-Fi. *No hardware.*
4. **Phase 4** — Real microphone + SD card (needs hardware).
5. **Phase 5** — Battery, enclosure, packaging (needs hardware).

Phases 1–3 cost nothing and validate ~80% of the project before any parts are bought.

## Tech stack

- **Brain:** Python, FastAPI, [faster-whisper](https://github.com/SYSTRAN/faster-whisper) (`small.en`), [Ollama](https://ollama.com) (`llama3.2:3b`), SQLite
- **Dashboard:** React, Vite, TypeScript
- **Device:** ESP32-S3, Arduino framework, PlatformIO, LVGL, tested in the [Wokwi](https://wokwi.com) simulator
- **Link:** HTTP over Wi-Fi (cloudflared tunnel to reach the laptop from the simulator)

## Running

Prerequisites: Python 3.12, Node 22+, [Ollama](https://ollama.com) running locally, and ~3 GB
free disk for the models.

```bash
# 1. one-time setup
cd brain && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
ollama pull llama3.2:3b
cd ../web && npm install

# 2. start the brain (terminal 1)
cd brain && .venv/bin/uvicorn app.main:app --reload --port 8000

# 3. start the dashboard (terminal 2)
cd web && npm run dev
```

Then open <http://localhost:5173>. API docs live at <http://localhost:8000/docs>.

Verify the whole pipeline end to end:

```bash
cd brain && .venv/bin/python test_pipeline.py --mode task
```

## License

TBD (personal project).
