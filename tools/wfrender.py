"""Render an unpacked AM05 watch face (layout.json + PNGs) to a 466x466 preview PNG.

usage: python -I wfrender.py indir/ out.png [--time 10:08:36] [--date 2026-09-25]
          [--steps 23456] [--heart 86] [--kcal 520] [--dist 12.3] [--battery 80]
          [--goal 30000] [--weather 1] [--temp 24] [--h24] [--frame 0] [--round]
          [--compare official.png]

The firmware's exact layout rules are inferred from samples (see FORMAT.md):
  * x,y are anchored according to `gravity` (JL "_R" bit layout: 1 left, 2 x-center, 4 right,
    8 top, 16 y-center, 32 bottom). The anchored box is the whole rendered string of glyphs.
  * time/date fields draw a fixed number of zero-padded digits; sensor values draw the
    natural number of digits.
  * needles rotate around (b19, h - b18) of their image, placed at screen (x, y).
"""
import argparse, datetime, json, os, sys
from PIL import Image, ImageChops

SIZE = 466


def anchor(g, x, y, w, h):
    if g & 2:
        x -= w // 2
    elif g & 4:
        x -= w
    if g & 16:
        y -= h // 2
    elif g & 32:
        y -= h
    return x, y


def glyph_indices(el, v, n):
    t = el["type"]
    if t in ("hour", "min", "sec", "day"):
        return [int(c) for c in "%02d" % v["values"][t]]
    if t == "month":
        if n == 12:
            return [v["values"]["month"] - 1]
        return [int(c) for c in "%02d" % v["values"]["month"]]
    if t == "year":
        return [int(c) for c in "%04d" % v["values"]["year"]] if n >= 10 else [0]
    if t == "weekday":
        return [v["values"]["weekday"] % n]
    if t == "ampm":
        return [v["values"]["pm"]]
    if t in ("step", "heart", "calorie", "battery"):
        return [int(c) for c in str(v["values"][t])]
    if t == "distance":
        s = "%.1f" % v["values"]["distance"]
        return [10 if c == "." else int(c) for c in s] if n > 10 else [int(c) for c in s if c != "."]
    if t in ("hour_tens", "hour_units", "min_tens", "min_units"):
        s = "%02d" % v["values"]["hour" if t.startswith("hour") else "min"]
        return [int(s[0 if t.endswith("tens") else 1])]
    if t == "weather_icon":
        return [v["values"]["weather"] % n]
    if t == "temperature":
        s = str(v["values"]["temp"])
        return [10 if c == "-" else int(c) for c in s] + ([11] if n > 11 else [])
    if t == "distance_unit":
        return [0]
    if t == "battery_level":
        return [min(n - 1, round(v["values"]["battery"] * (n - 1) / 100))]
    if t == "step_progress":
        return [min(n - 1, v["values"]["step"] * (n - 1) // max(1, v["goal"]))]
    if t in ("bg_dynamic", "bg_image_array"):
        return [v["frame"] % n]
    return [0]


def render(indir, v):
    lay = json.load(open(os.path.join(indir, "layout.json")))
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
    cache = {}

    def img(rel):
        if rel not in cache:
            cache[rel] = Image.open(os.path.join(indir, rel)).convert("RGBA")
        return cache[rel]

    for el in lay["elements"]:
        t = el["type"]
        if t == "preview":
            continue
        if t in ("needle_hour", "needle_min", "needle_sec"):
            im = img(el["images"][0])
            hh, mm, ss = v["values"]["h24"], v["values"]["min"], v["values"]["sec"]
            ang = {"needle_hour": (hh % 12 + mm / 60) * 30, "needle_min": (mm + ss / 60) * 6,
                   "needle_sec": ss * 6}[t]
            layer = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
            px, py = el["b19"], im.height - el["b18"]
            layer.paste(im, (el["x"] - px, el["y"] - py))
            layer = layer.rotate(-ang, resample=Image.BICUBIC, center=(el["x"], el["y"]))
            canvas.alpha_composite(layer)
            continue
        idx = glyph_indices(el, v, len(el["images"]))
        glyphs = [img(el["images"][i]) for i in idx if i < len(el["images"])]
        if not glyphs:
            continue
        w = sum(g.width for g in glyphs)
        h = max(g.height for g in glyphs)
        x, y = anchor(el["gravity"], el["x"], el["y"], w, h)
        for g in glyphs:
            if g.mode == "RGBA" and el.get("alpha"):
                canvas.alpha_composite(g, (x, y))
            else:
                canvas.paste(g, (x, y))
            x += g.width
    return canvas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("indir"); ap.add_argument("out")
    ap.add_argument("--time", default="10:08:36"); ap.add_argument("--date", default="2026-09-25")
    ap.add_argument("--steps", type=int, default=23456); ap.add_argument("--heart", type=int, default=86)
    ap.add_argument("--kcal", type=int, default=520); ap.add_argument("--dist", type=float, default=12.3)
    ap.add_argument("--battery", type=int, default=80); ap.add_argument("--goal", type=int, default=30000)
    ap.add_argument("--weather", type=int, default=1); ap.add_argument("--temp", type=int, default=24)
    ap.add_argument("--h24", action="store_true"); ap.add_argument("--frame", type=int, default=0)
    ap.add_argument("--round", action="store_true", help="mask to round screen")
    ap.add_argument("--compare", help="official preview; writes <out>_cmp.png side by side + diff")
    a = ap.parse_args()
    hh, mm, ss = (int(p) for p in a.time.split(":"))
    d = datetime.date.fromisoformat(a.date)
    vals = {"h24": hh, "hour": hh if a.h24 else (hh % 12 or 12), "min": mm, "sec": ss,
            "pm": 1 if hh >= 12 else 0, "year": d.year, "month": d.month, "day": d.day,
            "weekday": (d.weekday() + 1) % 7,  # 0 = Sunday
            "step": a.steps, "heart": a.heart, "calorie": a.kcal, "distance": a.dist,
            "battery": a.battery, "weather": a.weather, "temp": a.temp}
    lay = json.load(open(os.path.join(a.indir, "layout.json")))
    if not a.h24 and not any(e["type"] == "ampm" for e in lay["elements"]):
        vals["hour"] = hh  # no AM/PM element -> assume 24h
    out = render(a.indir, {"values": vals, "goal": a.goal, "frame": a.frame})
    if a.round:
        from PIL import ImageDraw
        m = Image.new("L", (SIZE, SIZE), 0)
        ImageDraw.Draw(m).ellipse((0, 0, SIZE - 1, SIZE - 1), fill=255)
        bg = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 255))
        out = Image.composite(out, bg, m)
    out.convert("RGB").save(a.out)
    if a.compare:
        ref = Image.open(a.compare).convert("RGB").resize((SIZE, SIZE))
        mine = out.convert("RGB")
        diff = ImageChops.difference(ref, mine).point(lambda p: min(255, p * 3))
        sheet = Image.new("RGB", (SIZE * 3 + 12, SIZE), (60, 60, 60))
        sheet.paste(ref, (0, 0)); sheet.paste(mine, (SIZE + 6, 0)); sheet.paste(diff, (2 * SIZE + 12, 0))
        base, ext = os.path.splitext(a.out)
        sheet.save(base + "_cmp" + ext)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
