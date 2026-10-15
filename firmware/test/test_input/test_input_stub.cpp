#include <unity.h>
#include "input_stub.h"

using namespace sb;

void test_stub_returns_queued_events_in_order(void) {
    InputStub in;
    in.push(Event::Down);
    in.push(Event::Ok);

    Event e;
    TEST_ASSERT_TRUE(in.poll(e));
    TEST_ASSERT_EQUAL_INT((int)Event::Down, (int)e);
    TEST_ASSERT_TRUE(in.poll(e));
    TEST_ASSERT_EQUAL_INT((int)Event::Ok, (int)e);
    TEST_ASSERT_FALSE(in.poll(e));  // queue empty
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_stub_returns_queued_events_in_order);
    return UNITY_END();
}
