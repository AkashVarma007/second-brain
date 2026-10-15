#pragma once

namespace sb {
// Wrap-around cursor movement. Both return 0 when count <= 0.
int menu_next(int cursor, int count);
int menu_prev(int cursor, int count);
// First visible row of a scrolling list: keeps the selection second from the
// top until the end of the list pins the window. 0 when everything fits.
int list_window_start(int sel, int count, int visible);
}
