"""Pustaka kecil untuk merancang watch face AM05 yang ringan.

Aturan ringan (hasil uji di jam): sedikit elemen, tanpa elemen sensor berat, glyph TANPA alpha.
Karena tanpa alpha, setiap glyph harus opaque dan "lengkap" sendiri: digambar di atas warna
latar polos di posisinya (bg_color), atau membawa kotaknya sendiri (jendela tanggal, kartu flip).
Jarum jam tetap RGBA (raw), sama seperti watch face resmi.
"""
import json
import math
import os
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
sys.path.insert(0, TOOLS)
import wfrender  # noqa: E402

SIZE, CX = 466, 233
BAHN = "C:/Windows/Fonts/bahnschrift.ttf"
DSEG = os.path.join(TOOLS, "fonts", "DSEG7Classic-Bold.ttf")
WEEKDAYS_ID = ("MIN", "SEN", "SEL", "RAB", "KAM", "JUM", "SAB")   # urutan jam: Minggu dulu


def bahn(size, style="SemiBold Condensed"):
    f = ImageFont.truetype(BAHN, size)
    try:
        f.set_variation_by_name(style)
    except Exception:  # noqa: BLE001
        pass
    return f


def ttf(path, size):
    return ImageFont.truetype(path, size)


def text_rgba(s, font, color, pad=1):
    l, t, r, b = font.getbbox(s)
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-l + pad, -t + pad), s, font=font, fill=color)
    return im


def glyph_set(chars, font, fg, bg, cell_chars="0123456789", padx=1, cell_w=None, cell_h=None, box=None):
    """Glyph opaque (RGB) dengan tinggi seragam; digit memakai lebar sel tetap.
    `box`: fungsi(draw, w, h) untuk menggambar kotak di belakang glyph (mis. kartu flip)."""
    top = min(font.getbbox(c)[1] for c in cell_chars)
    bottom = max(font.getbbox(c)[3] for c in cell_chars)
    gh = bottom - top
    cw = max(font.getbbox(c)[2] - font.getbbox(c)[0] for c in cell_chars) + 2 * padx
    out = []
    for c in chars:
        l, t, r, b = font.getbbox(c)
        w = cell_w or (cw if c in cell_chars else (r - l) + 2 * padx)
        h = cell_h or gh
        im = Image.new("RGB", (w, h), bg)
        dr = ImageDraw.Draw(im)
        if box:
            box(dr, w, h)
        dr.text(((w - (r - l)) // 2 - l, (h - gh) // 2 - top), c, font=font, fill=fg)
        out.append(im)
    return out


def word_set(words, font, fg, bg, w=None, h=None, box=None, align="center"):
    """Satu gambar per kata (hari, AM/PM) dengan ukuran seragam."""
    boxes = [font.getbbox(s) for s in words]
    W = w or max(b[2] - b[0] for b in boxes) + 4
    top = min(b[1] for b in boxes); bottom = max(b[3] for b in boxes)
    H = h or (bottom - top) + 2
    out = []
    for s, (l, t, r, b) in zip(words, boxes):
        im = Image.new("RGB", (W, H), bg)
        dr = ImageDraw.Draw(im)
        if box:
            box(dr, W, H)
        x = {"center": (W - (r - l)) // 2, "left": 2, "right": W - (r - l) - 2}[align] - l
        dr.text((x, (H - (bottom - top)) // 2 - top), s, font=font, fill=fg)
        out.append(im)
    return out


def needle(length, width, color, tail=0, shape="baton", ss=4, edge=None, tip=None):
    """Jarum menghadap ke atas, pivot di (w/2, h - tail). Digambar 4x lalu diperkecil (antialias)."""
    w, h = width + 4, length + tail
    big = Image.new("RGBA", (w * ss, h * ss), (0, 0, 0, 0))
    dr = ImageDraw.Draw(big)
    cx, py = w * ss / 2, (h - tail) * ss
    hw = width * ss / 2
    if shape == "dauphine":
        pts = [(cx, 0), (cx + hw, py * 0.55), (cx + hw * 0.55, py), (cx - hw * 0.55, py), (cx - hw, py * 0.55)]
        dr.polygon(pts, fill=color)
        if edge:
            dr.polygon([(cx, 0), (cx + hw, py * 0.55), (cx + hw * 0.55, py), (cx, py)], fill=edge)
    elif shape == "sword":
        dr.polygon([(cx, 0), (cx + hw, py * 0.18), (cx + hw * 0.8, py), (cx - hw * 0.8, py), (cx - hw, py * 0.18)], fill=color)
    else:  # baton
        dr.rounded_rectangle((cx - hw, 0, cx + hw, py + hw), radius=hw, fill=color)
    if tip:
        dr.rounded_rectangle((cx - hw * 0.45, py * 0.08, cx + hw * 0.45, py * 0.42), radius=hw * 0.4, fill=tip)
    if tail:
        dr.rounded_rectangle((cx - hw * 0.9, py, cx + hw * 0.9, h * ss), radius=hw * 0.9, fill=color)
    r = max(hw * 1.6, 4 * ss)
    dr.ellipse((cx - r, py - r, cx + r, py + r), fill=color)
    return big.resize((w, h), Image.LANCZOS), tail


class Design:
    def __init__(self, name, title, bg):
        # Simpan referensi (bukan salinan): desain boleh terus menggambar ke latar setelah Design dibuat.
        self.name, self.title, self.bg = name, title, bg if bg.mode == "RGB" else bg.convert("RGB")
        self.els = []
        self.center_x = None      # isi warna latar polos untuk menengahkan isi secara horizontal

    def _autocenter(self):
        """Geser seluruh isi (latar + elemen) supaya lebar isinya di tengah layar.
        Baris yang hampir selebar layar (tab bar, garis status) diabaikan saat mengukur."""
        from PIL import ImageChops
        col = self.center_x
        diff = ImageChops.difference(self.bg, Image.new("RGB", self.bg.size, col)).convert("L")
        diff = diff.point(lambda p: 255 if p > 24 else 0)
        rows = diff.resize((1, SIZE), Image.BOX)
        dr = ImageDraw.Draw(diff)
        for y in range(SIZE):
            if rows.getpixel((0, y)) > 150:
                dr.line((0, y, SIZE, y), fill=0)
        # Tempel juga glyph elemen (contoh nilai) ke mask, supaya ikut dihitung.
        for meta, imgs in self.els:
            n = {"hour": 2, "min": 2, "sec": 2, "day": 2, "month": 2, "step": 4, "heart": 2,
                 "calorie": 3, "temperature": 2}.get(meta["type"], 1)
            im = imgs[min(len(imgs) - 1, 8)]
            m = ImageChops.difference(im, Image.new("RGB", im.size, col)).convert("L").point(lambda p: 255 if p > 24 else 0)
            g, x, y = meta["gravity"], meta["x"], meta["y"]
            w = im.width * n
            x0 = x - w if g & 4 else x - w // 2 if g & 2 else x
            for k in range(n):
                diff.paste(255, (x0 + k * im.width, y), m)
        box = diff.getbbox()
        if not box:
            return
        # Pusat massa horizontal: tulisan rata kiri terasa seimbang di layar bulat.
        cols = diff.resize((SIZE, 1), Image.BOX)
        mass = [cols.getpixel((x, 0)) for x in range(SIZE)]
        total = sum(mass) or 1
        centroid = sum(x * m for x, m in enumerate(mass)) / total
        dx = int(round(CX - (centroid + (box[0] + box[2]) / 2) / 2))
        # Jangan sampai isi keluar dari layar bulat.
        dx = max(36 - box[0], min(430 - box[2], dx))
        if not dx:
            return
        shifted = Image.new("RGB", self.bg.size, col)
        shifted.paste(self.bg, (dx, 0))
        self.bg.paste(shifted)
        for meta, _ in self.els:
            meta["x"] += dx

    def add(self, type_, imgs, x, y, gravity=9):
        self.els.append(({"type": type_, "alpha": False, "x": x, "y": y, "w": imgs[0].width, "h": imgs[0].height,
                          "gravity": gravity, "mode": 4, "encoding": "rle", "b18": 0, "b19": 0},
                         [im.convert("RGB") for im in imgs]))

    def add_anim(self, frames, x, y, interval=12):
        """Animasi (bg_dynamic): frame opaque diputar bergantian; interval = b18
        (watch face resmi memakai 10..100; satuannya belum pasti, kemungkinan 10 ms)."""
        self.els.append(({"type": "bg_dynamic", "alpha": False, "x": x, "y": y, "w": frames[0].width,
                          "h": frames[0].height, "gravity": 9, "mode": 4, "encoding": "rle", "b18": interval,
                          "b19": 0}, [im.convert("RGB") for im in frames]))

    def add_needle(self, type_, img_tail):
        img, tail = img_tail
        self.els.append(({"type": type_, "alpha": True, "x": CX, "y": CX, "w": img.width, "h": img.height,
                          "gravity": 0, "mode": 0, "encoding": "raw", "b18": tail, "b19": img.width // 2}, [img]))

    def build(self, outdir, values=None):
        if self.center_x is not None:
            self._autocenter()
        work = os.path.join(HERE, "out", self.name)
        if os.path.isdir(work):
            shutil.rmtree(work)
        os.makedirs(work)
        full = [({"type": "preview", "alpha": False, "x": 0, "y": 0, "w": 280, "h": 280, "gravity": 0, "mode": 4,
                  "encoding": "rle", "b18": 0, "b19": 0}, [Image.new("RGB", (280, 280))]),
                ({"type": "background", "alpha": False, "x": 0, "y": 0, "w": SIZE, "h": SIZE, "gravity": 9, "mode": 4,
                  "encoding": "rle", "b18": 0, "b19": 0}, [self.bg])]
        # Jarum selalu paling akhir (digambar paling atas).
        full += [e for e in self.els if not e[0]["type"].startswith("needle")]
        full += [e for e in self.els if e[0]["type"].startswith("needle")]
        lay = {"format": "sma-jl-am05", "version": 2, "screen": [SIZE, SIZE], "elements": []}
        for n, (meta, imgs) in enumerate(full):
            sub = f"e{n:02d}_{meta['type']}"
            os.makedirs(os.path.join(work, sub))
            meta = dict(meta, images=[])
            for i, im in enumerate(imgs):
                rel = f"{sub}/{i:02d}.png"
                im.save(os.path.join(work, rel))
                meta["images"].append(rel)
            lay["elements"].append(meta)
        json.dump(lay, open(os.path.join(work, "layout.json"), "w"), indent=1)

        v = {"h24": 10, "hour": 10, "min": 8, "sec": 36, "pm": 0, "year": 2026, "month": 9, "day": 25,
             "weekday": 5, "step": 8432, "heart": 72, "calorie": 312, "distance": 6.4, "battery": 80,
             "weather": 1, "temp": 29}
        v.update(values or {})
        render = wfrender.render(work, {"values": v, "goal": 10000, "frame": 0})
        mask = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, SIZE - 1, SIZE - 1), fill=255)
        shown = Image.composite(render, Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255)), mask).convert("RGB")
        shown.resize((280, 280), Image.LANCZOS).save(os.path.join(work, "e00_preview", "00.png"))
        os.makedirs(outdir, exist_ok=True)
        shown.save(os.path.join(outdir, self.name + ".png"))
        binpath = os.path.join(outdir, self.name + ".bin")
        subprocess.run([sys.executable, "-I", os.path.join(TOOLS, "wfpack.py"), work, binpath],
                       check=True, stdout=subprocess.DEVNULL)
        n_img = sum(len(e["images"]) for e in lay["elements"])
        info = {"name": self.name, "title": self.title, "elements": len(lay["elements"]), "images": n_img,
                "bytes": os.path.getsize(binpath),
                "alpha_elements": sum(1 for e in lay["elements"] if e["alpha"])}
        print(f"{self.name:18} el={info['elements']:2} img={info['images']:3} {info['bytes'] // 1024} KB  alpha={info['alpha_elements']}")
        return info


# ---------- bahan latar ----------
def radial_gradient(inner, outer, size=SIZE, power=1.0):
    im = Image.new("RGB", (size, size))
    px = im.load()
    c = size / 2
    for y in range(size):
        for x in range(size):
            t = min(1.0, math.hypot(x - c, y - c) / c) ** power
            px[x, y] = tuple(int(inner[i] + (outer[i] - inner[i]) * t) for i in range(3))
    return im


def sunburst(base, rays=180, strength=10):
    """Tekstur sunburst: garis radial halus di atas warna dasar."""
    im = base.copy()
    over = Image.new("L", (SIZE, SIZE), 0)
    dr = ImageDraw.Draw(over)
    for k in range(rays):
        a = math.radians(k * 360 / rays)
        dr.line([(CX, CX), (CX + 330 * math.sin(a), CX - 330 * math.cos(a))], fill=255 if k % 2 else 0, width=2)
    over = over.filter(ImageFilter.GaussianBlur(1.2))
    light = Image.new("RGB", (SIZE, SIZE), tuple(min(255, c + strength) for c in base.getpixel((CX, CX))))
    return Image.composite(light, im, over.point(lambda p: p // 3))


def polar(r, deg):
    a = math.radians(deg)
    return CX + r * math.sin(a), CX - r * math.cos(a)
