#include <unity.h>
#include <string>
#include "router.h"

using namespace sb;

static void press(Router& r, Event e, uint32_t t) { r.handle(e, t); }

static int scr(const Router& r) { return (int)r.ui().screen; }
#define ASSERT_SCREEN(expected, r) TEST_ASSERT_EQUAL_INT((int)(expected), scr(r))

void test_starts_on_home(void) {
    Router r;
    ASSERT_SCREEN(ScreenId::Home, r);
    TEST_ASSERT_TRUE(r.ui().stack.empty());
}

void test_ok_opens_menu_and_back_returns_home(void) {
    Router r;
    press(r, Event::Ok, 10);
    ASSERT_SCREEN(ScreenId::Menu, r);
    press(r, Event::Back, 20);
    ASSERT_SCREEN(ScreenId::Home, r);
    TEST_ASSERT_TRUE(r.ui().stack.empty());
}

void test_home_shortcuts(void) {
    const Event keys[] = {Event::Up, Event::Down, Event::Left, Event::Right};
    const ScreenId want[] = {ScreenId::Pet, ScreenId::Notes, ScreenId::Quests, ScreenId::Recap};
    for (int i = 0; i < 4; ++i) {
        Router r;
        press(r, keys[i], 10);
        ASSERT_SCREEN(want[i], r);
        press(r, Event::Back, 20);
        ASSERT_SCREEN(ScreenId::Home, r);
    }
}

void test_menu_wraps_both_ways(void) {
    Router r;
    press(r, Event::Ok, 10);
    press(r, Event::Up, 20);
    TEST_ASSERT_EQUAL_INT(kMenuCount - 1, r.ui().menuSel);
    press(r, Event::Down, 30);
    TEST_ASSERT_EQUAL_INT(0, r.ui().menuSel);
}

void test_menu_ok_opens_selected_app(void) {
    for (int i = 0; i < kMenuCount; ++i) {
        Router r;
        press(r, Event::Ok, 10);
        for (int k = 0; k < i; ++k) press(r, Event::Down, 20);
        press(r, Event::Ok, 30);
        ASSERT_SCREEN(kMenu[i], r);
    }
}

void test_nested_back_chain(void) {
    Router r;
    press(r, Event::Ok, 10);                       // Menu
    for (int k = 0; k < 3; ++k) press(r, Event::Down, 20);
    press(r, Event::Ok, 30);                       // Pet (menu index 3)
    ASSERT_SCREEN(ScreenId::Pet, r);
    press(r, Event::Ok, 40);                       // Evolution
    ASSERT_SCREEN(ScreenId::Evo, r);
    press(r, Event::Back, 50);
    ASSERT_SCREEN(ScreenId::Pet, r);
    press(r, Event::Back, 60);
    ASSERT_SCREEN(ScreenId::Menu, r);
    press(r, Event::Back, 70);
    ASSERT_SCREEN(ScreenId::Home, r);
}

void test_back_on_home_stays_home(void) {
    Router r;
    press(r, Event::Back, 10);
    press(r, Event::Back, 20);
    ASSERT_SCREEN(ScreenId::Home, r);
    TEST_ASSERT_TRUE(r.ui().stack.empty());
}

void test_list_selection_wraps(void) {
    Router r;
    press(r, Event::Left, 10);                     // Quests (5 items)
    press(r, Event::Up, 20);
    TEST_ASSERT_EQUAL_INT(kQuestsCount - 1, r.ui().listSel);
    press(r, Event::Down, 30);
    TEST_ASSERT_EQUAL_INT(0, r.ui().listSel);
}

void test_opening_a_list_resets_selection(void) {
    Router r;
    press(r, Event::Left, 10);
    press(r, Event::Down, 20);
    press(r, Event::Back, 30);
    press(r, Event::Down, 40);                     // Notes
    TEST_ASSERT_EQUAL_INT(0, r.ui().listSel);
}

void test_quest_ok_toggles_and_shows_popup(void) {
    Router r;
    press(r, Event::Left, 10);
    press(r, Event::Down, 20);                     // quest 1
    press(r, Event::Ok, 100);
    TEST_ASSERT_EQUAL_UINT8(0x02, r.ui().questsDone);
    TEST_ASSERT_NOT_NULL(r.ui().popup);
    r.tick(100 + kPopupMs - 1);
    TEST_ASSERT_NOT_NULL(r.ui().popup);
    r.tick(100 + kPopupMs);
    TEST_ASSERT_NULL(r.ui().popup);
    press(r, Event::Ok, 3000);                     // untick: no pop-up
    TEST_ASSERT_EQUAL_UINT8(0x00, r.ui().questsDone);
    TEST_ASSERT_NULL(r.ui().popup);
}

void test_talk_flow_reaches_result(void) {
    Router r;
    press(r, Event::TalkDown, 1000);
    ASSERT_SCREEN(ScreenId::Recording, r);
    TEST_ASSERT_EQUAL_UINT32(1000, r.ui().recStartMs);
    press(r, Event::TalkUp, 4000);
    ASSERT_SCREEN(ScreenId::Thinking, r);
    r.tick(4000 + kThinkMs - 1);
    ASSERT_SCREEN(ScreenId::Thinking, r);
    r.tick(4000 + kThinkMs);
    ASSERT_SCREEN(ScreenId::Result, r);
    TEST_ASSERT_EQUAL_INT(0, r.ui().resultIdx);
}

void test_result_index_cycles(void) {
    Router r;
    uint32_t t = 1000;
    for (int i = 0; i < kResultCount + 1; ++i) {
        press(r, Event::TalkDown, t);
        press(r, Event::TalkUp, t + 500);
        r.tick(t + 500 + kThinkMs);
        TEST_ASSERT_EQUAL_INT(i % kResultCount, r.ui().resultIdx);
        press(r, Event::Ok, t + 5000);
        t += 10000;
    }
}

void test_result_ok_goes_home_and_back_goes_to_talk(void) {
    Router r;
    press(r, Event::Ok, 10);                       // Menu, stack [Home]
    press(r, Event::TalkDown, 100);
    press(r, Event::TalkUp, 200);
    r.tick(200 + kThinkMs);
    ASSERT_SCREEN(ScreenId::Result, r);
    press(r, Event::Back, 5000);
    ASSERT_SCREEN(ScreenId::Talk, r);
    TEST_ASSERT_EQUAL_INT(2, (int)r.ui().stack.size());
    press(r, Event::Back, 5100);
    ASSERT_SCREEN(ScreenId::Menu, r);

    Router r2;
    press(r2, Event::TalkDown, 100);
    press(r2, Event::TalkUp, 200);
    r2.tick(200 + kThinkMs);
    press(r2, Event::Ok, 5000);
    ASSERT_SCREEN(ScreenId::Home, r2);
    TEST_ASSERT_TRUE(r2.ui().stack.empty());
}

void test_stray_talk_release_is_ignored(void) {
    Router r;
    press(r, Event::Ok, 10);
    press(r, Event::TalkUp, 20);
    ASSERT_SCREEN(ScreenId::Menu, r);
}

void test_talk_press_while_thinking_is_ignored(void) {
    Router r;
    press(r, Event::TalkDown, 100);
    press(r, Event::TalkUp, 200);
    press(r, Event::TalkDown, 300);
    ASSERT_SCREEN(ScreenId::Thinking, r);
    press(r, Event::Back, 400);                    // busy: navigation ignored too
    ASSERT_SCREEN(ScreenId::Thinking, r);
}

void test_recording_auto_stops_at_cap(void) {
    Router r;
    press(r, Event::TalkDown, 1000);
    r.tick(1000 + kRecMaxMs - 1);
    ASSERT_SCREEN(ScreenId::Recording, r);
    r.tick(1000 + kRecMaxMs);
    ASSERT_SCREEN(ScreenId::Thinking, r);
}

void test_home_idle_sleeps_and_any_key_wakes(void) {
    Router r;
    r.tick(kSleepAfterMs - 1);
    ASSERT_SCREEN(ScreenId::Home, r);
    r.tick(kSleepAfterMs);
    ASSERT_SCREEN(ScreenId::Sleep, r);
    press(r, Event::Down, kSleepAfterMs + 10);     // wakes only, no shortcut
    ASSERT_SCREEN(ScreenId::Home, r);
}

void test_talk_wakes_without_recording(void) {
    Router r;
    r.tick(kSleepAfterMs);
    press(r, Event::TalkDown, kSleepAfterMs + 10);
    ASSERT_SCREEN(ScreenId::Home, r);
    press(r, Event::TalkUp, kSleepAfterMs + 20);
    ASSERT_SCREEN(ScreenId::Home, r);
}

void test_idle_off_home_does_not_sleep(void) {
    Router r;
    press(r, Event::Ok, 10);
    r.tick(10 + kSleepAfterMs * 2);
    ASSERT_SCREEN(ScreenId::Menu, r);
}

void test_deadline_across_millis_wrap(void) {
    Router r;
    const uint32_t start = 0xFFFFFF00u;            // 256 ms before wrap
    press(r, Event::TalkDown, start - 100);
    press(r, Event::TalkUp, start);                // deadline wraps past 0
    r.tick(start + 100);                           // now has NOT wrapped yet: too early
    ASSERT_SCREEN(ScreenId::Thinking, r);
    r.tick(start + kThinkMs - 1);                  // wrapped, still early
    ASSERT_SCREEN(ScreenId::Thinking, r);
    r.tick(start + kThinkMs);
    ASSERT_SCREEN(ScreenId::Result, r);
}

void test_screen_names_are_unique(void) {
    for (int a = 0; a <= (int)ScreenId::Sleep; ++a)
        for (int b = a + 1; b <= (int)ScreenId::Sleep; ++b)
            TEST_ASSERT_TRUE(std::string(screen_name((ScreenId)a)) != screen_name((ScreenId)b));
}

// Replays screens_scenario.yaml's button sequence and checks the screen trace
// its README documents, so the Wokwi run's expectations are proven on the host.
void test_wokwi_scenario_trace(void) {
    Router r;
    std::string trace = screen_name(r.ui().screen);
    uint32_t t = 600;
    auto note = [&]() {
        const char* n = screen_name(r.ui().screen);
        if (trace.rfind(n) != trace.size() - std::string(n).size()) trace += std::string(" ") + n;
    };
    auto step = [&](uint32_t ms) {
        for (uint32_t end = t + ms; t < end; t += 50) { r.tick(t); note(); }
    };
    auto press = [&](Event e, uint32_t after = 400) {
        r.handle(e, t); note();
        step(150 + after);
    };
    press(Event::Ok); press(Event::Down);                       // Menu
    press(Event::Up); press(Event::Ok);                         // Talk
    r.handle(Event::TalkDown, t); note(); step(2500);           // Recording
    r.handle(Event::TalkUp, t); note(); step(600 + 2400);       // Thinking -> Result
    press(Event::Ok); press(Event::Down); press(Event::Back);   // Home, Notes, Home
    press(Event::Left); press(Event::Ok, 1800); press(Event::Down);
    press(Event::Ok, 300); step(1500); press(Event::Back);      // Quests, Home
    press(Event::Up); press(Event::Ok); press(Event::Back); press(Event::Back);
    press(Event::Right); press(Event::Back);
    press(Event::Ok);
    for (int i = 0; i < 5; ++i) press(Event::Down, 250);
    press(Event::Ok); press(Event::Back); press(Event::Down); press(Event::Ok);
    press(Event::Back); press(Event::Back);
    step(21000);
    TEST_ASSERT_EQUAL_STRING(
        "Home Menu Talk Recording Thinking Result Home Notes Home Quests Home Pet Evo Pet Home "
        "Recap Home Menu Sync Menu Setup Menu Home Sleep",
        trace.c_str());
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_starts_on_home);
    RUN_TEST(test_ok_opens_menu_and_back_returns_home);
    RUN_TEST(test_home_shortcuts);
    RUN_TEST(test_menu_wraps_both_ways);
    RUN_TEST(test_menu_ok_opens_selected_app);
    RUN_TEST(test_nested_back_chain);
    RUN_TEST(test_back_on_home_stays_home);
    RUN_TEST(test_list_selection_wraps);
    RUN_TEST(test_opening_a_list_resets_selection);
    RUN_TEST(test_quest_ok_toggles_and_shows_popup);
    RUN_TEST(test_talk_flow_reaches_result);
    RUN_TEST(test_result_index_cycles);
    RUN_TEST(test_result_ok_goes_home_and_back_goes_to_talk);
    RUN_TEST(test_stray_talk_release_is_ignored);
    RUN_TEST(test_talk_press_while_thinking_is_ignored);
    RUN_TEST(test_recording_auto_stops_at_cap);
    RUN_TEST(test_home_idle_sleeps_and_any_key_wakes);
    RUN_TEST(test_talk_wakes_without_recording);
    RUN_TEST(test_idle_off_home_does_not_sleep);
    RUN_TEST(test_deadline_across_millis_wrap);
    RUN_TEST(test_screen_names_are_unique);
    RUN_TEST(test_wokwi_scenario_trace);
    return UNITY_END();
}
