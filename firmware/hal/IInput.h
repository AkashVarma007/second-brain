#pragma once
#include "domain.h"

namespace sb {
struct IInput {
    virtual ~IInput() = default;
    // Returns true and sets `out` if a button press occurred since the last
    // poll; returns false otherwise.
    virtual bool poll(Event& out) = 0;
};
}  // namespace sb
