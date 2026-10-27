"""Watch face bertema IT: Binary Clock, Matrix, htop, PCB, BSOD (parodi). Dipanggil dari koleksi.py."""
import os
import random

from PIL import Image, ImageDraw, ImageFont

from wflib import CX, DSEG, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, text_rgba, ttf, word_set

MONO, MONO_B = "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"


# ---------------------------------------------------------------- Binary Clock (BCD)
def binary_clock():
    BG, OFF, GRAY = (0, 0, 0), (34, 38, 48), (110, 118, 136)
    HC, MC, SC = (0, 210, 255), (80, 250, 123), (255, 90, 180)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("binary_clock", "Binary Clock", bg)
    COL, R, ROW = 44, 15, 42          # lebar kolom, jari-jari titik, jarak baris

    def column(digit, color):
        im = Image.new("RGB", (COL, 4 * ROW), BG)
        dr = ImageDraw.Draw(im)
        for k, bit in enumerate((8, 4, 2, 1)):
            cy = k * ROW + ROW // 2
            on = digit & bit
            dr.ellipse((COL // 2 - R, cy - R, COL // 2 + R, cy + R), fill=color if on else OFF)
            if on:
                dr.ellipse((COL // 2 - R + 5, cy - R + 4, COL // 2 - R + 11, cy - R + 9), fill=(255, 255, 255))
        return im

    GAP = 18
    x0 = CX - (6 * COL + 2 * GAP) // 2 + 12
    y0 = 118
    D.add("hour_tens", [column(n, HC) for n in range(10)], x0, y0)
    D.add("hour_units", [column(n, HC) for n in range(10)], x0 + COL, y0)
    D.add("min_tens", [column(n, MC) for n in range(10)], x0 + 2 * COL + GAP, y0)
    D.add("min_units", [column(n, MC) for n in range(10)], x0 + 3 * COL + GAP, y0)
    D.add("sec", [column(n, SC) for n in range(10)], x0 + 4 * COL + 2 * GAP, y0)   # 2 kolom berdampingan
    f = ttf(MONO, 15)
    for k, bit in enumerate("8421"):
        d.text((x0 - 24, y0 + k * ROW + ROW // 2 - 9), bit, font=f, fill=GRAY)
    for k, lab in enumerate(("HH", "MM", "SS")):
        cx = x0 + k * (2 * COL + GAP) + COL
        t = text_rgba(lab, ttf(MONO_B, 15), GRAY)
        bg.paste(t, (cx - t.width // 2, y0 + 4 * ROW + 6), t)
    title = text_rgba("0b_CLOCK", ttf(MONO_B, 18), GRAY)
    bg.paste(title, (CX - title.width // 2, 80), title)

    # Desimal kecil di bawah: 10:08  JUM 25.09
    fd = ttf(MONO_B, 34)
    dd = glyph_set("0123456789", fd, (230, 232, 240), BG, padx=0)
    ty = y0 + 4 * ROW + 36
    cw = dd[0].width
    wd = word_set(WEEKDAYS_ID, fd, HC, BG, align="left")
    total = 5 * cw + 16 + wd[0].width + 10 + 5 * cw
    x = CX - total // 2
    D.add("hour", dd, x, ty)
    d.text((x + 2 * cw, ty - fd.getbbox("0")[1]), ":", font=fd, fill=GRAY)
    D.add("min", dd, x + 3 * cw, ty)
    x += 5 * cw + 16
    D.add("weekday", wd, x, ty)
    x += wd[0].width + 10
    D.add("day", dd, x, ty)
    d.text((x + 2 * cw, ty - fd.getbbox("0")[1]), ".", font=fd, fill=GRAY)
    D.add("month", dd, x + 3 * cw, ty)
    return D


# ---------------------------------------------------------------- Matrix
def matrix():
    rnd = random.Random(7)
    BG, G, G_HI = (0, 0, 0), (0, 255, 70), (190, 255, 200)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    gothic = "C:/Windows/Fonts/msgothic.ttc"
    fk = ImageFont.truetype(gothic, 15) if os.path.exists(gothic) else ttf(MONO, 15)
    chars = "01アイウエオカキクケコサシスセソ<>{}[]#$%=+*" if os.path.exists(gothic) else "01<>{}[]#$%=+*"
    for col in range(0, SIZE, 15):
        head = rnd.randint(-100, SIZE + 150)
        length = rnd.randint(80, 260)
        for y in range(head - length, head, 17):
            if y < 0 or y > SIZE:
                continue
            t = (y - (head - length)) / length
            c = G_HI if head - y < 18 else (0, int(40 + 150 * t), int(10 + 30 * t))
            d.text((col, y), rnd.choice(chars), font=fk, fill=c)
    # Panel tengah polos, supaya glyph tanpa alpha menyatu.
    PX0, PY0, PX1, PY1 = 70, 150, 396, 318
    d.rounded_rectangle((PX0, PY0, PX1, PY1), radius=14, fill=BG, outline=(0, 160, 50), width=2)
    D = Design("matrix", "Matrix", bg)
    fb = ttf(MONO_B, 80)
    dd = glyph_set("0123456789", fb, G, BG, padx=0)
    cw, ch = dd[0].width, dd[0].height
    colon = int(fb.getlength(":")) - 14
    tx = CX - (4 * cw + colon) // 2 - 16
    ty = 190
    D.add("hour", dd, tx, ty)
    d.text((tx + 2 * cw - 7, ty - 16), ":", font=fb, fill=(0, 150, 45))
    D.add("min", dd, tx + 2 * cw + colon, ty)
    fs = ttf(MONO_B, 26)
    sd = glyph_set("0123456789", fs, G_HI, BG, padx=0)
    D.add("sec", sd, tx + 4 * cw + colon + 6, ty + ch - sd[0].height)
    t = text_rgba("> wake up, user...", ttf(MONO, 16), (0, 200, 60))
    bg.paste(t, (PX0 + 18, PY0 + 12), t)
    fd = ttf(MONO, 20)
    wd = word_set(WEEKDAYS_ID, fd, G, BG, align="left")
    dd2 = glyph_set("0123456789", fd, G, BG, padx=0)
    y = ty + ch + 18
    x = PX0 + 18
    D.add("weekday", wd, x, y)
    x += wd[0].width + 12
    D.add("day", dd2, x, y + wd[0].height - dd2[0].height)
    d.text((x + 2 * dd2[0].width, y - 2), "/", font=fd, fill=(0, 150, 45))
    D.add("month", dd2, x + 3 * dd2[0].width, y + wd[0].height - dd2[0].height)
    return D


# ---------------------------------------------------------------- htop
def htop():
    BG, FG, GREEN, CYAN, YELLOW, RED, BLUE, GRAY = (
        (0, 0, 0), (220, 224, 230), (80, 220, 100), (60, 200, 220), (240, 210, 80),
        (240, 80, 80), (70, 110, 220), (110, 116, 128))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    f, fb = ttf(MONO, 17), ttf(MONO_B, 17)
    cw = int(f.getlength("0"))
    D = Design("htop", "htop", bg)
    D.center_x = BG
    X = 70

    big = ttf(MONO_B, 84)
    bd = glyph_set("0123456789", big, FG, BG, padx=0)
    bw, bh = bd[0].width, bd[0].height
    colon = int(big.getlength(":")) - 14
    tx = CX - (4 * bw + colon) // 2 - 18
    ty = 62
    D.add("hour", bd, tx, ty)
    d.text((tx + 2 * bw - 7, ty - big.getbbox("0")[1]), ":", font=big, fill=GRAY)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    sf = ttf(MONO_B, 22)
    sd = glyph_set("0123456789", sf, CYAN, BG, padx=0)
    D.add("sec", sd, tx + 4 * bw + colon + 6, ty + bh - sd[0].height)

    y = ty + bh + 20
    d.text((X, y), "CPU", font=fb, fill=CYAN)
    d.text((X + 3 * cw, y), "[", font=fb, fill=FG)
    bars = []
    for lv in range(6):
        im = Image.new("RGB", (cw * 20, 22), BG)
        dr = ImageDraw.Draw(im)
        for k in range(lv * 4):
            dr.text((k * cw, 0), "|", font=fb, fill=GREEN if k < 12 else YELLOW if k < 17 else RED)
        pct = f"{lv * 20}%"
        dr.text(((20 - len(pct)) * cw, 0), pct, font=f, fill=GRAY)
        bars.append(im)
    D.add("battery_level", bars, X + 4 * cw, y)
    d.text((X + 24 * cw, y), "]", font=fb, fill=FG)
    d.text((X, y + 24), "Mem", font=fb, fill=CYAN)
    d.text((X + 3 * cw, y + 24), "[", font=fb, fill=FG)
    d.text((X + 4 * cw, y + 24), "|" * 9, font=fb, fill=GREEN)
    d.text((X + 13 * cw, y + 24), "|" * 3, font=fb, fill=BLUE)
    d.text((X + 19 * cw, y + 24), "1.2G", font=f, fill=GRAY)
    d.text((X + 24 * cw, y + 24), "]", font=fb, fill=FG)

    y2 = y + 58
    d.text((X, y2), "Tasks:", font=fb, fill=CYAN)
    D.add("step", glyph_set("0123456789", fb, GREEN, BG, padx=0, cell_w=cw), X + 7 * cw, y2 + 1)
    d.text((X + 13 * cw, y2), "steps", font=f, fill=GRAY)
    d.text((X, y2 + 22), "Date:", font=fb, fill=CYAN)
    wd = word_set(WEEKDAYS_ID, f, FG, BG, align="left")
    dd = glyph_set("0123456789", f, FG, BG, padx=0, cell_w=cw)
    D.add("weekday", wd, X + 7 * cw, y2 + 23)
    xd = X + 7 * cw + wd[0].width + cw
    D.add("day", dd, xd, y2 + 23 + wd[0].height - dd[0].height)
    d.text((xd + 2 * cw, y2 + 22), ".", font=f, fill=GRAY)
    D.add("month", dd, xd + 3 * cw, y2 + 23 + wd[0].height - dd[0].height)

    yt = y2 + 56
    d.rectangle((X - 6, yt - 2, SIZE - X + 6, yt + 19), fill=(40, 160, 90))
    d.text((X, yt), "  PID USER  CMD", font=fb, fill=(10, 20, 14))
    rows = [("   1", "root", "watchd", FG), ("  42", "you ", "walk --steps", GREEN), (" 233", "jl  ", "ble-stream", GRAY)]
    for k, (pid, user, cmd, col) in enumerate(rows):
        d.text((X, yt + 22 + k * 20), f"{pid} {user}  {cmd}", font=f, fill=col)
    yf, x = 404, 100
    for key, lab in (("F1", "Help"), ("F5", "Tree"), ("F10", "Quit")):
        d.text((x, yf), key, font=fb, fill=FG)
        x += int(fb.getlength(key))
        d.rectangle((x, yf, x + int(f.getlength(lab)) + 4, yf + 19), fill=(40, 120, 160))
        d.text((x + 2, yf), lab, font=f, fill=(0, 0, 0))
        x += int(f.getlength(lab)) + 14
    return D


# ---------------------------------------------------------------- PCB
def pcb():
    rnd = random.Random(3)
    BOARD, TRACE, PAD, CHIP, SILK, LED = (12, 70, 42), (190, 150, 70), (215, 180, 95), (22, 22, 24), (220, 230, 220), (255, 60, 40)
    bg = Image.new("RGB", (SIZE, SIZE), BOARD)
    d = ImageDraw.Draw(bg)
    for _ in range(24):                     # jalur tembaga + via
        x, y = rnd.choice([(rnd.randint(20, 446), rnd.choice((0, SIZE))), (rnd.choice((0, SIZE)), rnd.randint(20, 446))])
        pts = [(x, y)]
        for _ in range(3):
            tx, ty = rnd.randint(60, 406), rnd.randint(60, 406)
            if rnd.random() < .5:
                pts += [(tx, y), (tx, ty)]
                x, y = tx, ty
            else:
                dx = tx - x
                x, y = x + dx, y + abs(dx) * (1 if ty > y else -1)
                pts.append((x, y))
        d.line(pts, fill=TRACE, width=3, joint="curve")
        ex, ey = pts[-1]
        d.ellipse((ex - 5, ey - 5, ex + 5, ey + 5), fill=PAD)
        d.ellipse((ex - 2, ey - 2, ex + 2, ey + 2), fill=BOARD)
    CX0, CY0, CX1, CY1 = 92, 168, 374, 292  # chip utama
    for k in range(14):
        x = CX0 + 14 + k * 19
        d.rectangle((x, CY0 - 12, x + 8, CY0), fill=PAD)
        d.rectangle((x, CY1, x + 8, CY1 + 12), fill=PAD)
    d.rectangle((CX0, CY0, CX1, CY1), fill=CHIP)
    d.ellipse((CX0 + 8, CY0 + 8, CX0 + 16, CY0 + 16), fill=(60, 60, 64))
    lab = text_rgba("ISW-O43  RTC", ttf(MONO, 13), (120, 120, 124))
    bg.paste(lab, (CX1 - lab.width - 10, CY1 - 20), lab)
    D = Design("pcb", "PCB", bg)
    fd = ImageFont.truetype(DSEG, 74)
    lit = glyph_set("0123456789", fd, LED, CHIP)
    ghost = glyph_set("8", fd, (58, 22, 20), CHIP)[0]
    dd = []
    for im in lit:                          # segmen padam di belakang angka
        mask = im.convert("L").point(lambda p: 255 if p > 45 else 0)
        dd.append(Image.composite(im, ghost, mask))
    dw, dh = dd[0].width, dd[0].height
    colon = 18
    tx = CX - (4 * dw + colon) // 2
    ty = (CY0 + CY1) // 2 - dh // 2 - 16
    D.add("hour", dd, tx, ty)
    for yy in (ty + dh * .3, ty + dh * .7):
        d.rectangle((tx + 2 * dw + 5, yy - 4, tx + 2 * dw + 12, yy + 3), fill=LED)
    D.add("min", dd, tx + 2 * dw + colon, ty)
    fsec = ImageFont.truetype(DSEG, 22)
    slit = glyph_set("0123456789", fsec, LED, CHIP)
    sghost = glyph_set("8", fsec, (58, 22, 20), CHIP)[0]
    sdd = [Image.composite(im, sghost, im.convert("L").point(lambda p: 255 if p > 45 else 0)) for im in slit]
    D.add("sec", sdd, CX0 + 14, CY1 - sdd[0].height - 6)
    for (x0, y0, x1, y1) in ((126, 330, 236, 372), (250, 330, 340, 372)):   # chip kecil
        d.rectangle((x0, y0, x1, y1), fill=CHIP)
        for k in range(5):
            x = x0 + 10 + k * ((x1 - x0 - 20) // 4)
            d.rectangle((x - 3, y0 - 7, x + 3, y0), fill=PAD)
            d.rectangle((x - 3, y1, x + 3, y1 + 7), fill=PAD)
    fs = ttf(MONO_B, 18)
    wd = word_set(WEEKDAYS_ID, fs, SILK, CHIP, align="left")
    sd = glyph_set("0123456789", fs, SILK, CHIP, padx=0)
    D.add("weekday", wd, 134, 342)
    D.add("day", sd, 134 + wd[0].width + 6, 342 + wd[0].height - sd[0].height)
    D.add("step", sd, 295, 342 + wd[0].height - sd[0].height, gravity=0x0a)
    for txt, x, y in (("U2 DATE", 128, 312), ("U3 STEP", 252, 312), ("U1", CX0, CY0 - 30)):
        t = text_rgba(txt, ttf(MONO_B, 12), SILK)
        bg.paste(t, (x, y), t)
    return D


# ---------------------------------------------------------------- BSOD (parodi layar biru)
def bsod():
    BLUE, WHITE = (0, 112, 200), (255, 255, 255)
    bg = Image.new("RGB", (SIZE, SIZE), BLUE)
    d = ImageDraw.Draw(bg)
    seg = "C:/Windows/Fonts/segoeui.ttf"

    def font(n):
        return ImageFont.truetype(seg, n) if os.path.exists(seg) else bahn(n, "Regular")

    X = 74
    d.text((X, 66), ":(", font=font(74), fill=WHITE)
    d.multiline_text((X, 168), "Jam kamu mengalami masalah:\nwaktu terus berjalan.", font=font(17), fill=WHITE, spacing=4)
    D = Design("bsod", "BSOD", bg)
    D.center_x = BLUE
    ft = font(72)
    dd = glyph_set("0123456789", ft, WHITE, BLUE)
    y = 218
    D.add("hour", dd, X, y)
    d.text((X + 2 * dd[0].width + 2, y - ft.getbbox("0")[1] - 4), ":", font=ft, fill=WHITE)
    D.add("min", dd, X + 2 * dd[0].width + 22, y)
    fsec = font(34)
    sd = glyph_set("0123456789", fsec, WHITE, BLUE)
    xs = X + 4 * dd[0].width + 26
    d.text((xs, y + dd[0].height - sd[0].height - fsec.getbbox("0")[1] - 2), ":", font=fsec, fill=WHITE)
    D.add("sec", sd, xs + int(fsec.getlength(":")) + 2, y + dd[0].height - sd[0].height)
    pct = word_set([f"{p}% complete" for p in (0, 20, 40, 60, 80, 100)], font(17), WHITE, BLUE, align="left")
    D.add("battery_level", pct, X, y + dd[0].height + 14)
    rnd = random.Random(11)                 # "QR code" acak
    q0x, q0y, cell = X, 336, 3
    d.rectangle((q0x, q0y, q0x + 21 * cell, q0y + 21 * cell), fill=WHITE)
    finders = ((0, 0), (0, 14), (14, 0))
    for i in range(21):
        for j in range(21):
            fnd = next(((fi, fj) for fi, fj in finders if fi <= i < fi + 7 and fj <= j < fj + 7), None)
            if fnd:
                a, b = i - fnd[0], j - fnd[1]
                on = a in (0, 6) or b in (0, 6) or (2 <= a <= 4 and 2 <= b <= 4)
            else:
                on = rnd.random() < .45
            if on:
                d.rectangle((q0x + j * cell, q0y + i * cell, q0x + (j + 1) * cell - 1, q0y + (i + 1) * cell - 1), fill=BLUE)
    d.multiline_text((X + 76, 336), "Info: itel ISW-O43\nStop code:\nWATCH_FACE_TOO_COOL", font=font(12), fill=WHITE, spacing=3)
    fd = font(15)
    wd = word_set(WEEKDAYS_ID, fd, WHITE, BLUE, align="left")
    dd2 = glyph_set("0123456789", fd, WHITE, BLUE)
    D.add("weekday", wd, X + 76, 386)
    D.add("day", dd2, X + 76 + wd[0].width + 6, 386 + wd[0].height - dd2[0].height)
    return D


ALL = (binary_clock, matrix, htop, pcb, bsod)
