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

}  // namespace sb
