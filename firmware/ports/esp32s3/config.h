#pragma once

// ---- Pins (ESP32-S3). Keep in sync with diagram.json and WIRING.md. ----

// 128x64 mono display. Wokwi/bench: SSD1306 OLED on I2C (address 0x3c).
#define PIN_OLED_SDA  8
#define PIN_OLED_SCL  9

// Pocket build: ST7567 LCD on SPI (see display.cpp). Not wired in Wokwi.
#define PIN_LCD_SCK  12
#define PIN_LCD_MOSI 11
#define PIN_LCD_CS   10
#define PIN_LCD_DC   14
#define PIN_LCD_RST  21

// Buttons: active-low, internal pull-up.
#define PIN_BTN_UP     4
#define PIN_BTN_DOWN   5
#define PIN_BTN_LEFT   6
#define PIN_BTN_RIGHT  7
#define PIN_BTN_OK    15
#define PIN_BTN_BACK  16
#define PIN_BTN_TALK  17

// ---- Pin sanity, checked at compile time ----
// u8g2's hardware SPI calls SPI.begin(), which on the ESP32-S3 always claims
// GPIO 11 (MOSI), 12 (SCK) and 13 (MISO, set to input). No LCD control line
// may sit on them, or that line silently stops driving.
namespace sb {
namespace pins {
constexpr int kAll[] = {PIN_OLED_SDA, PIN_OLED_SCL, PIN_LCD_SCK, PIN_LCD_MOSI, PIN_LCD_CS, PIN_LCD_DC,
                        PIN_LCD_RST,  PIN_BTN_UP,   PIN_BTN_DOWN, PIN_BTN_LEFT, PIN_BTN_RIGHT,
                        PIN_BTN_OK,   PIN_BTN_BACK, PIN_BTN_TALK};
constexpr bool unique() {
    for (unsigned i = 0; i < sizeof kAll / sizeof kAll[0]; ++i)
        for (unsigned j = i + 1; j < sizeof kAll / sizeof kAll[0]; ++j)
            if (kAll[i] == kAll[j]) return false;
    return true;
}
constexpr bool onHwSpi(int p) { return p == 11 || p == 12 || p == 13; }
static_assert(unique(), "two functions share a GPIO");
static_assert(!onHwSpi(PIN_LCD_CS) && !onHwSpi(PIN_LCD_DC) && !onHwSpi(PIN_LCD_RST),
              "LCD CS/DC/RST must not use GPIO 11-13: hardware SPI claims them");
}  // namespace pins
}  // namespace sb
