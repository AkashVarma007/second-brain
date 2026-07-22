#include <unity.h>
#include "domain.h"

void test_priority_label_covers_all_values(void) {
    TEST_ASSERT_EQUAL_STRING("HIGH", sb::priority_label(sb::Priority::High));
    TEST_ASSERT_EQUAL_STRING("MEDIUM", sb::priority_label(sb::Priority::Medium));
    TEST_ASSERT_EQUAL_STRING("LOW", sb::priority_label(sb::Priority::Low));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_priority_label_covers_all_values);
    return UNITY_END();
}
