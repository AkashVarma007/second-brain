#pragma once
#include <deque>
#include "IInput.h"

namespace sb {
class InputStub : public IInput {
public:
    void push(Event e) { q_.push_back(e); }
    bool poll(Event& out) override {
        if (q_.empty()) return false;
        out = q_.front();
        q_.pop_front();
        return true;
    }
private:
    std::deque<Event> q_;
};
}  // namespace sb
