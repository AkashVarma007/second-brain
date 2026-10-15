#include "display.h"
#include <U8g2lib.h>
#include "config.h"

namespace sb {
namespace display {

// Wokwi + bench: SSD1306 128x64 OLED over hardware I2C.
static U8G2_SSD1306_128X64_NONAME_F_HW_I2C panel(U8G2_R0, U8X8_PIN_NONE, PIN_OLED_SCL, PIN_OLED_SDA);

// Pocket build: ST7567 128x64 LCD over hardware SPI. Swap the line above for
// the one matching your module (ST7567 boards differ: also try _JLX12864_ or
// _OS12864_), then tune contrast in begin() -- every panel needs its own value.
// static U8G2_ST7567_ENH_DG128064_F_4W_HW_SPI panel(U8G2_R0, PIN_LCD_CS, PIN_LCD_DC, PIN_LCD_RST);

void begin() {
    panel.setBusClock(400000);
    panel.begin();
    // panel.setContrast(...);  // ST7567: calibrate per module
}

u8g2_t* gfx() { return panel.getU8g2(); }

void flush() { panel.sendBuffer(); }

}  // namespace display
}  // namespace sb
