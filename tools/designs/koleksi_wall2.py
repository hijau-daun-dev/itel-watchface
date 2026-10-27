"""Watch face dari 7 wallpaper user (dipakai sendiri). Foto statis + satu animasi kecil yang ringan.

Prinsip ringan: angka tanpa alpha di atas inti hitam polos (dibuat dengan 'bayangan' lembut ke
foto), animasi hanya area kecil yang sebagian besar hitam (RLE kecil).
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from koleksi_wall import ASSETS, bolt, crop_square
from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, word_set

BLACK = (0, 0, 0)
FRAMES = 8


# ---------------------------------------------------------------- utilitas tata letak
def shadow(bg, box, radius=18, fade=22):
    """Bayangan hitam lembut di sekitar box + inti hitam polos (tempat glyph tanpa alpha)."""
    m = Image.new("L", bg.size, 0)
    x0, y0, x1, y1 = box
    ImageDraw.Draw(m).rounded_rectangle((x0 - fade // 2, y0 - fade // 2, x1 + fade // 2, y1 + fade // 2), radius=radius, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(fade / 2))
    bg.paste(Image.composite(Image.new("RGB", bg.size, BLACK), bg, m))
    ImageDraw.Draw(bg).rounded_rectangle(box, radius=radius // 2, fill=BLACK)


def digits(size, col, weight="Bold Condensed"):
    return glyph_set("0123456789", bahn(size, weight), col, BLACK)


def colon_dots(d, x, y, h, col, r=4):
    for yy in (y + h * .32, y + h * .70):
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=col)


def time_row(D, cx, y, size, col, colon_col, sec_col=None, sec_size=26, shadow_it=True, pad=10):
    """Jam horizontal terpusat di cx. Return (x0, x1, tinggi)."""
    bd = digits(size, col)
    bw, bh = bd[0].width, bd[0].height
    sd = digits(sec_size, sec_col) if sec_col else None
    colon = max(16, bw // 3)
    total = 4 * bw + colon + (2 * sd[0].width + 6 if sd else 0)
    x0 = cx - total // 2
    if shadow_it:
        shadow(D.bg, (x0 - pad, y - pad, x0 + total + pad, y + bh + pad))
    d = ImageDraw.Draw(D.bg)
    D.add("hour", bd, x0, y)
    colon_dots(d, x0 + 2 * bw + colon // 2, y, bh, colon_col, r=max(3, bw // 11))
    D.add("min", bd, x0 + 2 * bw + colon, y)
    if sd:
        D.add("sec", sd, x0 + 4 * bw + colon + 6, y + bh - sd[0].height)
    return x0, x0 + total, bh


def time_stack(D, cx, y, size, col, sep_col, sec_col, gap=8, pad=10):
    """Jam bertumpuk: jam di atas menit (untuk area hitam sempit di samping karakter)."""
    bd = digits(size, col)
    bw, bh = bd[0].width, bd[0].height
    x0 = cx - bw
    sd = digits(26, sec_col)
    total_h = 2 * bh + gap + 8 + sd[0].height
    shadow(D.bg, (x0 - pad, y - pad, x0 + 2 * bw + pad, y + total_h + pad))
    d = ImageDraw.Draw(D.bg)
    D.add("hour", bd, x0, y)
    d.rectangle((x0 + 8, y + bh + gap // 2 - 1, x0 + 2 * bw - 8, y + bh + gap // 2 + 1), fill=sep_col)
    D.add("min", bd, x0, y + bh + gap)
    D.add("sec", sd, cx - sd[0].width, y + 2 * bh + gap + 8)
    return x0, y + total_h


def date_row(D, cx, y, col_wd, col_num, size=22, sep=".", shadow_it=True):
    f = bahn(size, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, col_wd, BLACK)
    dd = glyph_set("0123456789", f, col_num, BLACK)
    total = wd[0].width + 10 + 5 * dd[0].width
    x = cx - total // 2
    if shadow_it:
        shadow(D.bg, (x - 8, y - 6, x + total + 8, y + wd[0].height + 6), radius=12, fade=16)
    d = ImageDraw.Draw(D.bg)
    D.add("weekday", wd, x, y)
    x += wd[0].width + 10
    yd = y + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    d.text((x + 2 * dd[0].width + 1, yd - f.getbbox("0")[1]), sep, font=f, fill=col_num)
    D.add("month", dd, x + 3 * dd[0].width, yd)


def add_first(D, frames, x, y, interval):
    D.add_anim(frames, x, y, interval=interval)
    D.els.insert(0, D.els.pop())


# ---------------------------------------------------------------- jenis animasi
def anim_embers(D, box, colors, n=16, seed=1, interval=10, rise=True):
    """Percikan/bara yang naik (atau turun) berulang, di atas potongan latar."""
    rnd = random.Random(seed)
    base = D.bg.crop(box)
    w, h = base.size
    parts = [(rnd.uniform(4, w - 4), rnd.uniform(0, h), rnd.uniform(1.2, 2.6), rnd.choice(colors), rnd.uniform(-6, 6)) for _ in range(n)]
    frames = []
    for k in range(FRAMES):
        layer = Image.new("RGB", (w, h), BLACK)
        ld = ImageDraw.Draw(layer)
        for (x, y, r, col, drift) in parts:
            yy = (y - (k / FRAMES) * h) % h if rise else (y + (k / FRAMES) * h) % h
            xx = x + drift * math.sin(k / FRAMES * 2 * math.pi + y)
            fade = min(1.0, yy / (h * 0.35)) if rise else min(1.0, (h - yy) / (h * 0.35))
            c = tuple(int(v * fade) for v in col)
            ld.ellipse((xx - r, yy - r, xx + r, yy + r), fill=c)
        glow = layer.filter(ImageFilter.GaussianBlur(2.5))
        frames.append(ImageChops.lighter(ImageChops.add(base, glow), layer))
    add_first(D, frames, box[0], box[1], interval)


def anim_lightning(D, box, is_bolt, color, seed=3, interval=9):
    """Petir di area box: terang, berpendar, redup, padam, petir baru (seperti Zenitsu)."""
    base = D.bg.crop(box)
    r, g, b = base.split()
    m = is_bolt(r, g, b)
    glow = base.filter(ImageFilter.GaussianBlur(3))
    # "Padam" = garis petir diredupkan kuat (bukan dihapus), supaya asap/latar di sekitarnya tetap utuh.
    off = Image.composite(base.point(lambda p: int(p * 0.12)), base, m.filter(ImageFilter.MaxFilter(3)))
    rnd = random.Random(seed)

    def scaled(f):
        return Image.composite(base.point(lambda p: int(p * f)), off, m.filter(ImageFilter.MaxFilter(3)))

    bright = Image.composite(ImageChops.add(base, glow), off, m.filter(ImageFilter.MaxFilter(5)))
    layer = Image.new("RGB", base.size, BLACK)
    ld = ImageDraw.Draw(layer)
    for _ in range(2):
        x = rnd.uniform(base.width * .2, base.width * .8)
        bolt(ld, x, 0, x + rnd.uniform(-50, 50), rnd.uniform(base.height * .6, base.height * .95), rnd, color, 2)
    fresh = ImageChops.lighter(ImageChops.add(off, layer.filter(ImageFilter.GaussianBlur(3))), layer)
    frames = [base, bright, base, scaled(0.35), off, fresh, bright, scaled(0.6)]
    add_first(D, frames, box[0], box[1], interval)


def anim_pulse(D, box, thr=150, lo=0.55, hi=1.35, interval=12):
    """Bagian terang (cahaya) di area box berdenyut."""
    base = D.bg.crop(box)
    lum = base.convert("L")
    m = lum.point(lambda p: 0 if p < thr else min(255, (p - thr) * 4))
    frames = []
    for k in range(FRAMES):
        f = lo + (hi - lo) * (1 + math.sin(k * 2 * math.pi / FRAMES)) / 2
        frames.append(Image.composite(base.point(lambda p, f=f: min(255, int(p * f))), base, m))
    add_first(D, frames, box[0], box[1], interval)


# ---------------------------------------------------------------- desain
def jjk_sorcerers_anim():
    D = Design("jjk_sorcerers_anim", "Jujutsu Kaisen - Sorcerers (animasi)", crop_square(os.path.join(ASSETS, "jjk.jpg"), 1920, -380, 2700))
    WHITE, PURPLE, RED, BLUE, ORANGE = (240, 240, 240), (170, 90, 255), (240, 60, 70), (40, 140, 255), (255, 140, 30)
    time_row(D, CX, 46, 70, WHITE, PURPLE, sec_col=ORANGE, sec_size=24)
    date_row(D, CX, 386, BLUE, WHITE)
    # 4 titik warna panel yang menyala bergantian.
    cols = (PURPLE, RED, BLUE, ORANGE)
    W, H = 120, 16
    frames = []
    for k in range(FRAMES):
        im = Image.new("RGB", (W, H), BLACK)
        d = ImageDraw.Draw(im)
        for i, c in enumerate(cols):
            on = i == k % 4
            r = 6 if on else 3
            cc = c if on else tuple(v // 3 for v in c)
            d.ellipse((15 + i * 30 - r, H // 2 - r, 15 + i * 30 + r, H // 2 + r), fill=cc)
        frames.append(im)
    add_first(D, frames, CX - W // 2, 420, 16)
    return D


def bleach_ichigo_anim():
    D = Design("bleach_ichigo_anim", "Bleach - Ichigo (animasi)", crop_square(os.path.join(ASSETS, "ichigo.jpg"), 1920, -120, 2400))
    WHITE, ORANGE, YEL = (240, 238, 232), (255, 130, 20), (255, 210, 80)
    # Jam terbelah oleh pedang api: "10" kiri, "08" kanan.
    bd = digits(80, WHITE)
    bw, bh = bd[0].width, bd[0].height
    y = 300
    shadow(D.bg, (196 - 2 * bw - 8, y - 8, 196 + 8, y + bh + 8))
    shadow(D.bg, (270 - 8, y - 8, 270 + 2 * bw + 8, y + bh + 8))
    D.add("hour", bd, 196 - 2 * bw, y)
    D.add("min", bd, 270, y)
    sd = digits(24, YEL)
    date_f = bahn(20, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, date_f, ORANGE, BLACK)
    dd = glyph_set("0123456789", date_f, WHITE, BLACK)
    yb = y + bh + 12
    shadow(D.bg, (196 - wd[0].width - 2 * dd[0].width - 14, yb - 4, 196 + 6, yb + wd[0].height + 4), radius=10, fade=14)
    D.add("weekday", wd, 196 - wd[0].width - 2 * dd[0].width - 8, yb)
    D.add("day", dd, 196 - 2 * dd[0].width, yb + wd[0].height - dd[0].height)
    shadow(D.bg, (270 - 6, yb - 4, 270 + 2 * sd[0].width + 6, yb + sd[0].height + 4), radius=10, fade=14)
    D.add("sec", sd, 270, yb)
    anim_embers(D, (334, 96, 430, 280), [(255, 150, 30), (255, 210, 80), (255, 90, 20)], n=14, seed=4)
    return D


def op_gear5_anim():
    D = Design("op_gear5_anim", "One Piece - Gear 5 (animasi)", crop_square(os.path.join(ASSETS, "luffy_gear5.jpg"), 1536, 0, 2160))
    WHITE, PURPLE, CYAN = (250, 250, 252), (190, 140, 255), (120, 220, 255)
    # Panel hitam di bawah (gambar penuh warna).
    shadow(D.bg, (96, 318, 370, 432), radius=26, fade=30)
    x0, x1, bh = time_row(D, CX, 326, 64, WHITE, PURPLE, sec_col=CYAN, sec_size=22, shadow_it=False)
    date_row(D, CX - 30, 326 + bh + 10, PURPLE, WHITE, size=19, shadow_it=False)
    # Drums of Liberation: bar ritme di kanan tanggal.
    W, H = 46, 22
    rnd = random.Random(5)
    frames = []
    for k in range(FRAMES):
        im = Image.new("RGB", (W, H), BLACK)
        d = ImageDraw.Draw(im)
        for i in range(5):
            hh = 4 + int((H - 4) * abs(math.sin(k * 0.9 + i * 1.3)))
            d.rectangle((i * 9, H - hh, i * 9 + 5, H), fill=WHITE if i % 2 == 0 else PURPLE)
        frames.append(im)
    add_first(D, frames, CX + 62, 326 + bh + 10, 10)
    return D


def jjk_gojo_purple_anim():
    D = Design("jjk_gojo_purple_anim", "Jujutsu Kaisen - Gojo Hollow Purple (animasi)", crop_square(os.path.join(ASSETS, "gojo1.png"), 2150, 0, 2700))
    WHITE, PURPLE, PINK = (244, 240, 250), (190, 90, 255), (255, 120, 220)
    xs, yend = time_stack(D, 350, 150, 74, WHITE, PURPLE, PINK)
    date_row(D, 350, yend + 16, PURPLE, WHITE, size=20)

    def purple(r, g, b):
        bright = ImageChops.lighter(r, b).point(lambda p: 255 if p > 175 else 0)
        not_green = ImageChops.subtract(b, g).point(lambda p: 255 if p > 30 else 0)
        return ImageChops.multiply(bright, not_green)

    anim_lightning(D, (40, 8, 300, 160), purple, (230, 150, 255), seed=7)
    return D


def kny_tanjiro_fire_anim():
    D = Design("kny_tanjiro_fire_anim", "Demon Slayer - Tanjiro Hinokami (animasi)", crop_square(os.path.join(ASSETS, "tanjiro_fire.jpg"), 1920, 60, 2160))
    WHITE, ORANGE, YEL, GREEN = (240, 238, 232), (255, 120, 30), (255, 210, 90), (40, 160, 100)
    xs, yend = time_stack(D, 388, 122, 66, WHITE, ORANGE, YEL)
    date_row(D, 388, yend + 16, GREEN, WHITE, size=19)
    anim_embers(D, (34, 110, 124, 320), [(255, 140, 30), (255, 200, 80), (255, 80, 20)], n=16, seed=11)
    return D


def jjk_gojo_blindfold_anim():
    D = Design("jjk_gojo_blindfold_anim", "Jujutsu Kaisen - Gojo Blindfold (animasi)", crop_square(os.path.join(ASSETS, "gojo2.jpg"), 2816, 0, 2880))
    WHITE, BLUE, CYAN = (242, 244, 250), (70, 140, 255), (140, 210, 255)
    x0, x1, bh = time_row(D, CX, 286, 80, WHITE, BLUE, sec_col=CYAN, sec_size=26)
    date_row(D, CX, 286 + bh + 18, BLUE, WHITE)
    anim_pulse(D, (226, 132, 330, 196), thr=110, lo=0.4, hi=1.7, interval=12)     # cahaya biru di sisi blindfold
    return D


def jjk_gojo_blue_anim():
    D = Design("jjk_gojo_blue_anim", "Jujutsu Kaisen - Gojo Blue (animasi)", crop_square(os.path.join(ASSETS, "gojo_amoled.jpg"), 2420, 0, 2160))
    WHITE, BLUE, CYAN = (240, 244, 255), (60, 110, 255), (130, 200, 255)
    xs, yend = time_stack(D, 368, 140, 76, WHITE, BLUE, CYAN)
    date_row(D, 368, yend + 16, BLUE, WHITE, size=20)
    anim_embers(D, (300, yend + 50, 420, yend + 120), [(90, 150, 255), (160, 210, 255), (60, 90, 255)], n=12, seed=13, rise=True)
    return D


def anim_flame(D, box, seed=21, interval=8):
    """Api berkobar: piksel api (terang & hangat) digoyang per baris (shimmer), nyala berdenyut,
    plus bara kecil yang naik."""
    base = D.bg.crop(box)
    w, h = base.size
    r, g, b = base.split()
    warm = ImageChops.subtract(r, b).point(lambda p: 255 if p > 60 else 0)
    hot = ImageChops.multiply(warm, r.point(lambda p: 255 if p > 110 else 0)).filter(ImageFilter.MaxFilter(3))
    rnd = random.Random(seed)
    embers = [(rnd.uniform(6, w - 6), rnd.uniform(0, h), rnd.uniform(1, 2.2)) for _ in range(10)]
    frames = []
    for k in range(FRAMES):
        ph = k * 2 * math.pi / FRAMES
        shimmer = Image.new("RGB", (w, h), BLACK)
        for y in range(h):
            amp = 3.2 * (1 - y / h)                      # ujung api (atas) bergoyang paling kuat
            dx = int(round(amp * math.sin(y / 9 + ph)))
            shimmer.paste(base.crop((0, y, w, y + 1)), (dx, y))
        f = 0.85 + 0.25 * (1 + math.sin(ph * 2)) / 2
        shimmer = shimmer.point(lambda p, f=f: min(255, int(p * f)))
        im = Image.composite(shimmer, base, hot)
        layer = Image.new("RGB", (w, h), BLACK)
        ld = ImageDraw.Draw(layer)
        for (x, y, rr) in embers:
            yy = (y - k / FRAMES * h) % h
            fade = min(1.0, yy / (h * 0.4))
            ld.ellipse((x - rr, yy - rr, x + rr, yy + rr), fill=(int(255 * fade), int(150 * fade), int(40 * fade)))
        im = ImageChops.lighter(ImageChops.add(im, layer.filter(ImageFilter.GaussianBlur(2))), layer)
        frames.append(im)
    add_first(D, frames, box[0], box[1], interval)


def op_luffy_fire_anim():
    D = Design("op_luffy_fire_anim", "One Piece - Luffy Tinju Api (animasi)",
               crop_square(os.path.join(ASSETS, "luffy_red.png"), 2150, -270, 2700))
    WHITE, RED, ORANGE, STRAW = (244, 240, 234), (220, 40, 30), (255, 140, 30), (234, 192, 96)
    xs, yend = time_stack(D, 374, 132, 70, WHITE, RED, ORANGE)
    date_row(D, 374, yend + 16, RED, WHITE, size=20)
    # Tulisan vertikal di kiri.
    d = ImageDraw.Draw(D.bg)
    jf = ImageFont.truetype("C:/Windows/Fonts/YuGothB.ttc", 18)
    for i, ch in enumerate("麦わらのルフィ"):
        d.text((46, 158 + i * 21), ch, font=jf, fill=STRAW if i < 4 else RED)
    anim_flame(D, (150, 52, 276, 206))
    return D


ALL = (op_luffy_fire_anim, jjk_sorcerers_anim, bleach_ichigo_anim, op_gear5_anim, jjk_gojo_purple_anim,
       kny_tanjiro_fire_anim, jjk_gojo_blindfold_anim, jjk_gojo_blue_anim)
