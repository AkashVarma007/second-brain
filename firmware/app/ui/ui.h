#pragma once
#include <clib/u8g2.h>
#include "domain.h"

namespace sb {
namespace ui {
// Draw `s` into the u8g2 frame buffer (clears it first). The caller pushes the
// buffer to the panel; the host render tool reads it back instead.
void render(u8g2_t* g, const UiState& s);
}  // namespace ui
}  // namespace sb
