#include "nav.h"
#include "menu.h"

namespace sb {

Nav::Nav(std::string sampleNote, Task sampleTask)
    : sampleNote_(std::move(sampleNote)), sampleTask_(std::move(sampleTask)) {}

void Nav::goTo(Screen s, int cursor) {
    state_.screen = s;
    state_.cursor = cursor;
}

void Nav::handle(Event e) {
    switch (state_.screen) {
        case Screen::Home:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, 2);
            else if (e == Event::Select) goTo(state_.cursor == 0 ? Screen::NotesMenu : Screen::TasksMenu);
            // Back on Home: stay.
            break;

        case Screen::NotesMenu:
            if (e == Event::Select) { state_.pendingNote = sampleNote_; goTo(Screen::NoteResult); }
            else if (e == Event::Back) goTo(Screen::Home);
            break;

        case Screen::NoteResult:
            if (e == Event::Select) goTo(Screen::NoteConfirm);       // cursor 0 = Save
            else if (e == Event::Back) goTo(Screen::NotesMenu);
            break;

        case Screen::NoteConfirm:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, 2);
            else if (e == Event::Back) goTo(Screen::NoteResult);
            else if (e == Event::Select) {
                if (state_.cursor == 0) state_.notes.push_back(state_.pendingNote);  // Save
                state_.pendingNote.clear();
                goTo(Screen::Home);
            }
            break;

        case Screen::TasksMenu:
            if (e == Event::Select) { state_.pendingTask = sampleTask_; goTo(Screen::TaskResult); }
            else if (e == Event::Back) goTo(Screen::Home);
            break;

        case Screen::TaskResult:
            if (e == Event::Select) { state_.tasks.push_back(state_.pendingTask); goTo(Screen::TaskList); }
            else if (e == Event::Back) goTo(Screen::TasksMenu);
            break;

        case Screen::TaskList:
            if (e == Event::Down) state_.cursor = menu_next(state_.cursor, (int)state_.tasks.size());
            else if (e == Event::Back) goTo(Screen::Home);
            break;
    }
}

}  // namespace sb
