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
