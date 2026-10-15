"""Turn the render tool's PBM frames into 4x amber PNGs plus one contact sheet.

Standard library only. Usage: python3 pbm2png.py <dir with *.pbm>
"""
import pathlib
import struct
import sys
import zlib

SCALE = 4
BG = (0xFF, 0x9A, 0x3D)    # amber backlight, as in the UI mock
INK = (0x1F, 0x10, 0x03)
GRID = (0xE8, 0x8A, 0x35)  # faint pixel grid, like a real LCD
GAP, COLS, PAD_BG = 16, 3, (0x0F, 0x0D, 0x14)


def read_pbm(path):
    tokens = path.read_text().split()
    if tokens[0] != "P1":
        raise ValueError(f"{path}: not a plain PBM")
    w, h = int(tokens[1]), int(tokens[2])
    bits = "".join(tokens[3:])
    if len(bits) != w * h:
        raise ValueError(f"{path}: expected {w * h} pixels, got {len(bits)}")
    return w, h, [[bits[y * w + x] == "1" for x in range(w)] for y in range(h)]


def scaled(w, h, px):
    rows = []
    for y in range(h * SCALE):
        row = []
        for x in range(w * SCALE):
            on = px[y // SCALE][x // SCALE]
            edge = (x % SCALE == SCALE - 1) or (y % SCALE == SCALE - 1)
            row.append(INK if on else (GRID if edge else BG))
        rows.append(row)
    return rows


def write_png(path, rows):
    h, w = len(rows), len(rows[0])
    raw = b"".join(b"\x00" + bytes(c for px in row for c in px) for row in rows)

    def chunk(tag, data):
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def main():
    folder = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".pio/renders")
    frames = sorted(folder.glob("*.pbm"))
    if not frames:
        sys.exit(f"no .pbm files in {folder}")
    images = []
    for f in frames:
        img = scaled(*read_pbm(f))
        write_png(f.with_suffix(".png"), img)
        images.append(img)
    fw, fh = len(images[0][0]), len(images[0])
    rows_n = (len(images) + COLS - 1) // COLS
    sw, sh = COLS * fw + (COLS + 1) * GAP, rows_n * fh + (rows_n + 1) * GAP
    sheet = [[PAD_BG] * sw for _ in range(sh)]
    for i, img in enumerate(images):
        ox = GAP + (i % COLS) * (fw + GAP)
        oy = GAP + (i // COLS) * (fh + GAP)
        for y, row in enumerate(img):
            sheet[oy + y][ox:ox + fw] = row
    write_png(folder / "sheet.png", sheet)
    print(f"{len(images)} PNGs + sheet.png in {folder}")


if __name__ == "__main__":
    main()
