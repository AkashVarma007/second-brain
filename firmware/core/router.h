#pragma once
#include <cstdint>
#include "domain.h"

namespace sb {

constexpr uint32_t kFrameMs = 400;       // animation step
constexpr uint32_t kThinkMs = 2200;      // Thinking -> Result
constexpr uint32_t kPopupMs = 1400;
constexpr uint32_t kSleepAfterMs = 20000;  // idle on Home
constexpr uint32_t kRecMaxMs = 30000;      // recording cap

constexpr int kMenuCount = 7;
constexpr int kNotesCount = 3;
constexpr int kQuestsCount = 5;
constexpr int kSetupCount = 4;
constexpr int kResultCount = 3;

// Menu order; demo::kMenuLabels draws the same order.
constexpr ScreenId kMenu[kMenuCount] = {
    ScreenId::Talk, ScreenId::Notes, ScreenId::Quests, ScreenId::Pet,
    ScreenId::Recap, ScreenId::Sync, ScreenId::Setup,
};

// UI navigation only: which screen shows, list selections, the hold-to-talk
// flow and pop-up timers. Time is always passed in, never read, so the host
// tests drive it directly.
class Router {
public:
    void handle(Event e, uint32_t nowMs);
    void tick(uint32_t nowMs);
    const UiState& ui() const { return s_; }

private:
    UiState s_;
    void open(ScreenId to);
    void back();
    void goHome();
    void toggleQuest(uint32_t nowMs);
    void startRecording(uint32_t nowMs);
    void stopRecording(uint32_t nowMs);
};

}  // namespace sb
