#include "ui.h"
#include <cmath>
#include <cstdio>
#include "demo.h"
#include "gfx.h"
#include "menu.h"
#include "router.h"
#include "sprites.h"

// Every NOG-OS screen, drawn into a 128x64 1-bit buffer. Layout follows the
// UI mock at 1 LCD pixel = 1 pixel. Draw colour 1 = lit; inverted rows draw
// their content in colour 0 on a filled box.
namespace sb {
namespace ui {

namespace {
using namespace gfx;
namespace sp = sprites;

constexpr int kRight = kW - 2;  // right text edge

uint32_t frameOf(const UiState& s) { return s.nowMs / kFrameMs; }
int bob(uint32_t f) { return (f % 2) ? -1 : 0; }

// 2 on, 1 off: the ground NOG stands on.
void ground(u8g2_t* g, int x, int y, int w) {
    for (int i = 0; i < w; i += 3) u8g2_DrawHLine(g, x + i, y, (w - i) < 2 ? (w - i) : 2);
}

// Selected row of a list: filled rounded box, then content in colour 0.
void rowBg(u8g2_t* g, int y, int h, bool selected) {
    if (!selected) return;
    u8g2_DrawRBox(g, 1, y, kW - 8, h, 2);  // stops short of the menu scrollbar
    u8g2_SetDrawColor(g, 0);
}

void xpBar(u8g2_t* g, int x, int y, int w) {
    bar(g, x, y, w, 7, demo::kXp * 1000 / demo::kXpNext);
}

void drawHome(u8g2_t* g, const UiState& s) {
    const uint32_t f = frameOf(s);
    font(g, Font::Bold);
    str(g, 2, 9, "NOG");
    font(g, Font::Body);
    char lv[8];
    std::snprintf(lv, sizeof lv, "LV%d", demo::kLevel);
    str(g, 31, 8, lv);
    sprite(g, 89, 3, sp::kUp);
    font(g, Font::Tiny);
    char q[4];
    std::snprintf(q, sizeof q, "%d", demo::kQueuedClips);
    str(g, 97, 8, q);
    sprite(g, 104, 3, sp::kWifi);
    sprite(g, 115, 3, sp::kBattery);
    hrule(g, 0, 10, kW);

    sprite(g, 6, 21 + bob(f), (f % 8 == 5) ? sp::kPetBlink : sp::kPetIdle);
    ground(g, 4, 41, 26);

    u8g2_DrawFrame(g, 36, 14, 90, 28);
    sprite(g, 32, 23, sp::kTail);
    font(g, Font::Body);
    lines(g, 41, 25, 10, demo::kQuips[(f / 10) % 3], 82);

    str(g, 2, 61, "XP");
    xpBar(g, 16, 55, 56);
    char xp[16];
    std::snprintf(xp, sizeof xp, "%d/%d", demo::kXp, demo::kXpNext);
    str(g, 77, 61, xp);
}

void drawMenu(u8g2_t* g, const UiState& s) {
    static const sp::Sprite* const icons[kMenuCount] = {&sp::kMic, &sp::kNote, &sp::kSword, &sp::kFace,
                                                       &sp::kStar, &sp::kSync, &sp::kGear};
    const int done = __builtin_popcount(s.questsDone);
    char counts[kMenuCount][8] = {"", "", "", "", "", "", ""};
    std::snprintf(counts[1], 8, "%d", demo::kNoteCount);
    std::snprintf(counts[2], 8, "%d", kQuestsCount - done);
    std::snprintf(counts[3], 8, "LV%d", demo::kLevel);
    std::snprintf(counts[5], 8, "%d", demo::kQueuedClips);

    const int start = list_window_start(s.menuSel, kMenuCount, 4);
    for (int row = 0; row < 4; ++row) {
        const int i = start + row;
        const int y = 4 + row * 14;
        rowBg(g, y, 13, i == s.menuSel);
        sprite(g, 6, y + 3, *icons[i]);
        font(g, Font::Bold);
        str(g, 20, y + 10, demo::kMenuLabels[i]);
        font(g, Font::Body);
        strRight(g, 116, y + 10, counts[i]);
        u8g2_SetDrawColor(g, 1);
    }
    vrule(g, 124, 4, 56);
    const int thumbH = 56 * 4 / kMenuCount;
    u8g2_DrawBox(g, 123, 4 + (56 - thumbH) * s.menuSel / (kMenuCount - 1), 3, thumbH);
}

void drawTalk(u8g2_t* g, const UiState&) {
    header(g, "TALK", "AUTO-SORT", true);
    sprite(g, 8, 20, sp::kPetListen);
    font(g, Font::Bold);
    str(g, 40, 24, "HOLD TALK");
    font(g, Font::Body);
    str(g, 40, 35, "AND SPEAK");
    str(g, 40, 45, "ALL EARS!");
    hrule(g, 0, 51, kW);
    strCenter(g, kW / 2, 61, "NOTE / QUEST / IDEA");
}

void drawRecording(u8g2_t* g, const UiState& s) {
    const uint32_t f = frameOf(s);
    if (f % 2 == 0) sprite(g, 2, 3, sp::kDot);
    font(g, Font::Bold);
    str(g, 10, 9, "REC");
    uint32_t secs = (s.nowMs - s.recStartMs) / 1000;
    if (secs > 59) secs = 59;
    char t[8];
    std::snprintf(t, sizeof t, "00:%02u", unsigned(secs));
    font(g, Font::Arcade);
    strRight(g, kRight, 9, t);
    hrule(g, 0, 11, kW);

    for (int i = 0; i < 30; ++i) {
        const float v = std::fabs(std::sin(i * 0.9f + f * 1.7f) * std::cos(i * 0.37f - f * 0.6f));
        const int h = 2 + 2 * int(std::lround(v * 14));
        u8g2_DrawBox(g, 5 + i * 4, 32 - h / 2, 2, h);
    }
    hrule(g, 0, 51, kW);
    font(g, Font::Body);
    strCenter(g, kW / 2, 61, "LET GO TO SEND");
}

void drawThinking(u8g2_t* g, const UiState& s) {
    const uint32_t f = frameOf(s);
    sprite(g, 8, 30, sp::kPetThink);
    const int puffs = f % 4;
    if (puffs > 0) u8g2_DrawBox(g, 30, 25, 2, 2);
    if (puffs > 1) u8g2_DrawFrame(g, 33, 17, 4, 4);
    if (puffs > 2) u8g2_DrawFrame(g, 37, 6, 6, 6);

    font(g, Font::Bold);
    str(g, 50, 20, "CHEWING ON");
    str(g, 50, 31, "YOUR WORDS");
    const int dots = f % 6;
    for (int i = 0; i < 5; ++i) {
        if (i < dots) u8g2_DrawBox(g, 50 + i * 7, 37, 5, 5);
        else u8g2_DrawFrame(g, 50 + i * 7, 37, 5, 5);
    }
    font(g, Font::Body);
    str(g, 50, 55, "ON YOUR LAPTOP", kW - 52);
}

void drawResult(u8g2_t* g, const UiState& s) {
    const demo::Result& r = demo::kResults[s.resultIdx % kResultCount];
    header(g, r.kind, r.xp, true);
    font(g, Font::Bold);
    str(g, 2, 24, r.line1, 98);
    str(g, 2, 35, r.line2, 98);
    font(g, Font::Body);
    str(g, 2, 46, r.meta, 98);
    sprite(g, 104, 18 + bob(frameOf(s)), sp::kPetHappy);
    hrule(g, 0, 51, kW);
    str(g, 2, 61, "OK KEEP");
    strRight(g, kRight, 61, "BACK UNDO");
}

void drawNotes(u8g2_t* g, const UiState& s) {
    char n[8];
    std::snprintf(n, sizeof n, "%d", demo::kNoteCount);
    header(g, "NOTES", n, false);
    for (int i = 0; i < kNotesCount; ++i) {
        const int y = 14 + i * 14;
        rowBg(g, y, 13, i == s.listSel);
        font(g, Font::Body);
        const int timeX = 116 - u8g2_GetStrWidth(g, demo::kNotes[i].when);
        str(g, timeX, y + 10, demo::kNotes[i].when);
        font(g, Font::Bold);
        str(g, 5, y + 10, demo::kNotes[i].title, timeX - 5 - 4);
        u8g2_SetDrawColor(g, 1);
    }
}

void drawQuests(u8g2_t* g, const UiState& s) {
    const int done = __builtin_popcount(s.questsDone);
    char n[8];
    std::snprintf(n, sizeof n, "%d/%d", done, kQuestsCount);
    header(g, "QUESTS", n, false);
    const int start = list_window_start(s.listSel, kQuestsCount, 4);
    for (int row = 0; row < 4; ++row) {
        const int i = start + row;
        const int y = 12 + row * 13;
        const bool ticked = s.questsDone & (1u << i);
        rowBg(g, y, 12, i == s.listSel);
        sprite(g, 5, y + 4, ticked ? sp::kBoxChecked : sp::kBox);
        font(g, Font::Body);
        str(g, 14, y + 10, demo::kQuests[i].prio);
        font(g, Font::Bold);
        str(g, 30, y + 10, demo::kQuests[i].title, 88);
        if (ticked) u8g2_DrawHLine(g, 30, y + 6, u8g2_GetStrWidth(g, demo::kQuests[i].title));
        u8g2_SetDrawColor(g, 1);
    }
}

void drawPet(u8g2_t* g, const UiState& s) {
    const uint32_t f = frameOf(s);
    u8g2_DrawRFrame(g, 1, 1, 40, 62, 3);
    sprite(g, 10, 12 + bob(f), sp::kPetHappy);
    font(g, Font::Bold);
    strCenter(g, 21, 46, "NOG");
    font(g, Font::Tiny);
    strCenter(g, 21, 56, demo::kRank);

    const int x = 46;
    char lv[24];
    std::snprintf(lv, sizeof lv, "LV%d %s", demo::kLevel, demo::kRank);
    font(g, Font::Bold);
    str(g, x, 10, lv, kW - x - 2);
    font(g, Font::Body);
    str(g, x, 21, "MOOD");
    const int full = 2 + __builtin_popcount(s.questsDone);
    for (int i = 0; i < 4; ++i) sprite(g, 74 + i * 7, 16, i < full ? sp::kHeart : sp::kHeartEmpty);
    char streak[16];
    std::snprintf(streak, sizeof streak, "STREAK %dD", demo::kStreakDays);
    str(g, x, 32, streak);
    xpBar(g, x, 36, 60);
    char xp[24];
    std::snprintf(xp, sizeof xp, "%d/%d XP", demo::kXp, demo::kXpNext);
    str(g, x, 52, xp);
    font(g, Font::Tiny);
    str(g, x, 62, "OK: EVOLUTION");
}

// Locked evolution: only every other pixel of the silhouette.
void silhouette(u8g2_t* g, int x, int y, const sp::Sprite& s) {
    for (int row = 0; row < s.h; ++row)
        for (int col = 0; col < s.w; ++col)
            if (s.rows[row][col] == '#' && ((col + row) % 2 == 0)) u8g2_DrawPixel(g, x + col, y + row);
}

void drawEvo(u8g2_t* g, const UiState&) {
    char lv[8];
    std::snprintf(lv, sizeof lv, "LV%d", demo::kLevel);
    header(g, "EVOLUTION", lv, false);
    sprite(g, 8, 22, sp::kEgg);
    sprite(g, 27, 27, sp::kArrow);
    sprite(g, 38, 20, sp::kPetIdle);
    sprite(g, 65, 27, sp::kArrow);
    silhouette(g, 76, 16, sp::kSage);
    font(g, Font::Bold);
    strCenter(g, 89, 31, "?");
    font(g, Font::Tiny);
    strCenter(g, 15, 46, "EGG");
    strCenter(g, 49, 46, "NOG");
    strCenter(g, 89, 46, "???");
    hrule(g, 0, 51, kW);
    font(g, Font::Body);
    strCenter(g, kW / 2, 61, "EVOLVES AT 1800 XP");
}

void drawRecap(u8g2_t* g, const UiState&) {
    header(g, "TODAY", "OCT 14", false);
    font(g, Font::Body);
    for (int i = 0; i < 3; ++i) str(g, 2, 23 + i * 10, demo::kHaiku[i], 80);
    sprite(g, 86, 14, sp::kPostcard);
    hrule(g, 0, 51, kW);
    strCenter(g, kW / 2, 61, "OK SAVE TO GALLERY");
}

void drawSync(u8g2_t* g, const UiState& s) {
    header(g, "SYNC", "", false);
    sprite(g, 119, 3, sp::kWifi);
    const char* rows[3][2] = {{"WIFI", "HOME-NET"}, {"BRAIN", "SB.LOCAL"}, {"QUEUE", "2 CLIPS"}};
    for (int i = 0; i < 3; ++i) {
        font(g, Font::Body);
        str(g, 2, 22 + i * 10, rows[i][0]);
        font(g, Font::Bold);
        str(g, 40, 22 + i * 10, rows[i][1], kW - 42);
    }
    bar(g, 2, 46, kW - 4, 7, int((frameOf(s) * 90) % 1000));
    font(g, Font::Body);
    str(g, 2, 62, "LAST 2 MIN AGO");
}

void drawSetup(u8g2_t* g, const UiState& s) {
    header(g, "SETUP", "", false);
    for (int i = 0; i < kSetupCount; ++i) {
        const demo::Setting& st = demo::kSettings[i];
        const int y = 12 + i * 13;
        const bool sel = i == s.listSel;
        rowBg(g, y, 12, sel);
        font(g, Font::Bold);
        str(g, 5, y + 10, st.label);
        if (st.bar > 0) {
            for (int j = 0; j < 4; ++j) {
                if (j < st.bar) u8g2_DrawBox(g, 94 + j * 6, y + 3, 4, 6);
                else u8g2_DrawFrame(g, 94 + j * 6, y + 3, 4, 6);
            }
        } else {
            font(g, Font::Body);
            strRight(g, 118, y + 10, st.value);
        }
        u8g2_SetDrawColor(g, 1);
    }
}

void drawSleep(u8g2_t* g, const UiState& s) {
    const uint32_t f = frameOf(s);
    sprite(g, 16, 26, sp::kPetSleep);
    ground(g, 14, 46, 26);
    font(g, Font::Tiny);
    str(g, 44, 26 - int((f + 0) % 3), "Z");
    font(g, Font::Body);
    str(g, 52, 19 - int((f + 1) % 3), "Z");
    font(g, Font::Bold);
    str(g, 62, 11 - int((f + 2) % 3), "Z");
    font(g, Font::Body);
    strRight(g, kRight, 61, "PRESS ANY KEY");
}

}  // namespace

void render(u8g2_t* g, const UiState& s) {
    u8g2_ClearBuffer(g);
    u8g2_SetFontMode(g, 1);  // transparent, so colour-0 text works on filled rows
    u8g2_SetDrawColor(g, 1);
    switch (s.screen) {
        case ScreenId::Home: drawHome(g, s); break;
        case ScreenId::Menu: drawMenu(g, s); break;
        case ScreenId::Talk: drawTalk(g, s); break;
        case ScreenId::Recording: drawRecording(g, s); break;
        case ScreenId::Thinking: drawThinking(g, s); break;
        case ScreenId::Result: drawResult(g, s); break;
        case ScreenId::Notes: drawNotes(g, s); break;
        case ScreenId::Quests: drawQuests(g, s); break;
        case ScreenId::Pet: drawPet(g, s); break;
        case ScreenId::Evo: drawEvo(g, s); break;
        case ScreenId::Recap: drawRecap(g, s); break;
        case ScreenId::Sync: drawSync(g, s); break;
        case ScreenId::Setup: drawSetup(g, s); break;
        case ScreenId::Sleep: drawSleep(g, s); break;
    }
    if (s.popup) popup(g, s.popup);
}

}  // namespace ui
}  // namespace sb
