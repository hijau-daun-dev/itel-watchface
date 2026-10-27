"""Ekspor latar untuk watch face DIY Haylou Solar Plus (LS16).

Haylou DIY = latar 466x466 + widget jam & tanggal yang digambar firmware. Untuk setiap desain di
D:/watch/koleksi.json: ambil latar (+ frame 0 animasi) TANPA angka dinamis, simpan
D:/watch/<nama>.hbg.png, dan catat posisi/warna jam & tanggal ke koleksi.json (field "haylou").

    python -I designs/export_haylou.py [D:/watch]
"""
import json
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
WATCH = sys.argv[1] if len(sys.argv) > 1 else "D:/watch"
SIZE = 466
ALIAS = {"taktis": "taktis_mini_sec"}           # nama di D:/watch -> folder kerja di out/
TIME_TYPES = ("hour", "hour_tens")
DATE_TYPES = ("weekday", "day", "month")


def bright_color(path):
    """Warna dominan piksel terang di gambar glyph (untuk warna widget)."""
    im = Image.open(path).convert("RGB")
    px = [p for p in im.getdata() if sum(p) > 200]
    if not px:
        return [255, 255, 255]
    px.sort(key=sum)
    top = px[len(px) // 2:]
    return [sum(c[i] for c in top) // len(top) for i in range(3)]


def anchor(el, n=2):
    """Pojok kiri atas kotak glyph (gravity JL: 2 = tengah-x, 4 = kanan)."""
    x, y, w = el["x"], el["y"], el["w"] * n
    if el["gravity"] & 2:
        x -= w // 2
    elif el["gravity"] & 4:
        x -= w
    return [int(x), int(y)]


def export(name):
    work = os.path.join(OUT, ALIAS.get(name, name))
    lay_path = os.path.join(work, "layout.json")
    if not os.path.exists(lay_path):
        return None
    lay = json.load(open(lay_path))
    els = lay["elements"]
    bg = None
    for el in els:
        if el["type"] == "background":
            bg = Image.open(os.path.join(work, el["images"][0])).convert("RGB")
    if bg is None:
        return None
    for el in els:                                   # frame 0 animasi ikut jadi latar (statis)
        if el["type"] in ("bg_dynamic", "bg_image_array"):
            fr = Image.open(os.path.join(work, el["images"][0])).convert("RGB")
            bg.paste(fr, (el["x"], el["y"]))
    m = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(m).ellipse((0, 0, SIZE - 1, SIZE - 1), fill=255)
    bg = Image.composite(bg, Image.new("RGB", (SIZE, SIZE)), m)
    bg.save(os.path.join(WATCH, name + ".hbg.png"))

    meta = {"bg": name + ".hbg.png", "analog": any(e["type"].startswith("needle") for e in els)}
    t = next((e for e in els if e["type"] in TIME_TYPES), None)
    if t:
        meta["time"] = anchor(t)
        meta["time_color"] = bright_color(os.path.join(work, t["images"][min(1, len(t["images"]) - 1)]))
    dt = next((e for e in els if e["type"] in DATE_TYPES), None)
    if dt:
        meta["date"] = anchor(dt, 1)
        meta["date_color"] = bright_color(os.path.join(work, dt["images"][min(1, len(dt["images"]) - 1)]))
    return meta


def main():
    p = os.path.join(WATCH, "koleksi.json")
    items = json.load(open(p, encoding="utf-8"))
    ok = 0
    for it in items:
        meta = export(it["name"])
        if meta:
            it["haylou"] = meta
            ok += 1
        else:
            it.pop("haylou", None)
    json.dump(items, open(p, "w"), indent=1)
    print(f"latar Haylou diekspor: {ok}/{len(items)}")


if __name__ == "__main__":
    main()
