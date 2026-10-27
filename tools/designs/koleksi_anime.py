"""Watch face anime (motif ikonik digambar sendiri, bukan artwork/logo resmi).

One Piece : op_jollyroger_anim, op_gomugomu
Naruto    : naruto_sharingan_anim, naruto_konoha
Dragon Ball: db_scouter
AoT       : aot_wings
Kimetsu   : kny_tanjiro
Death Note: deathnote
"""
import math

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, text_rgba, ttf, word_set

YUGO_B = "C:/Windows/Fonts/YuGothB.ttc"
SERIF_B, SERIF_BI = "C:/Windows/Fonts/georgiab.ttf", "C:/Windows/Fonts/georgiaz.ttf"
IMPACT = "C:/Windows/Fonts/impact.ttf"
MONO_B = "C:/Windows/Fonts/consolab.ttf"


def jp(n):
    return ImageFont.truetype(YUGO_B, n)


def ss_draw(w, h, ss=4):
    im = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), ss


def finish(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def time_block(D, d, font, col, colon_col, BG, cy, sec_font=None, sec_col=None, colon_dots=True, cx=CX, padx=2):
    """Jam besar terpusat (+ detik kecil kanan bawah). Return (x_kiri, tinggi)."""
    bd = glyph_set("0123456789", font, col, BG, padx=padx)
    bw, bh = bd[0].width, bd[0].height
    colon = max(16, bw // 3)
    sd = glyph_set("0123456789", sec_font, sec_col, BG, padx=0) if sec_font else None
    extra = 2 * sd[0].width + 8 if sd else 0
    tx = cx - (4 * bw + colon + extra) // 2
    D.add("hour", bd, tx, cy)
    if colon_dots:
        r = max(3, bw // 12)
        for yy in (cy + bh * .32, cy + bh * .70):
            d.ellipse((tx + 2 * bw + colon // 2 - r, yy - r, tx + 2 * bw + colon // 2 + r, yy + r), fill=colon_col)
    D.add("min", bd, tx + 2 * bw + colon, cy)
    if sd:
        D.add("sec", sd, tx + 4 * bw + colon + 8, cy + bh - sd[0].height)
    return tx, bh


def date_line(D, d, font, cy, wd_col, num_col, sep_col, BG, sep=".", cx=CX):
    wd = word_set(WEEKDAYS_ID, font, wd_col, BG)
    dd = glyph_set("0123456789", font, num_col, BG)
    total = wd[0].width + 12 + 5 * dd[0].width
    x = cx - total // 2
    D.add("weekday", wd, x, cy)
    x += wd[0].width + 12
    yd = cy + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    d.text((x + 2 * dd[0].width + 1, yd - font.getbbox("0")[1]), sep, font=font, fill=sep_col)
    D.add("month", dd, x + 3 * dd[0].width, yd)


def paste_c(bg, im, y, x=None):
    bg.paste(im, ((CX if x is None else x) - im.width // 2, y), im)


# ================================================================ ONE PIECE
def skull_strawhat(size, col=(245, 245, 240), hat=(234, 192, 96), band=(200, 40, 40), bg_col=(0, 0, 0)):
    """Tengkorak bertopi jerami + tulang bersilang (gaya fan, digambar ulang)."""
    W = H = size
    im, d, ss = ss_draw(W, H)
    S = W * ss
    c = S / 2
    # Tulang bersilang.
    for sgn in (1, -1):
        x0, y0, x1, y1 = c - S * .36, c + sgn * S * .30, c + S * .36, c - sgn * S * .08
        d.line((x0, y0, x1, y1), fill=col, width=int(S * .07))
        for (x, y) in ((x0, y0), (x1, y1)):
            for o in (-1, 1):
                d.ellipse((x - S * .05 + o * S * .03, y - S * .05 - o * S * .03, x + S * .05 + o * S * .03, y + S * .05 - o * S * .03), fill=col)
    # Tengkorak.
    d.ellipse((c - S * .22, c - S * .26, c + S * .22, c + S * .14), fill=col)
    d.rounded_rectangle((c - S * .13, c + S * .04, c + S * .13, c + S * .22), radius=S * .03, fill=col)
    for o in (-1, 1):
        d.ellipse((c + o * S * .10 - S * .065, c - S * .10, c + o * S * .10 + S * .065, c + S * .02), fill=bg_col)
    d.polygon([(c, c + S * .03), (c - S * .03, c + S * .09), (c + S * .03, c + S * .09)], fill=bg_col)
    for k in range(-2, 3):
        d.line((c + k * S * .045, c + S * .14, c + k * S * .045, c + S * .21), fill=bg_col, width=int(S * .012))
    # Topi jerami di atas tengkorak.
    d.ellipse((c - S * .36, c - S * .30, c + S * .36, c - S * .14), fill=(176, 134, 52))
    d.ellipse((c - S * .35, c - S * .31, c + S * .35, c - S * .17), fill=hat)
    d.chord((c - S * .20, c - S * .48, c + S * .20, c - S * .12), 180, 360, fill=hat)
    d.rectangle((c - S * .20, c - S * .33, c + S * .20, c - S * .26), fill=band)
    return finish(im, W, H)


def op_jollyroger_anim():
    BG, WHITE, STRAW, RED, GRAY, FLAG = (0, 0, 0), (240, 238, 232), (234, 192, 96), (210, 44, 44), (120, 116, 108), (26, 26, 28)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("op_jollyroger_anim", "One Piece - Jolly Roger (animasi)", bg)
    # Bendera berkibar: gambar datar lalu tiap kolom digeser sinus (8 frame).
    FW, FH = 210, 140
    flat = Image.new("RGB", (FW, FH), FLAG)
    sk = skull_strawhat(124, bg_col=FLAG)
    flat.paste(sk, (FW // 2 - 62, FH // 2 - 66), sk)
    AW, AH, A = FW + 8, FH + 24, 9
    PX = CX - AW // 2 + 10
    d.line((PX - 6, 54, PX - 6, 240), fill=(150, 120, 80), width=5)          # tiang
    d.ellipse((PX - 11, 48, PX - 1, 58), fill=STRAW)
    frames = []
    for k in range(8):
        im = Image.new("RGB", (AW, AH), BG)
        ph = k * 2 * math.pi / 8
        for x in range(FW):
            amp = A * (x / FW)                    # dekat tiang diam, ujung berkibar
            dy = int(round(amp * math.sin(x / 34 - ph)))
            col = flat.crop((x, 0, x + 1, FH))
            shade = 0.82 + 0.18 * math.cos(x / 34 - ph)
            col = col.point(lambda p, s=shade: int(p * s))
            im.paste(col, (x, 12 + dy))
        frames.append(im)
    D.add_anim(frames, PX, 58, interval=14)
    paste_c(bg, text_rgba("M U G I W A R A", bahn(16, "SemiBold"), STRAW), 234)
    tx, bh = time_block(D, d, bahn(96, "Bold Condensed"), WHITE, RED, BG, 260, bahn(28, "Bold Condensed"), RED)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 260 + bh + 14, STRAW, WHITE, GRAY, BG)
    return D


def op_gomugomu():
    BG, WHITE, PURPLE, PURPLE_L, PURPLE_D, STEM, GRAY, STRAW = (
        (0, 0, 0), (240, 238, 232), (120, 60, 160), (176, 120, 214), (70, 30, 100), (90, 160, 80), (120, 116, 108), (234, 192, 96))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("op_gomugomu", "One Piece - Gomu Gomu", bg)
    # Buah iblis: bulat ungu dengan pola pusaran + tangkai keriting.
    W = 150
    im, dr, ss = ss_draw(W, W)
    S = W * ss
    c = S / 2
    dr.ellipse((S * .06, S * .14, S * .94, S * .98), fill=PURPLE)
    for (x, y, r) in ((.30, .40, .14), (.62, .36, .12), (.46, .64, .15), (.74, .66, .11), (.24, .70, .10)):
        cx, cy, R = x * S, y * S, r * S
        for k in range(3):
            rr = R * (1 - k * .32)
            dr.arc((cx - rr, cy - rr, cx + rr, cy + rr), 30 + k * 40, 330 + k * 40, fill=PURPLE_L, width=int(S * .016))
    dr.arc((S * .08, S * .16, S * .92, S * .96), 200, 280, fill=(200, 160, 230), width=int(S * .02))
    dr.ellipse((S * .06, S * .14, S * .94, S * .98), outline=PURPLE_D, width=int(S * .012))
    # Tangkai keriting.
    dr.arc((c - S * .10, S * .00, c + S * .10, S * .18), 90, 360, fill=STEM, width=int(S * .03))
    dr.line((c, S * .16, c, S * .09), fill=STEM, width=int(S * .03))
    fruit = finish(im, W, W)
    bg.paste(fruit, (CX - W // 2, 46), fruit)
    tx, bh = time_block(D, d, bahn(104, "Bold Condensed"), WHITE, PURPLE_L, BG, 210, bahn(28, "Bold Condensed"), PURPLE_L)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 210 + bh + 12, PURPLE_L, WHITE, GRAY, BG)
    q = text_rgba("海賊王に俺はなる", jp(20), STRAW)
    paste_c(bg, q, 210 + bh + 52)
    return D


# ================================================================ NARUTO
def sharingan(size, rot):
    W = size
    im, d, ss = ss_draw(W, W)
    S = W * ss
    c = S / 2
    d.ellipse((0, 0, S - 1, S - 1), fill=(20, 0, 0))
    d.ellipse((S * .03, S * .03, S * .97, S * .97), fill=(190, 16, 24))
    d.ellipse((S * .10, S * .10, S * .90, S * .90), fill=(214, 28, 36))
    R = S * .30
    d.ellipse((c - R, c - R, c + R, c + R), outline=(60, 0, 4), width=int(S * .018))
    d.ellipse((c - S * .11, c - S * .11, c + S * .11, c + S * .11), fill=(8, 0, 0))
    for k in range(3):
        a0 = rot + k * 120
        # Tomoe = kepala bulat + ekor meruncing yang melengkung ke luar cincin (bentuk koma).
        head = S * .075
        for t in range(28):
            u = t / 27
            ang = math.radians(a0 - u * 55)
            rr = R + S * .02 + u * S * .07
            r = head * (1 - u) ** 1.3
            x, y = c + rr * math.sin(ang), c - rr * math.cos(ang)
            if r > 0.5:
                d.ellipse((x - r, y - r, x + r, y + r), fill=(8, 0, 0))
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse((S * .22, S * .16, S * .42, S * .30), fill=(255, 255, 255, 70))
    im.alpha_composite(hl)
    return finish(im, W, W)


def naruto_sharingan_anim():
    BG, WHITE, RED, GRAY = (0, 0, 0), (236, 236, 236), (214, 28, 36), (120, 120, 124)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("naruto_sharingan_anim", "Naruto - Sharingan (animasi)", bg)
    E = 156
    frames = []
    for k in range(8):
        im = Image.new("RGB", (E, E), BG)
        eye = sharingan(E, k * 15)              # 3 tomoe -> 120 derajat berulang
        im.paste(eye, (0, 0), eye)
        frames.append(im)
    D.add_anim(frames, CX - E // 2, 44, interval=10)
    tx, bh = time_block(D, d, bahn(96, "Bold Condensed"), WHITE, RED, BG, 220, bahn(28, "Bold Condensed"), RED)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 220 + bh + 14, RED, WHITE, GRAY, BG)
    paste_c(bg, text_rgba("写輪眼", jp(18), (110, 30, 34)), 220 + bh + 54)
    return D


def konoha_leaf(size, col):
    """Simbol daun Konoha versi sederhana: spiral searah jarum jam yang ujung luarnya
    menjadi ujung daun runcing (kanan atas), plus tangkai pendek di kiri bawah."""
    W = size
    im, d, ss = ss_draw(W, W)
    S = W * ss
    c = S / 2
    w = int(S * .075)
    cx, cy = c - S * .04, c + S * .06
    pts = []
    turns = 1.55
    for t in range(0, 101):
        u = t / 100
        th = u * turns * 2 * math.pi
        r = S * (.03 + .27 * u)
        pts.append((cx + r * math.cos(th + math.pi), cy + r * math.sin(th + math.pi)))
    d.line(pts, fill=col, width=w, joint="curve")
    for x, y in pts[::4]:
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=col)
    ex, ey = pts[-1]
    tip = (c + S * .44, c - S * .42)
    d.polygon([(ex - w * .6, ey - w * .2), tip, (ex + w * .5, ey + w * .9)], fill=col)
    d.line((cx - S * .22, cy + S * .22, cx - S * .36, cy + S * .36), fill=col, width=w)
    return finish(im, W, W)


def naruto_konoha():
    BG, CLOTH, CLOTH_D, METAL, METAL_D, ENGR, WHITE, ORANGE, GRAY = (
        (0, 0, 0), (24, 38, 84), (14, 22, 52), (196, 202, 210), (120, 126, 136), (52, 56, 64), (236, 236, 236), (255, 140, 30), (120, 120, 124))
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("naruto_konoha", "Naruto - Konoha", bg)
    # Kain ikat kepala selebar layar + pelat logam.
    d.rectangle((0, 78, SIZE, 196), fill=CLOTH)
    for y in range(80, 196, 6):
        d.line((0, y, SIZE, y), fill=CLOTH_D)
    PX0, PY0, PX1, PY1 = 112, 70, 354, 204
    plate = Image.new("RGB", (PX1 - PX0, PY1 - PY0))
    for y in range(plate.height):
        t = y / plate.height
        ImageDraw.Draw(plate).line((0, y, plate.width, y), fill=tuple(int(METAL[i] - (METAL[i] - METAL_D[i]) * t * .8) for i in range(3)))
    bg.paste(plate, (PX0, PY0))
    d.rounded_rectangle((PX0, PY0, PX1, PY1), radius=10, outline=METAL_D, width=3)
    for (x, y) in ((PX0 + 14, PY0 + 14), (PX1 - 14, PY0 + 14), (PX0 + 14, PY1 - 14), (PX1 - 14, PY1 - 14)):
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=METAL_D)
        d.ellipse((x - 2, y - 3, x + 1, y), fill=(230, 232, 236))
    leaf = konoha_leaf(110, ENGR)
    bg.paste(leaf, (CX - 55, PY0 + 12), leaf)
    tx, bh = time_block(D, d, bahn(92, "Bold Condensed"), WHITE, ORANGE, BG, 226, bahn(28, "Bold Condensed"), ORANGE)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 226 + bh + 14, ORANGE, WHITE, GRAY, BG)
    paste_c(bg, text_rgba("木ノ葉隠れの里", jp(16), (90, 96, 120)), 226 + bh + 52)
    return D


# ================================================================ DRAGON BALL
def db_scouter():
    BG, LENS, GRID, GREEN, GREEN_L, RED, YEL = (0, 0, 0), (0, 34, 14), (0, 70, 30), (60, 255, 110), (170, 255, 190), (255, 60, 50), (255, 220, 60)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("db_scouter", "Dragon Ball - Scouter", bg)
    # Lensa scouter (persegi panjang miring sudut) hijau gelap + grid.
    L0, T0, R0, B0 = 64, 92, 402, 360
    d.polygon([(L0 + 30, T0), (R0, T0), (R0, B0 - 40), (R0 - 40, B0), (L0, B0), (L0, T0 + 30)], fill=LENS)
    for x in range(L0, R0, 24):
        d.line((x, T0, x, B0), fill=GRID)
    for y in range(T0, B0, 24):
        d.line((L0, y, R0, y), fill=GRID)
    d.polygon([(L0 + 30, T0), (R0, T0), (R0, B0 - 40), (R0 - 40, B0), (L0, B0), (L0, T0 + 30)], outline=GREEN, width=2)
    # Reticle target.
    rx, ry = 330, 160
    d.ellipse((rx - 26, ry - 26, rx + 26, ry + 26), outline=RED, width=2)
    d.line((rx - 36, ry, rx - 14, ry), fill=RED, width=2); d.line((rx + 14, ry, rx + 36, ry), fill=RED, width=2)
    d.line((rx, ry - 36, rx, ry - 14), fill=RED, width=2); d.line((rx, ry + 14, rx, ry + 36), fill=RED, width=2)
    f = ImageFont.truetype(MONO_B, 16)
    d.text((L0 + 40, T0 + 14), "SCOUTER v2", font=f, fill=GREEN)
    # Elemen dinamis di atas warna lensa (glyph pakai latar LENS).
    tx, bh = time_block(D, d, ImageFont.truetype(MONO_B, 72), GREEN_L, GREEN, LENS, 150, ImageFont.truetype(MONO_B, 24), YEL,
                        cx=CX - 30, padx=0)
    d.text((L0 + 40, 254), "POWER LEVEL", font=f, fill=GREEN)
    D.add("step", glyph_set("0123456789", ImageFont.truetype(MONO_B, 34), YEL, LENS, padx=0), L0 + 40, 278)
    wd = word_set(WEEKDAYS_ID, f, GREEN, LENS)
    D.add("weekday", wd, 290, 262)
    dd = glyph_set("0123456789", f, GREEN_L, LENS, padx=0)
    D.add("day", dd, 290, 286)
    d.text((290 + 2 * dd[0].width + 2, 285), "/", font=f, fill=GREEN)
    D.add("month", dd, 290 + 3 * dd[0].width + 10, 286)
    # Bola naga bintang empat kecil di bawah.
    W = 46
    im, dr, ss = ss_draw(W, W)
    S = W * ss
    dr.ellipse((0, 0, S - 1, S - 1), fill=(255, 150, 20))
    dr.ellipse((S * .15, S * .10, S * .45, S * .35), fill=(255, 230, 160))
    for (x, y) in ((.38, .40), (.62, .40), (.38, .64), (.62, .64)):
        cx, cy, r = x * S, y * S, S * .1
        pts = [(cx + (r if i % 2 == 0 else r * .45) * math.sin(math.radians(i * 36)),
                cy - (r if i % 2 == 0 else r * .45) * math.cos(math.radians(i * 36))) for i in range(10)]
        dr.polygon(pts, fill=(220, 30, 30))
    ball = finish(im, W, W)
    bg.paste(ball, (CX - W // 2, 380), ball)
    return D


# ================================================================ ATTACK ON TITAN
def wings_of_freedom(size):
    W, H = size, int(size * .9)
    im, d, ss = ss_draw(W, H)
    S, Hs = W * ss, H * ss
    c = S / 2
    BROWN, BROWN_L, BLUE, WHITE = (120, 86, 52), (150, 112, 70), (40, 84, 170), (238, 238, 238)
    shield = [(S * .14, Hs * .04), (S * .86, Hs * .04), (S * .86, Hs * .60), (c, Hs * .98), (S * .14, Hs * .60)]
    d.polygon(shield, fill=BROWN)
    d.polygon([(S * .18, Hs * .08), (S * .82, Hs * .08), (S * .82, Hs * .58), (c, Hs * .92), (S * .18, Hs * .58)], fill=BROWN_L)

    def feather(root, ang, length, width, col):
        # Bulu = elips memanjang yang diputar, berakar di `root`.
        a = math.radians(ang)
        pts = []
        for t in range(24):
            u = t / 23 * 2 * math.pi
            x = (math.cos(u) + 1) / 2 * length
            y = math.sin(u) * width / 2 * (1 - 0.6 * (math.cos(u) + 1) / 2)
            pts.append((root[0] + x * math.cos(a) - y * math.sin(a), root[1] + x * math.sin(a) + y * math.cos(a)))
        d.polygon(pts, fill=col)

    root_y = Hs * .70
    # Sayap kiri putih (mengarah kiri atas), sayap kanan biru (mengarah kanan atas), saling menyilang di tengah.
    for k, (ang, ln) in enumerate(((-128, .66), (-146, .64), (-164, .58), (-182, .48))):
        feather((c + S * .06, root_y - k * Hs * .03), ang, S * ln, Hs * .17, WHITE)
    for k, (ang, ln) in enumerate(((-52, .66), (-34, .64), (-16, .58), (2, .48))):
        feather((c - S * .06, root_y - k * Hs * .03), ang, S * ln, Hs * .17, BLUE)
    out = finish(im, W, H)
    # Potong sayap supaya tetap di dalam perisai.
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(x / ss, y / ss) for x, y in shield], fill=255)
    clipped = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    clipped.paste(out, (0, 0), m)
    return clipped


def aot_wings():
    BG, WHITE, BLUE, BROWN, GRAY = (0, 0, 0), (236, 236, 236), (90, 130, 210), (176, 132, 84), (120, 120, 124)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("aot_wings", "Attack on Titan - Wings of Freedom", bg)
    emb = wings_of_freedom(158)
    bg.paste(emb, (CX - emb.width // 2, 40), emb)
    tx, bh = time_block(D, d, bahn(96, "Bold Condensed"), WHITE, BLUE, BG, 196, bahn(28, "Bold Condensed"), BLUE)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 196 + bh + 14, BROWN, WHITE, GRAY, BG)
    paste_c(bg, text_rgba("S U R V E Y   C O R P S", bahn(15, "SemiBold"), GRAY), 196 + bh + 52)
    paste_c(bg, text_rgba("心臓を捧げよ", jp(16), (90, 110, 160)), 196 + bh + 76)
    return D


# ================================================================ DEMON SLAYER
def kny_tanjiro():
    BG, GREEN, BLACK, WHITE, RED, GRAY = (0, 0, 0), (32, 140, 90), (0, 0, 0), (236, 236, 236), (210, 40, 40), (120, 120, 124)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("kny_tanjiro", "Demon Slayer - Tanjiro", bg)
    # Pita kotak-kotak haori (diagonal) di bawah layar.
    band = Image.new("RGB", (SIZE * 2, 120), BLACK)
    bd_ = ImageDraw.Draw(band)
    C = 30
    for x in range(0, band.width, C):
        for y in range(0, band.height, C):
            if (x // C + y // C) % 2 == 0:
                bd_.rectangle((x, y, x + C - 1, y + C - 1), fill=GREEN)
    band = band.rotate(-12, resample=Image.NEAREST, expand=True)
    mask = Image.new("L", band.size, 0)
    ImageDraw.Draw(mask).rectangle((0, band.height // 2 - 48, band.width, band.height // 2 + 48), fill=255)
    bg.paste(band, (CX - band.width // 2, 360 - band.height // 2), mask)
    # Anting hanafuda: kartu putih dengan matahari merah dan garis.
    W, H = 46, 72
    im, dr, ss = ss_draw(W, H)
    dr.rounded_rectangle((0, 0, W * ss - 1, H * ss - 1), radius=8 * ss, fill=(240, 236, 226))
    dr.ellipse((W * ss * .15, H * ss * .14, W * ss * .85, H * ss * .58), fill=(200, 30, 36))
    for k in range(4):
        y = H * ss * (.66 + k * .08)
        dr.line((W * ss * .14, y, W * ss * .86, y), fill=(200, 30, 36), width=2 * ss)
    card = finish(im, W, H)
    d.line((CX, 36, CX, 52), fill=(180, 180, 180), width=2)
    bg.paste(card, (CX - W // 2, 52), card)
    # Kanji 滅 di samping jam.
    tx, bh = time_block(D, d, bahn(100, "Bold Condensed"), WHITE, RED, BG, 146, bahn(28, "Bold Condensed"), GREEN)
    date_line(D, d, bahn(22, "SemiBold Condensed"), 146 + bh + 12, GREEN, WHITE, GRAY, BG)
    k = text_rgba("滅", jp(40), WHITE)
    paste_c(bg, k, 146 + bh + 46)
    return D


# ================================================================ DEATH NOTE
def deathnote():
    BG, WHITE, GRAY, RED, DIM = (0, 0, 0), (234, 230, 222), (110, 106, 100), (170, 20, 24), (60, 58, 54)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("deathnote", "Death Note", bg)
    title_f = ImageFont.truetype(SERIF_BI, 40)
    # Judul dengan jarak huruf.
    s = "DEATH NOTE"
    widths = [title_f.getlength(ch) for ch in s]
    total = sum(widths) + 4 * (len(s) - 1)
    x = CX - total / 2
    for ch, w in zip(s, widths):
        d.text((x, 70), ch, font=title_f, fill=WHITE)
        x += w + 4
    d.line((110, 126, 356, 126), fill=DIM, width=1)
    d.text((CX - 86, 134), "HOW TO USE IT", font=ImageFont.truetype(SERIF_B, 16), fill=GRAY)
    tx, bh = time_block(D, d, ImageFont.truetype(SERIF_B, 84), WHITE, RED, BG, 172, ImageFont.truetype(SERIF_B, 24), RED,
                        colon_dots=True)
    date_line(D, d, ImageFont.truetype(SERIF_B, 22), 172 + bh + 16, RED, WHITE, GRAY, BG)
    rules = ["The human whose name is written", "in this note shall die."]
    rf = ImageFont.truetype("C:/Windows/Fonts/georgiai.ttf", 15)
    for k, line in enumerate(rules):
        t = text_rgba(line, rf, GRAY)
        paste_c(bg, t, 172 + bh + 58 + k * 20)
    # Apel merah kecil (aksen).
    W = 30
    im, dr, ss = ss_draw(W, W)
    S = W * ss
    dr.ellipse((S * .05, S * .18, S * .55, S * .95), fill=RED)
    dr.ellipse((S * .45, S * .18, S * .95, S * .95), fill=RED)
    dr.line((S * .5, S * .25, S * .55, S * .02), fill=(90, 60, 30), width=2 * ss)
    dr.ellipse((S * .55, S * .02, S * .85, S * .16), fill=(60, 120, 50))
    apple = finish(im, W, W)
    bg.paste(apple, (CX - W // 2, 404), apple)
    return D


ALL = (op_jollyroger_anim, op_gomugomu, naruto_sharingan_anim, naruto_konoha, db_scouter, aot_wings, kny_tanjiro, deathnote)
