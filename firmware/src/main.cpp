#include <Arduino.h>
#include <lvgl.h>
#include "config.h"
#include "display_tft.h"
#include "buttons.h"
#include "nav.h"
#include "ui.h"

using namespace sb;

static Buttons buttons;
static Nav nav(SAMPLE_NOTE, Task{SAMPLE_TASK_TITLE, SAMPLE_TASK_PRIORITY});

static const char* screen_name(Screen s) {
    switch (s) {
        case Screen::Home: return "Home";
        case Screen::NotesMenu: return "NotesMenu";
        case Screen::NoteResult: return "NoteResult";
        case Screen::NoteConfirm: return "NoteConfirm";
        case Screen::TasksMenu: return "TasksMenu";
        case Screen::TaskResult: return "TaskResult";
        case Screen::TaskList: return "TaskList";
    }
    return "?";
}

void setup() {
    Serial.begin(115200);
    delay(100);
    Serial.println("Second Brain UI booting");
    sb::display::begin();
    buttons.begin();
    ui::render(nav.ui());
    Serial.printf("screen=%s cursor=%d\n", screen_name(nav.ui().screen), nav.ui().cursor);
}

void loop() {
    Event e;
    if (buttons.poll(e)) {
        nav.handle(e);
        ui::render(nav.ui());
        Serial.printf("event=%d -> screen=%s cursor=%d notes=%d tasks=%d\n",
                      (int)e, screen_name(nav.ui().screen), nav.ui().cursor,
                      (int)nav.ui().notes.size(), (int)nav.ui().tasks.size());
    }
    lv_timer_handler();
    delay(5);
}
