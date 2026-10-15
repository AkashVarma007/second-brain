#include "gfx.h"
#include <cstring>

namespace sb {
namespace gfx {

namespace {
int cuts = 0;
const char* lastCut = "";

// Copies the next '\n'-separated line of `p` into buf and advances p.
// Returns false once the text is used up.
bool nextLine(const char*& p, char (&buf)[64]) {
    if (!p || !*p) return false;
    const char* nl = std::strchr(p, '\n');
    size_t len = nl ? size_t(nl - p) : std::strlen(p);
    if (len > sizeof buf - 1) len = sizeof buf - 1;
    std::memcpy(buf, p, len);
    buf[len] = '\0';
    p = nl ? nl + 1 : p + std::strlen(p);
    return true;
}
}  // namespace

void font(u8g2_t* g, Font f) {
    switch (f) {
        case Font::Bold: u8g2_SetFont(g, u8g2_font_helvB08_tr); break;
        case Font::Body: u8g2_SetFont(g, u8g2_font_haxrcorp4089_tr); break;
        case Font::Tiny: u8g2_SetFont(g, u8g2_font_4x6_tr); break;
        case Font::Arcade: u8g2_SetFont(g, u8g2_font_pressstart2p_8r); break;
    }
}

void sprite(u8g2_t* g, int x, int y, const sprites::Sprite& s) {
    for (int row = 0; row < s.h; ++row) {
        const char* r = s.rows[row];
        int col = 0;
        while (col < s.w) {
            if (r[col] != '#') { ++col; continue; }
            const int start = col;
            while (col < s.w && r[col] == '#') ++col;
            u8g2_DrawHLine(g, x + start, y + row, col - start);
        }
    }
}

void hrule(u8g2_t* g, int x, int y, int w) {
    for (int i = 0; i < w; i += 2) u8g2_DrawPixel(g, x + i, y);
}

void vrule(u8g2_t* g, int x, int y, int h) {
    for (int i = 0; i < h; i += 2) u8g2_DrawPixel(g, x, y + i);
}

// `text` if it fits in maxW, else its longest prefix + ".." in buf (counted).
static const char* fit(u8g2_t* g, const char* text, int maxW, char (&buf)[64]) {
    if (u8g2_GetStrWidth(g, text) <= maxW) return text;
    size_t n = std::strlen(text);
    if (n > sizeof buf - 3) n = sizeof buf - 3;
    std::memcpy(buf, text, n);
    for (;;) {
        std::strcpy(buf + n, "..");
        if (n == 0 || u8g2_GetStrWidth(g, buf) <= maxW) break;
        --n;
    }
    ++cuts;
    lastCut = text;
    return buf;
}

void str(u8g2_t* g, int x, int baseline, const char* text, int maxW) {
    char buf[64];
    u8g2_DrawStr(g, x, baseline, fit(g, text, maxW < 0 ? kW - x : maxW, buf));
}

void strRight(u8g2_t* g, int xRight, int baseline, const char* text) {
    char buf[64];
    const char* t = fit(g, text, xRight, buf);
    u8g2_DrawStr(g, xRight - u8g2_GetStrWidth(g, t), baseline, t);
}

void strCenter(u8g2_t* g, int cx, int baseline, const char* text) {
    char buf[64];
    const int half = cx < kW - cx ? cx : kW - cx;
    const char* t = fit(g, text, 2 * half, buf);
    u8g2_DrawStr(g, cx - u8g2_GetStrWidth(g, t) / 2, baseline, t);
}

int truncations() { return cuts; }
const char* lastTruncated() { return lastCut; }

void lines(u8g2_t* g, int x, int baseline, int lineH, const char* text, int maxW) {
    char buf[64];
    for (const char* p = text; nextLine(p, buf); baseline += lineH) str(g, x, baseline, buf, maxW);
}

void header(u8g2_t* g, const char* left, const char* right, bool inverted) {
    if (inverted) {
        u8g2_SetDrawColor(g, 1);
        u8g2_DrawBox(g, 0, 0, kW, 10);
        u8g2_SetDrawColor(g, 0);
    } else {
        hrule(g, 0, 10, kW);
    }
    font(g, Font::Body);
    const int rightW = (right && *right) ? u8g2_GetStrWidth(g, right) + 4 : 0;
    font(g, Font::Bold);
    str(g, 2, 9, left, kW - 4 - rightW);
    if (rightW) {
        font(g, Font::Body);
        strRight(g, kW - 2, 8, right);
    }
    u8g2_SetDrawColor(g, 1);
}

void bar(u8g2_t* g, int x, int y, int w, int h, int permille) {
    if (permille < 0) permille = 0;
    if (permille > 1000) permille = 1000;
    u8g2_DrawFrame(g, x, y, w, h);
    const int fill = (w - 4) * permille / 1000;
    if (fill > 0) u8g2_DrawBox(g, x + 2, y + 2, fill, h - 4);
}

void popup(u8g2_t* g, const char* text) {
    font(g, Font::Bold);
    constexpr int kLineH = 11;
    char buf[64];
    int widest = 0;
    int count = 0;
    for (const char* p = text; nextLine(p, buf); ++count) {
        const int w = u8g2_GetStrWidth(g, buf);
        widest = w > widest ? w : widest;
    }
    const int w = widest + 14;
    const int h = count * kLineH + 8;
    const int x = (kW - w) / 2;
    const int y = (kH - h) / 2;
    u8g2_SetDrawColor(g, 0);
    u8g2_DrawBox(g, x - 3, y - 3, w + 6, h + 6);
    u8g2_SetDrawColor(g, 1);
    u8g2_DrawFrame(g, x - 2, y - 2, w + 4, h + 4);
    u8g2_DrawFrame(g, x, y, w, h);
    int baseline = y + 13;
    for (const char* p = text; nextLine(p, buf); baseline += kLineH) strCenter(g, kW / 2, baseline, buf);
}

}  // namespace gfx
}  // namespace sb
