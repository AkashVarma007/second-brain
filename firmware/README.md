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
`wokwi.toml` points at the built `firmware.bin`. Controls: the DOWN button moves the
cursor, SELECT enters/confirms, BACK goes up a level.

Pin map (matches `diagram.json`): TFT CS=10, MOSI=11, SCK=12, MISO=13, DC=7, RST=6,
BL=14; buttons DOWN=4, SELECT=5, BACK=15.
