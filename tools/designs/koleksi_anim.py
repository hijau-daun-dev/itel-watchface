"""Watch face beranimasi (elemen bg_dynamic) bertema IT: Build, Chomp, ECG, Rain.

Ringan seperti watch face animasi resmi: satu area animasi 6-8 frame, tanpa alpha, latar hitam
(RLE sangat efisien untuk area hitam).
"""
import math
import random

from PIL import Image, ImageDraw, ImageFont

from wflib import CX, SIZE, WEEKDAYS_ID, Design, glyph_set, text_rgba, ttf, word_set

MONO, MONO_B = "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"


def stamp(d, xy, s, font, col):
    """Teks statis yang rata atas dengan glyph_set (yang memotong di puncak digit)."""
    d.text((xy[0], xy[1] - font.getbbox("0")[1]), s, font=font, fill=col)


def date_row(D, d, font, cx, y, col_wd, col_num, col_sep, BG, sep="/"):
    wd = word_set(WEEKDAYS_ID, font, col_wd, BG, align="left")
    dd = glyph_set("0123456789", font, col_num, BG, padx=0)
    total = wd[0].width + 10 + 5 * dd[0].width
    x = cx - total // 2
    D.add("weekday", wd, x, y)
    x += wd[0].width + 10
    yd = y + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    stamp(d, (x + 2 * dd[0].width, yd), sep, font, col_sep)
    D.add("month", dd, x + 3 * dd[0].width, yd)


def big_time(D, d, font, col, colon_col, BG, cx, y, sec_font=None, sec_col=None):
    bd = glyph_set("0123456789", font, col, BG, padx=0)
    bw, bh = bd[0].width, bd[0].height
    colon = int(font.getlength(":")) - 14
    sd = glyph_set("0123456789", sec_font, sec_col, BG, padx=0) if sec_font else None
    extra = 2 * sd[0].width + 8 if sd else 0
    tx = cx - (4 * bw + colon + extra) // 2
    D.add("hour", bd, tx, y)
    stamp(d, (tx + 2 * bw - 7, y), ":", font, colon_col)
    D.add("min", bd, tx + 2 * bw + colon, y)
    if sd:
        D.add("sec", sd, tx + 4 * bw + colon + 8, y + bh - sd[0].height)
    return bh


# ---------------------------------------------------------------- Build (npm run build)
def build_anim():
    BG, FG, GREEN, CYAN, PURPLE, YELLOW, PINK, COMMENT = (
        (0, 0, 0), (248, 248, 242), (80, 250, 123), (139, 233, 253), (189, 147, 249),
        (241, 250, 140), (255, 121, 198), (98, 114, 164))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    f, fb = ttf(MONO, 19), ttf(MONO_B, 19)
    cw = int(f.getlength("0"))
    D = Design("build_anim", "Build (animasi)", bg)
    X = 82
    d.text((X, 70), "$ ", font=fb, fill=GREEN)
    d.text((X + 2 * cw, 70), "npm run build", font=f, fill=FG)

    # Animasi: spinner + progress bar 0..100% lalu "built".
    W, H = 302, 52
    spin = "|/-\\|/-\\"
    frames = []
    steps = [0, 15, 30, 45, 60, 75, 90, 100]
    for k, pct in enumerate(steps):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        if pct < 100:
            dr.text((0, 2), spin[k], font=fb, fill=YELLOW)
            dr.text((2 * cw, 2), "building...", font=f, fill=CYAN)
        else:
            dr.text((0, 2), "OK", font=fb, fill=GREEN)
            dr.text((3 * cw, 2), "built in 1.2s", font=f, fill=GREEN)
        n = round(pct / 10)
        dr.text((0, 28), "[", font=fb, fill=COMMENT)
        dr.text((cw, 28), "█" * n, font=fb, fill=GREEN if pct == 100 else PURPLE)
        dr.text(((1 + n) * cw, 28), "░" * (10 - n), font=fb, fill=(50, 54, 70))
        dr.text((11 * cw, 28), "]", font=fb, fill=COMMENT)
        dr.text((13 * cw, 28), f"{pct:>3}%", font=f, fill=FG)
        frames.append(im)
    D.add_anim(frames, X, 100, interval=25)

    bh = big_time(D, d, ttf(MONO_B, 88), GREEN, COMMENT, BG, CX, 176, ttf(MONO_B, 28), PINK)
    date_row(D, d, ttf(MONO, 21), CX, 176 + bh + 16, YELLOW, FG, COMMENT, BG, sep="-")
    y = 176 + bh + 56
    d.text((X, y), "battery", font=f, fill=CYAN)
    levels = []
    for lv in range(6):
        im = Image.new("RGB", (12 * cw, 22), BG)
        dr = ImageDraw.Draw(im)
        s = "[" + "#" * (lv * 2) + "-" * (10 - lv * 2) + "]"
        for c, ch in enumerate(s):
            dr.text((c * cw, 0), ch, font=f, fill=COMMENT if ch in "[]-" else (GREEN if lv > 1 else PINK))
        levels.append(im)
    D.add("battery_level", levels, X + 8 * cw, y)
    d.text((X, y + 28), "steps", font=f, fill=CYAN)
    D.add("step", glyph_set("0123456789", f, YELLOW, BG, padx=0, cell_w=cw), X + 8 * cw, y + 30)
    return D


# ---------------------------------------------------------------- Chomp (arcade 8-bit)
PIX = {
    "0": "01110 10001 10011 10101 11001 10001 01110", "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111", "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010", "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110", "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110", "9": "01110 10001 10001 01111 00001 00010 01100",
    "S": "01111 10000 10000 01110 00001 00001 11110", "C": "01110 10001 10000 10000 10000 10001 01110",
    "O": "01110 10001 10001 10001 10001 10001 01110", "R": "11110 10001 10001 11110 10100 10010 10001",
    "E": "11111 10000 10000 11110 10000 10000 11111", "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110", "P": "11110 10001 10001 11110 10000 10000 10000",
    "U": "10001 10001 10001 10001 10001 10001 01110", "A": "01110 10001 10001 11111 10001 10001 10001",
    "Y": "10001 10001 01010 00100 00100 00100 00100", "L": "10000 10000 10000 10000 10000 10000 11111",
    ":": "00000 01100 01100 00000 01100 01100 00000", " ": "00000 00000 00000 00000 00000 00000 00000",
    "-": "00000 00000 00000 11111 00000 00000 00000",
}


def pix_text(s, scale, col, bg, gap=1):
    w = len(s) * (5 + gap) * scale - gap * scale
    im = Image.new("RGB", (w, 7 * scale), bg)
    dr = ImageDraw.Draw(im)
    for i, ch in enumerate(s):
        rows = PIX[ch].split()
        for r, row in enumerate(rows):
            for c, bit in enumerate(row):
                if bit == "1":
                    x = (i * (5 + gap) + c) * scale
                    dr.rectangle((x, r * scale, x + scale - 2 if scale > 3 else x + scale - 1, (r + 1) * scale - (2 if scale > 3 else 1)), fill=col)
    return im


def chomp():
    BG, WALL, YEL, WHITE, RED, CYAN, PINK = (0, 0, 0), (33, 33, 222), (255, 230, 0), (255, 255, 255), (255, 60, 60), (0, 230, 255), (255, 150, 200)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("chomp_anim", "Chomp (animasi)", bg)
    # Dinding labirin.
    for y in (122, 316):
        d.rounded_rectangle((70, y, 396, y + 14), radius=7, outline=WALL, width=3)
    # Label arcade.
    up = pix_text("1UP", 3, RED, BG); bg.paste(up, (96, 72))
    hi = pix_text("HI-SCORE", 3, RED, BG); bg.paste(hi, (220, 72))
    sdig = []
    for c in "0123456789":
        g = pix_text(c, 3, WHITE, BG)
        im = Image.new("RGB", (g.width + 3, g.height), BG)
        im.paste(g, (0, 0))
        sdig.append(im)
    D.add("step", sdig, 96, 98)
    best = pix_text("99999", 3, WHITE, BG); bg.paste(best, (220, 98))
    # Jam pixel besar.
    digits = [pix_text(c, 11, YEL, BG) for c in "0123456789"]
    dw, dh = digits[0].width + 11, digits[0].height
    digits = [Image.new("RGB", (dw, dh), BG) for _ in digits]
    for k, im in enumerate(digits):
        im.paste(pix_text(str(k), 11, YEL, BG), (0, 0))
    colon = pix_text(":", 11, YEL, BG)
    cwid = 4 * 11
    total = 4 * dw + cwid
    tx, ty = CX - total // 2, 160
    D.add("hour", digits, tx, ty)
    bg.paste(colon.crop((11, 0, 11 + 3 * 11, dh)), (tx + 2 * dw, ty))
    D.add("min", digits, tx + 2 * dw + cwid, ty)
    sec = [pix_text(c, 3, CYAN, BG) for c in "0123456789"]
    sec = [Image.new("RGB", (im.width + 3, im.height), BG) for im in sec]
    for k, im in enumerate(sec):
        im.paste(pix_text(str(k), 3, CYAN, BG), (0, 0))
    D.add("sec", sec, CX - sec[0].width, ty + dh + 14)

    # Animasi: karakter kuning memakan titik di lorong bawah (8 frame).
    W, H = 300, 44
    frames = []
    dots = list(range(24, W, 24))
    for k in range(8):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        px = int(8 + k * (W - 30) / 7)
        for x in dots:
            if x > px + 12:
                dr.rectangle((x - 3, H // 2 - 3, x + 3, H // 2 + 3), fill=PINK)
        mouth = 40 if k % 2 == 0 else 6
        dr.pieslice((px - 16, H // 2 - 16, px + 16, H // 2 + 16), mouth, 360 - mouth, fill=YEL)
        frames.append(im)
    D.add_anim(frames, CX - W // 2, 330, interval=18)
    # Tanggal pixel di bawah.
    wd_names = ("MIN", "SEN", "SEL", "RAB", "KAM", "JUM", "SAB")
    PIX.update({"M": "10001 11011 10101 10101 10001 10001 10001", "N": "10001 11001 10101 10011 10001 10001 10001",
                "B": "11110 10001 10001 11110 10001 10001 11110", "K": "10001 10010 10100 11000 10100 10010 10001",
                "J": "00111 00010 00010 00010 00010 10010 01100"})
    wd = [pix_text(s, 3, WHITE, BG) for s in wd_names]
    D.add("weekday", wd, CX - 70, 392)
    dd = [pix_text(c, 3, WHITE, BG) for c in "0123456789"]
    dd = [Image.new("RGB", (im.width + 3, im.height), BG) for im in dd]
    for k, im in enumerate(dd):
        im.paste(pix_text(str(k), 3, WHITE, BG), (0, 0))
    D.add("day", dd, CX + 14, 392)
    return D


# ---------------------------------------------------------------- ECG (monitor detak jantung)
def ecg():
    BG, GRID, GREEN, DIM, FG, RED, GRAY = (0, 0, 0), (0, 34, 18), (60, 255, 120), (20, 110, 55), (230, 240, 235), (255, 70, 80), (110, 130, 120)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("ecg_anim", "ECG (animasi)", bg)
    fl = ttf(MONO_B, 16)
    d.text((112, 70), "MONITOR", font=fl, fill=GRAY)
    d.text((290, 70), "♥ HR", font=fl, fill=RED)
    bh = big_time(D, d, ttf(MONO_B, 80), FG, GRAY, BG, CX, 96, ttf(MONO_B, 26), GREEN)
    date_row(D, d, ttf(MONO, 20), CX, 96 + bh + 12, GREEN, FG, GRAY, BG)

    # Animasi: jejak EKG berjalan (8 frame, pola periodik digeser).
    W, H = 330, 96
    period = W // 2

    def beat(t):
        """Satu siklus PQRST (t 0..1) -> simpangan -1..1."""
        if 0.10 < t < 0.18:
            return 0.15 * math.sin((t - 0.10) / 0.08 * math.pi)
        if 0.24 < t < 0.27:
            return -0.25 * (t - 0.24) / 0.03
        if 0.27 <= t < 0.31:
            return -0.25 + 1.25 * (t - 0.27) / 0.04
        if 0.31 <= t < 0.35:
            return 1.0 - 1.4 * (t - 0.31) / 0.04
        if 0.35 <= t < 0.38:
            return -0.4 + 0.4 * (t - 0.35) / 0.03
        if 0.50 < t < 0.66:
            return 0.25 * math.sin((t - 0.50) / 0.16 * math.pi)
        return 0.0

    frames = []
    for k in range(8):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        for gx in range(0, W, 22):
            dr.line((gx, 0, gx, H), fill=GRID)
        for gy in range(0, H, 22):
            dr.line((0, gy, W, gy), fill=GRID)
        head = int((k + 1) * W / 8)
        pts = []
        for x in range(W):
            t = (x % period) / period
            pts.append((x, H // 2 - beat(t) * (H * 0.42)))
        # Bagian yang sudah "tergambar" (sampai kepala) terang, sisanya redup.
        dr.line(pts[:head], fill=GREEN, width=3)
        if head < W - 14:
            dr.line(pts[head + 14:], fill=DIM, width=2)
        hx, hy = pts[min(head, W - 1)]
        dr.ellipse((hx - 4, hy - 4, hx + 4, hy + 4), fill=(200, 255, 220))
        frames.append(im)
    yA = 96 + bh + 48
    D.add_anim(frames, CX - W // 2, yA, interval=12)
    # Detak jantung besar di bawah.
    fh = ttf(MONO_B, 40)
    D.add("heart", glyph_set("0123456789", fh, RED, BG, padx=0) + [glyph_set("-", fh, RED, BG, padx=0, cell_chars="0")[0]],
          CX - 4, yA + H + 12, gravity=0x0c)
    d.text((CX + 6, yA + H + 22), "BPM", font=ttf(MONO_B, 20), fill=GRAY)
    return D


# ---------------------------------------------------------------- Rain (Matrix beranimasi)
def rain():
    rnd = random.Random(5)
    BG, G, G_HI, G_DIM = (0, 0, 0), (0, 255, 70), (200, 255, 210), (0, 90, 30)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("rain_anim", "Rain (animasi)", bg)
    gothic = "C:/Windows/Fonts/msgothic.ttc"
    try:
        fk = ImageFont.truetype(gothic, 16)
        chars = "01アイウエオカキクケコサシスセソ"
    except OSError:
        fk = ttf(MONO, 16)
        chars = "01<>{}[]#$%=+*"
    # Strip animasi di atas: kolom karakter turun 1 baris per frame (pola berulang, 8 frame).
    W, H, LH, COLW = 330, 132, 17, 15
    cols = W // COLW
    rows = H // LH + 8
    seq = [[rnd.choice(chars) for _ in range(rows + 8)] for _ in range(cols)]
    heads = [rnd.randint(0, 8) for _ in range(cols)]
    lens = [rnd.randint(3, 7) for _ in range(cols)]
    frames = []
    for k in range(8):
        im = Image.new("RGB", (W, H), BG)
        dr = ImageDraw.Draw(im)
        for c in range(cols):
            head = (heads[c] + k) % 8
            for r in range(H // LH + 1):
                # Tiap kolom: beberapa "tetes" berjarak 8 baris; baris r menyala jika di ekor tetes.
                dist = (head - r) % 8
                if dist < lens[c]:
                    col = G_HI if dist == 0 else (0, int(255 - dist * 30), int(70 - dist * 8))
                    dr.text((c * COLW, r * LH), seq[c][(r + k) % len(seq[c])], font=fk, fill=col)
        frames.append(im)
    D.add_anim(frames, CX - W // 2, 40, interval=12)
    # Panel jam.
    PX0, PY0, PX1, PY1 = 70, 186, 396, 340
    d.rounded_rectangle((PX0, PY0, PX1, PY1), radius=14, outline=(0, 160, 50), width=2)
    d.text((PX0 + 16, PY0 + 10), "> wake up, user...", font=ttf(MONO, 16), fill=(0, 200, 60))
    bh = big_time(D, d, ttf(MONO_B, 76), G, (0, 150, 45), BG, CX, PY0 + 40, ttf(MONO_B, 24), G_HI)
    date_row(D, d, ttf(MONO, 20), CX, PY0 + 40 + bh + 14, G, G, (0, 150, 45), BG)
    # Garis kode statis di bawah panel.
    for k, s in enumerate(("01001011 10110", "  0x1F 0xA4 0x08")):
        t = text_rgba(s, ttf(MONO, 14), G_DIM)
        bg.paste(t, (CX - t.width // 2, PY1 + 14 + k * 20), t)
    return D


ALL = (build_anim, chomp, ecg, rain)
