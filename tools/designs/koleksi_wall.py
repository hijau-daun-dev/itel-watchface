"""Watch face dari wallpaper (gambar milik user, untuk dipakai sendiri).

kny_zenitsu_anim: wallpaper Zenitsu (latar hitam). Foto statis; yang dianimasikan hanya area
petir di kanan atas (hampir seluruhnya hitam -> frame RLE sangat kecil, tetap ringan).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, word_set

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
YUGO_B = "C:/Windows/Fonts/YuGothB.ttc"


def crop_square(path, cx, top, width):
    """Potong persegi (boleh melewati tepi -> diisi hitam), lalu kecilkan ke 466."""
    src = Image.open(path).convert("RGB")
    x0, y0 = int(cx - width / 2), int(top)
    canvas = Image.new("RGB", (width, width), (0, 0, 0))
    part = src.crop((max(0, x0), max(0, y0), min(src.width, x0 + width), min(src.height, y0 + width)))
    # Tepi foto yang berbatasan dengan area kosong dibuat memudar ke hitam (tanpa garis potong tegas).
    fade = int(width * 0.08)
    mask = Image.new("L", part.size, 255)
    md = ImageDraw.Draw(mask)
    edges = {"top": y0 < 0, "bottom": y0 + width > src.height, "left": x0 < 0, "right": x0 + width > src.width}
    for i in range(fade):
        v = int(255 * i / fade)
        if edges["top"]:
            md.line((0, i, part.width, i), fill=v)
        if edges["bottom"]:
            md.line((0, part.height - 1 - i, part.width, part.height - 1 - i), fill=v)
        if edges["left"]:
            md.line((i, 0, i, part.height), fill=v)
        if edges["right"]:
            md.line((part.width - 1 - i, 0, part.width - 1 - i, part.height), fill=v)
    canvas.paste(part, (max(0, -x0), max(0, -y0)), mask)
    return canvas.resize((SIZE, SIZE), Image.LANCZOS)


def lightning_mask(im, thr=70):
    """Piksel petir: terang dan kekuningan (bukan oranye jubah)."""
    r, g, b = im.split()
    bright = ImageChops.lighter(r, g).point(lambda p: 255 if p > thr else 0)
    yellowish = ImageChops.subtract(g, b).point(lambda p: 255 if p > 25 else 0)
    return ImageChops.multiply(bright, yellowish)


def bolt(d, x0, y0, x1, y1, rnd, col, width=2, depth=0):
    """Petir zig-zag dari (x0,y0) ke (x1,y1) dengan cabang kecil."""
    pts = [(x0, y0)]
    n = 7
    for i in range(1, n):
        t = i / n
        pts.append((x0 + (x1 - x0) * t + rnd.uniform(-9, 9), y0 + (y1 - y0) * t + rnd.uniform(-5, 5)))
    pts.append((x1, y1))
    d.line(pts, fill=col, width=width, joint="curve")
    if depth < 1:
        for _ in range(2):
            px, py = rnd.choice(pts[2:-1])
            bolt(d, px, py, px + rnd.uniform(-30, 30), py + rnd.uniform(15, 35), rnd, col, 1, depth + 1)


def kny_zenitsu_anim():
    GOLD, ORANGE, YEL, DIM, GRAY = (255, 196, 40), (255, 120, 20), (255, 236, 120), (170, 128, 36), (140, 120, 90)
    bg = crop_square(os.path.join(ASSETS, "zenitsu.png"), cx=3180 - (245 - 233) * 1750 / 466, top=402, width=1750)
    d = ImageDraw.Draw(bg)
    D = Design("kny_zenitsu_anim", "Demon Slayer - Zenitsu (animasi)", bg)

    # Animasi petir: area kanan atas.
    box = (300, 0, 446, 166)
    base = bg.crop(box)
    m = lightning_mask(base)
    glow = base.filter(ImageFilter.GaussianBlur(3))
    off = Image.composite(Image.new("RGB", base.size, (0, 0, 0)), base, m.filter(ImageFilter.MaxFilter(5)))
    rnd = random.Random(9)

    def scaled(f):
        return Image.composite(base.point(lambda p: int(p * f)), off, m.filter(ImageFilter.MaxFilter(3)))

    def bright():
        im = ImageChops.add(base, glow)
        return Image.composite(im, off, m.filter(ImageFilter.MaxFilter(5)))

    def new_bolts():
        im = off.copy()
        layer = Image.new("RGB", base.size, (0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for _ in range(2):
            x = rnd.uniform(30, 120)
            bolt(ld, x, 0, x + rnd.uniform(-40, 30), rnd.uniform(110, 160), rnd, YEL, 2)
        im = ImageChops.add(im, layer.filter(ImageFilter.GaussianBlur(3)))
        return ImageChops.lighter(im, layer)

    frames = [base, bright(), base, scaled(0.35), off, new_bolts(), bright(), scaled(0.6)]
    D.add_anim(frames, box[0], box[1], interval=9)

    # Jam di area hitam kiri atas.
    big = bahn(84, "Bold Condensed")
    bd = glyph_set("0123456789", big, GOLD, (0, 0, 0))
    bw, bh = bd[0].width, bd[0].height
    sd = glyph_set("0123456789", bahn(26, "Bold Condensed"), YEL, (0, 0, 0))
    colon = 18
    tx, ty = 200 - (4 * bw + colon + 2 * sd[0].width + 6) // 2, 52
    d.rectangle((tx - 4, ty - 4, tx + 4 * bw + colon + 2 * sd[0].width + 10, ty + bh + 44), fill=(0, 0, 0))
    D.add("hour", bd, tx, ty)
    for yy in (ty + bh * .32, ty + bh * .70):
        d.ellipse((tx + 2 * bw + 5, yy - 4, tx + 2 * bw + 13, yy + 4), fill=ORANGE)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    D.add("sec", sd, tx + 4 * bw + colon + 6, ty + bh - sd[0].height)
    f = bahn(22, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, ORANGE, (0, 0, 0))
    dd = glyph_set("0123456789", f, YEL, (0, 0, 0))
    y = ty + bh + 12
    D.add("weekday", wd, tx + 2, y)
    x = tx + 2 + wd[0].width + 10
    yd = y + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    d.text((x + 2 * dd[0].width + 1, yd - f.getbbox("0")[1]), ".", font=f, fill=GRAY)
    D.add("month", dd, x + 3 * dd[0].width, yd)

    # Tulisan vertikal di kiri: 雷の呼吸 / 霹靂一閃.
    jf = ImageFont.truetype(YUGO_B, 17)
    for col, (xx, s) in enumerate(((66, "雷の呼吸"), (44, "霹靂一閃"))):
        for i, ch in enumerate(s):
            d.text((xx + 18, 140 + i * 20), ch, font=jf, fill=DIM if col == 0 else GOLD)
    return D


ALL = (kny_zenitsu_anim,)
