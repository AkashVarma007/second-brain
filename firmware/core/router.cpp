#include "router.h"
#include "demo.h"
#include "menu.h"

namespace sb {

namespace {
// Wrap-safe "now has reached deadline": millis() wraps after ~49 days.
bool reached(uint32_t now, uint32_t deadline) { return int32_t(now - deadline) >= 0; }

int listCount(ScreenId s) {
    switch (s) {
        case ScreenId::Notes: return kNotesCount;
        case ScreenId::Quests: return kQuestsCount;
        case ScreenId::Setup: return kSetupCount;
        default: return 0;
    }
}
}  // namespace

void Router::open(ScreenId to) {
    s_.stack.push_back(s_.screen);
    s_.screen = to;
    s_.listSel = 0;
}

void Router::back() {
    if (s_.stack.empty()) return goHome();
    s_.screen = s_.stack.back();
    s_.stack.pop_back();
    s_.listSel = 0;
}

void Router::goHome() {
    s_.screen = ScreenId::Home;
    s_.stack.clear();
    s_.listSel = 0;
}

void Router::handle(Event e, uint32_t nowMs) {
    s_.nowMs = nowMs;
    s_.lastInputMs = nowMs;

    if (s_.screen == ScreenId::Sleep) return goHome();  // any key only wakes
    if (e == Event::TalkDown) return startRecording(nowMs);
    if (e == Event::TalkUp) return stopRecording(nowMs);

    switch (s_.screen) {
        case ScreenId::Recording:
        case ScreenId::Thinking:
            return;  // busy: only the TALK release matters
        case ScreenId::Home:
            switch (e) {
                case Event::Ok: return open(ScreenId::Menu);
                case Event::Up: return open(ScreenId::Pet);
                case Event::Down: return open(ScreenId::Notes);
                case Event::Left: return open(ScreenId::Quests);
                case Event::Right: return open(ScreenId::Recap);
                default: return;
            }
        case ScreenId::Menu:
            switch (e) {
                case Event::Up: s_.menuSel = menu_prev(s_.menuSel, kMenuCount); return;
                case Event::Down: s_.menuSel = menu_next(s_.menuSel, kMenuCount); return;
                case Event::Ok:
                case Event::Right: return open(kMenu[s_.menuSel]);
                case Event::Back:
                case Event::Left: return back();
                default: return;
            }
        case ScreenId::Result:
            if (e == Event::Ok) return goHome();
            if (e == Event::Back) {  // "undo": back to the Talk screen
                s_.screen = ScreenId::Talk;
                s_.stack = {ScreenId::Home, ScreenId::Menu};
            }
            return;
        default:
            break;
    }

    const int n = listCount(s_.screen);
    if (n > 0 && e == Event::Up) { s_.listSel = menu_prev(s_.listSel, n); return; }
    if (n > 0 && e == Event::Down) { s_.listSel = menu_next(s_.listSel, n); return; }
    if (s_.screen == ScreenId::Quests && e == Event::Ok) return toggleQuest(nowMs);
    if (s_.screen == ScreenId::Pet && e == Event::Ok) return open(ScreenId::Evo);
    if (e == Event::Back) back();
}

void Router::tick(uint32_t nowMs) {
    s_.nowMs = nowMs;
    if (s_.popup && reached(nowMs, s_.popupUntilMs)) s_.popup = nullptr;
    if (s_.screen == ScreenId::Recording && reached(nowMs, s_.recStartMs + kRecMaxMs)) stopRecording(nowMs);
    if (s_.screen == ScreenId::Thinking && reached(nowMs, s_.thinkUntilMs)) {
        s_.screen = ScreenId::Result;
        s_.resultIdx = s_.resultsShown % kResultCount;
        ++s_.resultsShown;
    }
    if (s_.screen == ScreenId::Home && reached(nowMs, s_.lastInputMs + kSleepAfterMs)) s_.screen = ScreenId::Sleep;
}

void Router::toggleQuest(uint32_t nowMs) {
    const uint8_t bit = uint8_t(1u << s_.listSel);
    if (s_.questsDone & bit) {
        s_.questsDone = uint8_t(s_.questsDone & ~bit);
        s_.popup = nullptr;
        return;
    }
    s_.questsDone = uint8_t(s_.questsDone | bit);
    s_.popup = demo::kPopupQuestDone;
    s_.popupUntilMs = nowMs + kPopupMs;
}

void Router::startRecording(uint32_t nowMs) {
    if (s_.screen == ScreenId::Recording || s_.screen == ScreenId::Thinking) return;
    s_.screen = ScreenId::Recording;  // replaces the current screen; the back stack is kept
    s_.recStartMs = nowMs;
}

void Router::stopRecording(uint32_t nowMs) {
    if (s_.screen != ScreenId::Recording) return;
    s_.screen = ScreenId::Thinking;
    s_.thinkUntilMs = nowMs + kThinkMs;
}

}  // namespace sb
