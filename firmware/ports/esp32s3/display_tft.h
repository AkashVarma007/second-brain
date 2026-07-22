#pragma once

namespace sb {
namespace display {
// Initialize TFT_eSPI + LVGL (draw buffer, display driver, flush callback,
// backlight). Call once from setup() before creating any LVGL widgets.
void begin();
}  // namespace display
}  // namespace sb
