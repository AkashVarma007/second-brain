# Firmware (ESP32-S3, simulated in Wokwi)

A 3-button notes/tasks menu UI built with LVGL on an ILI9341 display. Phase 2 has no
microphone or networking — a hardcoded sample string stands in for transcribed text.

## Architecture

- `core/` — framework-free C++ (domain types, menu helpers, navigation state machine).
  Compiles and unit-tests on the laptop with **no simulator**.
- `hal/` — hardware interfaces (`IInput`).
- `ports/esp32s3/` — TFT_eSPI + LVGL display, GPIO buttons, pin map.
- `ports/native/` — host stubs for testing.
- `app/ui/` — renders the core's UI state into LVGL widgets (pure presentation).
- `src/main.cpp` — wires it together for the ESP32-S3.

## Build

```bash
cd firmware
pio run -e esp32-s3        # compile the firmware
```

## Test the logic (no hardware, no simulator)

```bash
pio test -e native         # runs the nav/menu/input unit tests on the host
```

## Run in the Wokwi simulator

Open the `firmware/` folder in VS Code with the Wokwi extension, or use the Wokwi CLI.
`wokwi.toml` points at the built `firmware.bin` (a bare application image — Wokwi
flashes it at 0x10000 itself; do **not** feed it a merged bootloader image, that
boot-loops). Controls: the DOWN button moves the cursor, SELECT enters/confirms,
BACK goes up a level.

Pin map (matches `diagram.json`): TFT CS=10, MOSI=11, SCK=12, MISO=13, DC=7, RST=6,
BL=14; buttons DOWN=4, SELECT=5, BACK=15.

### Automated UI regression run

`nav_scenario.yaml` drives all three buttons through every screen and screenshots
each one. It is the only check that covers the *rendered* UI — `pio test -e native`
stops at `core/`. Needs [`wokwi-cli`](https://github.com/wokwi/wokwi-cli/releases)
and a CI token from <https://wokwi.com/dashboard/ci> (a Wokwi Club *license* key is
a different thing and will not authenticate).

```bash
pio run -e esp32-s3
wokwi-cli lint .                      # catches dropped wires; must report 0 errors
WOKWI_CLI_TOKEN=<token> wokwi-cli --timeout 30000 --timeout-exit-code 0 \
  --scenario nav_scenario.yaml --serial-log-file .pio/wokwi-serial.log .
grep 'screen=' .pio/wokwi-serial.log   # the expected transition trace
```

Screenshots land in `.pio/` (gitignored) as `wokwi-shot-*.png`. Expected trace:

```
screen=Home cursor=0
screen=Home cursor=1 notes=0 tasks=0      # DOWN
screen=Home cursor=0 notes=0 tasks=0      # DOWN wraps
screen=NotesMenu    ...                   # SELECT
screen=NoteResult   ...
screen=NoteConfirm  ...
screen=Home cursor=0 notes=1 tasks=0      # SELECT on Save -> note stored
screen=Home cursor=1 notes=1 tasks=0
screen=TasksMenu    ...
screen=TaskResult   ...
screen=TaskList cursor=0 notes=1 tasks=1
screen=Home cursor=0 notes=1 tasks=1      # BACK
```

`wokwi-cli lint` matters: Wokwi silently drops any connection that names a pin the
part does not have. On `board-esp32-s3-devkitc-1` the rails are `3V3.1`, `3V3.2`,
`5V` and `GND.1`..`GND.4` — there is no plain `3V3` or `GND`, and each ground wire
needs its own `GND.n`. The serial terminal also stays blank unless `esp:TX`/`esp:RX`
are wired to `$serialMonitor`.
