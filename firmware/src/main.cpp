#include <Arduino.h>
#include "buttons.h"
#include "display.h"
#include "router.h"
#include "ui.h"

using namespace sb;

static Buttons buttons;
static Router router;
static uint32_t lastFrame = UINT32_MAX;
static ScreenId lastScreen = ScreenId::Home;

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("NOG-OS booting");
    display::begin();
    buttons.begin();
    Serial.printf("screen=%s\n", screen_name(router.ui().screen));
}

void loop() {
    const uint32_t now = millis();
    bool changed = false;
    Event e;
    while (buttons.poll(e)) {
        router.handle(e, now);
        changed = true;
    }
    router.tick(now);

    const ScreenId screen = router.ui().screen;
    if (screen != lastScreen) {
        lastScreen = screen;
        Serial.printf("screen=%s\n", screen_name(screen));
    }

    // Redraw on input and on every animation frame (pet bob, waveform, timers).
    const uint32_t frame = now / kFrameMs;
    if (changed || frame != lastFrame) {
        lastFrame = frame;
        ui::render(display::gfx(), router.ui());
        display::flush();
    }
    delay(5);
}
