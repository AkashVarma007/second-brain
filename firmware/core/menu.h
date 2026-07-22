#pragma once

namespace sb {
// Wrap-around cursor movement. Both return 0 when count <= 0.
int menu_next(int cursor, int count);
int menu_prev(int cursor, int count);
}
