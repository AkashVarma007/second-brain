#include <unity.h>
#include "nav.h"

using namespace sb;

static Nav make() {
    return Nav("buy milk tomorrow", Task{"Buy milk", Priority::High});
}

void test_starts_on_home(void) {
    Nav n = make();
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);
}

void test_home_down_toggles_cursor(void) {
    Nav n = make();
    n.handle(Event::Down);
    TEST_ASSERT_EQUAL_INT(1, n.ui().cursor);
    n.handle(Event::Down);
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);  // wraps over 2 items
}

void test_notes_flow_saves_a_note(void) {
    Nav n = make();
    n.handle(Event::Select);   // Home(cursor 0=Notes) -> NotesMenu
    TEST_ASSERT_EQUAL_INT((int)Screen::NotesMenu, (int)n.ui().screen);
    n.handle(Event::Select);   // NotesMenu(Record) -> NoteResult, pendingNote set
    TEST_ASSERT_EQUAL_INT((int)Screen::NoteResult, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_STRING("buy milk tomorrow", n.ui().pendingNote.c_str());
    n.handle(Event::Select);   // NoteResult -> NoteConfirm
    TEST_ASSERT_EQUAL_INT((int)Screen::NoteConfirm, (int)n.ui().screen);
    n.handle(Event::Select);   // Confirm(cursor 0=Save) -> saves, back to Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(1, (int)n.ui().notes.size());
    TEST_ASSERT_EQUAL_STRING("buy milk tomorrow", n.ui().notes[0].c_str());
}

void test_note_discard_does_not_save(void) {
    Nav n = make();
    n.handle(Event::Select);   // NotesMenu
    n.handle(Event::Select);   // NoteResult
    n.handle(Event::Select);   // NoteConfirm
    n.handle(Event::Down);     // cursor -> 1 = Discard
    n.handle(Event::Select);   // discard -> Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(0, (int)n.ui().notes.size());
}

void test_back_from_notes_menu_returns_home(void) {
    Nav n = make();
    n.handle(Event::Select);   // NotesMenu
    n.handle(Event::Back);     // -> Home
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
}

void test_tasks_flow_saves_a_task_and_shows_list(void) {
    Nav n = make();
    n.handle(Event::Down);     // cursor -> 1 = Tasks
    n.handle(Event::Select);   // -> TasksMenu
    TEST_ASSERT_EQUAL_INT((int)Screen::TasksMenu, (int)n.ui().screen);
    n.handle(Event::Select);   // New task -> TaskResult, pendingTask set
    TEST_ASSERT_EQUAL_INT((int)Screen::TaskResult, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_STRING("Buy milk", n.ui().pendingTask.title.c_str());
    TEST_ASSERT_EQUAL_INT((int)Priority::High, (int)n.ui().pendingTask.priority);
    n.handle(Event::Select);   // -> saves, TaskList
    TEST_ASSERT_EQUAL_INT((int)Screen::TaskList, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(1, (int)n.ui().tasks.size());
    TEST_ASSERT_EQUAL_STRING("Buy milk", n.ui().tasks[0].title.c_str());
}

void test_back_from_home_stays_home(void) {
    Nav n = make();
    n.handle(Event::Back);
    TEST_ASSERT_EQUAL_INT((int)Screen::Home, (int)n.ui().screen);
}

void test_tasklist_down_scrolls_and_wraps(void) {
    Nav n = make();
    // Save two tasks so TaskList has more than one row.
    for (int i = 0; i < 2; ++i) {
        n.handle(Event::Down);     // Home cursor -> Tasks
        n.handle(Event::Select);   // TasksMenu
        n.handle(Event::Select);   // TaskResult
        n.handle(Event::Select);   // save -> TaskList
        if (i == 0) n.handle(Event::Back);  // back to Home to add the next
    }
    TEST_ASSERT_EQUAL_INT((int)Screen::TaskList, (int)n.ui().screen);
    TEST_ASSERT_EQUAL_INT(2, (int)n.ui().tasks.size());
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);
    n.handle(Event::Down);         // 0 -> 1
    TEST_ASSERT_EQUAL_INT(1, n.ui().cursor);
    n.handle(Event::Down);         // 1 -> 0 (wraps over 2 tasks)
    TEST_ASSERT_EQUAL_INT(0, n.ui().cursor);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_starts_on_home);
    RUN_TEST(test_home_down_toggles_cursor);
    RUN_TEST(test_notes_flow_saves_a_note);
    RUN_TEST(test_note_discard_does_not_save);
    RUN_TEST(test_back_from_notes_menu_returns_home);
    RUN_TEST(test_tasks_flow_saves_a_task_and_shows_list);
    RUN_TEST(test_back_from_home_stays_home);
    RUN_TEST(test_tasklist_down_scrolls_and_wraps);
    return UNITY_END();
}
