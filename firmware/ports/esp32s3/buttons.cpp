#include "buttons.h"
#include <Arduino.h>
#include "config.h"

namespace sb {

void Buttons::begin() {
    btns_[0] = {PIN_BTN_UP,    Event::Up,       true, 0};
    btns_[1] = {PIN_BTN_DOWN,  Event::Down,     true, 0};
    btns_[2] = {PIN_BTN_LEFT,  Event::Left,     true, 0};
    btns_[3] = {PIN_BTN_RIGHT, Event::Right,    true, 0};
    btns_[4] = {PIN_BTN_OK,    Event::Ok,       true, 0};
    btns_[5] = {PIN_BTN_BACK,  Event::Back,     true, 0};
    btns_[6] = {PIN_BTN_TALK,  Event::TalkDown, true, 0};
    for (auto& b : btns_) pinMode(b.pin, INPUT_PULLUP);
}

bool Buttons::poll(Event& out) {
    const unsigned long now = millis();
    for (auto& b : btns_) {
        const bool level = digitalRead(b.pin);  // HIGH = released, LOW = pressed
        if (level == b.last || (now - b.changedAt) <= 25) continue;
        b.changedAt = now;
        b.last = level;
        if (level == LOW) {                     // falling edge = press
            out = b.press;
            return true;
        }
        if (b.press == Event::TalkDown) {       // rising edge on TALK = release
            out = Event::TalkUp;
            return true;
        }
    }
    return false;
}

}  // namespace sb
