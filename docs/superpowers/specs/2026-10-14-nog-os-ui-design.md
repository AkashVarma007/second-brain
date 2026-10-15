# NOG-OS UI — first build (design)

**Date:** 2026-10-14 · **Status:** approved to proceed ("proceed as you like") · **Scope:** firmware UI only

Source of truth for the look: the UI mock canvas
(https://claude.ai/artifact/N4j4FnrEww5LbYWzwsV5RV) and the feature roadmap doc
(https://claude.ai/code/artifact/25204d2c-d735-47e7-955e-d02a2b1fc2c9).

## Goal

Replace the Phase-2 LVGL/TFT UI with the NOG-OS pocket UI: all 15 screens of the mock, drawn on a
128×64 monochrome display, driven by a 5-way joystick + Back + TALK. Demo data only. No backend,
no real audio, nothing persisted.

## Decisions

| Area | Decision | Why |
|---|---|---|
| Display | u8g2, 128×64 1-bit, full-buffer mode | Matches the mock and the pocket build; standard for 128×64 mono; Flipper's canvas uses u8g2 fonts |
| Simulator part | Wokwi `board-ssd1306` over I2C (SDA GPIO 8, SCL GPIO 9) | Same 128×64 resolution, built into Wokwi |
| Real hardware | ST7567 LCD over SPI — one constructor swap in the display port | Flipper-class LCD; not in Wokwi |
| Removed | LVGL, TFT_eSPI, ILI9341 wiring | Replaced by u8g2 |
| Input | 7 buttons, active-low, internal pull-up: UP 4, DOWN 5, LEFT 6, RIGHT 7, OK 15, BACK 16, TALK 17 | Joystick + Back + hold-to-talk; TALK reports press *and* release |
| Desktop simulator (SDL) | Not now | Needs a system package; Wokwi covers it |
| Branch | Stay on `main`, uncommitted | User choice |
| Backup | `../second-brain-backups/firmware-phase2-lvgl-2026-10-14.tar.gz` + HEAD `517084d` | User asked for a backup before changes |

## Architecture

```
src/main.cpp        poll keys -> Router; 400 ms tick -> animation frame; redraw on change
core/   (portable, host-tested)
  domain.h          Key, ScreenId, UiState (screen + back stack, cursors, frame, popup, rec timer)
  router.h/.cpp     UI navigation only — the mock's flow; time passed in, never read
  menu.h/.cpp       existing wrap helpers + list window start
  demo.h            demo notes, quests, quips, haiku, results
app/ui/ (device: draws with U8G2)
  sprites.h         pixel art as text rows ('#' = lit), same art as the mock
  gfx.h/.cpp        sprite, dotted rule, inverted row, progress bar, header, popup helpers
  screens.cpp       one draw function per screen
  ui.h/.cpp         render(UiState) dispatch
ports/esp32s3/
  config.h          pins
  display.h/.cpp    the U8G2 instance (SSD1306 for Wokwi; ST7567 line ready)
  buttons.h/.cpp    7 buttons, debounced, TALK press + release
```

## Screens (all 15, as in the mock)

Home (NOG idles, quips rotate, XP bar) · Menu (7 apps, scrollbar) · Talk · Recording (live
waveform, timer) · Thinking (puffs, dots) · Result (kind, text, +XP) · Notes · Quests (checkbox,
priority, strike-through) · Quest-done pop-up · NOG card (level, mood hearts, streak, XP) ·
Evolution (egg → NOG → ???) · Daily recap (haiku + pixel postcard) · Sync (queue, progress) ·
Setup (brightness bar, toggles) · Sleep (Z's).

## Behaviour (UI only)

- Home: OK → Menu; Up → NOG card; Down → Notes; Left → Quests; Right → Recap.
- Menu: Up/Down move (wraps), OK/Right opens, Back/Left → Home.
- Lists (Notes 3, Quests 5, Setup 4): Up/Down move; Back pops. OK on a quest toggles it and shows
  the "QUEST DONE +20 XP" pop-up for 1.4 s.
- NOG card: OK → Evolution. Back always pops the stack (empty stack → Home).
- TALK held anywhere (except while recording/thinking) → Recording; release → Thinking; after
  2.2 s → Result (cycles quest / idea / journal). Result: OK → Home, Back → Talk screen.
  Recording auto-stops at 30 s.
- Home idle 20 s → Sleep; any key wakes to Home.

## Testing

1. `pio test -e native` — Router: shortcuts, menu wrap, back stack, list windows, quest toggle +
   pop-up expiry, talk flow timing, sleep/wake.
2. `pio run -e esp32-s3` — firmware builds.
3. `wokwi-cli lint` + `screens_scenario.yaml` — drives the 7 buttons and screenshots every screen
   to `.pio/`; screenshots compared by eye against the mock.

## Out of scope

Backend/sync, real mic/SD/Wi-Fi, persistence, XP/level maths, desktop SDL simulator, the 3D wiring
page and GIF in `docs/` (now outdated — flagged, not regenerated).
