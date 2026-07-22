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
