"""Versi *_info_anim dari watch face wallpaper: + persen baterai, langkah, BPM.

Tidak mengubah desain aslinya: memanggil fungsi asli lalu menambah blok info (nama baru).
Catatan: elemen 'battery' (tipe 18, angka persen) belum pernah terlihat di watch face resmi;
uji dulu zz_tes_baterai.bin di jam.
"""
from PIL import Image, ImageDraw

import koleksi_wall as Z
import koleksi_wall2 as W
from wflib import CX, bahn, glyph_set

BLACK = (0, 0, 0)


def icon(d, kind, x, y, s, col):
    """Ikon kecil: baterai, langkah (jejak kaki), hati."""
    if kind == "bat":
        d.rounded_rectangle((x, y + s * .22, x + s * .86, y + s * .78), radius=2, outline=col, width=2)
        d.rectangle((x + s * .86, y + s * .4, x + s, y + s * .6), fill=col)
        d.rectangle((x + 3, y + s * .22 + 3, x + s * .55, y + s * .78 - 3), fill=col)
    elif kind == "step":
        d.ellipse((x + s * .05, y + s * .30, x + s * .40, y + s * .92), fill=col)
        d.ellipse((x + s * .50, y + s * .05, x + s * .85, y + s * .67), fill=col)
    else:  # heart
        d.ellipse((x, y + s * .12, x + s * .55, y + s * .62), fill=col)
        d.ellipse((x + s * .45, y + s * .12, x + s, y + s * .62), fill=col)
        d.polygon([(x + s * .02, y + s * .45), (x + s * .98, y + s * .45), (x + s * .5, y + s * .98)], fill=col)


def _parts(size, num_col):
    f = bahn(size, "SemiBold Condensed")
    return f, glyph_set("0123456789", f, num_col, BLACK)


def info_row(D, cx, y, size=18, icon_cols=((90, 230, 120), (120, 190, 255), (255, 80, 90)), num_col=(240, 240, 240)):
    """Satu baris terpusat: [bat] 80%   [langkah] 8432   [hati] 72."""
    f, dd = _parts(size, num_col)
    dw, dh = dd[0].width, dd[0].height
    s = dh
    pct_w = int(f.getlength("%")) + 2
    slots = [("bat", s + 4 + 3 * dw + pct_w), ("step", s + 4 + 5 * dw), ("heart", s + 4 + 3 * dw)]
    gap = 12
    total = sum(w for _, w in slots) + gap * 2
    x = cx - total // 2
    W.shadow(D.bg, (x - 8, y - 6, x + total + 8, y + dh + 6), radius=12, fade=16)
    d = ImageDraw.Draw(D.bg)
    for (kind, w), col in zip(slots, icon_cols):
        icon(d, kind, x, y, s, col)
        nx = x + s + 4
        if kind == "bat":
            D.add("battery", dd, nx + 3 * dw, y, gravity=0x0c)      # rata kanan, lalu "%"
            d.text((nx + 3 * dw + 1, y - f.getbbox("0")[1]), "%", font=f, fill=num_col)
        elif kind == "step":
            D.add("step", dd, nx, y)
        else:
            D.add("heart", dd + [glyph_set("-", f, num_col, BLACK, cell_chars="0")[0]], nx, y)
        x += w + gap


def info_col(D, x, y, size=18, icon_cols=((90, 230, 120), (120, 190, 255), (255, 80, 90)), num_col=(240, 240, 240), lh=None):
    """Tiga baris rata kiri di x (untuk area hitam sempit di samping karakter)."""
    f, dd = _parts(size, num_col)
    dw, dh = dd[0].width, dd[0].height
    s = dh
    lh = lh or dh + 9
    width = s + 4 + 5 * dw
    W.shadow(D.bg, (x - 8, y - 6, x + width + 8, y + 2 * lh + dh + 6), radius=12, fade=16)
    d = ImageDraw.Draw(D.bg)
    for i, (kind, col) in enumerate(zip(("bat", "step", "heart"), icon_cols)):
        yy = y + i * lh
        icon(d, kind, x, yy, s, col)
        nx = x + s + 4
        if kind == "bat":
            D.add("battery", dd, nx + 3 * dw, yy, gravity=0x0c)
            d.text((nx + 3 * dw + 1, yy - f.getbbox("0")[1]), "%", font=f, fill=num_col)
        elif kind == "step":
            D.add("step", dd, nx, yy)
        else:
            D.add("heart", dd + [glyph_set("-", f, num_col, BLACK, cell_chars="0")[0]], nx, yy)


def renamed(D, base):
    D.name = base.replace("_anim", "") + "_info_anim"
    D.title = D.title.replace(" (animasi)", "") + " + info (animasi)"
    return D


# ---------------------------------------------------------------- varian
def kny_zenitsu_info_anim():
    D = renamed(Z.kny_zenitsu_anim(), "kny_zenitsu_anim")
    info_row(D, CX, 410, size=17)
    return D


def op_luffy_fire_info_anim():
    D = renamed(W.op_luffy_fire_anim(), "op_luffy_fire_anim")
    info_col(D, 338, 316, icon_cols=((90, 230, 120), (234, 192, 96), (255, 70, 60)))
    return D


def bleach_ichigo_info_anim():
    D = renamed(W.bleach_ichigo_anim(), "bleach_ichigo_anim")
    info_col(D, 58, 126, icon_cols=((90, 230, 120), (255, 200, 90), (255, 90, 40)))
    return D


def op_gear5_info_anim():
    D = renamed(W.op_gear5_anim(), "op_gear5_anim")
    info_row(D, CX, 288, size=17, icon_cols=((90, 230, 120), (190, 140, 255), (255, 90, 120)))
    return D


def jjk_gojo_purple_info_anim():
    D = renamed(W.jjk_gojo_purple_anim(), "jjk_gojo_purple_anim")
    info_col(D, 316, 330, icon_cols=((90, 230, 120), (190, 90, 255), (255, 120, 220)))
    return D


def kny_tanjiro_fire_info_anim():
    D = renamed(W.kny_tanjiro_fire_anim(), "kny_tanjiro_fire_anim")
    info_col(D, 344, 300, icon_cols=((90, 230, 120), (255, 160, 60), (255, 80, 60)))
    return D


def jjk_gojo_blindfold_info_anim():
    D = renamed(W.jjk_gojo_blindfold_anim(), "jjk_gojo_blindfold_anim")
    info_row(D, CX, 404, size=17, icon_cols=((90, 230, 120), (120, 190, 255), (255, 90, 110)))
    return D


def jjk_gojo_blue_info_anim():
    D = renamed(W.jjk_gojo_blue_anim(), "jjk_gojo_blue_anim")
    D.els.pop(0)                                       # pindahkan percikan biru ke kanan atas
    info_col(D, 318, 330, icon_cols=((90, 230, 120), (120, 190, 255), (255, 90, 110)))
    W.anim_embers(D, (300, 44, 420, 128), [(90, 150, 255), (160, 210, 255), (60, 90, 255)], n=12, seed=13)
    return D


ALL = (kny_zenitsu_info_anim, op_luffy_fire_info_anim, bleach_ichigo_info_anim, op_gear5_info_anim,
       jjk_gojo_purple_info_anim, kny_tanjiro_fire_info_anim, jjk_gojo_blindfold_info_anim, jjk_gojo_blue_info_anim)
