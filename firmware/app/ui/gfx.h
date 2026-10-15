#pragma once
#include <clib/u8g2.h>
#include "sprites.h"

// Small drawing kit over the u8g2 C API, shared by every screen. 128x64, 1-bit.
namespace sb {
namespace gfx {

constexpr int kW = 128;
constexpr int kH = 64;

// bold = Flipper's primary font, body = its secondary, tiny for status
// numbers, arcade for big words (timer, LEVEL UP).
enum class Font { Bold, Body, Tiny, Arcade };
void font(u8g2_t* g, Font f);

// Lit pixels of `s` in the current draw colour, top-left at (x, y).
void sprite(u8g2_t* g, int x, int y, const sprites::Sprite& s);

// Dotted rules: one pixel on, one off.
void hrule(u8g2_t* g, int x, int y, int w);
void vrule(u8g2_t* g, int x, int y, int h);

// Text at (x, baseline). If wider than maxW (default: up to the right edge) it
// is cut and ends in ".."; every cut is counted so the render tool can fail on
// demo text that overflows. strRight/strCenter cut and count the same way when
// the text would leave the screen.
void str(u8g2_t* g, int x, int baseline, const char* text, int maxW = -1);
void strRight(u8g2_t* g, int xRight, int baseline, const char* text);
void strCenter(u8g2_t* g, int cx, int baseline, const char* text);
int truncations();
const char* lastTruncated();

// '\n'-separated lines, first baseline at `baseline`.
void lines(u8g2_t* g, int x, int baseline, int lineH, const char* text, int maxW = -1);

// Rows 0-9: bold title left, body text right (the title is cut, and counted,
// if it would run into the value). Inverted = filled bar; otherwise a dotted
// rule at y 10.
void header(u8g2_t* g, const char* left, const char* right, bool inverted);

// Framed progress bar with a 1 px gap around the fill. permille 0-1000.
void bar(u8g2_t* g, int x, int y, int w, int h, int permille);

// Centred double-framed box over whatever is drawn ('\n' splits lines).
void popup(u8g2_t* g, const char* text);

}  // namespace gfx
}  // namespace sb
