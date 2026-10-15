#pragma once

// Demo content for the UI-only build. Everything here is a stand-in for data
// the laptop brain will send later; nothing is persisted.
namespace sb {
namespace demo {

constexpr const char* kPopupQuestDone = "QUEST DONE\n+20 XP";

// Same order as Router's kMenu.
constexpr const char* kMenuLabels[] = {"TALK", "NOTES", "QUESTS", "NOG", "RECAP", "SYNC", "SETUP"};

struct Note { const char* title; const char* when; };
constexpr Note kNotes[] = {
    {"SOLAR LAMP", "09:12"},
    {"DREAM LOG", "07:40"},
    {"BIKE ROUTE", "Y-DAY"},
};

struct Quest { const char* prio; const char* title; };
constexpr Quest kQuests[] = {
    {"!!!", "CALL MOM"},
    {"!!", "FIX BIKE"},
    {"!!", "SEND INVOICE"},
    {"!", "BUY COFFEE"},
    {"!", "WATER PLANTS"},
};

struct Result { const char* kind; const char* xp; const char* line1; const char* line2; const char* meta; };
constexpr Result kResults[] = {
    {"NEW QUEST", "+15XP", "CALL MOM ABOUT", "SUNDAY LUNCH", "!!! HIGH, SUN"},
    {"NEW IDEA", "+10XP", "SOLAR LAMP FOR", "THE BALCONY", "SAVED TO NOTES"},
    {"JOURNAL", "+10XP", "GOOD RUN TODAY", "KNEE FELT OK", "MOOD: BRIGHT"},
};

constexpr const char* kQuips[] = {
    "3 IDEAS FED\nMORE PLEASE",
    "MOM CALL?\nTICK TOCK",
    "6 DAY STREAK\nDONT BREAK IT",
};

constexpr const char* kHaiku[] = {"SPARKS AT 9,", "A CALL UNMADE", "TEA GOES COLD"};

struct Setting { const char* label; const char* value; int bar; };  // bar > 0 = level of 4
constexpr Setting kSettings[] = {
    {"BRIGHT", "", 3},
    {"SOUND", "OFF", 0},
    {"PET NAME", "NOG", 0},
    {"WIFI", "HOME-NET", 0},
};

constexpr int kXp = 860;
constexpr int kXpNext = 900;
constexpr int kLevel = 2;
constexpr const char* kRank = "NOODLER";
constexpr int kStreakDays = 6;
constexpr int kQueuedClips = 2;
constexpr int kNoteCount = 12;

}  // namespace demo
}  // namespace sb
