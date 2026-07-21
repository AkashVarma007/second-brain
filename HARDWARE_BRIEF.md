# Second Brain — Hardware & Feature Brief (for review)

**What it is:** A tiny voice-driven wearable. You press a button, talk, and it records a
short voice clip. The clip syncs over Wi-Fi to a laptop running a local AI server, which
transcribes the speech and turns it into a cleaned-up **note** or a **task with a priority**.
Results show on the device's small screen. Everything runs locally — no cloud, no subscriptions.

**Design model:** *Store-and-forward.* The device records audio to an SD card and uploads it
to the laptop whenever Wi-Fi is available. The device is a thin client; all the heavy AI work
(speech-to-text + language model) happens on the laptop.

**Build order:** Software + simulator first (costs $0), physical hardware last. This brief
describes the **intended full hardware**, so you can sanity-check the whole thing — even though
the first working version runs in a simulator with no real parts.

---

## Intended hardware (full bill of materials)

| # | Part | Suggested specific part | Interface | Rough cost (AliExpress) | Build phase |
|---|------|------------------------|-----------|------------------------|-------------|
| 1 | **MCU / brain** | ESP32-**S3** module with PSRAM (e.g. ESP32-S3-DevKitC-1, WROOM-1 N16R8 = 16MB flash + 8MB PSRAM) | — | $6–8 | Sim + all phases |
| 2 | **Display** | 2.4" ILI9341 SPI TFT, 240×320 *(for wearable, maybe smaller 1.3" ST7789 IPS 240×240 instead — see open questions)* | SPI | $4 | Phase 2 |
| 3 | **Buttons** | 3× tactile push buttons (Down / Select / Back) | GPIO | $0.30 | Phase 2 |
| 4 | **Microphone** | INMP441 I2S MEMS mic | I2S | $2 | Phase 4 |
| 5 | **Storage** | microSD card breakout (SPI) + microSD card | SPI | $1.50 + card | Phase 4 |
| 6 | **Battery** | 3.7V LiPo, ~500–1000 mAh | — | $3–4 | Phase 5 |
| 7 | **Charge + protect** | TP4056 module **with** battery protection (DW01+FS8205) | — | $0.60 | Phase 5 |
| 8 | Protoboard, wires, headers | — | — | ~$1 | Phase 5 |

**Estimated total: ~$18–21.** Sub-$20 is achievable on AliExpress but **tight** — protection
module, decent battery, and enclosure eat the margin. On Amazon / US retail this is $30+.

**Alternative all-in-one option worth asking about:** *Seeed XIAO ESP32-S3 Sense* (~$14) has a
PSRAM S3 **plus an onboard microphone and microSD slot** in a thumbnail-sized board. It could
replace parts 1, 4, and 5 and shrink the wearable a lot — but its mic is **PDM** (different code
than INMP441 I2S) and it has fewer exposed pins. Listed as an open question below.

---

## How the parts connect (interface plan)

```
                 ESP32-S3
        ┌──────────────────────┐
  SPI ──┤ TFT display (CS #1)   │   TFT + SD share ONE SPI bus,
  SPI ──┤ microSD card (CS #2)  │   separate chip-select (CS) pins  ← please sanity-check
  I2S ──┤ INMP441 microphone    │   (BCLK, WS, DATA)
  GPIO ─┤ 3 buttons             │   (each button → GPIO + GND, internal pull-up)
  GPIO ─┤ TFT backlight         │
  USB ──┤ + LiPo via TP4056     │   run logic at 3.3V
        └──────────────────────┘
```

- **TFT + SD on a shared SPI bus** with separate CS is the common wiring. Flagged for review
  because store-and-forward writes audio to SD while the UI drives the display — possible
  contention.
- **Mic on I2S** (its own peripheral, doesn't touch SPI).
- **3 buttons** on plain GPIO with internal pull-ups.

---

## Features (what the device actually does)

**Core:**
1. **Voice note** — button → record → (sync) → laptop transcribes + AI cleans up grammar → note saved + shown.
2. **Voice task** — button → record → (sync) → laptop transcribes + AI extracts a task title and assigns **priority (high / medium / low)** → task saved + shown in a list.
3. **Store-and-forward sync** — record offline to SD, auto-upload when Wi-Fi is available.
4. **3-button menu** — Home → Notes / Tasks, with Down / Select / Back navigation.
5. **On-screen results** — cleaned note text / parsed task + priority shown on the TFT.

**Laptop side (the "brain," runs locally, free):**
- Speech-to-text: **faster-whisper** (`small.en` model), runs on CPU.
- AI processing: **Ollama** running `llama3.2:3b` (cleans notes / parses tasks).
- Small local API (FastAPI) + local database (SQLite) for notes and tasks.

**Deliberately NOT in v1:** cloud sync, phone app, always-on wake-word, on-device AI.

---

## Software portability (why hardware swaps stay cheap)

The firmware is built in layers with a **Hardware Abstraction Layer (HAL)**:

```
App logic (menu, screens, task flow)   ← never changes when hardware changes
        ↓ talks only to interfaces ↓
HAL: display / input / mic / storage / net
        ↓ actual chip drivers ↓
ILI9341 · INMP441 · SD · Wi-Fi
```

- **Laptop server:** hardware-agnostic. Swap the whole device → zero server changes.
- **UI + app logic:** untouched by hardware swaps.
- **Swapping a component** (different display, mic, or even a different ESP32 variant) = edit
  one HAL file. All pins live in a single `config.h`.

---

## Open questions for you (the hardware expert)

Please poke holes in any of these:

1. **Board choice:** discrete ESP32-S3 DevKit + separate modules (better for learning/wiring),
   vs all-in-one **XIAO ESP32-S3 Sense** (onboard PDM mic + SD, tiny, but fewer pins)? Which
   would you pick for a first wearable?
2. **SPI sharing:** TFT + SD on one SPI bus with separate CS — any real-world problems when we
   write audio to SD while refreshing the display?
3. **Display for a wearable:** is 2.4" ILI9341 too big? Better to use a 1.3" ST7789 IPS? What's
   the backlight power draw / battery hit?
4. **Mic quality:** is INMP441 (or the XIAO's PDM mic) good enough for clean speech-to-text on
   short spoken commands? Any placement / gain gotchas?
5. **Power:** what LiPo capacity for, say, a full day of light use? Is a bare TP4056 fine or do
   we definitely want the protection (DW01) variant? Do we need a boost converter or is 3.3V
   direct from LiPo OK for this display?
6. **Pin budget:** does an ESP32-S3 DevKit have enough usable GPIO for TFT (SPI ~5 pins) + SD
   (shared SPI + 1 CS) + mic I2S (3 pins) + 3 buttons + backlight, with no conflicts?
7. **Is sub-$20 realistic** for this parts list where you'd source, or should I relax that target?

---

*This describes intent for a hobby build. Software (laptop AI + simulated device UI) is built
and proven first; parts are only purchased once the software round-trip works end to end.*
