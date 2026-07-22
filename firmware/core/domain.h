#pragma once
#include <string>
#include <vector>

namespace sb {

enum class Priority { High, Medium, Low };

struct Task {
    std::string title;
    Priority priority = Priority::Medium;
};

enum class Screen {
    Home,
    NotesMenu,
    NoteResult,
    NoteConfirm,
    TasksMenu,
    TaskResult,
    TaskList,
};

enum class Event { Down, Select, Back };

// The full UI model the renderer draws. Owned and mutated only by Nav.
struct UiState {
    Screen screen = Screen::Home;
    int cursor = 0;                    // highlighted index on list/menu screens
    std::vector<std::string> notes;    // saved notes (newest last)
    std::vector<Task> tasks;           // saved tasks (newest last)
    std::string pendingNote;           // note text awaiting Save/Discard
    Task pendingTask;                  // task awaiting confirmation
};

inline const char* priority_label(Priority p) {
    switch (p) {
        case Priority::High: return "HIGH";
        case Priority::Medium: return "MEDIUM";
        case Priority::Low: return "LOW";
    }
    return "MEDIUM";
}

}  // namespace sb
