#include <unity.h>
#include "menu.h"

void test_next_wraps_around(void) {
    TEST_ASSERT_EQUAL_INT(1, sb::menu_next(0, 3));
    TEST_ASSERT_EQUAL_INT(0, sb::menu_next(2, 3));  // wraps
}

void test_prev_wraps_around(void) {
    TEST_ASSERT_EQUAL_INT(2, sb::menu_prev(0, 3));  // wraps
    TEST_ASSERT_EQUAL_INT(0, sb::menu_prev(1, 3));
}

void test_empty_list_is_noop(void) {
    TEST_ASSERT_EQUAL_INT(0, sb::menu_next(0, 0));
    TEST_ASSERT_EQUAL_INT(0, sb::menu_prev(0, 0));
}

void test_window_keeps_selection_visible(void) {
    // 7 items, 4 visible rows: the selected row sits second from the top
    // until the list end pins the window.
    TEST_ASSERT_EQUAL_INT(0, sb::list_window_start(0, 7, 4));
    TEST_ASSERT_EQUAL_INT(0, sb::list_window_start(1, 7, 4));
    TEST_ASSERT_EQUAL_INT(1, sb::list_window_start(2, 7, 4));
    TEST_ASSERT_EQUAL_INT(3, sb::list_window_start(5, 7, 4));
    TEST_ASSERT_EQUAL_INT(3, sb::list_window_start(6, 7, 4));
}

void test_window_short_list_starts_at_zero(void) {
    TEST_ASSERT_EQUAL_INT(0, sb::list_window_start(2, 3, 4));
    TEST_ASSERT_EQUAL_INT(0, sb::list_window_start(0, 0, 4));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_next_wraps_around);
    RUN_TEST(test_prev_wraps_around);
    RUN_TEST(test_empty_list_is_noop);
    RUN_TEST(test_window_keeps_selection_visible);
    RUN_TEST(test_window_short_list_starts_at_zero);
    return UNITY_END();
}
