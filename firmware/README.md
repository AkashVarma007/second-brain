# Firmware (ESP32-S3) — NOG-OS UI

The pocket UI of Second Brain: NOG the pixel pet, a Flipper-style menu and 15 screens on a
128×64 monochrome display, driven by a 5-way joystick, BACK and a hold-to-talk button.
This build is **UI only**: notes, quests, results and sync are demo data, nothing is saved
and there is no microphone or networking yet.

Design: [`docs/superpowers/specs/2026-10-14-nog-os-ui-design.md`](../docs/superpowers/specs/2026-10-14-nog-os-ui-design.md).

## Architecture

- `core/` — framework-free C++: `Router` (which screen shows, list selection, the
  hold-to-talk flow, pop-up and sleep timers) and `demo.h` (demo content). Time is passed in,
  so it unit-tests on the laptop.
- `app/ui/` — draws every screen with the **u8g2 C API** (`u8g2_t*`): `ui.cpp` (screens),
  `gfx.*` (drawing kit), `sprites.h` (pixel art as `'#'` rows — edit them directly).
  Because it only needs u8g2's portable C core, the same code also renders on the laptop.
- `hal/` — `IInput`.
- `ports/esp32s3/` — the panel (`display.cpp`), the 7 buttons and the pin map.
- `ports/native/` — host stubs for tests.
- `tools/render/` — host render tool: every screen to PNG, no board or simulator.
- `src/main.cpp` — buttons → `Router`, 400 ms animation tick, redraw.

## Build

```bash
cd firmware
pio run -e esp32-s3        # compile the firmware (first run downloads u8g2)
```

## Test

```bash
pio test -e native         # Router + menu + input logic on the host
tools/render/render.sh     # draws all 15 screens to .pio/renders/*.png + sheet.png
```

`render.sh` also self-checks the drawing kit and **fails if any demo text overflows its
slot**. It needs `g++` and `python3` and the u8g2 copy that `pio run -e esp32-s3` downloads.

## Controls

| Key | Home | Menu | Lists (Notes, Quests, Setup) |
|---|---|---|---|
| OK | open menu | open app | Quests: tick / untick |
| UP / DOWN | NOG card / Notes | move | move |
| LEFT / RIGHT | Quests / Recap | back / open | — |
| BACK | — | Home | up a level |
| TALK (hold) | record from anywhere; release → thinking → result | | |

NOG card: OK opens Evolution. Result: OK keeps it (Home), BACK "undoes" it (Talk screen).
20 s idle on Home and NOG falls asleep; any key wakes it.

## Display: simulator vs pocket build

Wokwi has no ST7567, so the simulator (and a bench build) uses an **SSD1306 128×64 OLED over
I2C** — same resolution, same UI. The pocket build uses an **ST7567 128×64 LCD over SPI**:
swap the panel constructor in `ports/esp32s3/display.cpp` (the line is there, commented) and
calibrate its contrast. Pins for both are in `ports/esp32s3/config.h`; wiring in
[`WIRING.md`](WIRING.md).

## Run in the Wokwi simulator

Open `firmware/` in VS Code with the Wokwi extension, or use the CLI. `wokwi.toml` points at
the bare `firmware.bin` (Wokwi flashes it at 0x10000 itself; a merged bootloader image
boot-loops).

### Automated UI regression run

`screens_scenario.yaml` drives all 7 buttons through every screen and screenshots each one.
Needs [`wokwi-cli`](https://github.com/wokwi/wokwi-cli/releases) and a CI token from
<https://wokwi.com/dashboard/ci> (a Wokwi Club *license* key will not authenticate).

```bash
pio run -e esp32-s3
wokwi-cli lint .                      # catches dropped wires; must report 0 errors
WOKWI_CLI_TOKEN=<token> wokwi-cli --timeout 60000 --timeout-exit-code 0 \
  --scenario screens_scenario.yaml --serial-log-file .pio/wokwi-serial.log .
grep 'screen=' .pio/wokwi-serial.log   # the transition trace
```

Screenshots land in `.pio/` (gitignored) as `wokwi-shot-NN-<screen>.png`. Expected trace:

```
screen=Home → Menu → Talk → Recording → Thinking → Result → Home → Notes → Home
→ Quests → Home → Pet → Evo → Pet → Home → Recap → Home → Menu → Sync → Menu
→ Setup → Menu → Home → Sleep
```

`wokwi-cli lint` matters: Wokwi silently drops any connection that names a pin the part
does not have. On `board-esp32-s3-devkitc-1` the rails are `3V3.1`, `3V3.2`, `5V` and
`GND.1`..`GND.4`; there is no plain `3V3` or `GND`. The seven buttons share `GND.2` by
daisy-chaining their ground legs. The serial terminal stays blank unless `esp:TX`/`esp:RX`
are wired to `$serialMonitor`.
