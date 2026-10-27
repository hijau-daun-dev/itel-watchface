"""Watch face gaming: hud_fps, rpg_status (statis), blok_anim, alien_anim (beranimasi).

Nama yang berakhiran _anim = punya elemen animasi (bg_dynamic).
"""
import math
import random

from PIL import Image, ImageDraw

from koleksi_anim import PIX, pix_text
from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, text_rgba, ttf, word_set

MONO_B = "C:/Windows/Fonts/consolab.ttf"

# Huruf tambahan untuk font pixel 5x7.
PIX.update({
    "F": "11111 10000 10000 11110 10000 10000 10000", "G": "01110 10001 10000 10111 10001 10001 01111",
    "T": "11111 00100 00100 00100 00100 00100 00100", "V": "10001 10001 10001 10001 10001 01010 00100",
    "X": "10001 10001 01010 00100 01010 10001 10001", "W": "10001 10001 10001 10101 10101 10101 01010",
    "D": "11110 10001 10001 10001 10001 10001 11110", "N": "10001 11001 10101 10011 10001 10001 10001",
    "M": "10001 11011 10101 10101 10001 10001 10001", "B": "11110 10001 10001 11110 10001 10001 11110",
    "K": "10001 10010 10100 11000 10100 10010 10001", "J": "00111 00010 00010 00010 00010 10010 01100",
    ">": "10000 01000 00100 00010 00100 01000 10000", "/": "00001 00010 00010 00100 01000 01000 10000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
})
WD_PIX = ("MIN", "SEN", "SEL", "RAB", "KAM", "JUM", "SAB")


def pix_digits(scale, col, bg, gap=None):
    """Digit pixel dengan jarak antar-digit (supaya elemen angka tidak dempet)."""
    gap = scale if gap is None else gap
    out = []
    for c in "0123456789":
        g = pix_text(c, scale, col, bg)
        im = Image.new("RGB", (g.width + gap, g.height), bg)
        im.paste(g, (0, 0))
        out.append(im)
    return out


def paste_pix(bg, s, scale, col, xy, center=False):
    im = pix_text(s, scale, col, (0, 0, 0) if bg.getpixel((0, 0)) == (0, 0, 0) else bg.getpixel(xy))
    x, y = xy
    if center:
        x -= im.width // 2
    bg.paste(im, (x, y))
    return im


# ---------------------------------------------------------------- HUD FPS (statis)
def hud_fps():
    BG, WHITE, GREEN, RED, YEL, GRAY, CYAN = (0, 0, 0), (240, 240, 240), (90, 255, 120), (255, 70, 70), (255, 210, 60), (110, 116, 124), (0, 220, 255)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("hud_fps", "HUD FPS", bg)
    fl = bahn(15, "SemiBold Condensed")
    # Match timer di atas.
    t = text_rgba("MATCH TIME", fl, GRAY)
    bg.paste(t, (CX - t.width // 2, 54), t)
    big = bahn(70, "Bold Condensed")
    bd = glyph_set("0123456789", big, WHITE, BG)
    bw, bh = bd[0].width, bd[0].height
    sd = glyph_set("0123456789", bahn(26, "Bold Condensed"), YEL, BG)
    colon = 16
    tx = CX - (4 * bw + colon + 2 * sd[0].width + 6) // 2
    ty = 76
    D.add("hour", bd, tx, ty)
    for yy in (ty + bh * .3, ty + bh * .7):
        d.rectangle((tx + 2 * bw + 4, yy - 4, tx + 2 * bw + 11, yy + 3), fill=WHITE)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    D.add("sec", sd, tx + 4 * bw + colon + 6, ty + bh - sd[0].height)
    f = bahn(18, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, CYAN, BG)
    D.add("weekday", wd, CX - wd[0].width - 4, ty + bh + 8)
    D.add("day", glyph_set("0123456789", f, WHITE, BG), CX + 4, ty + bh + 8 + wd[0].height - glyph_set("0", f, WHITE, BG)[0].height)

    # Crosshair di tengah.
    cy = 252
    for (x1, y1, x2, y2) in ((CX - 30, cy, CX - 10, cy), (CX + 10, cy, CX + 30, cy), (CX, cy - 30, CX, cy - 10), (CX, cy + 10, CX, cy + 30)):
        d.line((x1, y1, x2, y2), fill=GREEN, width=3)
    d.ellipse((CX - 2, cy - 2, CX + 2, cy + 2), fill=GREEN)
    # Minimap radar (kiri) dan kill feed (kanan) - dekorasi.
    mx, my, mr = 96, 252, 34
    d.ellipse((mx - mr, my - mr, mx + mr, my + mr), outline=(40, 90, 50), width=2)
    d.line((mx - mr, my, mx + mr, my), fill=(30, 60, 36)); d.line((mx, my - mr, mx, my + mr), fill=(30, 60, 36))
    d.polygon([(mx, my - 7), (mx - 5, my + 5), (mx + 5, my + 5)], fill=WHITE)
    for (dx, dy) in ((14, -12), (-18, 10), (8, 20)):
        d.ellipse((mx + dx - 3, my + dy - 3, mx + dx + 3, my + dy + 3), fill=RED)
    for k, (s, col) in enumerate((("+100 XP", YEL), ("HEADSHOT", RED))):
        tt = text_rgba(s, fl, col)
        bg.paste(tt, (330, 230 + k * 22), tt)

    # HP = baterai (bawah kiri), XP = langkah (bawah kanan).
    d.text((92, 318), "HP", font=bahn(20, "Bold Condensed"), fill=WHITE)
    bars = []
    for lv in range(6):
        im = Image.new("RGB", (126, 16), BG)
        dr = ImageDraw.Draw(im)
        dr.polygon([(6, 0), (125, 0), (119, 15), (0, 15)], outline=GRAY)
        if lv:
            col = RED if lv <= 1 else YEL if lv <= 2 else GREEN
            w = int(119 * lv / 5)
            dr.polygon([(7, 2), (6 + w, 2), (1 + w, 13), (2, 13)], fill=col)
        bars.append(im)
    D.add("battery_level", bars, 92, 344)
    d.text((290, 318), "XP", font=bahn(20, "Bold Condensed"), fill=WHITE)
    D.add("step", glyph_set("0123456789", bahn(34, "Bold Condensed"), YEL, BG), 374, 338, gravity=0x0c)
    return D


# ---------------------------------------------------------------- RPG status window (statis)
def rpg_status():
    BG, WIN_T, WIN_B, BORDER, WHITE, YEL, RED, GREEN, GRAY = (
        (0, 0, 0), (24, 40, 150), (6, 12, 70), (230, 230, 240), (245, 245, 245), (255, 220, 70), (255, 80, 80), (90, 230, 110), (150, 160, 200))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("rpg_status", "RPG Status", bg)
    # Jam pixel besar di atas jendela.
    dig = pix_digits(9, YEL, BG)
    dw, dh = dig[0].width, dig[0].height
    colon_w = 3 * 9
    total = 4 * dw + colon_w
    tx, ty = CX - total // 2, 70
    D.add("hour", dig, tx, ty)
    for yy in (ty + 2 * 9, ty + 5 * 9):
        d.rectangle((tx + 2 * dw + 2, yy - 4, tx + 2 * dw + 13, yy + 7), fill=YEL)
    D.add("min", dig, tx + 2 * dw + colon_w, ty)
    sec = pix_digits(3, WHITE, BG)
    D.add("sec", sec, tx + 4 * dw + colon_w - 4, ty + dh - sec[0].height)

    # Jendela status (gradien biru + bingkai putih ganda).
    X0, Y0, X1, Y1 = 66, 150, 400, 360
    win = Image.new("RGB", (X1 - X0, Y1 - Y0))
    for y in range(win.height):
        t = y / win.height
        ImageDraw.Draw(win).line((0, y, win.width, y), fill=tuple(int(WIN_T[i] + (WIN_B[i] - WIN_T[i]) * t) for i in range(3)))
    bg.paste(win, (X0, Y0))
    d.rounded_rectangle((X0, Y0, X1, Y1), radius=10, outline=BORDER, width=4)
    d.rounded_rectangle((X0 + 6, Y0 + 6, X1 - 6, Y1 - 6), radius=6, outline=(120, 130, 200), width=1)

    S = 3
    LX = X0 + 22

    def label(s, y, col=WHITE):
        im = pix_text(s, S, col, WIN_T)
        # Latar label mengikuti gradien: tempel ulang dengan mask piksel saja.
        m = im.convert("L").point(lambda p: 255 if p > 60 else 0)
        bg.paste(Image.new("RGB", im.size, col), (LX if isinstance(y, int) else y[0], y if isinstance(y, int) else y[1]), m)

    # Baris dengan elemen dinamis harus di area warna polos: pakai kotak isi gelap per baris.
    def slot(x, y, w, h):
        d.rectangle((x, y, x + w, y + h), fill=WIN_B)

    # Nama + level (LV = tanggal) + hari.
    label("HERO", Y0 + 22)
    slot(X0 + 150, Y0 + 18, 170, 30)
    lv = pix_text("LV", S, GRAY, WIN_B); bg.paste(lv, (X0 + 156, Y0 + 22))
    D.add("day", pix_digits(S, YEL, WIN_B), X0 + 156 + lv.width + 8, Y0 + 22)
    D.add("weekday", [pix_text(s, S, WHITE, WIN_B) for s in WD_PIX], X0 + 252, Y0 + 22)
    # HP = baterai.
    label("HP", Y0 + 66)
    slot(X0 + 70, Y0 + 60, 250, 30)
    bars = []
    for lvl in range(6):
        im = Image.new("RGB", (230, 18), WIN_B)
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 0, 229, 17), outline=BORDER, width=2)
        if lvl:
            col = RED if lvl <= 1 else YEL if lvl <= 2 else GREEN
            dr.rectangle((3, 3, 3 + int(223 * lvl / 5), 14), fill=col)
        bars.append(im)
    D.add("battery_level", bars, X0 + 78, Y0 + 66)
    # EXP = langkah.
    label("EXP", Y0 + 108)
    slot(X0 + 110, Y0 + 102, 210, 30)
    D.add("step", pix_digits(S, WHITE, WIN_B), X0 + 116, Y0 + 108)
    # Hati = detak jantung.
    heart = ["01010", "11111", "11111", "01110", "00100"]
    for r, row in enumerate(heart):
        for c, b in enumerate(row):
            if b == "1":
                d.rectangle((LX + c * 4, Y0 + 152 + r * 4, LX + c * 4 + 3, Y0 + 152 + r * 4 + 3), fill=RED)
    slot(X0 + 60, Y0 + 144, 100, 30)
    D.add("heart", pix_digits(S, WHITE, WIN_B), X0 + 66, Y0 + 150)
    # Menu.
    label(">FIGHT", (X0 + 180, Y0 + 150), YEL)
    label("ITEM", (X0 + 196, Y0 + 176))
    return D


# ---------------------------------------------------------------- Blok (puzzle balok jatuh) - animasi
def blok_anim():
    BG, WALL, GRAY, WHITE, YEL = (0, 0, 0), (90, 96, 110), (40, 44, 52), (240, 240, 240), (255, 220, 60)
    COLS = {"I": (0, 230, 240), "O": (250, 220, 0), "T": (170, 60, 230), "S": (60, 220, 80),
            "Z": (240, 60, 60), "J": (60, 100, 255), "L": (255, 150, 0)}
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("blok_anim", "Blok (animasi)", bg)
    C, NC, NR = 15, 8, 15             # ukuran sel, kolom, baris
    WX, WY = 92, 104                  # pojok kiri atas sumur
    W, H = NC * C, NR * C
    d.rectangle((WX - 4, WY - 2, WX + W + 3, WY + H + 3), outline=WALL, width=3)

    def cell(dr, cx, cy, col, ox=0, oy=0):
        x, y = ox + cx * C, oy + cy * C
        dr.rectangle((x + 1, y + 1, x + C - 2, y + C - 2), fill=col)
        dr.line((x + 2, y + 2, x + C - 4, y + 2), fill=tuple(min(255, v + 70) for v in col))

    stack = {(0, 14): "L", (1, 14): "L", (2, 14): "L", (2, 13): "L", (3, 14): "Z", (4, 14): "Z", (4, 13): "Z", (5, 13): "Z",
             (6, 14): "I", (7, 14): "I", (6, 13): "O", (7, 13): "O", (6, 12): "O", (7, 12): "O", (0, 13): "J", (0, 12): "J", (1, 12): "J",
             (5, 14): "S"}
    piece = [(0, 0), (1, 0), (2, 0), (1, 1)]   # T
    frames = []
    for k in range(8):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        for x in range(NC):
            for y in range(NR):
                dr.point((x * C + C // 2, y * C + C // 2), fill=GRAY)
        for (cx, cy), p in stack.items():
            cell(dr, cx, cy, COLS[p])
        drop = min(k * 2 - 1, 11)       # T jatuh 2 baris per frame lalu mendarat
        for (px, py) in piece:
            if py + drop >= 0:
                cell(dr, 2 + px, py + drop, COLS["T"])
        frames.append(im)
    D.add_anim(frames, WX, WY, interval=30)

    # Panel kanan: jam pixel (jam di atas menit), detik, LINES = langkah, NEXT.
    RX = 236
    dig = pix_digits(8, WHITE, BG)
    D.add("hour", dig, RX, 104)
    D.add("min", dig, RX, 104 + dig[0].height + 12)
    sec = pix_digits(3, YEL, BG)
    D.add("sec", sec, RX + 2 * dig[0].width + 4, 104 + 2 * dig[0].height + 12 - sec[0].height)
    bg.paste(pix_text("LINES", 3, (150, 156, 170), BG), (RX, 262))
    D.add("step", pix_digits(3, YEL, BG), RX, 288)
    bg.paste(pix_text("NEXT", 3, (150, 156, 170), BG), (RX, 322))
    for (px, py) in ((0, 0), (1, 0), (1, 1), (2, 1)):
        cell(d, px, py, COLS["Z"], RX + 4, 348)
    bg.paste(pix_text("LV", 3, (150, 156, 170), BG), (RX + 92, 322))
    D.add("day", pix_digits(3, WHITE, BG), RX + 92, 350)
    return D


# ---------------------------------------------------------------- Alien (barisan alien) - animasi
def alien_anim():
    BG, GREEN, WHITE, YEL, CYAN, PINK = (0, 0, 0), (60, 255, 80), (240, 240, 240), (255, 220, 60), (0, 220, 255), (255, 90, 200)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("alien_anim", "Alien (animasi)", bg)
    A1 = ["00100000100", "00010001000", "00111111100", "01101110110", "11111111111", "10111111101", "10100000101", "00011011000"]
    A2 = ["00100000100", "10010001001", "10111111101", "11101110111", "11111111111", "01111111110", "00100000100", "01000000010"]
    PX = 3

    def sprite(dr, pat, x, y, col):
        for r, row in enumerate(pat):
            for c, b in enumerate(row):
                if b == "1":
                    dr.rectangle((x + c * PX, y + r * PX, x + c * PX + PX - 1, y + r * PX + PX - 1), fill=col)

    # Animasi: 3 baris x 6 alien, bergeser kanan lalu kiri, kaki bergantian.
    W, H = 300, 92
    frames = []
    offs = [0, 8, 16, 24, 24, 16, 8, 0]
    for k, ox in enumerate(offs):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        pat = A1 if k % 2 == 0 else A2
        for r, col in enumerate((PINK, CYAN, GREEN)):
            for c in range(6):
                sprite(dr, pat, 14 + ox + c * 42, 4 + r * 30, col)
        frames.append(im)
    D.add_anim(frames, CX - W // 2, 58, interval=40)

    # Jam pixel di tengah.
    dig = pix_digits(9, WHITE, BG)
    dw, dh = dig[0].width, dig[0].height
    colon_w = 3 * 9
    sec = pix_digits(3, YEL, BG)
    total = 4 * dw + colon_w + 2 * sec[0].width
    tx, ty = CX - total // 2, 176
    D.add("hour", dig, tx, ty)
    for yy in (ty + 2 * 9, ty + 5 * 9):
        d.rectangle((tx + 2 * dw + 2, yy - 4, tx + 2 * dw + 13, yy + 7), fill=WHITE)
    D.add("min", dig, tx + 2 * dw + colon_w, ty)
    D.add("sec", sec, tx + 4 * dw + colon_w, ty + dh - sec[0].height)
    # SCORE = langkah, tanggal.
    bg.paste(pix_text("SCORE", 3, (160, 160, 170), BG), (98, 254))
    D.add("step", pix_digits(3, WHITE, BG), 98, 280)
    D.add("weekday", [pix_text(s, 3, CYAN, BG) for s in WD_PIX], 272, 254)
    D.add("day", pix_digits(3, WHITE, BG), 272, 280)
    # Perisai + meriam statis.
    for sx in (110, 210, 310):
        d.chord((sx, 314, sx + 46, 350), 180, 360, fill=GREEN)
        d.rectangle((sx, 332, sx + 46, 344), fill=GREEN)
        d.rectangle((sx + 16, 336, sx + 30, 344), fill=BG)
    cannon = ["00000100000", "00001110000", "00001110000", "01111111110", "11111111111", "11111111111"]
    sprite(d, cannon, CX - 16, 360, GREEN)
    d.line((CX, 300, CX, 352), fill=WHITE, width=2)      # tembakan
    # LIVES = baterai (0..5 ikon meriam).
    lives = []
    for lv in range(6):
        im = Image.new("RGB", (5 * 26, 20), BG)
        dr = ImageDraw.Draw(im)
        for k in range(5):
            pat_col = GREEN if k < lv else (40, 60, 40)
            for r, row in enumerate(cannon):
                for c, b in enumerate(row):
                    if b == "1":
                        dr.rectangle((k * 26 + c * 2, r * 2 + 4, k * 26 + c * 2 + 1, r * 2 + 5), fill=pat_col)
        lives.append(im)
    D.add("battery_level", lives, CX - 65, 396)
    return D


ALL = (hud_fps, rpg_status, blok_anim, alien_anim)
