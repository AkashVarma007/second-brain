#!/usr/bin/env bash
# Render every NOG-OS screen on the laptop: .pio/renders/NN-<screen>.png + sheet.png.
# Needs the u8g2 library that `pio run -e esp32-s3` downloads, plus g++ and python3.
set -euo pipefail
cd "$(dirname "$0")/../.."  # firmware/

U8G2=.pio/libdeps/esp32-s3/U8g2/src
if [ ! -d "$U8G2/clib" ]; then
    echo "u8g2 not downloaded yet: run 'pio run -e esp32-s3' first" >&2
    exit 1
fi
OUT=.pio/renders
OBJ=.pio/render-obj
mkdir -p "$OUT" "$OBJ"
rm -f "$OUT"/*.pbm "$OUT"/*.png

# The u8g2 C core (incl. the large font table) builds once, then is reused.
LIB="$OBJ/libu8g2host.a"
if [ ! -f "$LIB" ]; then
    for c in "$U8G2"/clib/*.c; do
        gcc -O1 -w -c "$c" -I "$U8G2/clib" -o "$OBJ/$(basename "${c%.c}").o"
    done
    ar rcs "$LIB" "$OBJ"/*.o
fi

g++ -std=gnu++17 -O1 -Wall -Wextra -I core -I app/ui -I "$U8G2" \
    tools/render/render.cpp app/ui/*.cpp core/router.cpp core/menu.cpp \
    "$LIB" -o "$OBJ/render"

"$OBJ/render" "$OUT"
python3 tools/render/pbm2png.py "$OUT"
