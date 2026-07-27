# Phase 2: Simulated ESP32-S3 UI (Wokwi) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the ESP32-S3 firmware for a 3-button notes/tasks menu UI (LVGL on an ILI9341 display), structured as a portable core + HAL + ports, running in the Wokwi simulator. No real hardware, no audio — a hardcoded sample string stands in for transcribed text.

**Architecture:** Approach B from the design spec (§7). Pure, framework-free `core/` holds the domain types + menu model + navigation state machine, and is unit-tested on the laptop via `pio test -e native` with zero simulator. `hal/` defines interfaces; `ports/esp32s3/` implements them with TFT_eSPI + LVGL + GPIO buttons; `ports/native/` provides host stubs. `app/ui/` renders the core's UI state through LVGL — LVGL is a pure display layer; all navigation logic lives in `core/` where it is testable.

**Tech Stack:** C++17, PlatformIO, Arduino framework for ESP32-S3, LVGL 8.3.4, TFT_eSPI 2.5.23, Unity (host tests). Wokwi simulator (`board-esp32-s3-devkitc-1` + `wokwi-ili9341` + 3× `wokwi-pushbutton`).

## Global Constraints

From `docs/superpowers/specs/2026-07-21-second-brain-design.md` (§7, §8) and the verified environment:

- **Board:** ESP32-S3 (`esp32-s3-devkitc-1`). Display: ILI9341 (240×320). Buttons: 3 (DOWN / SELECT / BACK).
- **Library versions (pinned, Wokwi-compatible):** `lvgl/lvgl@^8.3.4`, `bodmer/TFT_eSPI@^2.5.23`.
- **LVGL + TFT config is done entirely via `build_flags`** in `platformio.ini` — no committed `lv_conf.h` and no committed `User_Setup.h`. This keeps the repo self-contained. LVGL uses `-D LV_CONF_SKIP -D LV_CONF_INCLUDE_SIMPLE`; TFT_eSPI uses `-D USER_SETUP_LOADED=1` plus per-pin defines.
- **Pin map (ESP32-S3, in `ports/esp32s3/config.h`):** TFT: `CS=10, MOSI=11, SCLK=12, MISO=13, DC=7, RST=6, BL=14`. Buttons (INPUT_PULLUP, pressed = LOW): `BTN_DOWN=4, BTN_SELECT=5, BTN_BACK=15`. No pin is used twice.
- **`core/` must not include any Arduino, LVGL, or TFT header.** It is plain C++17 (`std::string`, `std::vector` are allowed — the ESP32 Arduino core supports the STL). This is what lets it compile and run under the `native` test environment.
- **Navigation logic lives only in `core/nav`.** `app/ui` never decides transitions; it only renders `nav.ui()`.
- **The "transcribed text" is injected, not hardcoded in logic.** `Nav` is constructed with a sample note string and a sample task; tests inject known values, `main` injects the Phase-2 stand-in. (Phase 3 will replace the injected value with a server response.)
- **Verification is compile + host tests + a headless sim run.** Every firmware task gates on `pio run -e esp32-s3` (compiles, produces `firmware.bin`) and/or `pio test -e native` (logic passes). ~~The Wokwi files are made correct-by-construction (valid JSON/TOML, pins cross-checked against `config.h`); running the visual sim is left to the user.~~
  **CORRECTED 2026-07-23 — "correct-by-construction" was not good enough and shipped three real defects** (invalid `esp:3V3`/`esp:GND` pin names that silently dropped 5 wires, a missing `$serialMonitor` link, and a bogus `rotation` attr), plus it hid a fourth defect in the firmware itself (the `USE_FSPI_PORT` null-SPI-base crash — see Task 3). Valid JSON is not a working diagram. The sim is now run headless from this machine via `wokwi-cli` (`--scenario nav_scenario.yaml`), which lints the diagram, captures serial, drives the buttons and screenshots every screen. Requires a Wokwi CI token.

## Verified Environment (checked 2026-07-22)

- PlatformIO Core 6.1.18; `~/.platformio` present with `espressif32` and `native` platforms already installed (first `esp32-s3` build still downloads the toolchain packages, ~1–2 GB).
- g++ 13.3.0 (host compiler for `pio test -e native`).
- Disk: 15 GB free. Node 22 available (not needed for this phase).
- Wokwi part types confirmed: `board-esp32-s3-devkitc-1`, `wokwi-ili9341`, `wokwi-pushbutton`.
- LVGL 8 init API confirmed (context7): `lv_init()` → `lv_disp_draw_buf_init()` → `lv_disp_drv_init/register()` with a `flush_cb` → `lv_timer_handler()` in loop.

## File Structure

| Path | Responsibility |
|---|---|
| `firmware/platformio.ini` | Two envs: `esp32-s3` (build + Wokwi target) and `native` (host tests). All LVGL/TFT build flags. |
| `firmware/core/domain.h` | `Priority`, `Task`, `Screen`, `Event`, `UiState` — plain C++ types |
| `firmware/core/menu.h` / `.cpp` | Cursor/list helpers used by nav (bounded increment/decrement) |
| `firmware/core/nav.h` / `.cpp` | The navigation state machine: `Nav::handle(Event)`, `Nav::ui()` |
| `firmware/hal/IInput.h` | `enum class InputEvent`, `struct IInput { virtual Event poll() = 0; }` |
| `firmware/hal/IDisplayUI.h` | `struct IDisplayUI { virtual void render(const UiState&) = 0; }` (app/ui implements) |
| `firmware/ports/esp32s3/config.h` | All pin numbers + the Phase-2 sample note/task |
| `firmware/ports/esp32s3/buttons.h` / `.cpp` | Reads the 3 GPIO buttons → debounced `Event` (implements `IInput`) |
| `firmware/ports/esp32s3/display_tft.h` / `.cpp` | LVGL + TFT_eSPI init and flush callback |
| `firmware/ports/native/input_stub.h` | Scripted `IInput` for host tests (queue of events) |
| `firmware/app/ui/ui.h` / `.cpp` | Builds LVGL widgets for each `Screen` from `UiState` |
| `firmware/src/main.cpp` | Wires port + core + ui for the ESP32-S3 target; the loop |
| `firmware/test/test_nav/test_nav.cpp` | Unity tests for the nav state machine (host) |
| `firmware/test/test_menu/test_menu.cpp` | Unity tests for menu cursor helpers (host) |
| `firmware/wokwi.toml` | Points Wokwi at the built firmware |
| `firmware/diagram.json` | ESP32-S3 + ILI9341 + 3 buttons, wired to the `config.h` pins |
| `firmware/README.md` | How to build, host-test, and run in Wokwi |
| `firmware/.gitignore` | `.pio/` |

---

### Task 1: Firmware scaffold + native test harness

**Files:**
- Create: `firmware/platformio.ini`
- Create: `firmware/.gitignore`
- Create: `firmware/core/domain.h`
- Create: `firmware/test/test_menu/test_menu.cpp`
- Create: `firmware/core/menu.h`, `firmware/core/menu.cpp`

**Interfaces:**
- Consumes: nothing
- Produces:
  - `core/domain.h`: `enum class Priority { High, Medium, Low }`, `struct Task { std::string title; Priority priority; }`, `enum class Screen { Home, NotesMenu, NoteResult, NoteConfirm, TasksMenu, TaskResult, TaskList }`, `enum class Event { Down, Select, Back }`
  - `core/menu.h`: `int menu_next(int cursor, int count)` and `int menu_prev(int cursor, int count)` — wrap-around cursor movement, both no-ops when `count <= 0`
  - a working `pio test -e native`

- [ ] **Step 1: Create `firmware/.gitignore`**

```
.pio/
```

- [ ] **Step 2: Write `firmware/platformio.ini`**

```ini
; Second Brain — Phase 2 firmware
; Two environments:
;   esp32-s3 : builds the real firmware (also the Wokwi target)
;   native   : compiles core/ on the host and runs Unity tests (no simulator)

[platformio]
src_dir = src

[env:esp32-s3]
platform = espressif32
board = esp32-s3-devkitc-1
framework = arduino
lib_deps =
    lvgl/lvgl@^8.3.4
    bodmer/TFT_eSPI@^2.5.23
build_flags =
    -std=gnu++17
    -I core
    -I hal
    -I ports/esp32s3
    -I app/ui
    ; ---- LVGL: configure via flags, no lv_conf.h ----
    -D LV_CONF_SKIP
    -D LV_CONF_INCLUDE_SIMPLE
    -D LV_COLOR_DEPTH=16
    ; LV_COLOR_16_SWAP is left at its default (0): the flush uses
    ; tft.pushColors(..., swap=true), which already byte-swaps for the panel's
    ; big-endian wire order. Setting SWAP=1 too would double-swap -> wrong colors.
    ; LVGL reads the tick from Arduino millis() via LV_TICK_CUSTOM=1. Do NOT set
    ; LV_TICK_CUSTOM_INCLUDE / _SYS_TIME_EXPR: their defaults ("Arduino.h" and
    ; (millis())) already apply, and passing "(millis())" through build_flags
    ; breaks the shell (unbalanced paren).
    -D LV_TICK_CUSTOM=1
    -D LV_USE_LOG=1
    ; LV_FONT_DEFAULT is left at LVGL's default (&lv_font_montserrat_14 when the
    ; font is enabled below). Setting it via -D passes a bare '&' to the shell,
    ; read as "run in background", which breaks the build.
    -D LV_FONT_MONTSERRAT_14=1
    -D LV_FONT_MONTSERRAT_16=1
    -D LV_THEME_DEFAULT_DARK=1
    ; ---- TFT_eSPI: ILI9341 on ESP32-S3, configured via flags ----
    ; USE_FSPI_PORT is REQUIRED on the S3, it is not a preference. Without it
    ; TFT_eSPI_ESP32_S3.h falls back to "#define SPI_PORT FSPI", and the Arduino
    ; core defines FSPI as 1. The IDF macro is
    ;   REG_SPI_BASE(i) = ((i)>=2) ? (DR_REG_SPI2_BASE + (i-2)*0x1000) : (0)
    ; so REG_SPI_BASE(1) evaluates to 0 and every direct register write in the
    ; driver (*_spi_cmd, *_spi_w, ...) targets address 0x0 -> the first
    ; tft.begin() dies with "Guru Meditation Error: StoreProhibited,
    ; EXCVADDR: 0x00000000". USE_FSPI_PORT forces SPI_PORT to 2, i.e.
    ; DR_REG_SPI2_BASE (GPSPI2), which is the same peripheral the Arduino
    ; SPIClass(FSPI) instance drives, so the two stay in sync.
    -D USE_FSPI_PORT
    -D USER_SETUP_LOADED=1
    -D ILI9341_DRIVER=1
    -D TFT_WIDTH=240
    -D TFT_HEIGHT=320
    -D TFT_MISO=13
    -D TFT_MOSI=11
    -D TFT_SCLK=12
    -D TFT_CS=10
    -D TFT_DC=7
    -D TFT_RST=6
    -D TFT_BL=14
    -D TFT_BACKLIGHT_ON=HIGH
    -D LOAD_GLCD=1
    -D LOAD_FONT2=1
    -D LOAD_FONT4=1
    -D LOAD_GFXFF=1
    -D SPI_FREQUENCY=40000000
build_unflags =
    -std=gnu++11
; Compile src/ plus the portable core/ and the esp32s3 port. app/ui/ is
; appended in Task 5 once that directory exists.
build_src_filter =
    +<*>
    +<../core/>
    +<../ports/esp32s3/>

[env:native]
platform = native
test_framework = unity
; test_build_src makes `pio test` compile src_dir sources; combined with the
; filter below it links core/ into the test binary.
test_build_src = true
build_flags =
    -std=gnu++17
    -I core
    -I hal
    -I ports/native
build_src_filter =
    +<../core/>
```

> Note: `build_src_filter` for the native env compiles only `core/` (no Arduino/LVGL). The `esp32-s3` env compiles everything under `src/` plus the `-I` include paths; `main.cpp` pulls in the ports/app sources it needs.

- [ ] **Step 3: Write `firmware/core/domain.h`**

```cpp
#pragma once
#include <string>
#include <vector>

namespace sb {

enum class Priority { High, Medium, Low };

struct Task {
    std::string title;
    Priority priority = Priority::Medium;
};

enum class Screen {
    Home,
    NotesMenu,
    NoteResult,
    NoteConfirm,
    TasksMenu,
    TaskResult,
    TaskList,
};

enum class Event { Down, Select, Back };

// The full UI model the renderer draws. Owned and mutated only by Nav.
struct UiState {
    Screen screen = Screen::Home;
    int cursor = 0;                    // highlighted index on list/menu screens
    std::vector<std::string> notes;    // saved notes (newest last)
    std::vector<Task> tasks;           // saved tasks (newest last)
    std::string pendingNote;           // note text awaiting Save/Discard
    Task pendingTask;                  // task awaiting confirmation
};

inline const char* priority_label(Priority p) {
    switch (p) {
        case Priority::High: return "HIGH";
        case Priority::Medium: return "MEDIUM";
        case Priority::Low: return "LOW";
    }
    return "MEDIUM";
}

}  // namespace sb
```

- [ ] **Step 4: Write the failing menu test**

Create `firmware/test/test_menu/test_menu.cpp`:

```cpp
#include <unity.h>
#include "menu.h"

void test_next_wraps_around(void) {
    TEST_ASSERT_EQUAL_INT(1, sb::menu_next(0, 3));
    TEST_ASSERT_EQUAL_INT(0, sb::menu_next(2, 3));  // wraps
}

void test_prev_wraps_around(void) {
    TEST_ASSERT_EQUAL_INT(2, sb::menu_prev(0, 3));  // wraps
    TEST_ASSERT_EQUAL_INT(0, sb::menu_prev(1, 3));
}

void test_empty_list_is_noop(void) {
    TEST_ASSERT_EQUAL_INT(0, sb::menu_next(0, 0));
    TEST_ASSERT_EQUAL_INT(0, sb::menu_prev(0, 0));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_next_wraps_around);
    RUN_TEST(test_prev_wraps_around);
    RUN_TEST(test_empty_list_is_noop);
    return UNITY_END();
}
```

- [ ] **Step 5: Run the test to verify it fails**

Run: `cd firmware && pio test -e native`
Expected: FAIL — build error, `menu.h` not found / `menu_next` undefined.

- [ ] **Step 6: Write `firmware/core/menu.h` and `firmware/core/menu.cpp`**

`menu.h`:

```cpp
#pragma once

namespace sb {
// Wrap-around cursor movement. Both return 0 when count <= 0.
int menu_next(int cursor, int count);
int menu_prev(int cursor, int count);
}
```

`menu.cpp`:

```cpp
#include "menu.h"

namespace sb {

int menu_next(int cursor, int count) {
    if (count <= 0) return 0;
    return (cursor + 1) % count;
}

int menu_prev(int cursor, int count) {
    if (count <= 0) return 0;
    return (cursor - 1 + count) % count;
}

}  // namespace sb
```

- [ ] **Step 7: Run the test to verify it passes**

Run: `cd firmware && pio test -e native`
Expected: PASS — 3 tests pass. (First run installs the `native`/Unity toolchain.)

- [ ] **Step 8: Create a `src/` placeholder so the native filter resolves from a clean clone**

The `native` env's `build_src_filter = +<../core/>` is resolved relative to `src_dir`
(`src/`), which does not exist until Task 3. Create a placeholder so `pio test -e native`
works from a fresh checkout now:

```bash
mkdir -p firmware/src && touch firmware/src/.gitkeep
```

- [ ] **Step 9: Commit**

```bash
git add firmware/platformio.ini firmware/.gitignore firmware/core/domain.h firmware/core/menu.h firmware/core/menu.cpp firmware/test/test_menu/test_menu.cpp firmware/src/.gitkeep
git commit -m "feat(firmware): scaffold PlatformIO project with native test harness"
```

---

### Task 2: Navigation state machine (core, TDD)

**Files:**
- Create: `firmware/core/nav.h`, `firmware/core/nav.cpp`
- Test: `firmware/test/test_nav/test_nav.cpp`

**Interfaces:**
- Consumes: `core/domain.h`, `core/menu.h`
- Produces:
  - `core/nav.h`: `class Nav` with `Nav(std::string sampleNote, Task sampleTask)`, `void handle(Event e)`, `const UiState& ui() const`
  - navigation transitions matching the design's Notes/Tasks flows

- [ ] **Step 1: Write the failing test**

Create `firmware/test/test_nav/test_nav.cpp`:

```cpp
#include <unity.h>
#include "nav.h"

using namespace sb;

static Nav make() {
    return Nav("buy milk tomorrow", Task{"Buy milk", Priority::High});
}

void test_starts_on_home(void) {
    Nav n = make();
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);
}

void test_home_down_toggles_cursor(void) {
    Nav n = make();
    n.handle(Event::Down);
    TEST_ASSERT_EQUAL_INT(1, n.ui().cursor);
    n.handle(Event::Down);
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);  // wraps over 2 items
}

void test_notes_flow_saves_a_note(void) {
    Nav n = make();
    n.handle(Event::Select);   // Home(cursor 0=Notes) -> NotesMenu
    TEST_ASSERT_EQUAL_INT((int)Screen::NotesMenu, (int)n.ui().screen);
    n.handle(Event::Select);   // NotesMenu(Record) -> NoteResult, pendingNote set
    TEST_ASSERT_EQUAL_INT((int)Screen::NoteResult, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_STRING("buy milk tomorrow", n.ui().pendingNote.c_str());
    n.handle(Event::Select);   // NoteResult -> NoteConfirm
    TEST_ASSERT_EQUAL_INT((int)Screen::NoteConfirm, (int)n.ui().screen);
    n.handle(Event::Select);   // Confirm(cursor 0=Save) -> saves, back to Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(1, (int)n.ui().notes.size());
    TEST_ASSERT_EQUAL_STRING("buy milk tomorrow", n.ui().notes[0].c_str());
}

void test_note_discard_does_not_save(void) {
    Nav n = make();
    n.handle(Event::Select);   // NotesMenu
    n.handle(Event::Select);   // NoteResult
    n.handle(Event::Select);   // NoteConfirm
    n.handle(Event::Down);     // cursor -> 1 = Discard
    n.handle(Event::Select);   // discard -> Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(0, (int)n.ui().notes.size());
}

void test_back_from_notes_menu_returns_home(void) {
    Nav n = make();
    n.handle(Event::Select);   // NotesMenu
    n.handle(Event::Back);     // -> Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
}

void test_tasks_flow_saves_a_task_and_shows_list(void) {
    Nav n = make();
    n.handle(Event::Down);     // cursor -> 1 = Tasks
    n.handle(Event::Select);   // -> TasksMenu
    TEST_ASSERT_EQUAL_INT((int)Screen::TasksMenu, (int)n.ui().screen);
    n.handle(Event::Select);   // New task -> TaskResult, pendingTask set
    TEST_ASSERT_EQUAL_INT((int)Screen::TaskResult, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_STRING("Buy milk", n.ui().pendingTask.title.c_str());
    TEST_ASSERT_EQUAL_INT((int)Priority::High, (int)n.ui().pendingTask.priority);
    n.handle(Event::Select);   // -> saves, TaskList
    TEST_ASSERT_EQUAL_INT((int)Screen::TaskList, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(1, (int)n.ui().tasks.size());
    TEST_ASSERT_EQUAL_STRING("Buy milk", n.ui().tasks[0].title.c_str());
}

void test_back_from_home_stays_home(void) {
    Nav n = make();
    n.handle(Event::Back);
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_starts_on_home);
    RUN_TEST(test_home_down_toggles_cursor);
    RUN_TEST(test_notes_flow_saves_a_note);
    RUN_TEST(test_note_discard_does_not_save);
    RUN_TEST(test_back_from_notes_menu_returns_home);
    RUN_TEST(test_tasks_flow_saves_a_task_and_shows_list);
    RUN_TEST(test_back_from_home_stays_home);
    return UNITY_END();
}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd firmware && pio test -e native -f test_nav`
Expected: FAIL — `nav.h` not found.

- [ ] **Step 3: Write `firmware/core/nav.h`**

```cpp
#pragma once
#include <string>
#include "domain.h"

namespace sb {

class Nav {
public:
    Nav(std::string sampleNote, Task sampleTask);
    void handle(Event e);
    const UiState& ui() const { return state_; }

private:
    UiState state_;
    std::string sampleNote_;
    Task sampleTask_;

    void goTo(Screen s, int cursor = 0);
};

}  // namespace sb
```

- [ ] **Step 4: Write `firmware/core/nav.cpp`**

```cpp
#include "nav.h"
#include "menu.h"

namespace sb {

Nav::Nav(std::string sampleNote, Task sampleTask)
    : sampleNote_(std::move(sampleNote)), sampleTask_(std::move(sampleTask)) {}

void Nav::goTo(Screen s, int cursor) {
    state_.screen = s;
    state_.cursor = cursor;
}

void Nav::handle(Event e) {
    switch (state_.screen) {
        case Screen::Home:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, 2);
            else if (e == Event::Select) goTo(state_.cursor == 0 ? Screen::NotesMenu : Screen::TasksMenu);
            // Back on Home: stay.
            break;

        case Screen::NotesMenu:
            if (e == Event::Select) { state_.pendingNote = sampleNote_; goTo(Screen::NoteResult); }
            else if (e == Event::Back) goTo(Screen::Home);
            break;

        case Screen::NoteResult:
            if (e == Event::Select) goTo(Screen::NoteConfirm);       // cursor 0 = Save
            else if (e == Event::Back) goTo(Screen::NotesMenu);
            break;

        case Screen::NoteConfirm:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, 2);
            else if (e == Event::Back) goTo(Screen::NoteResult);
            else if (e == Event::Select) {
                if (state_.cursor == 0) state_.notes.push_back(state_.pendingNote);  // Save
                state_.pendingNote.clear();
                goTo(Screen::Home);
            }
            break;

        case Screen::TasksMenu:
            if (e == Event::Select) { state_.pendingTask = sampleTask_; goTo(Screen::TaskResult); }
            else if (e == Event::Back) goTo(Screen::Home);
            break;

        case Screen::TaskResult:
            if (e == Event::Select) { state_.tasks.push_back(state_.pendingTask); goTo(Screen::TaskList); }
            else if (e == Event::Back) goTo(Screen::TasksMenu);
            break;

        case Screen::TaskList:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, (int)state_.tasks.size());
            else if (e == Event::Back) goTo(Screen::Home);
            break;
    }
}

}  // namespace sb
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd firmware && pio test -e native`
Expected: PASS — all `test_nav` and `test_menu` tests pass (10 total).

- [ ] **Step 6: Commit**

```bash
git add firmware/core/nav.h firmware/core/nav.cpp firmware/test/test_nav/test_nav.cpp
git commit -m "feat(firmware): add navigation state machine with host tests"
```

---

### Task 3: Display port (LVGL + TFT_eSPI) + first ESP32-S3 compile

**Files:**
- Create: `firmware/ports/esp32s3/config.h`
- Create: `firmware/ports/esp32s3/display_tft.h`, `firmware/ports/esp32s3/display_tft.cpp`
- Create: `firmware/src/main.cpp` (minimal, temporary — replaced in Task 6)

**Interfaces:**
- Consumes: `core/domain.h`
- Produces:
  - `ports/esp32s3/config.h`: pin `#define`s + `SAMPLE_NOTE`, `SAMPLE_TASK_TITLE`, `SAMPLE_TASK_PRIORITY`
  - `ports/esp32s3/display_tft.h`: `namespace sb::display { void begin(); }` — initializes TFT + LVGL (buffer, driver, flush). After `begin()`, LVGL calls may create widgets.

- [ ] **Step 1: Write `firmware/ports/esp32s3/config.h`**

```cpp
#pragma once
#include "domain.h"

// ---- Pins (ESP32-S3). Keep in sync with diagram.json. ----
#define PIN_TFT_CS    10
#define PIN_TFT_MOSI  11
#define PIN_TFT_SCLK  12
#define PIN_TFT_MISO  13
#define PIN_TFT_DC     7
#define PIN_TFT_RST    6
#define PIN_TFT_BL    14

#define PIN_BTN_DOWN    4
#define PIN_BTN_SELECT  5
#define PIN_BTN_BACK   15

// ---- Phase-2 stand-in for the (not-yet-present) microphone + AI ----
#define SAMPLE_NOTE "Buy milk and call the dentist tomorrow morning."
#define SAMPLE_TASK_TITLE "Call the dentist"
#define SAMPLE_TASK_PRIORITY sb::Priority::High
```

- [ ] **Step 2: Write `firmware/ports/esp32s3/display_tft.h`**

```cpp
#pragma once

namespace sb {
namespace display {
// Initialize TFT_eSPI + LVGL (draw buffer, display driver, flush callback,
// backlight). Call once from setup() before creating any LVGL widgets.
void begin();
}  // namespace display
}  // namespace sb
```

- [ ] **Step 3: Write `firmware/ports/esp32s3/display_tft.cpp`**

```cpp
#include "display_tft.h"
#include <Arduino.h>
#include <TFT_eSPI.h>
#include <lvgl.h>
#include "config.h"

namespace {
TFT_eSPI tft;
constexpr int kHor = 240;
constexpr int kVer = 320;
// ~10 lines of draw buffer (240 * 10 px).
lv_disp_draw_buf_t draw_buf;
lv_color_t buf1[kHor * 10];

void flush_cb(lv_disp_drv_t* drv, const lv_area_t* area, lv_color_t* color_p) {
    uint32_t w = (area->x2 - area->x1 + 1);
    uint32_t h = (area->y2 - area->y1 + 1);
    tft.startWrite();
    tft.setAddrWindow(area->x1, area->y1, w, h);
    tft.pushColors((uint16_t*)color_p, w * h, true);
    tft.endWrite();
    lv_disp_flush_ready(drv);
}
}  // namespace

namespace sb {
namespace display {

void begin() {
    pinMode(PIN_TFT_BL, OUTPUT);
    digitalWrite(PIN_TFT_BL, HIGH);

    tft.begin();
    tft.setRotation(0);  // 240x320 portrait

    lv_init();
    lv_disp_draw_buf_init(&draw_buf, buf1, nullptr, kHor * 10);

    static lv_disp_drv_t disp_drv;
    lv_disp_drv_init(&disp_drv);
    disp_drv.hor_res = kHor;
    disp_drv.ver_res = kVer;
    disp_drv.flush_cb = flush_cb;
    disp_drv.draw_buf = &draw_buf;
    lv_disp_drv_register(&disp_drv);
}

}  // namespace display
}  // namespace sb
```

- [ ] **Step 4: Write a minimal temporary `firmware/src/main.cpp`**

```cpp
#include <Arduino.h>
#include <lvgl.h>
#include "display_tft.h"

void setup() {
    Serial.begin(115200);
    sb::display::begin();

    // Temporary smoke screen — replaced by the real UI in Task 6.
    lv_obj_t* label = lv_label_create(lv_scr_act());
    lv_label_set_text(label, "Second Brain");
    lv_obj_center(label);
}

void loop() {
    lv_timer_handler();
    delay(5);
}
```

- [ ] **Step 5: Compile for ESP32-S3 (first full build — downloads toolchain + libs)**

Run: `cd firmware && pio run -e esp32-s3`
Expected: SUCCESS — build completes, ends with `firmware.bin` produced under `.pio/build/esp32-s3/`. The first run downloads the ESP32-S3 toolchain, LVGL, and TFT_eSPI (several minutes). If LVGL/TFT flags need adjustment, fix them in `platformio.ini` until it compiles cleanly — do not proceed until the build is green.

- [ ] **Step 6: Confirm the artifacts exist**

Run: `ls -la firmware/.pio/build/esp32-s3/firmware.bin firmware/.pio/build/esp32-s3/firmware.elf`
Expected: both files exist, non-zero size.

- [ ] **Step 7: Commit**

```bash
git add firmware/ports/esp32s3/config.h firmware/ports/esp32s3/display_tft.h firmware/ports/esp32s3/display_tft.cpp firmware/src/main.cpp
git commit -m "feat(firmware): add LVGL + TFT_eSPI display port, first ESP32-S3 build"
```

---

### Task 4: Input HAL + button port + native stub

**Files:**
- Create: `firmware/hal/IInput.h`
- Create: `firmware/ports/esp32s3/buttons.h`, `firmware/ports/esp32s3/buttons.cpp`
- Create: `firmware/ports/native/input_stub.h`
- Test: `firmware/test/test_input/test_input_stub.cpp`

**Interfaces:**
- Consumes: `core/domain.h` (`Event`)
- Produces:
  - `hal/IInput.h`: `struct IInput { virtual bool poll(Event& out) = 0; virtual ~IInput() = default; };` — returns `true` and sets `out` when a button was pressed this call, else `false`
  - `ports/native/input_stub.h`: `class InputStub : public IInput` with `void push(Event)` (enqueue scripted events)
  - `ports/esp32s3/buttons.h`: `class Buttons : public IInput { public: void begin(); bool poll(Event&) override; }` — debounced, edge-triggered reads of the 3 pins

- [ ] **Step 1: Write the failing test**

Create `firmware/test/test_input/test_input_stub.cpp`:

```cpp
#include <unity.h>
#include "input_stub.h"

using namespace sb;

void test_stub_returns_queued_events_in_order(void) {
    InputStub in;
    in.push(Event::Down);
    in.push(Event::Select);

    Event e;
    TEST_ASSERT_TRUE(in.poll(e));
    TEST_ASSERT_EQUAL_INT((int)Event::Down, (int)e);
    TEST_ASSERT_TRUE(in.poll(e));
    TEST_ASSERT_EQUAL_INT((int)Event::Select, (int)e);
    TEST_ASSERT_FALSE(in.poll(e));  // queue empty
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_stub_returns_queued_events_in_order);
    return UNITY_END();
}
```

Add `-I ports/native` is already in the `native` env include path (Task 1). Also add `test_input` — no config change needed; `pio test` discovers `test/test_*` folders.

- [ ] **Step 2: Run to verify it fails**

Run: `cd firmware && pio test -e native -f test_input`
Expected: FAIL — `input_stub.h` not found.

- [ ] **Step 3: Write `firmware/hal/IInput.h`**

```cpp
#pragma once
#include "domain.h"

namespace sb {
struct IInput {
    virtual ~IInput() = default;
    // Returns true and sets `out` if a button press occurred since the last
    // poll; returns false otherwise.
    virtual bool poll(Event& out) = 0;
};
}  // namespace sb
```

- [ ] **Step 4: Write `firmware/ports/native/input_stub.h`**

```cpp
#pragma once
#include <deque>
#include "IInput.h"

namespace sb {
class InputStub : public IInput {
public:
    void push(Event e) { q_.push_back(e); }
    bool poll(Event& out) override {
        if (q_.empty()) return false;
        out = q_.front();
        q_.pop_front();
        return true;
    }
private:
    std::deque<Event> q_;
};
}  // namespace sb
```

- [ ] **Step 5: Run to verify it passes**

Run: `cd firmware && pio test -e native`
Expected: PASS — all tests (menu + nav + input) pass.

- [ ] **Step 6: Write `firmware/ports/esp32s3/buttons.h`**

```cpp
#pragma once
#include "IInput.h"

namespace sb {
// Reads 3 active-low buttons (INPUT_PULLUP) and emits one Event per press
// (falling edge), with simple time-based debouncing.
class Buttons : public IInput {
public:
    void begin();
    bool poll(Event& out) override;
private:
    struct Btn { int pin; Event event; bool last; unsigned long changedAt; };
    Btn btns_[3];
};
}  // namespace sb
```

- [ ] **Step 7: Write `firmware/ports/esp32s3/buttons.cpp`**

```cpp
#include "buttons.h"
#include <Arduino.h>
#include "config.h"

namespace sb {

void Buttons::begin() {
    btns_[0] = {PIN_BTN_DOWN,   Event::Down,   true, 0};
    btns_[1] = {PIN_BTN_SELECT, Event::Select, true, 0};
    btns_[2] = {PIN_BTN_BACK,   Event::Back,   true, 0};
    for (auto& b : btns_) pinMode(b.pin, INPUT_PULLUP);
}

bool Buttons::poll(Event& out) {
    const unsigned long now = millis();
    for (auto& b : btns_) {
        bool level = digitalRead(b.pin);          // HIGH = released, LOW = pressed
        if (level != b.last && (now - b.changedAt) > 25) {
            b.changedAt = now;
            b.last = level;
            if (level == LOW) {                    // falling edge = a press
                out = b.event;
                return true;
            }
        }
    }
    return false;
}

}  // namespace sb
```

- [ ] **Step 8: Commit**

```bash
git add firmware/hal/IInput.h firmware/ports/native/input_stub.h firmware/ports/esp32s3/buttons.h firmware/ports/esp32s3/buttons.cpp firmware/test/test_input/test_input_stub.cpp
git commit -m "feat(firmware): add input HAL, ESP32-S3 button port and native stub"
```

---

### Task 5: UI renderer (LVGL screens from UiState)

**Files:**
- Create: `firmware/app/ui/ui.h`, `firmware/app/ui/ui.cpp`

**Interfaces:**
- Consumes: `core/domain.h`, LVGL
- Produces:
  - `app/ui/ui.h`: `namespace sb::ui { void render(const UiState& s); }` — clears the active screen and rebuilds LVGL widgets for `s.screen`. Called whenever the state changes.

- [ ] **Step 1: Write `firmware/app/ui/ui.h`**

```cpp
#pragma once
#include "domain.h"

namespace sb {
namespace ui {
// Rebuild the active LVGL screen to reflect `s`. Call after each state change.
void render(const UiState& s);
}  // namespace ui
}  // namespace sb
```

- [ ] **Step 2: Write `firmware/app/ui/ui.cpp`**

Render each screen by clearing `lv_scr_act()` and building fresh widgets. Use a title label at top and a body below; highlight the row at `s.cursor` on list/menu screens. This is presentation only — no navigation logic.

```cpp
#include "ui.h"
#include <lvgl.h>
#include <string>

namespace {
using namespace sb;

lv_obj_t* title(const char* text) {
    lv_obj_t* t = lv_label_create(lv_scr_act());
    lv_label_set_text(t, text);
    lv_obj_align(t, LV_ALIGN_TOP_MID, 0, 8);
    return t;
}

// A simple vertical list; the row at `cursor` gets a highlighted style.
void list(const char* const* items, int count, int cursor) {
    lv_obj_t* cont = lv_obj_create(lv_scr_act());
    lv_obj_set_size(cont, 224, 240);
    lv_obj_align(cont, LV_ALIGN_TOP_MID, 0, 40);
    lv_obj_set_flex_flow(cont, LV_FLEX_FLOW_COLUMN);
    for (int i = 0; i < count; ++i) {
        lv_obj_t* row = lv_label_create(cont);
        lv_label_set_text(row, items[i]);
        if (i == cursor) {
            lv_obj_set_style_text_color(row, lv_color_hex(0x4ADE80), 0);  // green highlight
        }
    }
}

void body(const char* text) {
    lv_obj_t* b = lv_label_create(lv_scr_act());
    lv_label_set_long_mode(b, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(b, 220);
    lv_label_set_text(b, text);
    lv_obj_align(b, LV_ALIGN_TOP_LEFT, 10, 44);
}
}  // namespace

namespace sb {
namespace ui {

void render(const UiState& s) {
    lv_obj_clean(lv_scr_act());
    switch (s.screen) {
        case Screen::Home: {
            title("Second Brain");
            const char* items[] = {"Notes", "Tasks"};
            list(items, 2, s.cursor);
            break;
        }
        case Screen::NotesMenu: {
            title("Notes");
            const char* items[] = {"Record"};
            list(items, 1, 0);
            break;
        }
        case Screen::NoteResult: {
            title("Note");
            body(s.pendingNote.c_str());
            break;
        }
        case Screen::NoteConfirm: {
            title("Save note?");
            const char* items[] = {"Save", "Discard"};
            list(items, 2, s.cursor);
            break;
        }
        case Screen::TasksMenu: {
            title("Tasks");
            const char* items[] = {"New task"};
            list(items, 1, 0);
            break;
        }
        case Screen::TaskResult: {
            title("Task");
            std::string t = std::string(s.pendingTask.title) + "\n[" +
                            priority_label(s.pendingTask.priority) + "]";
            body(t.c_str());
            break;
        }
        case Screen::TaskList: {
            title("Task list");
            lv_obj_t* cont = lv_obj_create(lv_scr_act());
            lv_obj_set_size(cont, 224, 240);
            lv_obj_align(cont, LV_ALIGN_TOP_MID, 0, 40);
            lv_obj_set_flex_flow(cont, LV_FLEX_FLOW_COLUMN);
            for (size_t i = 0; i < s.tasks.size(); ++i) {
                lv_obj_t* row = lv_label_create(cont);
                std::string line = "[" + std::string(priority_label(s.tasks[i].priority)) +
                                   "] " + s.tasks[i].title;
                lv_label_set_text(row, line.c_str());
                if ((int)i == s.cursor) lv_obj_set_style_text_color(row, lv_color_hex(0x4ADE80), 0);
            }
            if (s.tasks.empty()) body("(no tasks yet)");
            break;
        }
    }
}

}  // namespace ui
}  // namespace sb
```

- [ ] **Step 3: Add `app/ui/` to the ESP32-S3 build**

The `[env:esp32-s3]` `build_src_filter` already exists (added in Task 3) with `src/`, `core/`,
and `ports/esp32s3/`. Now that `app/ui/` exists, append it so `ui.cpp` is compiled:

```ini
build_src_filter =
    +<*>
    +<../core/>
    +<../ports/esp32s3/>
    +<../app/ui/>
```

- [ ] **Step 4: Compile**

Run: `cd firmware && pio run -e esp32-s3`
Expected: SUCCESS. Fix any LVGL API mismatches until green.

- [ ] **Step 5: Commit**

```bash
git add firmware/app/ui/ui.h firmware/app/ui/ui.cpp firmware/platformio.ini
git commit -m "feat(firmware): render LVGL screens from core UI state"
```

---

### Task 6: Wire it together in main.cpp

**Files:**
- Modify: `firmware/src/main.cpp` (replace the Task 3 smoke screen entirely)

**Interfaces:**
- Consumes: `core/nav.h`, `hal/IInput.h`, `ports/esp32s3/buttons.h`, `ports/esp32s3/display_tft.h`, `ports/esp32s3/config.h`, `app/ui/ui.h`
- Produces: the running firmware — buttons drive `Nav`, `ui::render` reflects state, `lv_timer_handler` services LVGL

- [ ] **Step 1: Replace `firmware/src/main.cpp`**

```cpp
#include <Arduino.h>
#include <lvgl.h>
#include "config.h"
#include "display_tft.h"
#include "buttons.h"
#include "nav.h"
#include "ui.h"

using namespace sb;

static Buttons buttons;
static Nav nav(SAMPLE_NOTE, Task{SAMPLE_TASK_TITLE, SAMPLE_TASK_PRIORITY});

static const char* screen_name(Screen s) {
    switch (s) {
        case Screen::Home: return "Home";
        case Screen::NotesMenu: return "NotesMenu";
        case Screen::NoteResult: return "NoteResult";
        case Screen::NoteConfirm: return "NoteConfirm";
        case Screen::TasksMenu: return "TasksMenu";
        case Screen::TaskResult: return "TaskResult";
        case Screen::TaskList: return "TaskList";
    }
    return "?";
}

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("Second Brain UI booting");
    sb::display::begin();
    buttons.begin();
    ui::render(nav.ui());
    Serial.printf("screen=%s cursor=%d\n", screen_name(nav.ui().screen), nav.ui().cursor);
}

void loop() {
    Event e;
    if (buttons.poll(e)) {
        nav.handle(e);
        ui::render(nav.ui());
        Serial.printf("event=%d -> screen=%s cursor=%d notes=%d tasks=%d\n",
                      (int)e, screen_name(nav.ui().screen), nav.ui().cursor,
                      (int)nav.ui().notes.size(), (int)nav.ui().tasks.size());
    }
    lv_timer_handler();
    delay(5);
}
```

- [ ] **Step 2: Compile**

Run: `cd firmware && pio run -e esp32-s3`
Expected: SUCCESS — `firmware.bin` + `firmware.elf` rebuilt.

- [ ] **Step 3: Confirm host tests still pass (nothing in core changed, but verify the build stayed green)**

Run: `cd firmware && pio test -e native`
Expected: PASS — all tests.

- [ ] **Step 4: Commit**

```bash
git add firmware/src/main.cpp
git commit -m "feat(firmware): wire buttons, nav and UI into the main loop"
```

---

### Task 7: Wokwi simulation files

**Files:**
- Create: `firmware/wokwi.toml`
- Create: `firmware/diagram.json`

**Interfaces:**
- Consumes: the built `firmware.bin`/`firmware.elf`; the pin map in `config.h`
- Produces: a Wokwi project that boots the firmware with an ILI9341 + 3 buttons wired to the `config.h` pins

- [ ] **Step 1: Write `firmware/wokwi.toml`**

```toml
[wokwi]
version = 1
firmware = '.pio/build/esp32-s3/firmware.bin'
elf = '.pio/build/esp32-s3/firmware.elf'
```

- [ ] **Step 2: Write `firmware/diagram.json`**

Wire the ILI9341 to the SPI + control pins and the 3 buttons to their GPIOs. Each button connects GPIO→button→GND and relies on the internal pull-up. Every pin here must match `config.h`.

```json
{
  "version": 1,
  "author": "AkashVarma007",
  "editor": "wokwi",
  "parts": [
    { "type": "board-esp32-s3-devkitc-1", "id": "esp", "top": 0, "left": 0, "attrs": {} },
    { "type": "wokwi-ili9341", "id": "lcd", "top": -120, "left": 200, "attrs": {} },
    { "type": "wokwi-pushbutton", "id": "btnDown", "top": 100, "left": -180,
      "attrs": { "color": "green", "label": "DOWN", "bounce": "0" } },
    { "type": "wokwi-pushbutton", "id": "btnSelect", "top": 160, "left": -180,
      "attrs": { "color": "blue", "label": "SELECT", "bounce": "0" } },
    { "type": "wokwi-pushbutton", "id": "btnBack", "top": 220, "left": -180,
      "attrs": { "color": "red", "label": "BACK", "bounce": "0" } }
  ],
  "connections": [
    [ "esp:TX", "$serialMonitor:RX", "", [] ],
    [ "esp:RX", "$serialMonitor:TX", "", [] ],
    [ "lcd:VCC", "esp:3V3.1", "red", [] ],
    [ "lcd:GND", "esp:GND.1", "black", [] ],
    [ "lcd:CS", "esp:10", "orange", [] ],
    [ "lcd:RST", "esp:6", "yellow", [] ],
    [ "lcd:D/C", "esp:7", "green", [] ],
    [ "lcd:MOSI", "esp:11", "blue", [] ],
    [ "lcd:SCK", "esp:12", "purple", [] ],
    [ "lcd:LED", "esp:14", "white", [] ],
    [ "lcd:MISO", "esp:13", "gray", [] ],
    [ "btnDown:1.l", "esp:4", "green", [] ],
    [ "btnDown:2.l", "esp:GND.2", "black", [] ],
    [ "btnSelect:1.l", "esp:5", "blue", [] ],
    [ "btnSelect:2.l", "esp:GND.3", "black", [] ],
    [ "btnBack:1.l", "esp:15", "red", [] ],
    [ "btnBack:2.l", "esp:GND.4", "black", [] ]
  ]
}
```

- [ ] **Step 3: Validate the files**

Run: `cd firmware && python3 -c "import json; json.load(open('diagram.json')); print('diagram.json valid')"` and `python3 -c "import tomllib; tomllib.load(open('wokwi.toml','rb')); print('wokwi.toml valid')"`
Expected: both print "valid".

**Parsing as JSON is NOT enough — also run `wokwi-cli lint .`.** Wokwi silently drops any connection naming a pin the part does not have, so a syntactically perfect diagram can leave the display unpowered. On `board-esp32-s3-devkitc-1` the power/ground pins are `3V3.1`, `3V3.2`, `5V`, `GND.1`..`GND.4` — there is no plain `3V3` or `GND`. Each ground wire needs its own `GND.n`. Expected: 0 errors (one info about the undocumented board type is fine).

- [ ] **Step 4: Cross-check pins against `config.h`**

Run: `cd firmware && grep -E "PIN_(TFT|BTN)" ports/esp32s3/config.h`
Confirm by eye that every GPIO number in `diagram.json` connections matches a `config.h` pin: TFT CS=10, RST=6, DC=7, MOSI=11, SCK=12, LED/BL=14, MISO=13; buttons DOWN=4, SELECT=5, BACK=15. Any mismatch is a bug — fix `diagram.json` to match `config.h`.

- [ ] **Step 5: Commit**

```bash
git add firmware/wokwi.toml firmware/diagram.json
git commit -m "feat(firmware): add Wokwi diagram and simulation config"
```

---

### Task 8: Firmware README + verification recap

**Files:**
- Create: `firmware/README.md`
- Modify: root `README.md` (mark Phase 2, update firmware row)

**Interfaces:**
- Consumes: everything above
- Produces: docs a stranger can follow to build, host-test, and run the sim

- [ ] **Step 1: Write `firmware/README.md`**

```markdown
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
```

- [ ] **Step 2: Update the root `README.md` repository-layout row**

Change the `firmware/` row to show Phase 2 in progress/done and note it's simulator-only:

```markdown
| `firmware/` | ESP32-S3 firmware (LVGL UI), runs in Wokwi simulator | ✅ Phase 2 (sim UI) |
```

- [ ] **Step 3: Final verification — both gates green**

Run: `cd firmware && pio test -e native && pio run -e esp32-s3`
Expected: host tests all pass AND the ESP32-S3 build succeeds.

- [ ] **Step 4: Commit**

```bash
git add firmware/README.md README.md
git commit -m "docs: document Phase 2 firmware build, tests and simulation"
```

---

## Self-Review

**1. Spec coverage** (design §7–§8):

| Spec requirement | Task |
|---|---|
| PlatformIO project for ESP32-S3, Wokwi-runnable (`platformio.ini`, `wokwi.toml`, `diagram.json`) | Tasks 1, 7 |
| Display + 3 buttons in the simulator | Tasks 3, 4, 7 |
| LVGL UI: Home → Notes/Tasks | Task 5 |
| Notes flow: select → record → confirmation | Tasks 2 (logic), 5 (UI) |
| Tasks flow: new task → priority display → task list | Tasks 2 (logic), 5 (UI) |
| Button navigation (down/select/back) | Task 2 (nav), Task 4 (input), Task 6 (wiring) |
| Hardcoded sample string stands in for transcribed text | `config.h` (Task 3), injected into `Nav` (Task 6) |
| Portable core + HAL + ports, host-testable (§7) | Tasks 1–4 |

**2. Placeholder scan:** every code step contains complete code; every command step states expected output. The Task 3 `main.cpp` is explicitly temporary and fully replaced in Task 6.

**3. Type/name consistency:** `Event`, `Screen`, `Priority`, `Task`, `UiState` are defined in `core/domain.h` (Task 1) and used unchanged in `nav` (Task 2), `IInput` (Task 4), `ui` (Task 5), `main` (Task 6). `Nav(sampleNote, sampleTask)` signature is identical in the Task 2 tests, the Task 2 header, and the Task 6 `main`. `IInput::poll(Event&) -> bool` is identical in the stub (Task 4), the button port (Task 4), and `main` (Task 6). `sb::display::begin()` and `sb::ui::render()` names match across their headers and call sites.

**4. Verification honesty:** every firmware task gates on a real command — `pio test -e native` (host logic) or `pio run -e esp32-s3` (compile). The one thing not automatable here (the visual Wokwi run) is made correct-by-construction (valid JSON/TOML + pin cross-check) and left to the user, per the Global Constraints.

**Risk note:** the first `pio run -e esp32-s3` may surface LVGL/TFT_eSPI flag mismatches (color swap, font, tick). Task 3 isolates this with a minimal `main.cpp` so the integration is debugged before any UI code exists. If the build fights the flags, adjust `platformio.ini` build flags (not the app code) until green.
