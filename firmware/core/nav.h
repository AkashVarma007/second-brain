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
