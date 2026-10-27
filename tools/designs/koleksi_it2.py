"""Watch face IT seri 2 yang memamerkan fitur jam (cuaca, detak, langkah, baterai, progres target).

Tetap ringan: glyph tanpa alpha, maksimal 2-3 elemen sensor per desain.
Trik angka panjang-variabel (langkah, detak): pakai gravity rata kanan (0x0c) supaya tanda baca
statis di belakangnya (",") selalu menempel di posisi tetap.
"""
import math

from PIL import Image, ImageDraw

from wflib import CX, SIZE, WEEKDAYS_ID, Design, glyph_set, text_rgba, ttf, word_set

MONO, MONO_B = "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"
RIGHT_TOP = 0x0c   # x = tepi kanan, y = atas


def battery_blocks(n_lv, font, on, off, bg, prefix="", suffix=""):
    """6 gambar level baterai berupa blok teks: ■■■■□."""
    out = []
    for lv in range(n_lv):
        s_on, s_off = "■" * lv, "□" * (n_lv - 1 - lv)
        w = int(font.getlength(prefix + "■" * (n_lv - 1) + suffix)) + 2
        im = Image.new("RGB", (w, font.size + 6), bg)
        dr = ImageDraw.Draw(im)
        x = 0
        for s, col in ((prefix, off), (s_on, on), (s_off, off), (suffix, off)):
            dr.text((x, 1), s, font=font, fill=col)
            x += int(font.getlength(s))
        out.append(im)
    return out


# ---------------------------------------------------------------- JSON API
def json_api():
    BG, FG, KEY, STR, NUM, PUNC, GREEN, GRAY = (
        (0, 0, 0), (171, 178, 191), (224, 108, 117), (152, 195, 121), (209, 154, 102),
        (171, 178, 191), (80, 200, 120), (92, 99, 112))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    f, fb = ttf(MONO, 21), ttf(MONO_B, 21)
    cw = int(f.getlength("0"))
    D = Design("json_api", "JSON API", bg)
    D.center_x = BG
    X = 66

    d.text((X + 4, 60), "GET /api/watch", font=fb, fill=FG)
    d.text((X + 4 + 15 * cw, 60), "200 OK", font=fb, fill=GREEN)
    d.text((X, 90), "{", font=fb, fill=PUNC)

    def key(y, name):
        d.text((X + 2 * cw, y), f'"{name}"', font=f, fill=KEY)
        d.text((X + (4 + len(name)) * cw, y), ":", font=f, fill=PUNC)
        return X + (6 + len(name)) * cw

    # "time": lalu nilainya besar di baris sendiri.
    key(120, "time")
    big = ttf(MONO_B, 62)
    bd = glyph_set("0123456789", big, STR, BG, padx=0)
    bw, bh = bd[0].width, bd[0].height
    top = big.getbbox("0")[1]
    q = int(big.getlength('"'))
    total = q + 5 * bw + int(big.getlength('",'))
    bx, by = CX - total // 2 + 6, 150
    d.text((bx, by - top), '"', font=big, fill=STR)
    D.add("hour", bd, bx + q, by)
    d.text((bx + q + 2 * bw, by - top), ":", font=big, fill=STR)
    D.add("min", bd, bx + q + 3 * bw, by)
    fsec = ttf(MONO_B, 30)
    sd = glyph_set("0123456789", fsec, STR, BG, padx=0)
    xs = bx + q + 5 * bw
    d.text((xs, by + bh - sd[0].height - fsec.getbbox("0")[1]), ":", font=fsec, fill=STR)
    xs += int(fsec.getlength(":"))
    D.add("sec", sd, xs, by + bh - sd[0].height)
    d.text((xs + 2 * sd[0].width, by - top), '",', font=big, fill=STR)

    y0, LH = by + bh + 18, 32
    # "day": "JUM 25.09",
    x = key(y0, "day")
    d.text((x, y0), '"', font=f, fill=STR)
    wd = word_set(WEEKDAYS_ID, f, STR, BG, align="left")
    D.add("weekday", wd, x + cw, y0 + 1)
    dd = glyph_set("0123456789", f, STR, BG, padx=0, cell_w=cw)
    xd = x + cw + wd[0].width + cw
    yy = y0 + 1 + wd[0].height - dd[0].height
    D.add("day", dd, xd, yy)
    d.text((xd + 2 * cw, y0), ".", font=f, fill=STR)
    D.add("month", dd, xd + 3 * cw, yy)
    d.text((xd + 5 * cw, y0), '",', font=f, fill=STR)

    nums = glyph_set("0123456789", f, NUM, BG, padx=0, cell_w=cw)
    end = X + 19 * cw                     # angka rata kanan supaya koma tetap di tempat
    y = y0 + LH
    key(y, "steps")
    D.add("step", nums, end, y + 2, gravity=RIGHT_TOP)
    d.text((end, y), ",", font=f, fill=PUNC)
    y += LH
    key(y, "bpm")
    D.add("heart", nums + [text_rgba("--", f, NUM).convert("RGB")], end, y + 2, gravity=RIGHT_TOP)
    d.text((end, y), ",", font=f, fill=PUNC)
    y += LH
    x = key(y, "battery")
    d.text((x, y), '"', font=f, fill=STR)
    D.add("battery_level", battery_blocks(6, f, STR, GRAY, BG), x + cw, y)
    d.text((x + cw + int(f.getlength("■" * 5)) + 2, y), '"', font=f, fill=STR)
    d.text((X, y + LH), "}", font=fb, fill=PUNC)
    d.text((CX - 76, y + LH + 34), "// 12 ms · cached", font=ttf(MONO, 15), fill=GRAY)
    return D


# ---------------------------------------------------------------- curl wttr.in
WTTR_ART = {   # ikon cuaca gaya wttr.in; urutan indeks = dugaan dari watch face resmi
    0: ["    .-.    ", "     __)   ", "    (      ", "     `-'   ", "      *    "],
    1: ["   \\   /   ", "    .-.    ", " - (   ) - ", "    `-'    ", "   /   \\   "],
    2: ["           ", "    .--.   ", " .-(    ). ", "(___.__)__)", "           "],
    3: ["  \\  /     ", '_ /"".-.   ', "  \\_(   ). ", "  /(___(__)", "           "],
    4: ["    .-.    ", "   (   ).  ", "  (___(__) ", "   ' ' ' ' ", "  ' ' ' '  "],
    5: ["    .-.    ", "   (   ).  ", "  (___(__) ", "    /_ /_  ", "    /  /   "],
    6: ["    .-.    ", "   (   ).  ", "  (___(__) ", "  ,/_,/_,  ", "  ,/ ,/ ,  "],
    7: ["           ", " ~~~~~~~~  ", "   ~~~~~~~ ", " ~~~~~~    ", "           "],
    8: ["    .-.    ", "   (   ).  ", "  (___(__) ", "   *  *  * ", "  *  *  *  "],
    9: ["           ", " _ - _ - _ ", "  _ - _ - _", " _ - _ - _ ", "           "],
    10: ["           ", " . : . : . ", "  : . : . :", " . : . : . ", "           "],
    11: ["    .-.    ", "   (   ).  ", "  (___(__) ", "  ,',',',' ", "  ,',',',' "],
}


def wttr():
    BG, FG, GRAY, YEL, CLOUD, RAIN, SNOW, GREEN = (
        (0, 0, 0), (220, 220, 220), (120, 120, 120), (255, 215, 0), (200, 200, 210),
        (90, 160, 255), (240, 240, 255), (80, 220, 100))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    f = ttf(MONO, 17)
    fb = ttf(MONO_B, 17)
    cw, lh = int(f.getlength("0")), 19
    D = Design("wttr", "wttr.in", bg)
    X = 96
    d.text((X, 78), "$ ", font=fb, fill=GREEN)
    d.text((X + 2 * cw, 78), "curl wttr.in", font=f, fill=FG)
    d.text((X, 104), "Weather report: lokal", font=f, fill=GRAY)

    def art(idx):
        lines = WTTR_ART[idx]
        im = Image.new("RGB", (11 * cw + 2, 5 * lh), BG)
        dr = ImageDraw.Draw(im)
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == " ":
                    continue
                if idx == 1 or (idx == 3 and r < 2 and c < 5) or (idx in (5, 6) and r >= 3 and ch in "/_"):
                    col = YEL
                elif r >= 3 and idx in (4, 6, 11):
                    col = RAIN
                elif r >= 3 and idx == 8:
                    col = SNOW
                elif idx in (0, 9, 10):
                    col = GRAY
                else:
                    col = CLOUD
                dr.text((c * cw, r * lh), ch, font=fb, fill=col)
        return im

    D.add("weather_icon", [art(i) for i in range(12)], X - 4, 132)
    ft = ttf(MONO_B, 30)
    # Suhu rata kanan supaya "°C" statis selalu menempel; glyph indeks 11 ("°") dibuat kosong.
    tdig = glyph_set("0123456789", ft, YEL, BG, padx=0)
    minus = glyph_set("-", ft, YEL, BG, padx=0, cell_chars="0")[0]
    tend = X + 16 * cw
    D.add("temperature", tdig + [minus, Image.new("RGB", (1, tdig[0].height), BG)], tend, 150, gravity=RIGHT_TOP)
    d.ellipse((tend + 4, 152, tend + 12, 160), outline=YEL, width=2)
    d.text((tend + 15, 150), "C", font=ft, fill=YEL)
    d.text((X + 12 * cw + 8, 194), "suhu", font=f, fill=GRAY)
    # Jam besar + tanggal.
    big = ttf(MONO_B, 88)
    bd = glyph_set("0123456789", big, FG, BG, padx=0)
    bw = bd[0].width
    colon = int(big.getlength(":")) - 14
    fsec = ttf(MONO_B, 30)
    sd = glyph_set("0123456789", fsec, YEL, BG, padx=0)
    tx = CX - (4 * bw + colon + 2 * sd[0].width + 8) // 2
    ty = 244
    D.add("hour", bd, tx, ty)
    d.text((tx + 2 * bw - 7, ty - big.getbbox("0")[1]), ":", font=big, fill=GRAY)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    D.add("sec", sd, tx + 4 * bw + colon + 8, ty + bd[0].height - sd[0].height)
    fd = ttf(MONO, 20)
    wd = word_set(WEEKDAYS_ID, fd, YEL, BG, align="left")
    dd = glyph_set("0123456789", fd, FG, BG, padx=0)
    total = wd[0].width + 10 + 5 * dd[0].width
    x = CX - total // 2
    y = ty + bd[0].height + 14
    D.add("weekday", wd, x, y)
    x += wd[0].width + 10
    D.add("day", dd, x, y + wd[0].height - dd[0].height)
    d.text((x + 2 * dd[0].width, y - 1), "/", font=fd, fill=GRAY)
    D.add("month", dd, x + 3 * dd[0].width, y + wd[0].height - dd[0].height)
    return D


# ---------------------------------------------------------------- VS Code
def vscode():
    BG, LN, FG, KW, VAR, PROP, STR, NUM, COM, LINE, BLUE = (
        (0, 0, 0), (90, 96, 106), (212, 212, 212), (86, 156, 214), (79, 193, 255),
        (156, 220, 254), (206, 145, 120), (181, 206, 168), (106, 153, 85), (40, 40, 44), (0, 122, 204))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    f = ttf(MONO, 22)
    cw = int(f.getlength("0"))
    D = Design("vscode", "VS Code", bg)
    D.center_x = BG
    # Tab bar.
    d.line((0, 88, SIZE, 88), fill=LINE, width=1)
    d.rectangle((150, 54, 300, 88), outline=LINE)
    d.line((151, 54, 299, 54), fill=BLUE, width=2)       # tab aktif
    d.text((162, 58), "watch.ts", font=ttf(MONO, 20), fill=FG)
    d.text((268, 58), "×", font=ttf(MONO, 20), fill=LN)
    X0, CODE = 58, 96

    def ln(n, y):
        d.text((X0, y), f"{n:>2}", font=f, fill=LN)
        return y

    def put(x_chars, y, s, col):
        d.text((CODE + x_chars * cw, y), s, font=f, fill=col)

    y = ln(1, 98); put(0, y, "const", KW); put(6, y, "now", VAR); put(10, y, "= {", FG)
    y = ln(2, 128); put(2, y, "time:", PROP)
    # Baris 3: nilai waktu besar.
    big = ttf(MONO_B, 56)
    bd = glyph_set("0123456789", big, STR, BG, padx=0)
    bw, bh = bd[0].width, bd[0].height
    top = big.getbbox("0")[1]
    by = 160
    ln(3, by + bh // 2 - 12)
    bx = CODE + cw
    q = int(big.getlength('"'))
    d.text((bx, by - top), '"', font=big, fill=STR)
    D.add("hour", bd, bx + q, by)
    d.text((bx + q + 2 * bw, by - top), ":", font=big, fill=STR)
    D.add("min", bd, bx + q + 3 * bw, by)
    fsec = ttf(MONO_B, 30)
    sd = glyph_set("0123456789", fsec, STR, BG, padx=0)
    xs = bx + q + 5 * bw
    d.text((xs, by + bh - sd[0].height - fsec.getbbox("0")[1]), ":", font=fsec, fill=STR)
    xs += int(fsec.getlength(":"))
    D.add("sec", sd, xs, by + bh - sd[0].height)
    d.text((xs + 2 * sd[0].width, by - top), '",', font=big, fill=STR)

    y = ln(4, by + bh + 14); put(2, y, "day:", PROP); put(7, y, '"', STR)
    hd = glyph_set("0123456789", f, STR, BG, padx=0, cell_w=cw)
    wd = word_set(WEEKDAYS_ID, f, STR, BG, align="left")
    D.add("weekday", wd, CODE + 8 * cw, y + 1)
    xd = CODE + 8 * cw + wd[0].width + cw
    yy = y + 1 + wd[0].height - hd[0].height
    D.add("day", hd, xd, yy)
    d.text((xd + 2 * cw, y), "/", font=f, fill=STR)
    D.add("month", hd, xd + 3 * cw, yy)
    d.text((xd + 5 * cw, y), '",', font=f, fill=STR)
    nums = glyph_set("0123456789", f, NUM, BG, padx=0, cell_w=cw)
    y = ln(5, y + 30); put(2, y, "steps:", PROP)
    D.add("step", nums, CODE + 14 * cw, y + 2, gravity=RIGHT_TOP); put(14, y, ",", FG)
    y = ln(6, y + 30); put(2, y, "bpm:", PROP)
    D.add("heart", nums + [text_rgba("--", f, NUM).convert("RGB")], CODE + 14 * cw, y + 2, gravity=RIGHT_TOP); put(14, y, ",", FG)
    y = ln(7, y + 30); put(0, y, "};", FG)
    y = ln(8, y + 30); put(0, y, "// TODO: istirahat", COM)
    # Status bar.
    d.line((0, 384, SIZE, 384), fill=BLUE, width=2)
    d.text((86, 390), "git:main", font=ttf(MONO, 19), fill=VAR)
    fs = ttf(MONO, 19)
    D.add("battery_level", battery_blocks(6, fs, VAR, (40, 70, 100), BG, prefix="BAT "), 238, 388)
    return D


# ---------------------------------------------------------------- Grafana dashboard
def grafana():
    BG, PANEL, LINE, TXT, MUTED, GREEN, YEL, ORANGE, BLUE = (
        (0, 0, 0), (0, 0, 0), (40, 44, 52), (204, 204, 220), (130, 136, 150),
        (115, 191, 105), (250, 222, 42), (255, 120, 10), (87, 148, 242))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    fl = ttf(MONO, 13)
    D = Design("grafana", "Grafana", bg)

    def panel(x0, y0, x1, y1, title):
        d.rounded_rectangle((x0, y0, x1, y1), radius=4, fill=PANEL, outline=LINE)
        d.text((x0 + 8, y0 + 5), title, font=fl, fill=MUTED)

    # Header: jam + tanggal.
    big = ttf(MONO_B, 72)
    bd = glyph_set("0123456789", big, TXT, BG, padx=0)
    bw = bd[0].width
    colon = int(big.getlength(":")) - 14
    tx = CX - (4 * bw + colon) // 2 - 44
    ty = 64
    D.add("hour", bd, tx, ty)
    d.text((tx + 2 * bw - 7, ty - big.getbbox("0")[1]), ":", font=big, fill=MUTED)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    fd = ttf(MONO, 17)
    wd = word_set(WEEKDAYS_ID, fd, BLUE, BG, align="left")
    dd = glyph_set("0123456789", fd, TXT, BG, padx=0)
    xr = tx + 4 * bw + colon + 14
    D.add("weekday", wd, xr, ty - 2)
    D.add("day", dd, xr, ty + 22)
    d.text((xr + 2 * dd[0].width, ty + 21), "/", font=fd, fill=MUTED)
    D.add("month", dd, xr + 3 * dd[0].width, ty + 22)
    D.add("sec", glyph_set("0123456789", fd, GREEN, BG, padx=0), xr, ty + 46)
    d.text((xr + 2 * dd[0].width + 2, ty + 45), "s", font=fd, fill=MUTED)

    # Panel kiri: gauge target langkah (step_progress 11 frame) + angka langkah.
    panel(58, 156, 228, 316, "Steps / goal")
    gw, gh = 150, 92
    gcx, gcy, r = gw // 2, 82, 66
    frames = []
    for fr in range(11):
        im = Image.new("RGB", (gw, gh), PANEL)
        dr = ImageDraw.Draw(im)
        dr.arc((gcx - r, gcy - r, gcx + r, gcy + r), 180, 360, fill=LINE, width=14)
        if fr:
            col = ORANGE if fr < 4 else YEL if fr < 8 else GREEN
            dr.arc((gcx - r, gcy - r, gcx + r, gcy + r), 180, 180 + 18 * fr, fill=col, width=14)
        frames.append(im)
    D.add("step_progress", frames, 143, 182, gravity=0x0a)
    fn = ttf(MONO_B, 24)
    D.add("step", glyph_set("0123456789", fn, TXT, PANEL, padx=0), 143, 252, gravity=0x0a)
    d.text((126, 282), "steps", font=fl, fill=MUTED)

    # Panel kanan atas: detak jantung + sparkline dekoratif.
    panel(238, 156, 408, 232, "Heart rate")
    fh = ttf(MONO_B, 30)
    D.add("heart", glyph_set("0123456789", fh, GREEN, PANEL, padx=0) + [text_rgba("--", fh, GREEN).convert("RGB")],
          250, 180)
    d.text((330, 196), "bpm", font=fl, fill=MUTED)
    pts = [(350 + k * 6, 212 - 9 * math.sin(k * 1.3) - (14 if k == 5 else 0)) for k in range(9)]
    d.line(pts, fill=(60, 120, 60), width=2)
    # Panel kanan bawah: baterai (bar gauge).
    panel(238, 240, 408, 316, "Battery")
    bars = []
    for lv in range(6):
        im = Image.new("RGB", (150, 22), PANEL)
        dr = ImageDraw.Draw(im)
        dr.rectangle((0, 2, 149, 19), fill=LINE)
        if lv:
            col = ORANGE if lv <= 1 else YEL if lv <= 2 else GREEN
            dr.rectangle((0, 2, int(149 * lv / 5), 19), fill=col)
        bars.append(im)
    D.add("battery_level", bars, 248, 274)
    # Legend / time range bawah.
    d.text((128, 332), "Last 24 hours  ·  refresh 1m", font=fl, fill=MUTED)
    return D


ALL = (json_api, wttr, vscode, grafana)
