#pragma once
#include "domain.h"

namespace sb {
namespace ui {
// Rebuild the active LVGL screen to reflect `s`. Call after each state change.
void render(const UiState& s);
}  // namespace ui
}  // namespace sb
