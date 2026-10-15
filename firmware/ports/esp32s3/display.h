#pragma once
#include <clib/u8g2.h>

namespace sb {
namespace display {
// Bring up the 128x64 panel. Call once from setup().
void begin();
// The u8g2 C handle the UI draws into (full frame buffer).
u8g2_t* gfx();
// Push the frame buffer to the panel.
void flush();
}  // namespace display
}  // namespace sb
