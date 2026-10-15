#pragma once
#include "IInput.h"

namespace sb {
// Reads 7 active-low buttons (INPUT_PULLUP) with time-based debouncing.
// Every button emits its Event on press; TALK also emits TalkUp on release.
class Buttons : public IInput {
public:
    void begin();
    bool poll(Event& out) override;

private:
    struct Btn { int pin; Event press; bool last; unsigned long changedAt; };
    static constexpr int kCount = 7;
    Btn btns_[kCount];
};
}  // namespace sb
