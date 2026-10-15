// Host render tool: draws every NOG-OS screen with the real UI code into a
// u8g2 frame buffer on the laptop and writes one PBM per screen.
// Built and run by render.sh; no hardware or simulator needed.
#include <cstdio>
#include <cstring>
#include <string>
#include <clib/u8g2.h>
#include "demo.h"
#include "gfx.h"
#include "router.h"
#include "ui.h"

using namespace sb;

namespace {

int pixel(u8g2_t* g, int x, int y) {
    // SSD1306 full buffer: 8 pages of 128 bytes, LSB = top row of the page.
    const uint8_t* buf = u8g2_GetBufferPtr(g);
    return (buf[(y / 8) * gfx::kW + x] >> (y % 8)) & 1;
}

bool writePbm(u8g2_t* g, const std::string& path) {
    FILE* f = std::fopen(path.c_str(), "w");
    if (!f) return false;
    std::fprintf(f, "P1\n%d %d\n", gfx::kW, gfx::kH);
    for (int y = 0; y < gfx::kH; ++y) {
        for (int x = 0; x < gfx::kW; ++x) std::fputc(pixel(g, x, y) ? '1' : '0', f);
        std::fputc('\n', f);
    }
    return std::fclose(f) == 0;
}

int failures = 0;
void check(bool ok, const char* what) {
    if (!ok) {
        std::fprintf(stderr, "SELF-TEST FAIL: %s\n", what);
        ++failures;
    }
}

// The kit's own behaviour, checked on real u8g2 pixels before any screen is drawn.
void selfTest(u8g2_t* g) {
    u8g2_ClearBuffer(g);
    u8g2_SetDrawColor(g, 1);
    gfx::sprite(g, 10, 20, sprites::kHeart);
    bool same = true;
    for (int y = 0; y < sprites::kHeart.h; ++y)
        for (int x = 0; x < sprites::kHeart.w; ++x)
            same &= pixel(g, 10 + x, 20 + y) == (sprites::kHeart.rows[y][x] == '#');
    check(same, "sprite pixels match their rows");
    check(!pixel(g, 9, 20) && !pixel(g, 15, 20), "sprite draws nothing outside its box");

    u8g2_ClearBuffer(g);
    gfx::hrule(g, 0, 5, 6);
    check(pixel(g, 0, 5) && !pixel(g, 1, 5) && pixel(g, 2, 5), "hrule is dotted");

    u8g2_ClearBuffer(g);
    gfx::font(g, gfx::Font::Body);
    const int before = gfx::truncations();
    gfx::str(g, 0, 10, "SHORT", 100);
    check(gfx::truncations() == before, "short text is not cut");
    gfx::str(g, 0, 20, "A VERY LONG LINE OF TEXT THAT CANNOT FIT", 40);
    check(gfx::truncations() == before + 1, "long text is cut and counted");
    int maxLit = -1;
    for (int y = 12; y < 24; ++y)
        for (int x = 0; x < gfx::kW; ++x)
            if (pixel(g, x, y)) maxLit = x > maxLit ? x : maxLit;
    check(maxLit >= 0 && maxLit < 40, "cut text stays inside maxW");

    // Every text helper must count overflow, not only str() with an explicit width.
    const char* longText = "A VERY LONG LINE OF TEXT THAT CANNOT FIT";
    int n = gfx::truncations();
    gfx::str(g, 100, 30, "LONGER THAN THE EDGE");
    check(gfx::truncations() == n + 1, "str() without maxW stops at the right edge");
    n = gfx::truncations();
    gfx::strRight(g, 20, 40, longText);
    check(gfx::truncations() == n + 1, "strRight() counts text running off the left edge");
    n = gfx::truncations();
    gfx::strCenter(g, 64, 50, longText);
    check(gfx::truncations() == n + 1, "strCenter() counts text wider than the screen");
    n = gfx::truncations();
    gfx::header(g, "A VERY LONG TITLE", "AND A LONG VALUE", false);
    check(gfx::truncations() == n + 1, "header() counts a title colliding with its value");
}

struct Cell {
    const char* name;
    UiState s;
};

UiState at(ScreenId screen, uint32_t frame) {
    UiState s;
    s.screen = screen;
    s.nowMs = frame * kFrameMs;
    return s;
}

}  // namespace

int main(int argc, char** argv) {
    const std::string out = argc > 1 ? argv[1] : ".pio/renders";
    u8g2_t g;
    u8g2_Setup_ssd1306_128x64_noname_f(&g, U8G2_R0, u8x8_byte_empty, u8x8_dummy_cb);
    u8g2_InitDisplay(&g);

    selfTest(&g);
    const int selfTestCuts = gfx::truncations();

    // The same 15 states as the mock's screen map.
    Cell cells[15] = {
        {"home", at(ScreenId::Home, 1)},
        {"menu", at(ScreenId::Menu, 1)},
        {"talk", at(ScreenId::Talk, 1)},
        {"recording", at(ScreenId::Recording, 4)},
        {"thinking", at(ScreenId::Thinking, 3)},
        {"result", at(ScreenId::Result, 1)},
        {"notes", at(ScreenId::Notes, 1)},
        {"quests", at(ScreenId::Quests, 1)},
        {"quest-done", at(ScreenId::Quests, 1)},
        {"pet", at(ScreenId::Pet, 2)},
        {"evolution", at(ScreenId::Evo, 1)},
        {"recap", at(ScreenId::Recap, 1)},
        {"sync", at(ScreenId::Sync, 5)},
        {"setup", at(ScreenId::Setup, 1)},
        {"sleep", at(ScreenId::Sleep, 1)},
    };
    cells[1].s.menuSel = 1;
    cells[3].s.recStartMs = cells[3].s.nowMs - 7000;
    cells[7].s.listSel = 1;
    cells[7].s.questsDone = 0x01;
    cells[8].s.listSel = 1;
    cells[8].s.questsDone = 0x03;
    cells[8].s.popup = demo::kPopupQuestDone;
    cells[9].s.questsDone = 0x01;

    for (int i = 0; i < 15; ++i) {
        ui::render(&g, cells[i].s);
        char path[512];
        std::snprintf(path, sizeof path, "%s/%02d-%s.pbm", out.c_str(), i + 1, cells[i].name);
        if (!writePbm(&g, path)) {
            std::fprintf(stderr, "cannot write %s\n", path);
            return 2;
        }
    }

    // States the 15 pictures don't show, drawn only to check their text fits:
    // every result, every quip, the end of each scrolling list.
    UiState extra[] = {at(ScreenId::Result, 1), at(ScreenId::Result, 1), at(ScreenId::Result, 1),
                       at(ScreenId::Home, 0),   at(ScreenId::Home, 10),  at(ScreenId::Home, 20),
                       at(ScreenId::Quests, 1), at(ScreenId::Menu, 1),   at(ScreenId::Notes, 1),
                       at(ScreenId::Setup, 1)};
    for (int i = 0; i < 3; ++i) extra[i].resultIdx = i;
    extra[6].listSel = kQuestsCount - 1;
    extra[6].questsDone = 0x1F;  // every title struck through
    extra[7].menuSel = kMenuCount - 1;
    extra[8].listSel = kNotesCount - 1;
    extra[9].listSel = kSetupCount - 1;
    for (const UiState& s : extra) ui::render(&g, s);

    const int cuts = gfx::truncations() - selfTestCuts;
    if (cuts > 0) {
        std::fprintf(stderr, "%d demo string(s) overflow their slot, last: \"%s\"\n", cuts, gfx::lastTruncated());
        ++failures;
    }
    std::printf("rendered 15 screens to %s, %d failure(s)\n", out.c_str(), failures);
    return failures ? 1 : 0;
}
