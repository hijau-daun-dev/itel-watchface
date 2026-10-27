"""Koleksi watch face ringan untuk itel ISW-O43 -> D:/watch

    python -I designs/koleksi.py [D:/watch]
"""
import json
import math
import os
import shutil
import sys

from PIL import Image, ImageDraw, ImageFilter

from wflib import (CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, needle, polar,
                   radial_gradient, sunburst, text_rgba, word_set)

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else "D:/watch"


# ---------------------------------------------------------------- 1. Noir Gold (analog)
def noir_gold():
    GOLD, GOLD_D = (214, 178, 96), (150, 118, 52)
    bg = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    d = ImageDraw.Draw(bg)
    for m in range(60):
        if m % 5:
            x, y = polar(218, m * 6)
            d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(90, 84, 72))
    for h in range(12):
        deg = h * 30
        if h == 3:
            continue  # tempat jendela tanggal
        widths = [(-5, 5)] if h else [(-13, -4), (4, 13)]
        for a, b in widths:
            pts = []
            for r, off in ((178, a), (178, b), (212, b), (212, a)):
                ang = math.radians(deg)
                x0, y0 = polar(r, deg)
                pts.append((x0 + off * math.cos(ang), y0 + off * math.sin(ang)))
            d.polygon(pts, fill=GOLD)
            d.line(pts[:2] + pts[2:3], fill=GOLD_D, width=1)
    logo = text_rgba("I T E L", bahn(15, "SemiBold"), GOLD)
    bg.paste(logo, (CX - logo.width // 2, 128), logo)
    sub = text_rgba("AUTOMATIC", bahn(11, "Regular"), (120, 112, 96))
    bg.paste(sub, (CX - sub.width // 2, 150), sub)

    # Jendela tanggal di jam 3.
    CREAM = (238, 230, 210)
    digits = glyph_set("0123456789", bahn(26, "SemiBold"), (30, 28, 24), CREAM, cell_w=19, cell_h=30)
    wx, wy = 352, CX - 15
    d.rectangle((wx - 3, wy - 3, wx + 2 * 19 + 2, wy + 30 + 2), outline=GOLD, width=2)
    D = Design("noir_gold", "Noir Gold", bg)
    D.add("day", digits, wx, wy)
    D.add_needle("needle_hour", needle(118, 16, GOLD, shape="dauphine", edge=GOLD_D))
    D.add_needle("needle_min", needle(178, 12, GOLD, shape="dauphine", edge=GOLD_D))
    D.add_needle("needle_sec", needle(196, 3, (200, 60, 50), tail=40))
    return D


# ---------------------------------------------------------------- 2. Chrono Biru (analog sunburst)
def chrono_biru():
    SILVER, LUME, ORANGE = (226, 230, 236), (190, 255, 210), (255, 112, 40)
    base = radial_gradient((40, 78, 150), (6, 16, 40), power=1.2)
    bg = sunburst(base, rays=200, strength=14)
    d = ImageDraw.Draw(bg)
    for m in range(60):
        x0, y0 = polar(222, m * 6); x1, y1 = polar(214 if m % 5 else 206, m * 6)
        d.line([(x0, y0), (x1, y1)], fill=(170, 186, 210) if m % 5 == 0 else (90, 110, 150), width=2 if m % 5 == 0 else 1)
    for h in range(12):
        if h in (3, 12 % 12) and h != 0:
            pass
        if h == 3:
            continue
        deg = h * 30
        r0, r1 = (160, 198) if h else (150, 198)
        w = 7 if h else 10
        ang = math.radians(deg)
        pts = []
        for r, off in ((r0, -w), (r0, w), (r1, w), (r1, -w)):
            x0, y0 = polar(r, deg)
            pts.append((x0 + off * math.cos(ang), y0 + off * math.sin(ang)))
        shadow = [(x + 2, y + 2) for x, y in pts]
        d.polygon(shadow, fill=(4, 10, 26))
        d.polygon(pts, fill=SILVER)
        xm, ym = polar((r0 + r1) / 2 + 4, deg)
        d.ellipse((xm - 3, ym - 3, xm + 3, ym + 3), fill=LUME)
    # Subdial dekoratif di jam 6.
    for r in (44, 43):
        d.ellipse((CX - r, 318 - r, CX + r, 318 + r), outline=(120, 140, 180))
    for k in range(30):
        a = math.radians(k * 12)
        r1 = 36 if k % 5 else 32
        d.line([(CX + 42 * math.sin(a), 318 - 42 * math.cos(a)), (CX + r1 * math.sin(a), 318 - r1 * math.cos(a))],
               fill=(150, 168, 200), width=1)
    t = text_rgba("CHRONO", bahn(13, "SemiBold"), (190, 205, 230))
    bg.paste(t, (CX - t.width // 2, 298 + 14), t)

    WHITE_W, NAVY = (244, 244, 240), (16, 30, 60)
    box = lambda dr, w, h: None
    wd = word_set(WEEKDAYS_ID, bahn(22, "SemiBold"), NAVY, WHITE_W, w=56, h=28)
    days = glyph_set("0123456789", bahn(24, "SemiBold"), NAVY, WHITE_W, cell_w=18, cell_h=28)
    # Bingkai jendela.
    d.rectangle((CX - 30, 108 - 2, CX + 30, 108 + 30), fill=(10, 20, 44)); d.rectangle((CX - 31, 105, CX + 31, 139), outline=SILVER, width=2)
    d.rectangle((346, CX - 16, 346 + 40, CX + 16), outline=SILVER, width=2)
    D = Design("chrono_biru", "Chrono Biru", bg)
    D.add("weekday", wd, CX - 28, 108)
    D.add("day", days, 348, CX - 14)
    D.add_needle("needle_hour", needle(116, 14, SILVER, shape="sword", tip=LUME))
    D.add_needle("needle_min", needle(176, 11, SILVER, shape="sword", tip=LUME))
    D.add_needle("needle_sec", needle(200, 3, ORANGE, tail=46))
    return D


# ---------------------------------------------------------------- 3. Neon Arc (digital)
def neon_arc():
    BLACK, WHITE, TEAL, MAG = (0, 0, 0), (240, 244, 248), (0, 225, 255), (255, 70, 170)
    bg = Image.new("RGB", (SIZE, SIZE), BLACK)
    glow = Image.new("RGB", (SIZE, SIZE), BLACK)
    gd = ImageDraw.Draw(glow)
    start, end = 220, 500  # derajat searah jarum jam dari jam 12 (terbuka di bawah)
    steps = 280
    for k in range(steps):
        t = k / (steps - 1)
        col = tuple(int(TEAL[i] + (MAG[i] - TEAL[i]) * t) for i in range(3))
        a0 = start + (end - start) * k / steps
        x0, y0 = polar(206, a0); x1, y1 = polar(206, a0 + (end - start) / steps + 0.6)
        gd.line([(x0, y0), (x1, y1)], fill=col, width=9)
    bg = Image.blend(glow.filter(ImageFilter.GaussianBlur(7)), glow, 0.6)
    d = ImageDraw.Draw(bg)
    for (deg, col) in ((start, TEAL), (end, MAG)):
        x, y = polar(206, deg)
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=col)

    f_big = bahn(132, "Light Condensed")
    digits = glyph_set("0123456789", f_big, WHITE, BLACK, padx=3)
    dw, dh = digits[0].width, digits[0].height
    colon = 26
    tx = CX - (4 * dw + colon) // 2
    ty = CX - dh // 2 - 6
    for k, yy in enumerate((ty + dh * 0.32, ty + dh * 0.68)):
        col = TEAL if k == 0 else MAG
        d.ellipse((tx + 2 * dw + 8, yy - 5, tx + 2 * dw + 18, yy + 5), fill=col)
    D = Design("neon_arc", "Neon Arc", bg)
    D.add("hour", digits, tx, ty)
    D.add("min", digits, tx + 2 * dw + colon, ty)

    f_s = bahn(30, "SemiBold Condensed")
    D.add("sec", glyph_set("0123456789", f_s, MAG, BLACK), tx + 4 * dw + colon - 2 * glyph_set("0", f_s, MAG, BLACK)[0].width, ty + dh + 10)
    f_d = bahn(26, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f_d, TEAL, BLACK, align="right")
    dd = glyph_set("0123456789", f_d, WHITE, BLACK)
    dot = text_rgba(".", f_d, WHITE)
    total = wd[0].width + 10 + 4 * dd[0].width + dot.width
    x0 = CX - total // 2
    y0 = ty - 46
    D.add("weekday", wd, x0, y0)
    xd = x0 + wd[0].width + 10
    D.add("day", dd, xd, y0 + wd[0].height - dd[0].height)
    bg.paste(dot, (xd + 2 * dd[0].width, y0 + wd[0].height - dot.height), dot)
    D.add("month", dd, xd + 2 * dd[0].width + dot.width, y0 + wd[0].height - dd[0].height)

    f_v = bahn(24, "SemiBold Condensed")
    lab = text_rgba("LANGKAH", bahn(14, "SemiBold Condensed"), (130, 140, 150))
    bg.paste(lab, (CX - lab.width // 2, 352), lab)
    D.add("step", glyph_set("0123456789", f_v, WHITE, BLACK), CX, 370, gravity=0x0a)
    # Baterai: 5 titik.
    dots = []
    for lv in range(6):
        im = Image.new("RGB", (5 * 14, 8), BLACK)
        dr = ImageDraw.Draw(im)
        for k in range(5):
            dr.ellipse((k * 14 + 1, 0, k * 14 + 8, 7), fill=TEAL if k < lv else (50, 56, 62))
        dots.append(im)
    D.add("battery_level", dots, CX - 35, 408)
    D.bg = bg
    return D


# ---------------------------------------------------------------- 4. Retro Flip (digital)
def retro_flip():
    BG, CARD, INK, SPLIT = (0, 0, 0), (240, 231, 212), (34, 32, 36), (200, 190, 170)
    STRIPES = [(232, 93, 53), (245, 166, 35), (246, 209, 82), (64, 160, 150)]
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    for k, col in enumerate(STRIPES):        # garis retro di bawah
        y = 360 + k * 11
        d.rectangle((70, y, 396, y + 6), fill=col)

    CW, CH, GAP = 78, 112, 8

    def card(dr, w, h):
        dr.rounded_rectangle((GAP // 2, 0, w - GAP // 2 - 1, h - 1), radius=12, fill=CARD)
        dr.line([(GAP // 2, h // 2), (w - GAP // 2 - 1, h // 2)], fill=SPLIT, width=2)
        for x in (GAP // 2 + 2, w - GAP // 2 - 4):   # engsel
            dr.rectangle((x, h // 2 - 5, x + 2, h // 2 + 5), fill=BG)

    digits = glyph_set("0123456789", bahn(104, "Bold Condensed"), INK, BG, cell_w=CW + GAP, cell_h=CH, box=card)
    colon = 18
    total = 4 * (CW + GAP) + colon
    tx, ty = CX - total // 2, 168
    for yy in (ty + 38, ty + 74):
        d.ellipse((tx + 2 * (CW + GAP) + 4, yy - 5, tx + 2 * (CW + GAP) + 14, yy + 5), fill=STRIPES[1])
    D = Design("retro_flip", "Retro Flip", bg)
    D.add("hour", digits, tx, ty)
    D.add("min", digits, tx + 2 * (CW + GAP) + colon, ty)

    f = bahn(26, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, STRIPES[2], BG, align="right")
    dd = glyph_set("0123456789", f, CARD, BG)
    slash = text_rgba("/", f, (120, 116, 110))
    total = wd[0].width + 12 + 4 * dd[0].width + slash.width
    x0, y0 = CX - total // 2, 118
    D.add("weekday", wd, x0, y0)
    xd = x0 + wd[0].width + 12
    D.add("day", dd, xd, y0 + wd[0].height - dd[0].height)
    bg.paste(slash, (xd + 2 * dd[0].width, y0 + wd[0].height - slash.height), slash)
    D.add("month", dd, xd + 2 * dd[0].width + slash.width, y0 + wd[0].height - dd[0].height)
    D.add("ampm", word_set(("AM", "PM"), bahn(18, "SemiBold"), STRIPES[0], BG), CX - 52, ty + CH + 16)

    def mini_card(dr, w, h):
        dr.rounded_rectangle((1, 0, w - 2, h - 1), radius=5, fill=(48, 46, 50))
    sec = glyph_set("0123456789", bahn(26, "Bold Condensed"), STRIPES[1], BG, cell_w=22, cell_h=32, box=mini_card)
    D.add("sec", sec, CX + 4, ty + CH + 10)
    return D


# ---------------------------------------------------------------- 5. Terminal (mode programmer)
def terminal():
    # Palet Dracula.
    BG, FG, GREEN, CYAN, PURPLE, YELLOW, PINK, COMMENT = (
        (0, 0, 0), (248, 248, 242), (80, 250, 123), (139, 233, 253), (189, 147, 249),
        (241, 250, 140), (255, 121, 198), (98, 114, 164))
    MONO, MONO_B = "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"
    from wflib import ttf
    f = ttf(MONO, 19)
    fb = ttf(MONO_B, 19)
    cw = int(f.getlength("0"))           # lebar satu karakter monospace
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)

    # Bilah judul jendela terminal.
    d.line((0, 74, SIZE, 74), fill=(40, 42, 54), width=1)
    for k, col in enumerate(((255, 85, 85), (241, 250, 140), (80, 250, 123))):
        d.ellipse((150 + k * 22, 50, 162 + k * 22, 62), fill=col)
    d.text((222, 48), "zsh — isw-o43", font=ttf(MONO, 15), fill=COMMENT)

    X = 78                                # margin kiri teks

    def line(y, parts):
        x = X
        for s, col, font in parts:
            d.text((x, y), s, font=font, fill=col)
            x += int(font.getlength(s))
        return x

    D = Design("terminal", "Terminal", bg)
    D.center_x = BG
    # $ date
    line(92, [("$ ", GREEN, fb), ("~ ", CYAN, fb), ("date", FG, f)])
    y = 118
    wd = word_set(WEEKDAYS_ID, f, YELLOW, BG, align="left")
    D.add("weekday", wd, X, y)
    dd = glyph_set("0123456789", f, FG, BG, padx=0, cell_w=cw)
    xd = X + wd[0].width + cw
    D.add("day", dd, xd, y + wd[0].height - dd[0].height)
    d.text((xd + 2 * cw, y + wd[0].height - dd[0].height - 1), "-", font=f, fill=COMMENT)
    D.add("month", dd, xd + 3 * cw, y + wd[0].height - dd[0].height)
    d.text((xd + 5 * cw, y + wd[0].height - dd[0].height - 1), "  # WIB", font=f, fill=COMMENT)

    # $ time  -> jam besar
    line(150, [("$ ", GREEN, fb), ("~ ", CYAN, fb), ("time ", FG, f), ("--now", PURPLE, f)])
    big = ttf(MONO_B, 88)
    bd = glyph_set("0123456789", big, GREEN, BG, padx=0)
    bw, bh = bd[0].width, bd[0].height
    ty = 182
    D.add("hour", bd, X, ty)
    colon_w = int(big.getlength(":")) - 14
    d.text((X + 2 * bw - 7, ty - big.getbbox("0")[1]), ":", font=big, fill=COMMENT)
    D.add("min", bd, X + 2 * bw + colon_w, ty)
    sf = ttf(MONO_B, 26)
    sd = glyph_set("0123456789", sf, PINK, BG, padx=0)
    xs = X + 4 * bw + colon_w + 8
    d.text((xs, ty + bh - sd[0].height - 2), ":", font=sf, fill=COMMENT)
    D.add("sec", sd, xs + int(sf.getlength(":")), ty + bh - sd[0].height)

    # $ battery -> bar ASCII
    yb = ty + bh + 22
    line(yb, [("battery ", CYAN, f)])
    levels = []
    for lv in range(6):
        s = "[" + "#" * (lv * 2) + "-" * (10 - lv * 2) + "]"
        im = Image.new("RGB", (int(f.getlength(s)) + 2, 22), BG)
        dr = ImageDraw.Draw(im)
        x = 0
        for ch in s:
            col = COMMENT if ch in "[]-" else (GREEN if lv > 1 else PINK)
            dr.text((x, 0), ch, font=f, fill=col)
            x += cw
        levels.append(im)
    D.add("battery_level", levels, X + 8 * cw, yb)
    # steps
    ys = yb + 28
    line(ys, [("steps   ", CYAN, f)])
    D.add("step", glyph_set("0123456789", f, YELLOW, BG, padx=0, cell_w=cw), X + 8 * cw, ys + 2)

    # prompt + kursor
    yc = ys + 34
    x = line(yc, [("$ ", GREEN, fb), ("~ ", CYAN, fb)])
    d.rectangle((x, yc + 2, x + cw - 1, yc + 21), fill=FG)
    d.text((CX - 52, 418), "// exit 0", font=ttf(MONO, 14), fill=COMMENT)
    return D


ANALOG = {"noir_gold", "chrono_biru", "orbit", "orbit_lite"}
GAMING = {"hud_fps", "rpg_status", "blok_anim", "alien_anim", "chomp_anim"}
IT = {"terminal", "binary_clock", "matrix", "htop", "pcb", "bsod", "json_api", "wttr", "vscode", "grafana",
      "build_anim", "rain_anim", "ecg_anim"}
ANIME_PREFIX = ("op_", "naruto_", "db_", "aot_", "kny_", "deathnote", "jjk_", "bleach_")


def category_of(name):
    """Kategori untuk katalog web (dibaca server dari koleksi.json)."""
    if name in ANALOG:
        return "Analog"
    if name.startswith(ANIME_PREFIX):
        return "Anime"
    if name in GAMING:
        return "Gaming"
    if name in IT:
        return "IT & Programmer"
    return "Digital"


def main():
    infos = []
    import koleksi_it
    import koleksi_it2
    import koleksi_anim
    import koleksi_orbit
    import koleksi_game
    import koleksi_op
    import koleksi_anime
    import koleksi_anime2
    import koleksi_wall
    import koleksi_wall2
    import koleksi_wall3
    for fn in (noir_gold, chrono_biru, neon_arc, retro_flip, terminal) + koleksi_it.ALL + koleksi_it2.ALL + koleksi_anim.ALL + koleksi_orbit.ALL + koleksi_game.ALL + (koleksi_anime.op_jollyroger_anim, koleksi_anime.naruto_sharingan_anim) + koleksi_anime2.ALL + koleksi_wall.ALL + koleksi_wall2.ALL + koleksi_wall3.ALL:
        infos.append(fn().build(OUTDIR))
    # Taktis mini + detik (sudah diuji lancar tanpa detik) dari generator terpisah.
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    for ext in ("bin", "png"):
        shutil.copy(os.path.join(src, "taktis_mini_sec." + ext), os.path.join(OUTDIR, "taktis." + ext))
    infos.append({"name": "taktis", "title": "Taktis", "bytes": os.path.getsize(os.path.join(OUTDIR, "taktis.bin"))})
    for info in infos:
        info["category"] = category_of(info["name"])
        info["anim"] = info["name"].endswith("_anim")
    json.dump(infos, open(os.path.join(OUTDIR, "koleksi.json"), "w"), indent=1)
    # Lembar kontak semua desain (grid 6 kolom).
    names = [i["name"] for i in infos]
    cols = 6
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 246 + 10, rows * 266 + 10), (20, 20, 20))
    for k, n in enumerate(names):
        x, y = 10 + (k % cols) * 246, 10 + (k // cols) * 266
        im = Image.open(os.path.join(OUTDIR, n + ".png")).resize((236, 236), Image.LANCZOS)
        sheet.paste(im, (x, y))
        ImageDraw.Draw(sheet).text((x + 4, y + 238), n, fill=(200, 200, 200))
    sheet.save(os.path.join(OUTDIR, "_semua.png"))
    # Latar + metadata untuk watch face DIY Haylou (field "haylou" di koleksi.json).
    import export_haylou
    export_haylou.WATCH = OUTDIR
    export_haylou.main()


if __name__ == "__main__":
    main()
