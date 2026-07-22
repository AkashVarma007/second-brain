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
