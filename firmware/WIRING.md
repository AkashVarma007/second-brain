# Second Brain — Wiring & Electrical Reference (Phase 2)

This documents the **Phase-2 electrical setup** exactly as wired in the Wokwi simulator.

**Source of truth:** [`firmware/diagram.json`](diagram.json) (the Wokwi netlist). It is kept in
sync with two firmware files that must always agree with it:

- [`ports/esp32s3/config.h`](ports/esp32s3/config.h) — the pin `#define`s the app code uses.
- [`platformio.ini`](platformio.ini) — the `TFT_*` pin `#define`s the TFT_eSPI driver uses.

If any GPIO number changes, it has to change in **all three** or the build and the simulation
disagree silently. `wokwi-cli lint .` catches wires that point at pins that don't exist.

> **Phase 2 = display + 3 buttons only.** No microphone, SD card, battery, or Wi-Fi radio
> wiring yet. Those parts are specified in [`../HARDWARE_BRIEF.md`](../HARDWARE_BRIEF.md) and
> summarised under [Future hardware](#future-hardware-phase-4-5) below.

---

## Components

| ID | Part | Interface | Notes |
|----|------|-----------|-------|
| `esp` | ESP32-S3-DevKitC-1 | — | MCU. Logic level **3.3 V**. |
| `lcd` | ILI9341 2.4″ TFT, 240×320 | SPI | Write-only in this UI. Backlight active-**HIGH**. |
| `btnDown` | Tactile push button (green) | GPIO | DOWN — moves cursor. |
| `btnSelect` | Tactile push button (blue) | GPIO | SELECT — enters / confirms. |
| `btnBack` | Tactile push button (red) | GPIO | BACK — up a level. |

---

## Master connection list

Every wire in `diagram.json`, grouped by function. **Colour** is the wire colour in the
diagram so this table and the picture match.

### Power & ground

| From | To (ESP32-S3) | Wokwi rail | Colour | Function |
|------|---------------|-----------|--------|----------|
| `lcd:VCC` | 3.3 V | `3V3.1` | 🔴 red | Display supply |
| `lcd:GND` | GND | `GND.1` | ⚫ black | Display ground |
| `btnDown:2` | GND | `GND.2` | ⚫ black | Button return |
| `btnSelect:2` | GND | `GND.3` | ⚫ black | Button return |
| `btnBack:2` | GND | `GND.4` | ⚫ black | Button return |

### Display — SPI bus + control lines

| From (`lcd`) | To GPIO | Colour | Function |
|--------------|--------:|--------|----------|
| `MOSI` | **11** | 🔵 blue | SPI data, MCU → display |
| `SCK` | **12** | 🟣 purple | SPI clock |
| `MISO` | **13** | ⚪ gray | SPI data, display → MCU (unused by draw; wired for a complete bus) |
| `CS` | **10** | 🟠 orange | SPI chip-select (active low) |
| `D/C` | **7** | 🟢 green | Data / Command select |
| `RST` | **6** | 🟡 yellow | Hardware reset |
| `LED` | **14** | ⚪ white | Backlight enable (active HIGH) |

SPI clock: **40 MHz** (`SPI_FREQUENCY=40000000`). Port: **FSPI / GPSPI2** — see
[SPI notes](#spi-bus-notes).

### Buttons — signal lines (active-low)

| Button | Signal → GPIO | Colour | GND → rail |
|--------|--------------:|--------|-----------|
| DOWN | **4** | 🟢 green | `GND.2` |
| SELECT | **5** | 🔵 blue | `GND.3` |
| BACK | **15** | 🔴 red | `GND.4` |

### Serial (simulator only)

| From | To | Function |
|------|----|---------|
| `esp:TX` | `$serialMonitor:RX` | Firmware logs → Wokwi terminal |
| `esp:RX` | `$serialMonitor:TX` | Terminal → firmware |

This pair only exists to give the simulator a console. It is not part of the physical device
wiring.

---

## ESP32-S3 GPIO usage map

| GPIO | Used by | Direction |
|-----:|---------|-----------|
| 4 | Button DOWN | input, pull-up |
| 5 | Button SELECT | input, pull-up |
| 6 | TFT RST | output |
| 7 | TFT D/C | output |
| 10 | TFT CS | output |
| 11 | TFT MOSI | output (SPI) |
| 12 | TFT SCK | output (SPI) |
| 13 | TFT MISO | input (SPI, idle) |
| 14 | TFT backlight | output |
| 15 | Button BACK | input, pull-up |

10 GPIO used. The S3 DevKitC-1 has plenty left for the Phase 4/5 parts (SD shares the SPI bus
and needs only one more CS; the mic needs 3 for I2S).

---

## Button circuit

All three buttons are **active-low with the MCU's internal pull-up** — no external resistors.

- Firmware: `pinMode(pin, INPUT_PULLUP)` ([`buttons.cpp`](ports/esp32s3/buttons.cpp)).
- Idle the pin reads **HIGH**; pressing connects it to GND, so it reads **LOW**.
- A press is the HIGH→LOW (falling) edge, with a **25 ms** debounce window in firmware.
- In the simulator the parts set `bounce: 0` so the virtual buttons don't add contact bounce.

```
   3.3V
    │
   [internal pull-up ~45kΩ]     (inside the ESP32-S3)
    │
    ├──────────────► GPIO (4 / 5 / 15)   reads HIGH idle, LOW pressed
    │
   ─┴─  push button
    │
   GND (GND.2 / GND.3 / GND.4)
```

Each button gets **its own GND pin** (`GND.2`, `.3`, `.4`). On a real board they can share one
ground rail; the separate pins here are because Wokwi drops a duplicate-named ground wire.

---

## Power & ground

- Everything runs at **3.3 V**. The display is fed from the DevKitC-1's `3V3` rail (`3V3.1`),
  which the board's regulator supplies from USB 5 V.
- The board exposes the 3.3 V rail as `3V3.1` / `3V3.2` and ground as `GND.1`…`GND.4`. There is
  **no** plain `3V3` or `GND` pad name — naming one makes Wokwi silently drop that wire.
- **Real-hardware flag:** GPIO 14 drives the backlight LED **directly** here. That is fine in
  the simulator, but a physical panel's backlight can pull more current than a GPIO should
  source — on the real build, drive it through a transistor or a series resistor, or confirm
  the specific module has an onboard backlight driver.

---

## SPI bus notes

The display is on the ESP32-S3's **FSPI** peripheral, which resolves to hardware **GPSPI2**
(register base `0x60024000`).

`platformio.ini` sets **`-D USE_FSPI_PORT`**. This is **required**, not a preference: without it,
TFT_eSPI's S3 header falls back to `SPI_PORT = FSPI = 1`, and the IDF macro
`REG_SPI_BASE(1)` evaluates to `0`, so every SPI register write lands on address `0x0` and the
first `tft.begin()` dies with `Guru Meditation Error: StoreProhibited, EXCVADDR: 0x00000000`.
The full chain is documented in the comment on that flag in `platformio.ini`. This would crash
real hardware too, not just the simulator.

---

## Keeping it in sync

Three files carry the pin numbers and **must agree**:

| File | Holds | Example |
|------|-------|---------|
| `diagram.json` | the physical wires (Wokwi) | `["lcd:CS", "esp:10", ...]` |
| `ports/esp32s3/config.h` | pins the app logic reads | `#define PIN_TFT_CS 10` |
| `platformio.ini` | pins the TFT_eSPI driver reads | `-D TFT_CS=10` |

After any change: run **`wokwi-cli lint .`** (catches wires to non-existent pins — the failure
mode that silently unpowered the display before), then `pio run -e esp32-s3` to confirm the
driver defines still compile.

---

## Future hardware (Phase 4–5)

Not wired yet. Planned additions from [`../HARDWARE_BRIEF.md`](../HARDWARE_BRIEF.md):

| Part | Interface | Pins needed | Note |
|------|-----------|-------------|------|
| microSD breakout | SPI (**shared** with the display) | +1 CS | Same MOSI/MISO/SCK as the TFT, separate CS. Possible bus contention while writing audio during a screen refresh — flagged for hardware review. |
| INMP441 mic | I2S (own peripheral) | 3 (BCLK, WS, DATA) | Doesn't touch the SPI bus. |
| LiPo + TP4056 | power | — | 3.7 V cell, charge/protect module; logic still 3.3 V. |

When these land, add their wires to `diagram.json` (or the real schematic), extend the GPIO map
above, and re-run the sync checks.
