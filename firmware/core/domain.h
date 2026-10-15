#pragma once
#include <cstdint>
#include <vector>

namespace sb {

// One input from the 5-way joystick, BACK or the hold-to-talk button.
// TALK is the only key that reports its release.
enum class Event { Up, Down, Left, Right, Ok, Back, TalkDown, TalkUp };

enum class ScreenId {
    Home,
    Menu,
    Talk,
    Recording,
    Thinking,
    Result,
    Notes,
    Quests,
    Pet,
    Evo,
    Recap,
    Sync,
    Setup,
    Sleep,
};

// The whole UI model the renderer draws. Owned and mutated only by Router.
struct UiState {
    ScreenId screen = ScreenId::Home;
    std::vector<ScreenId> stack;  // where BACK returns to; top = back()
    int menuSel = 0;
    int listSel = 0;              // selection on Notes / Quests / Setup
    uint8_t questsDone = 0;       // bit i set = demo quest i ticked
    int resultIdx = 0;            // demo result shown on the Result screen
    int resultsShown = 0;
    const char* popup = nullptr;  // overlay text, '\n' splits lines
    uint32_t popupUntilMs = 0;
    uint32_t recStartMs = 0;
    uint32_t thinkUntilMs = 0;
    uint32_t lastInputMs = 0;
    uint32_t nowMs = 0;           // last time seen; the renderer derives animation frames from it
};

inline const char* screen_name(ScreenId s) {
    switch (s) {
        case ScreenId::Home: return "Home";
        case ScreenId::Menu: return "Menu";
        case ScreenId::Talk: return "Talk";
        case ScreenId::Recording: return "Recording";
        case ScreenId::Thinking: return "Thinking";
        case ScreenId::Result: return "Result";
        case ScreenId::Notes: return "Notes";
        case ScreenId::Quests: return "Quests";
        case ScreenId::Pet: return "Pet";
        case ScreenId::Evo: return "Evo";
        case ScreenId::Recap: return "Recap";
        case ScreenId::Sync: return "Sync";
        case ScreenId::Setup: return "Setup";
        case ScreenId::Sleep: return "Sleep";
    }
    return "?";
}

}  // namespace sb
