#include "menu.h"

namespace sb {

int menu_next(int cursor, int count) {
    if (count <= 0) return 0;
    return (cursor + 1) % count;
}

int menu_prev(int cursor, int count) {
    if (count <= 0) return 0;
    return (cursor - 1 + count) % count;
}

int list_window_start(int sel, int count, int visible) {
    if (count <= visible) return 0;
    const int start = sel - 1;
    if (start < 0) return 0;
    return start > count - visible ? count - visible : start;
}

}  // namespace sb
