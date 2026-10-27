"""Versi beranimasi dari semua watch face anime.

Cara kerja: ambil Design statisnya, lalu sisipkan elemen animasi (bg_dynamic) sebagai elemen
PERTAMA (digambar tepat di atas latar, di bawah jam/tanggal). Frame berupa:
  * objek yang bergerak di atas latar hitam (topi, buah, anting, jubah), atau
  * potongan latar + efek (kilau, denyut, bidikan berputar, tulisan yang ditulis).
"""
import math

from PIL import Image, ImageDraw, ImageFont

import koleksi_anime as KA
import koleksi_op as KO
from wflib import CX, SIZE, text_rgba

FRAMES = 8


def insert_anim(D, frames, x, y, interval=14):
    """Tambah animasi lalu pindahkan ke urutan pertama (di bawah elemen lain)."""
    D.add_anim(frames, x, y, interval=interval)
    D.els.insert(0, D.els.pop())


def erase(D, box):
    """Hapus objek statis dari latar (diganti animasinya)."""
    ImageDraw.Draw(D.bg).rectangle(box, fill=(0, 0, 0))


def crop_frames(D, box, effect):
    """Frame = potongan latar + efek(k, im)."""
    base = D.bg.crop(box)
    out = []
    for k in range(FRAMES):
        im = base.copy()
        effect(k, im)
        out.append(im)
    return out


def glint(im, k, angle_deg=-25, width=26, strength=90, mask=None):
    """Kilau diagonal yang menyapu dari kiri ke kanan."""
    w, h = im.size
    layer = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rectangle((0, 0, width, h * 2), fill=(255, 255, 255, strength))
    layer = layer.rotate(angle_deg, resample=Image.BICUBIC, center=(width // 2, h))
    x = int(-w * 0.6 + (w * 2.2) * k / (FRAMES - 1)) - w // 2
    rgba = im.convert("RGBA")
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    over.paste(layer, (x, -h // 2), layer)
    if mask is not None:
        over.putalpha(Image.composite(over.getchannel("A"), Image.new("L", im.size, 0), mask))
    rgba.alpha_composite(over)
    im.paste(rgba.convert("RGB"))


# ---------------------------------------------------------------- One Piece
def gomu_fruit(W, rot):
    PURPLE, PURPLE_L, PURPLE_D, STEM = (120, 60, 160), (176, 120, 214), (70, 30, 100), (90, 160, 80)
    im, dr, ss = KA.ss_draw(W, W)
    S = W * ss
    c = S / 2
    dr.ellipse((S * .06, S * .14, S * .94, S * .98), fill=PURPLE)
    for (x, y, r) in ((.30, .40, .14), (.62, .36, .12), (.46, .64, .15), (.74, .66, .11), (.24, .70, .10)):
        cx, cy, R = x * S, y * S, r * S
        for k in range(3):
            rr = R * (1 - k * .32)
            a = rot + 30 + k * 40
            dr.arc((cx - rr, cy - rr, cx + rr, cy + rr), a, a + 300, fill=PURPLE_L, width=int(S * .016))
    dr.arc((S * .08, S * .16, S * .92, S * .96), 200, 280, fill=(200, 160, 230), width=int(S * .02))
    dr.ellipse((S * .06, S * .14, S * .94, S * .98), outline=PURPLE_D, width=int(S * .012))
    dr.arc((c - S * .10, S * .00, c + S * .10, S * .18), 90, 360, fill=STEM, width=int(S * .03))
    dr.line((c, S * .16, c, S * .09), fill=STEM, width=int(S * .03))
    return KA.finish(im, W, W)


def op_gomugomu_anim():
    D = KA.op_gomugomu()
    D.name, D.title = "op_gomugomu_anim", "One Piece - Gomu Gomu (animasi)"
    W, X, Y = 150, CX - 75, 46
    erase(D, (X, Y, X + W, Y + W))
    frames = []
    for k in range(FRAMES):
        im = Image.new("RGB", (W, W), (0, 0, 0))
        f = gomu_fruit(W, k * 45)                       # pusaran berputar 360 derajat per siklus
        im.paste(f, (0, 0), f)
        m = f.getchannel("A").point(lambda p: 255 if p > 128 else 0)
        glint(im, k, mask=m, strength=55)
        frames.append(im)
    insert_anim(D, frames, X, Y, interval=16)
    return D


def op_strawhat_anim():
    D = KO.op_strawhat()
    D.name, D.title = "op_strawhat_anim", "One Piece - Straw Hat (animasi)"
    hat = KO.straw_hat(132)
    W, H = 176, 104
    X, Y = CX - W // 2, 50
    erase(D, (CX - 70, 60, CX + 70, 134))
    frames = []
    for k in range(FRAMES):
        ang = 7 * math.sin(k * 2 * math.pi / FRAMES)     # bergoyang tertiup angin
        lift = int(3 * math.sin(k * 2 * math.pi / FRAMES + 1))
        im = Image.new("RGB", (W, H), (0, 0, 0))
        r = hat.rotate(ang, resample=Image.BICUBIC, expand=True)
        im.paste(r, (W // 2 - r.width // 2, H // 2 - r.height // 2 - lift), r)
        frames.append(im)
    insert_anim(D, frames, X, Y, interval=18)
    return D


def op_logpose_anim():
    D = KO.op_logpose()
    D.name, D.title = "op_logpose_anim", "One Piece - Log Pose (animasi)"
    R = 132
    box = (CX - R, CX - R, CX + R, CX + R)

    def eff(k, im):
        d = ImageDraw.Draw(im)
        a0 = k * 360 / FRAMES - 90
        for i, (span, col) in enumerate(((34, (150, 200, 210)), (18, (230, 250, 255)))):
            d.arc((R - 120, R - 120, R + 120, R + 120), a0 - span / 2, a0 + span / 2, fill=col, width=3 + i)

    insert_anim(D, crop_frames(D, box, eff), box[0], box[1], interval=16)
    return D


def op_wanted_anim():
    D = KO.op_wanted()
    D.name, D.title = "op_wanted_anim", "One Piece - Wanted (animasi)"
    box = (112, 258, 354, 290)
    font = KO.serif(17)

    def eff(k, im):
        t = (1 + math.sin(k * 2 * math.pi / FRAMES)) / 2        # 0..1 denyut
        col = tuple(int(a + (b - a) * t) for a, b in zip((222, 198, 148), (220, 60, 50)))
        ImageDraw.Draw(im).rectangle((0, 0, im.width, im.height), fill=(0, 0, 0))
        s = KO.spaced("DEAD OR ALIVE", font, col, 4)
        im.paste(s, (im.width // 2 - s.width // 2, 264 - box[1]), s)

    insert_anim(D, crop_frames(D, box, eff), box[0], box[1], interval=14)
    return D


# ---------------------------------------------------------------- Naruto
def naruto_konoha_anim():
    D = KA.naruto_konoha()
    D.name, D.title = "naruto_konoha_anim", "Naruto - Konoha (animasi)"
    box = (112, 70, 355, 205)
    mask = Image.new("L", (box[2] - box[0], box[3] - box[1]), 0)
    ImageDraw.Draw(mask).rounded_rectangle((2, 2, mask.width - 3, mask.height - 3), radius=10, fill=255)
    insert_anim(D, crop_frames(D, box, lambda k, im: glint(im, k, width=30, strength=110, mask=mask)),
                box[0], box[1], interval=12)
    return D


# ---------------------------------------------------------------- Dragon Ball
def db_scouter_anim():
    D = KA.db_scouter()
    D.name, D.title = "db_scouter_anim", "Dragon Ball - Scouter (animasi)"
    rx, ry, R = 330, 160, 50
    box = (rx - R, ry - R, rx + R, ry + R)
    RED = (255, 60, 50)
    # Hapus bidikan statis dari latar, ganti latar lensa polos + grid.
    base = D.bg.crop(box)
    bd = ImageDraw.Draw(base)
    bd.rectangle((0, 0, base.width, base.height), fill=(0, 34, 14))
    for gx in range(64 - box[0] % 24, base.width, 24):
        pass
    for x in range(-(box[0] - 64) % 24, base.width, 24):
        bd.line((x, 0, x, base.height), fill=(0, 70, 30))
    for y in range(-(box[1] - 92) % 24, base.height, 24):
        bd.line((0, y, base.width, y), fill=(0, 70, 30))
    frames = []
    for k in range(FRAMES):
        im = base.copy()
        d = ImageDraw.Draw(im)
        a0 = k * 90 / FRAMES                         # 4 kaki -> simetri 90 derajat
        c = R
        d.ellipse((c - 26, c - 26, c + 26, c + 26), outline=RED, width=2)
        for j in range(4):
            a = math.radians(a0 + j * 90)
            d.line((c + 14 * math.sin(a), c - 14 * math.cos(a), c + 38 * math.sin(a), c - 38 * math.cos(a)), fill=RED, width=2)
        if k % 2 == 0:
            d.rectangle((c - 3, c - 3, c + 3, c + 3), fill=RED)
        frames.append(im)
    insert_anim(D, frames, box[0], box[1], interval=12)
    return D


# ---------------------------------------------------------------- Attack on Titan
def aot_wings_anim():
    D = KA.aot_wings()
    D.name, D.title = "aot_wings_anim", "Attack on Titan - Wings of Freedom (animasi)"
    erase(D, (CX - 82, 38, CX + 82, 186))
    CLOAK, CLOAK_D = (34, 84, 54), (20, 54, 34)
    FW, FH = 176, 150
    flat = Image.new("RGB", (FW, FH), CLOAK)
    fd = ImageDraw.Draw(flat)
    for x in range(0, FW, 14):
        fd.line((x, 0, x, FH), fill=CLOAK_D)
    emb = KA.wings_of_freedom(120)
    flat.paste(emb, (FW // 2 - emb.width // 2, 14), emb)
    AW, AH, A = FW + 4, FH + 18, 6
    frames = []
    for k in range(FRAMES):
        im = Image.new("RGB", (AW, AH), (0, 0, 0))
        ph = k * 2 * math.pi / FRAMES
        for y in range(FH):                           # jubah: berkibar makin kuat ke bawah
            amp = A * (y / FH)
            dx = int(round(amp * math.sin(y / 30 - ph)))
            row = flat.crop((0, y, FW, y + 1))
            shade = 0.85 + 0.15 * math.cos(y / 30 - ph)
            im.paste(row.point(lambda p, s=shade: int(p * s)), (2 + dx, 4 + y))
        frames.append(im)
    insert_anim(D, frames, CX - AW // 2, 32, interval=14)
    return D


# ---------------------------------------------------------------- Demon Slayer
def hanafuda(W=46, H=72):
    im, dr, ss = KA.ss_draw(W, H)
    dr.rounded_rectangle((0, 0, W * ss - 1, H * ss - 1), radius=8 * ss, fill=(240, 236, 226))
    dr.ellipse((W * ss * .15, H * ss * .14, W * ss * .85, H * ss * .58), fill=(200, 30, 36))
    for k in range(4):
        y = H * ss * (.66 + k * .08)
        dr.line((W * ss * .14, y, W * ss * .86, y), fill=(200, 30, 36), width=2 * ss)
    return KA.finish(im, W, H)


def kny_tanjiro_anim():
    D = KA.kny_tanjiro()
    D.name, D.title = "kny_tanjiro_anim", "Demon Slayer - Tanjiro (animasi)"
    erase(D, (CX - 26, 34, CX + 26, 126))
    card = hanafuda()
    W, H = 110, 104
    px, py = W // 2, 4                                # titik gantung
    frames = []
    for k in range(FRAMES):
        ang = 14 * math.sin(k * 2 * math.pi / FRAMES)  # anting berayun
        im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.line((px, py, px, py + 16), fill=(180, 180, 180, 255), width=2)
        layer.paste(card, (px - card.width // 2, py + 16), card)
        layer = layer.rotate(ang, resample=Image.BICUBIC, center=(px, py))
        im.alpha_composite(layer)
        frames.append(im.convert("RGB"))
    insert_anim(D, frames, CX - W // 2, 34, interval=14)
    return D


# ---------------------------------------------------------------- Death Note
def deathnote_anim():
    D = KA.deathnote()
    D.name, D.title = "deathnote_anim", "Death Note (animasi)"
    font = ImageFont.truetype("C:/Windows/Fonts/georgiai.ttf", 24)
    W, H = 220, 34
    X, Y = CX - W // 2, 352
    name = "KIRA"
    stages = [1, 2, 3, 4, 4, 4, 4, 0]                # tulis per huruf, tahan, lalu hilang
    frames = []
    for k, n in enumerate(stages):
        im = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(im)
        d.line((20, H - 4, W - 20, H - 4), fill=(60, 58, 54), width=1)
        txt = name[:n]
        tw = font.getlength(name)
        x0 = W / 2 - tw / 2
        d.text((x0, 0), txt, font=font, fill=(234, 230, 222))
        if 0 < n < 4:                                 # ujung pena
            xe = x0 + font.getlength(txt)
            d.line((xe + 2, 24, xe + 14, 6), fill=(170, 20, 24), width=2)
        frames.append(im)
    insert_anim(D, frames, X, Y, interval=40)
    return D


ALL = (op_gomugomu_anim, op_strawhat_anim, op_logpose_anim, op_wanted_anim,
       naruto_konoha_anim, db_scouter_anim, aot_wings_anim, kny_tanjiro_anim, deathnote_anim)
