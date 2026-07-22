#include "ui.h"
#include <lvgl.h>
#include <string>

namespace {
using namespace sb;

lv_obj_t* title(const char* text) {
    lv_obj_t* t = lv_label_create(lv_scr_act());
    lv_label_set_text(t, text);
    lv_obj_align(t, LV_ALIGN_TOP_MID, 0, 8);
    return t;
}

// A simple vertical list; the row at `cursor` gets a highlighted style.
void list(const char* const* items, int count, int cursor) {
    lv_obj_t* cont = lv_obj_create(lv_scr_act());
    lv_obj_set_size(cont, 224, 240);
    lv_obj_align(cont, LV_ALIGN_TOP_MID, 0, 40);
    lv_obj_set_flex_flow(cont, LV_FLEX_FLOW_COLUMN);
    for (int i = 0; i < count; ++i) {
        lv_obj_t* row = lv_label_create(cont);
        lv_label_set_text(row, items[i]);
        if (i == cursor) {
            lv_obj_set_style_text_color(row, lv_color_hex(0x4ADE80), 0);  // green highlight
        }
    }
}

void body(const char* text) {
    lv_obj_t* b = lv_label_create(lv_scr_act());
    lv_label_set_long_mode(b, LV_LABEL_LONG_WRAP);
    lv_obj_set_width(b, 220);
    lv_label_set_text(b, text);
    lv_obj_align(b, LV_ALIGN_TOP_LEFT, 10, 44);
}
}  // namespace

namespace sb {
namespace ui {

void render(const UiState& s) {
    lv_obj_clean(lv_scr_act());
    switch (s.screen) {
        case Screen::Home: {
            title("Second Brain");
            const char* items[] = {"Notes", "Tasks"};
            list(items, 2, s.cursor);
            break;
        }
        case Screen::NotesMenu: {
            title("Notes");
            const char* items[] = {"Record"};
            list(items, 1, 0);
            break;
        }
        case Screen::NoteResult: {
            title("Note");
            body(s.pendingNote.c_str());
            break;
        }
        case Screen::NoteConfirm: {
            title("Save note?");
            const char* items[] = {"Save", "Discard"};
            list(items, 2, s.cursor);
            break;
        }
        case Screen::TasksMenu: {
            title("Tasks");
            const char* items[] = {"New task"};
            list(items, 1, 0);
            break;
        }
        case Screen::TaskResult: {
            title("Task");
            std::string t = std::string(s.pendingTask.title) + "\n[" +
                            priority_label(s.pendingTask.priority) + "]";
            body(t.c_str());
            break;
        }
        case Screen::TaskList: {
            title("Task list");
            lv_obj_t* cont = lv_obj_create(lv_scr_act());
            lv_obj_set_size(cont, 224, 240);
            lv_obj_align(cont, LV_ALIGN_TOP_MID, 0, 40);
            lv_obj_set_flex_flow(cont, LV_FLEX_FLOW_COLUMN);
            for (size_t i = 0; i < s.tasks.size(); ++i) {
                lv_obj_t* row = lv_label_create(cont);
                std::string line = "[" + std::string(priority_label(s.tasks[i].priority)) +
                                   "] " + s.tasks[i].title;
                lv_label_set_text(row, line.c_str());
                if ((int)i == s.cursor) lv_obj_set_style_text_color(row, lv_color_hex(0x4ADE80), 0);
            }
            if (s.tasks.empty()) body("(no tasks yet)");
            break;
        }
    }
}

}  // namespace ui
}  // namespace sb
