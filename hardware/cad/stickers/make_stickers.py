# Sticker artwork for the case designs (hardware/cad/designs.py). Each sticker is a small HTML/SVG page
# screenshotted by headless Chrome on a transparent background, then cropped.
# Usage: python3 hardware/cad/stickers/make_stickers.py   (needs internet for Google Fonts)
import os, random, subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
os.makedirs(OUT, exist_ok=True)

NOG = [".......########.......", ".....##hh......##.....", "....#..ff.ff.ff..#....", "...#..f..f..f..f..#...",
       "..#.h..............#..", "..#................#..", ".#..................#.", ".#....e........e....#.",
       ".#...e.e......e.e...#.", ".#..cc..........cc..#.", ".#.......eeee.......#.", ".#........ee........#.",
       "..#................#..", "..#................#..", "...##............##...", ".....############.....",
       "......##......##......", "......##......##......"]


def nog_svg(px=18, body="#F2A65A", line="#1D1823"):
    rects = []
    for r, row in enumerate(NOG):
        ins = [i for i, ch in enumerate(row) if ch == "#"]
        lo, hi = (min(ins), max(ins)) if ins else (99, -1)
        for c, ch in enumerate(row):
            col = {"#": line, "e": line, "h": "#FFE3C2", "f": "#D9822B", "c": "#FF8FA3"}.get(ch)
            if col is None and lo < c < hi and r < 16:
                col = body
            if col:
                rects.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>' % (c * px, r * px, px, px, col))
    return '<svg width="%d" height="%d" shape-rendering="crispEdges">%s</svg>' % (len(NOG[0]) * px, len(NOG) * px, "".join(rects))


random.seed(7)
bars = "".join('<rect x="%d" y="0" width="%d" height="90" fill="#111"/>' % (x, w)
               for x, w in ((i * 9, random.choice((2, 3, 5))) for i in range(30)))
CUT = "filter:drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff);"
S = {
    "nog": '<div style="%s">%s</div>' % (CUT, nog_svg()),
    "talk": '<div style="%s"><svg width="420" height="250"><path d="M30 20h360a20 20 0 0 1 20 20v130a20 20 0 0 1-20 20H150l-60 50 10-50H30a20 20 0 0 1-20-20V40a20 20 0 0 1 20-20z" fill="#FF6B6B"/>'
            '<text x="210" y="125" text-anchor="middle" font-family="Bungee" font-size="54" fill="#fff">TALK TO ME</text></svg></div>' % CUT,
    "fragile": '<div style="%s;background:#FFD23F;border:6px solid #111;padding:14px 26px;font-family:Bungee;text-align:center;color:#111;width:380px">'
               '<div style="height:22px;background:repeating-linear-gradient(45deg,#111 0 16px,#FFD23F 16px 32px);margin:-6px -12px 10px"></div>'
               '<div style="font-size:64px;line-height:1">FRAGILE</div><div style="font-family:Silkscreen;font-size:26px;margin-top:6px">IDEAS INSIDE</div></div>' % CUT,
    "player1": '<div style="%s"><svg width="320" height="320"><circle cx="160" cy="160" r="150" fill="#6B4BCF"/><circle cx="160" cy="160" r="128" fill="none" stroke="#FFD23F" stroke-width="8" stroke-dasharray="14 12"/>'
               '<text x="160" y="150" text-anchor="middle" font-family="Silkscreen" font-weight="700" font-size="52" fill="#fff">PLAYER</text>'
               '<text x="160" y="222" text-anchor="middle" font-family="Bungee" font-size="88" fill="#FFD23F">1</text></svg></div>' % CUT,
    "bolt": '<div style="%s"><svg width="200" height="320"><polygon points="120,10 20,180 95,180 70,310 185,120 108,120 150,10" fill="#FFD23F" stroke="#111" stroke-width="10" stroke-linejoin="round"/></svg></div>' % CUT,
    "holo": '<div style="%s;border-radius:999px;padding:26px 44px;background:linear-gradient(110deg,#FF9AD5,#9AF7FF 40%%,#FFF59A 70%%,#C59BFF);font-family:Manrope;font-weight:800;font-size:60px;color:#1D1823;letter-spacing:-1px">second brain</div>' % CUT,
    "barcode": '<div style="%s;background:#fff;padding:14px 18px;border:3px solid #111"><svg width="270" height="90">%s</svg>'
               '<div style="font-family:Silkscreen;font-size:24px;color:#111;margin-top:6px">SB-1 · 2026 · 3.2&quot;</div></div>' % (CUT, bars),
    "smiley": '<div style="%s"><svg width="260" height="260"><circle cx="130" cy="130" r="122" fill="#FF8FC8" stroke="#111" stroke-width="8"/>'
              '<ellipse cx="90" cy="105" rx="14" ry="22" fill="#111"/><ellipse cx="170" cy="105" rx="14" ry="22" fill="#111"/>'
              '<path d="M70 160 q60 60 120 0" fill="none" stroke="#111" stroke-width="12" stroke-linecap="round"/></svg></div>' % CUT,
    "hundred": '<div style="%s"><svg width="300" height="300"><circle cx="150" cy="150" r="140" fill="#fff" stroke="#E0342F" stroke-width="10"/>'
               '<circle cx="150" cy="150" r="118" fill="none" stroke="#E0342F" stroke-width="4"/>'
               '<text x="150" y="150" text-anchor="middle" font-family="Bungee" font-size="72" fill="#E0342F">100%%</text>'
               '<text x="150" y="196" text-anchor="middle" font-family="Silkscreen" font-weight="700" font-size="26" fill="#E0342F">HUMAN</text>'
               '<text x="150" y="226" text-anchor="middle" font-family="Silkscreen" font-weight="700" font-size="26" fill="#E0342F">THOUGHTS</text></svg></div>' % CUT,
    "stripes": '<div style="width:440px;height:120px;background:linear-gradient(#FF6B6B 0 33%,#FFD23F 33% 66%,#2EC4B6 66%);transform:skewX(-20deg)"></div>',
    "cheek": '<div style="width:220px;height:130px;border-radius:50%;background:radial-gradient(#FF8FA3 30%,rgba(255,143,163,0) 70%)"></div>',
    "paw": '<div style="%s"><svg width="260" height="260" fill="#C9708A"><ellipse cx="130" cy="170" rx="70" ry="58"/><circle cx="55" cy="95" r="28"/>'
           '<circle cx="105" cy="55" r="28"/><circle cx="160" cy="55" r="28"/><circle cx="208" cy="95" r="28"/></svg></div>' % CUT,
    "press": '<div style="%s;background:#1D1823;color:#FFD23F;font-family:Silkscreen;font-weight:700;font-size:34px;padding:16px 24px;border-radius:10px">PRESS TALK ▸</div>' % CUT,
}
HEAD = ('<!doctype html><html><head><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bungee&family=Manrope:wght@800'
        '&family=Silkscreen:wght@400;700&display=swap"><style>html,body{margin:0;background:transparent}'
        'body{width:700px;height:600px;display:grid;place-items:center}</style></head><body>')
for name, body in S.items():
    page = os.path.join(OUT, name + ".html")
    open(page, "w").write(HEAD + body + "</body></html>")
    png = os.path.join(OUT, name + ".png")
    subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--hide-scrollbars", "--virtual-time-budget=8000",
                    "--default-background-color=00000000", "--force-device-scale-factor=1", "--window-size=700,700",
                    "--screenshot=" + png, "file://" + page], capture_output=True, timeout=120)
    im = Image.open(png).convert("RGBA")
    im.crop(im.getchannel("A").point(lambda v: 255 if v > 12 else 0).getbbox()).save(png)
    os.remove(page)
    print(name, Image.open(png).size)
