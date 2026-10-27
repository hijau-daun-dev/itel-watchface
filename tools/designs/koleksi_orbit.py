"""Watch face "angka yang berputar" (rotating dial): penanda diam di atas, cincin angka yang berputar.

Trik: elemen jarum = gambar yang diputar firmware searah jarum jam sebesar sudut waktu. Kalau gambar
jarumnya berupa cincin angka yang ditulis BERLAWANAN arah jarum jam (angka n di sudut -n*30 / -n*6),
angka yang sedang berlaku selalu berhenti tepat di puncak (di bawah penanda).
Catatan: jarum disimpan raw ARGB (3 byte/piksel), jadi ukuran cincin = ukuran file.
"""
from PIL import Image, ImageDraw

from wflib import CX, SIZE, WEEKDAYS_ID, Design, bahn, glyph_set, polar, text_rgba, ttf, word_set

MONO_B = "C:/Windows/Fonts/consolab.ttf"


def ring(size, labels, angle_step, r_text, font, col, tick_r=None, ticks=0, tick_col=None, major_every=1, ss=2):
    """Cincin RGBA: label i di sudut -i*angle_step (berlawanan jarum jam), tegak menghadap keluar."""
    S = size * ss
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    c = S / 2
    dr = ImageDraw.Draw(im)
    if ticks:
        for k in range(ticks):
            deg = -k * 360 / ticks
            major = k % major_every == 0
            r1 = tick_r[0] * ss
            r2 = (tick_r[1] if major else (tick_r[0] + tick_r[1]) / 2) * ss
            x1, y1 = polar_c(c, r1, deg); x2, y2 = polar_c(c, r2, deg)
            dr.line((x1, y1, x2, y2), fill=tick_col if major else tuple(v // 2 for v in tick_col[:3]) + (255,),
                    width=(3 if major else 2) * ss // 2 + 1)
    for i, s in enumerate(labels):
        if not s:
            continue
        lf, lc = (font, col) if isinstance(s, str) else (s[1], s[2])
        s = s if isinstance(s, str) else s[0]
        deg = -i * angle_step
        t = text_rgba(s, lf.font_variant(size=lf.size * ss), lc)
        t = t.rotate(-deg, resample=Image.BICUBIC, expand=True)
        x, y = polar_c(c, r_text * ss, deg)
        im.alpha_composite(t, (int(x - t.width / 2), int(y - t.height / 2)))
    return im.resize((size, size), Image.LANCZOS)


def polar_c(c, r, deg):
    import math
    a = math.radians(deg)
    return c + r * math.sin(a), c - r * math.cos(a)


def orbit_design(name, title, min_size, min_r, hour_size, hour_r, fmin, fhour):
    BG, ORANGE, WHITE, GRAY, CYAN = (0, 0, 0), (255, 122, 26), (240, 240, 240), (120, 124, 130), (0, 210, 255)
    bg = Image.new("RGB", (SIZE, SIZE), BG)
    d = ImageDraw.Draw(bg)
    D = Design(name, title, bg)

    # Penanda tetap di puncak + jendela "kaca pembesar" untuk jam & menit.
    d.polygon([(CX - 9, 6), (CX + 9, 6), (CX, 20)], fill=ORANGE)
    top_min = CX - min_r
    top_hour = CX - hour_r
    d.rounded_rectangle((CX - 34, top_min - 22, CX + 34, top_min + 22), radius=10, outline=ORANGE, width=2)
    d.rounded_rectangle((CX - 30, top_hour - 24, CX + 30, top_hour + 24), radius=10, outline=ORANGE, width=2)

    # Tengah: hari + tanggal + detik.
    f = bahn(24, "SemiBold Condensed")
    wd = word_set(WEEKDAYS_ID, f, CYAN, BG)
    D.add("weekday", wd, CX - wd[0].width // 2, CX + 6)
    dd = glyph_set("0123456789", f, WHITE, BG)
    D.add("day", dd, CX - dd[0].width, CX + 36)
    fs = ttf(MONO_B, 26)
    sd = glyph_set("0123456789", fs, ORANGE, BG, padx=0)
    D.add("sec", sd, CX - sd[0].width, CX - 40)

    # Cincin menit (00..55 tiap 5 menit, tick tiap menit) -> needle_min.
    fsmall = fmin.font_variant(size=max(11, fmin.size * 11 // 20))
    mins = [(f"{m:02d}", fmin, (240, 240, 240, 255)) if m % 5 == 0 else (f"{m:02d}", fsmall, (130, 134, 140, 255))
            for m in range(60)]
    mring = ring(min_size, mins, 6, min_r, fmin, (230, 230, 230, 255), tick_r=(min_r + 22, min_r + 34),
                 ticks=60, tick_col=(150, 150, 150, 255), major_every=5)
    D.add_needle("needle_min", (mring, mring.height // 2))
    # Cincin jam (12, 1..11) -> needle_hour; digambar di atas cincin menit.
    hours = [str(h if h else 12) for h in range(12)]
    hring = ring(hour_size, hours, 30, hour_r, fhour, (255, 255, 255, 255), tick_r=(hour_r + 26, hour_r + 32),
                 ticks=12, tick_col=(255, 122, 26, 255))
    D.add_needle("needle_hour", (hring, hring.height // 2))
    return D


def orbit():
    return orbit_design("orbit", "Orbit (angka berputar)", 400, 166, 240, 88,
                        bahn(26, "SemiBold Condensed"), bahn(36, "Bold Condensed"))


def orbit_lite():
    return orbit_design("orbit_lite", "Orbit Lite (angka berputar)", 330, 136, 204, 74,
                        bahn(23, "SemiBold Condensed"), bahn(30, "Bold Condensed"))


ALL = (orbit_lite, orbit)
