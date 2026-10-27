"""Watch face bertema One Piece, gaya minimal (bukan artwork/logo resmi; motif digambar sendiri).

op_wanted   poster WANTED versi gelap: jam di bingkai foto, BOUNTY = langkah
op_logpose  analog ala Log Pose / kompas navigasi, jarum menit berujung merah
op_strawhat digital minimal dengan topi jerami line-art
"""
import math

from PIL import Image, ImageDraw, ImageFont

from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, needle, polar, text_rgba, word_set

SERIF_B = "C:/Windows/Fonts/georgiab.ttf"
SERIF = "C:/Windows/Fonts/georgia.ttf"


def serif(n, bold=True):
    return ImageFont.truetype(SERIF_B if bold else SERIF, n)


def spaced(s, font, col, tracking):
    """Teks dengan jarak antar-huruf (tracking) untuk kesan poster/elegan."""
    widths = [font.getlength(ch) for ch in s]
    w = int(sum(widths) + tracking * (len(s) - 1)) + 4
    l, t, r, b = font.getbbox("WANTED")
    im = Image.new("RGBA", (w, b - t + 4), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    x = 2
    for ch, cw in zip(s, widths):
        dr.text((x, -t + 2), ch, font=font, fill=col)
        x += cw + tracking
    return im


def paste_c(bg, im, y):
    bg.paste(im, (CX - im.width // 2, y), im)


# ---------------------------------------------------------------- WANTED (gelap)
def op_wanted():
    BG, PAPER, DIM, RED = (0, 0, 0), (222, 198, 148), (120, 104, 76), (170, 50, 40)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("op_wanted", "One Piece - Wanted", bg)
    # Bingkai poster: garis ganda tipis.
    d.rectangle((102, 52, 364, 414), outline=DIM, width=1)
    d.rectangle((108, 58, 358, 408), outline=PAPER, width=2)
    paste_c(bg, spaced("WANTED", serif(40), PAPER, 5), 70)
    # Bingkai foto berisi jam.
    PX0, PY0, PX1, PY1 = 124, 124, 342, 252
    d.rectangle((PX0, PY0, PX1, PY1), outline=PAPER, width=2)
    big = serif(64)
    bd = glyph_set("0123456789", big, PAPER, BG)
    bw, bh = bd[0].width, bd[0].height
    colon = 18
    sd = glyph_set("0123456789", serif(24), RED, BG)
    total = 4 * bw + colon
    tx, ty = CX - total // 2, (PY0 + PY1) // 2 - bh // 2 - 8
    D.add("hour", bd, tx, ty)
    for yy in (ty + bh * .32, ty + bh * .72):
        d.ellipse((tx + 2 * bw + 5, yy - 4, tx + 2 * bw + 13, yy + 4), fill=PAPER)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    D.add("sec", sd, CX - sd[0].width, ty + bh + 12)
    paste_c(bg, spaced("DEAD OR ALIVE", serif(17), PAPER, 4), 264)
    # Nama = hari + tanggal.
    f = serif(26)
    wd = word_set(WEEKDAYS_ID, f, PAPER, BG)
    dd = glyph_set("0123456789", f, PAPER, BG)
    total = wd[0].width + 12 + 5 * dd[0].width
    x = CX - total // 2
    y = 296
    D.add("weekday", wd, x, y)
    x += wd[0].width + 12
    yd = y + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    d.text((x + 2 * dd[0].width + 2, yd - f.getbbox("0")[1]), ".", font=f, fill=PAPER)
    D.add("month", dd, x + 3 * dd[0].width, yd)
    # Bounty: simbol berry (B dengan dua garis) + langkah, rata kanan di tengah.
    fb = serif(30)
    yb = 344
    sd2 = glyph_set("0123456789", fb, PAPER, BG)
    bx = CX - 62
    D.add("step", sd2, bx + 32, yb)
    d.text((bx, yb - fb.getbbox("0")[1]), "B", font=fb, fill=PAPER)
    for ox in (7, 14):
        d.line((bx + ox, yb - 6, bx + ox, yb + sd2[0].height + 5), fill=PAPER, width=2)
    paste_c(bg, spaced("MARINE", serif(13, False), DIM, 5), 386)
    return D


# ---------------------------------------------------------------- Log Pose (analog navigasi)
def op_logpose():
    BG, GOLD, GOLD_D, CHART, WHITE, RED, GLASS = (0, 0, 0), (212, 176, 100), (130, 104, 56), (18, 40, 46), (236, 232, 222), (200, 50, 40), (60, 90, 100)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    # Peta laut samar: lingkaran lintang + garis rhumb.
    for r in (60, 110, 160, 210):
        d.ellipse((CX - r, CX - r, CX + r, CX + r), outline=CHART, width=1)
    for k in range(16):
        x, y = polar(230, k * 22.5)
        d.line((CX, CX, x, y), fill=CHART, width=1)
    # Tanda menit + jam.
    for m in range(60):
        r1, r2, w, col = (206, 222, 1, GOLD_D) if m % 5 else (198, 222, 3, GOLD)
        if m % 15 == 0:
            continue
        x1, y1 = polar(r1, m * 6); x2, y2 = polar(r2, m * 6)
        d.line((x1, y1, x2, y2), fill=col, width=w)
    f = ImageFont.truetype(SERIF_B, 30)
    for s, deg in (("N", 0), ("E", 90), ("S", 180), ("W", 270)):
        t = text_rgba(s, f, GOLD if s != "N" else RED)
        x, y = polar(204, deg)
        bg.paste(t, (int(x - t.width / 2), int(y - t.height / 2)), t)
    # Mawar angin kecil di tengah + cincin "kaca" Log Pose.
    for k in range(8):
        deg = k * 45
        L = 54 if k % 2 == 0 else 32
        tip = polar(L, deg); l = polar(9, deg - 45); r = polar(9, deg + 45)
        d.polygon([tip, l, (CX, CX)], fill=GOLD_D)
        d.polygon([tip, r, (CX, CX)], fill=(70, 58, 34))
    d.ellipse((CX - 128, CX - 128, CX + 128, CX + 128), outline=GLASS, width=2)
    d.arc((CX - 120, CX - 120, CX + 120, CX + 120), 200, 250, fill=(120, 160, 170), width=3)
    lab = text_rgba("LOG POSE", ImageFont.truetype(SERIF, 13), GOLD_D)
    bg.paste(lab, (CX - lab.width // 2, CX - 92), lab)
    lab2 = text_rgba("GRAND LINE", ImageFont.truetype(SERIF, 13), GOLD_D)
    bg.paste(lab2, (CX - lab2.width // 2, CX + 76), lab2)
    D = Design("op_logpose", "One Piece - Log Pose", bg)
    # Tanggal kecil di bawah tengah.
    dd = glyph_set("0123456789", ImageFont.truetype(SERIF_B, 20), WHITE, BG)
    D.add("day", dd, CX - dd[0].width, CX + 98)
    D.add_needle("needle_hour", needle(112, 14, GOLD, shape="dauphine", edge=GOLD_D))
    # Jarum menit: putih dengan ujung merah (ciri jarum Log Pose).
    img, tail = needle(176, 8, WHITE, shape="sword")
    dr = ImageDraw.Draw(img)
    w = img.width
    dr.polygon([(w / 2, 0), (w / 2 + 4, 40), (w / 2 - 4, 40)], fill=RED)
    D.add_needle("needle_min", (img, tail))
    D.add_needle("needle_sec", needle(196, 2, RED, tail=36))
    return D


# ---------------------------------------------------------------- Topi jerami (digital minimal)
def straw_hat(width):
    """Line-art topi jerami (tampak samping sedikit atas) di gambar RGBA."""
    ss = 4
    W, H = width * ss, int(width * 0.52) * ss
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    STRAW, STRAW_D, BAND = (234, 192, 96, 255), (176, 134, 52, 255), (196, 38, 38, 255)
    cx = W / 2
    # Pinggiran (brim).
    dr.ellipse((0, H * 0.52, W, H * 0.98), fill=STRAW_D)
    dr.ellipse((W * 0.02, H * 0.50, W * 0.98, H * 0.92), fill=STRAW)
    # Mahkota (crown).
    dr.chord((cx - W * 0.27, H * 0.02, cx + W * 0.27, H * 1.02), 180, 360, fill=STRAW)
    dr.rectangle((cx - W * 0.27, H * 0.50, cx + W * 0.27, H * 0.66), fill=STRAW)
    # Pita merah.
    dr.rectangle((cx - W * 0.27, H * 0.44, cx + W * 0.27, H * 0.60), fill=BAND)
    dr.ellipse((cx - W * 0.27, H * 0.56, cx + W * 0.27, H * 0.74), fill=STRAW)
    dr.chord((cx - W * 0.27, H * 0.36, cx + W * 0.27, H * 0.52), 0, 180, fill=BAND)
    # Anyaman halus.
    for k in range(1, 6):
        y = H * (0.10 + k * 0.06)
        dr.arc((cx - W * 0.25, y, cx + W * 0.25, y + H * 0.5), 200, 340, fill=STRAW_D, width=ss)
    return im.resize((width, int(width * 0.52)), Image.LANCZOS)


def op_strawhat():
    BG, WHITE, STRAW, RED, GRAY = (0, 0, 0), (240, 238, 232), (234, 192, 96), (210, 44, 44), (120, 116, 108)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design("op_strawhat", "One Piece - Straw Hat", bg)
    hat = straw_hat(132)
    bg.paste(hat, (CX - hat.width // 2, 62), hat)
    big = bahn(128, "Light Condensed")
    bd = glyph_set("0123456789", big, WHITE, BG, padx=3)
    bw, bh = bd[0].width, bd[0].height
    colon = 26
    tx, ty = CX - (4 * bw + colon) // 2, 158
    D.add("hour", bd, tx, ty)
    for yy in (ty + bh * .32, ty + bh * .70):
        d.ellipse((tx + 2 * bw + 8, yy - 5, tx + 2 * bw + 18, yy + 5), fill=RED)
    D.add("min", bd, tx + 2 * bw + colon, ty)
    f = bahn(24, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, STRAW, BG)
    dd = glyph_set("0123456789", f, WHITE, BG)
    sd = glyph_set("0123456789", f, RED, BG)
    total = wd[0].width + 12 + 5 * dd[0].width + 22 + 2 * sd[0].width
    x = CX - total // 2
    y = ty + bh + 22
    D.add("weekday", wd, x, y)
    x += wd[0].width + 12
    yd = y + wd[0].height - dd[0].height
    D.add("day", dd, x, yd)
    d.text((x + 2 * dd[0].width + 1, yd - f.getbbox("0")[1]), ".", font=f, fill=GRAY)
    D.add("month", dd, x + 3 * dd[0].width, yd)
    x += 5 * dd[0].width + 22
    D.add("sec", sd, x, yd)
    return D


ALL = (op_wanted, op_logpose, op_strawhat)
