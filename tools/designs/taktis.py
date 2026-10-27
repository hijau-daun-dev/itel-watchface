"""Watch face "Taktis": digital gaya jam taktis (7-segmen), label bahasa Indonesia.

Desain orisinal (font DSEG7 - OFL, dan Bahnschrift bawaan Windows).
Hasil: designs/out/taktis/ (layout.json + PNG), taktis.bin dan taktis.png (render).

    python -I designs/taktis.py
"""
import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import wfrender  # noqa: E402

LITE = "--lite" in sys.argv          # <= 124 gambar (batas aman yang terlihat di watch face resmi)
# v2: tanpa alpha (latar hitam polos, jadi glyph cukup ditempel di atas hitam) -> jauh lebih ringan
# untuk chip JL. --nosec: tanpa detik (tidak perlu gambar ulang tiap detik).
NOSEC = "--nosec" in sys.argv
# --mini: hanya jam/menit/hari/tanggal/AM-PM/baterai/langkah (mirip watch face resmi yang ringan).
MINI = "--mini" in sys.argv
if MINI:
    LITE = True
    NOSEC = "--sec" not in sys.argv
NAME = ("taktis_mini" + ("" if NOSEC else "_sec")) if MINI else ("taktis_lite" if LITE else "taktis") + "_v2" + ("_nosec" if NOSEC else "")
OUT = os.path.join(HERE, "out", NAME)
SIZE, CX = 466, 233

WHITE = (237, 237, 237, 255)
GRAY = (140, 140, 140, 255)
DIM = (34, 34, 34, 255)          # segmen padam
ACCENT = (255, 122, 26, 255)     # oranye
UNLIT = (58, 58, 58, 255)

DSEG = os.path.join(TOOLS, "fonts", "DSEG7Classic-Bold.ttf")
BAHN = "C:/Windows/Fonts/bahnschrift.ttf"


def bahn(size, style="SemiBold Condensed"):
    f = ImageFont.truetype(BAHN, size)
    try:
        f.set_variation_by_name(style)
    except Exception:  # noqa: BLE001
        pass
    return f


def glyphs(font, chars, color, cell_chars="0123456789"):
    """Render tiap karakter ke gambar RGBA dengan tinggi seragam.
    Digit memakai lebar sel tetap (lebar "0".."9" terbesar) supaya angka tidak goyang."""
    asc, desc = font.getmetrics()
    top = min(font.getbbox(c)[1] for c in cell_chars)
    bottom = max(font.getbbox(c)[3] for c in cell_chars)
    h = bottom - top
    cell = max(font.getbbox(c)[2] - font.getbbox(c)[0] for c in cell_chars) + 2
    out = []
    for c in chars:
        l, t, r, b = font.getbbox(c)
        w = cell if c in cell_chars else (r - l) + 4
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ImageDraw.Draw(im).text(((w - (r - l)) // 2 - l, -top), c, font=font, fill=color)
        out.append(im)
    return out


def text_img(s, font, color):
    l, t, r, b = font.getbbox(s)
    im = Image.new("RGBA", (r - l + 2, b - t + 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l + 1, -t + 1), s, font=font, fill=color)
    return im


# ---------- elemen-elemen ----------
elements = []   # (meta, [Image])


def add(type_, imgs, x, y, gravity=9, under=None):
    """Glyph diratakan ke RGB di atas hitam (atau di atas `under`, mis. segmen padam)."""
    flat = []
    for im in imgs:
        base = under.copy() if under is not None and under.size == im.size else Image.new("RGBA", im.size, (0, 0, 0, 255))
        base.alpha_composite(im)
        flat.append(base.convert("RGB"))
    imgs = flat
    elements.append(({"type": type_, "alpha": False, "x": x, "y": y, "w": imgs[0].width, "h": imgs[0].height,
                      "gravity": gravity, "mode": 4, "encoding": "rle", "b18": 0, "b19": 0}, imgs))


bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
d = ImageDraw.Draw(bg)

# Ring tanda menit; tiap 5 menit lebih panjang dan terang.
for i in range(60):
    a = math.radians(i * 6)
    r1 = 214 if i % 5 == 0 else 222
    col = (110, 110, 110, 255) if i % 5 == 0 else (52, 52, 52, 255)
    d.line([(CX + r1 * math.sin(a), CX - r1 * math.cos(a)), (CX + 229 * math.sin(a), CX - 229 * math.cos(a))],
           fill=col, width=3 if i % 5 == 0 else 2)
# Penanda segitiga di jam 12 dan 6.
d.polygon([(CX - 7, 20), (CX + 7, 20), (CX, 30)], fill=ACCENT)
d.polygon([(CX - 7, 446), (CX + 7, 446), (CX, 436)], fill=GRAY)

f_label = bahn(17)
f_val = bahn(30)
f_date = bahn(31)


def label(s, cx, y, color=GRAY):
    im = text_img(s, f_label, color)
    bg.alpha_composite(im, (cx - im.width // 2, y))


digits_val = glyphs(f_val, "0123456789", WHITE)

# Baris atas: baterai (ikon + bar 6 level, diisi di bawah).
label("BATERAI", CX, 84 if MINI else 46)

# Baris 2: suhu | cuaca | detak.
if not MINI:
    label("SUHU", 120, 108)
    label("CUACA", CX, 108)
    label("DETAK", 346, 108)
    add("temperature", digits_val + glyphs(f_val, "-°", WHITE), 120, 128, gravity=0x0a)
    add("heart", digits_val + [text_img("--", f_val, WHITE)], 346, 128, gravity=0x0a)


def weather_icons():
    """12 ikon garis sederhana. Urutan (dugaan dari sampel resmi): 0 ?, 1 cerah, 2 berawan,
    3 cerah berawan, 4 hujan, 5 petir, 6 petir+hujan, 7 angin, 8 salju, 9 kabut, 10 debu, 11 hujan lebat."""
    S = 40
    icons = []

    def base():
        im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def sun(dr, cx, cy, r, col=ACCENT):
        dr.ellipse((cx - r, cy - r, cx + r, cy + r), outline=col, width=3)
        for k in range(8):
            a = math.radians(k * 45)
            dr.line([(cx + (r + 3) * math.cos(a), cy + (r + 3) * math.sin(a)),
                     (cx + (r + 7) * math.cos(a), cy + (r + 7) * math.sin(a))], fill=col, width=2)

    def cloud(dr, y0=14, col=WHITE):
        dr.rounded_rectangle((5, y0 + 8, 35, y0 + 20), radius=6, outline=col, width=3)
        dr.ellipse((11, y0, 27, y0 + 16), outline=col, width=3)
        dr.rectangle((8, y0 + 11, 32, y0 + 17), fill=(0, 0, 0, 0))

    def drops(dr, n=3, y=32, col=WHITE):
        for k in range(n):
            x = 11 + k * 9
            dr.line([(x, y), (x - 3, y + 6)], fill=col, width=2)

    def bolt(dr, col=ACCENT):
        dr.line([(22, 26), (17, 33), (23, 33), (18, 40)], fill=col, width=3)

    im, dr = base(); dr.text((13, 6), "?", font=bahn(26), fill=GRAY); icons.append(im)              # 0
    im, dr = base(); sun(dr, 20, 20, 8); icons.append(im)                                           # 1
    im, dr = base(); cloud(dr, 10); icons.append(im)                                                # 2
    im, dr = base(); sun(dr, 14, 13, 6); cloud(dr, 14); icons.append(im)                            # 3
    im, dr = base(); cloud(dr, 4); drops(dr, 3, 28); icons.append(im)                               # 4
    im, dr = base(); cloud(dr, 4); bolt(dr); icons.append(im)                                       # 5
    im, dr = base(); cloud(dr, 4); bolt(dr); dr.line([(10, 29), (7, 35)], fill=WHITE, width=2); dr.line([(31, 29), (28, 35)], fill=WHITE, width=2); icons.append(im)  # 6
    im, dr = base()
    for k, yy in enumerate((12, 20, 28)):
        dr.line([(5, yy), (30 - k * 5, yy)], fill=WHITE, width=3)
    icons.append(im)                                                                                # 7
    im, dr = base(); cloud(dr, 4)
    for k in range(3):
        x = 11 + k * 9; dr.text((x - 4, 26), "*", font=bahn(16), fill=WHITE)
    icons.append(im)                                                                                # 8
    im, dr = base()
    for yy in (12, 19, 26, 33):
        dr.line([(6, yy), (34, yy)], fill=GRAY, width=3)
    icons.append(im)                                                                                # 9
    im, dr = base()
    for k in range(9):
        dr.ellipse((6 + (k % 3) * 11, 9 + (k // 3) * 9, 10 + (k % 3) * 11, 13 + (k // 3) * 9), fill=GRAY)
    icons.append(im)                                                                                # 10
    im, dr = base(); cloud(dr, 4); drops(dr, 3, 26); drops(dr, 3, 33); icons.append(im)             # 11
    return icons


if not MINI:
    add("weather_icon", weather_icons(), CX, 126, gravity=0x0a)

# Baris tanggal: "SEN  25.09".
weekdays = [text_img(s, f_date, WHITE) for s in ("MIN", "SEN", "SEL", "RAB", "KAM", "JUM", "SAB")]
date_digits = glyphs(f_date, "0123456789", WHITE)
wd_w = max(im.width for im in weekdays)
dd_w = date_digits[0].width
dot = text_img(".", f_date, WHITE)
gap = 14
total = wd_w + gap + 2 * dd_w + dot.width + 2 * dd_w
x0 = CX - total // 2
date_y = 176
weekdays = [Image.new("RGBA", (wd_w, im.height), (0, 0, 0, 0)) for im in weekdays]  # lebar seragam
for im, s in zip(weekdays, ("MIN", "SEN", "SEL", "RAB", "KAM", "JUM", "SAB")):
    t = text_img(s, f_date, WHITE)
    im.alpha_composite(t, (wd_w - t.width, 0))     # rata kanan, dekat angka
add("weekday", weekdays, x0, date_y)
xd = x0 + wd_w + gap
add("day", date_digits, xd, date_y + (weekdays[0].height - date_digits[0].height))
xdot = xd + 2 * dd_w
bg.alpha_composite(dot, (xdot, date_y + weekdays[0].height - dot.height))
add("month", date_digits, xdot + dot.width, date_y + (weekdays[0].height - date_digits[0].height))

# Jam besar 7-segmen dengan bayangan segmen padam.
f_time = ImageFont.truetype(DSEG, 84)
t_digits = glyphs(f_time, "0123456789", WHITE)
ghost = glyphs(f_time, "8", DIM)[0]
tw, th = t_digits[0].width, t_digits[0].height
colon_w = 22
sec_font = ImageFont.truetype(DSEG, 28)
s_digits = glyphs(sec_font, "0123456789", ACCENT)
sec_w = 2 * s_digits[0].width
time_total = 4 * tw + colon_w
tx = CX - time_total // 2 - 12      # sedikit ke kiri, memberi ruang detik
ty = 226
for k, xx in enumerate((tx, tx + tw, tx + 2 * tw + colon_w, tx + 3 * tw + colon_w)):
    bg.alpha_composite(ghost, (xx, ty))
for yy in (ty + th * 0.3, ty + th * 0.68):
    d.rounded_rectangle((tx + 2 * tw + 6, yy - 5, tx + 2 * tw + 16, yy + 5), radius=2, fill=WHITE)
add("hour", t_digits, tx, ty, under=ghost)
add("min", t_digits, tx + 2 * tw + colon_w, ty, under=ghost)
sx = tx + time_total + 8
ampm_font = bahn(18)
add("ampm", [text_img("AM", ampm_font, ACCENT), text_img("PM", ampm_font, ACCENT)], sx + 2, ty + 6)
if not NOSEC:
    add("sec", s_digits, sx, ty + th - s_digits[0].height)

# Bar baterai (6 level: 0..5) di baris atas.
bar_y = 110 if MINI else 72
TICKS, tick_w, tick_gap = 20, 4, 3
levels = []
for lv in range(6):
    im = Image.new("RGBA", (TICKS * (tick_w + tick_gap), 12), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    lit = round(lv * TICKS / 5)
    for k in range(TICKS):
        x = k * (tick_w + tick_gap)
        dr.rectangle((x, 0, x + tick_w - 1, 11), fill=(WHITE if lv > 1 else ACCENT) if k < lit else UNLIT)
    levels.append(im)
add("battery_level", levels, CX - (TICKS * (tick_w + tick_gap) - tick_gap) // 2, bar_y)

# Di bawah jam: jarak (versi full saja).
if not LITE:
    f_small = bahn(24)
    add("distance", glyphs(f_small, "0123456789", WHITE) + glyphs(f_small, ".", WHITE), CX, ty + th + 18, gravity=0x0a)
    km = text_img("KM", f_label, GRAY)
    bg.alpha_composite(km, (CX + 46, ty + th + 23))
    jr = text_img("JARAK", f_label, GRAY)
    bg.alpha_composite(jr, (CX - 46 - jr.width, ty + th + 23))

# Baris bawah: kalori | progres langkah | langkah.
if MINI:
    label("LANGKAH", CX, 352)
    add("step", digits_val, CX, 372, gravity=0x0a)
else:
    label("KALORI", 132, 352)
    label("LANGKAH", 334, 352)
    add("calorie", digits_val, 132, 372, gravity=0x0a)
    add("step", digits_val, 334, 372, gravity=0x0a)
bars = []
for fr in range(11):
    im = Image.new("RGBA", (50, 40), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    lit = round(fr * 6 / 10)
    for k in range(6):
        hh = 10 + k * 6
        x = k * 9
        dr.rectangle((x, 40 - hh, x + 5, 39), fill=ACCENT if k < lit else UNLIT)
    bars.append(im)
if MINI:
    pass
elif LITE:
    bg.alpha_composite(bars[7], (CX - 25, 362))     # statis, sekadar ornamen
else:
    add("step_progress", bars, CX, 362, gravity=0x0a)


# ---------- tulis layout, render, preview, pack ----------
def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    full = [({"type": "preview", "alpha": False, "x": 0, "y": 0, "w": 280, "h": 280, "gravity": 0, "mode": 4,
              "encoding": "rle", "b18": 0, "b19": 0}, [Image.new("RGB", (280, 280))]),
            ({"type": "background", "alpha": False, "x": 0, "y": 0, "w": SIZE, "h": SIZE, "gravity": 9, "mode": 4,
              "encoding": "rle", "b18": 0, "b19": 0}, [bg.convert("RGB")])] + elements
    lay = {"format": "sma-jl-am05", "version": 2, "screen": [SIZE, SIZE], "elements": []}
    for n, (meta, imgs) in enumerate(full):
        sub = f"e{n:02d}_{meta['type']}"
        os.makedirs(os.path.join(OUT, sub))
        meta = dict(meta, images=[])
        for i, im in enumerate(imgs):
            rel = f"{sub}/{i:02d}.png"
            im.save(os.path.join(OUT, rel))
            meta["images"].append(rel)
        lay["elements"].append(meta)
    with open(os.path.join(OUT, "layout.json"), "w") as f:
        json.dump(lay, f, indent=1)

    vals = {"h24": 10, "hour": 10, "min": 8, "sec": 36, "pm": 0, "year": 2026, "month": 9, "day": 25,
            "weekday": 5, "step": 8432, "heart": 72, "calorie": 312, "distance": 6.4, "battery": 80,
            "weather": 3, "temp": 29}
    render = wfrender.render(OUT, {"values": vals, "goal": 10000, "frame": 0})
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, SIZE - 1, SIZE - 1), fill=255)
    shown = Image.composite(render, Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255)), mask).convert("RGB")
    shown.save(os.path.join(HERE, "out", NAME + ".png"))
    shown.resize((280, 280), Image.LANCZOS).save(os.path.join(OUT, "e00_preview", "00.png"))
    subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "wfpack.py"), OUT,
                    os.path.join(HERE, "out", NAME + ".bin")], check=True)
    n_img = sum(len(e["images"]) for e in lay["elements"])
    print(f"elemen={len(lay['elements'])} gambar={n_img} ukuran={os.path.getsize(os.path.join(HERE, 'out', NAME + '.bin'))} byte")


if __name__ == "__main__":
    main()
