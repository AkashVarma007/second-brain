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

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_next_wraps_around);
    RUN_TEST(test_prev_wraps_around);
    RUN_TEST(test_empty_list_is_noop);
    return UNITY_END();
}
