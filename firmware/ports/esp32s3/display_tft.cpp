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
