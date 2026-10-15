# Second Brain — Wiring & Electrical Reference (NOG-OS UI)

This documents the electrical setup **exactly as wired in the Wokwi simulator**, plus the
pocket-build display it stands in for.

**Source of truth:** [`firmware/diagram.json`](diagram.json) (the Wokwi netlist). It must
agree with [`ports/esp32s3/config.h`](ports/esp32s3/config.h), the pin `#define`s the
firmware uses. If a GPIO changes, change both, then run `wokwi-cli lint .`.

> **Scope:** 128×64 display + 7 buttons. No microphone, SD card, battery or Wi-Fi wiring yet.
> Those parts are in [`../HARDWARE_BRIEF.md`](../HARDWARE_BRIEF.md).
>
> **Outdated elsewhere:** the 3D inspector ([`docs/wiring-3d.html`](../docs/wiring-3d.html))
> and its GIF still show the earlier Phase-2 wiring (2.4" ILI9341 + 3 buttons).

---

## Components

| ID | Part | Interface | Notes |
|----|------|-----------|-------|
| `esp` | ESP32-S3-DevKitC-1 | — | Logic level **3.3 V**. |
| `oled` | SSD1306 128×64 OLED (`board-ssd1306`) | I2C, address `0x3c` | Simulator/bench stand-in for the pocket build's ST7567 LCD. |
| `btnUp` `btnDown` `btnLeft` `btnRight` | Push buttons (black) | GPIO | The 5-way joystick's directions. |
| `btnOk` | Push button (yellow) | GPIO | Joystick centre press. |
| `btnBack` | Push button (white) | GPIO | Up a level. |
| `btnTalk` | Push button (red) | GPIO | Hold to talk — the firmware reads press **and** release. |

---

## Master connection list

### Display (I2C)

| From (`oled`) | To (ESP32-S3) | Colour | Function |
|---|---|---|---|
| `VCC` | 3.3 V (`3V3.1`) | red | Supply |
| `GND` | `GND.1` | black | Ground |
| `SDA` | **GPIO 8** | blue | I2C data |
| `SCL` | **GPIO 9** | purple | I2C clock, 400 kHz |

### Buttons (active-low, internal pull-up)

| Button | Signal → GPIO | Colour |
|---|---:|---|
| UP | **4** | green |
| DOWN | **5** | green |
| LEFT | **6** | green |
| RIGHT | **7** | green |
| OK | **15** | orange |
| BACK | **16** | white |
| TALK | **17** | red |

**Ground chain:** the board has only `GND.1`..`GND.4`, and Wokwi drops a second wire on the
same named pin. So `btnUp:2.r` goes to `GND.2` and each button's `2.l` connects to the next
button's `2.r` (Up → Left → OK → Right → Down → Back → Talk). Each button's two `2.*` legs are
the same contact, so the chain is one ground net. On a real board, all buttons share a GND rail.

### Serial (simulator only)

`esp:TX` → `$serialMonitor:RX`, `esp:RX` → `$serialMonitor:TX`: the Wokwi console.

---

## ESP32-S3 GPIO usage map

| GPIO | Used by | Direction |
|-----:|---------|-----------|
| 4 | Button UP | input, pull-up |
| 5 | Button DOWN | input, pull-up |
| 6 | Button LEFT | input, pull-up |
| 7 | Button RIGHT | input, pull-up |
| 8 | OLED SDA | I2C |
| 9 | OLED SCL | I2C |
| 15 | Button OK | input, pull-up |
| 16 | Button BACK | input, pull-up |
| 17 | Button TALK | input, pull-up |
| 10, 11, 12, 14, 21 | Reserved: ST7567 LCD (pocket build): CS, MOSI, SCK, DC, RST | SPI + control |
| 13 | Reserved: claimed as MISO whenever hardware SPI starts — keep it free | — |

---

## Button circuit

All seven buttons are **active-low with the MCU's internal pull-up** (no external resistors):
`pinMode(pin, INPUT_PULLUP)`, idle reads HIGH, pressed reads LOW, 25 ms debounce in
[`buttons.cpp`](ports/esp32s3/buttons.cpp). A press is the HIGH→LOW edge; TALK also reports
the LOW→HIGH edge as its release. In the simulator the parts set `bounce: 0`.

---

## Pocket build: ST7567 LCD (SPI)

Not in Wokwi. Planned pins (reserved in `config.h`): SCK 12, MOSI 11, CS 10, DC 14, RST 21.
Hardware SPI on the S3 always claims GPIO 11, 12 **and 13** (MISO, forced to input), so no
control line may use them; `config.h` enforces this with a compile-time check.
To switch, replace the SSD1306 constructor in [`display.cpp`](ports/esp32s3/display.cpp) with
the commented ST7567 one matching your module (`_ENH_DG128064_`, `_JLX12864_` or
`_OS12864_`), then **calibrate contrast** — it differs per panel. The ST7567's backlight LED
should be driven through a transistor or a series resistor, not straight from a GPIO.

---

## Keeping it in sync

| File | Holds |
|---|---|
| `diagram.json` | the physical wires (Wokwi) |
| `ports/esp32s3/config.h` | the pins the firmware reads |
| this file | the human-readable map |

After any change: `wokwi-cli lint .` (must report 0 errors), then `pio run -e esp32-s3`.
