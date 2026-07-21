# Second Brain

> 🚧 **Work in progress — early development.** Personal project under active construction.
> The design is complete, but most code isn't written yet and **nothing here runs today.**
> Structure and details will change. The phases below show where it's headed.

A voice-driven wearable "second brain." Press a button, speak, and get back a cleaned-up
**note** or a parsed **task with a priority** — all processed locally, free, no cloud.

> **Status:** 🟡 Design complete, implementation starting. Phases 1–3 (software + simulator)
> are being built first; hardware (Phases 4–5) comes later. See
> [`docs/superpowers/specs/2026-07-21-second-brain-design.md`](docs/superpowers/specs/2026-07-21-second-brain-design.md).

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
| `brain/` | Python FastAPI server — Whisper + Ollama + SQLite | ⏳ Phase 1 |
| `web/` | React + Vite + TypeScript monitoring dashboard | ⏳ Phase 1 |
| `firmware/` | ESP32-S3 firmware (LVGL UI), runs in Wokwi simulator | ⏳ Phase 2–3 |

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

> Setup instructions land here as each phase is built. Nothing to run yet — implementation
> begins with Phase 1 (the Python brain).

## License

TBD (personal project).
