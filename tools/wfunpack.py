"""Unpack an AM05 watch-face .bin into PNG images + layout.json.

usage: python -I wfunpack.py in.bin outdir/
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wfformat as wf


def gravity_desc(g):
    parts = []
    # JL/AM05 uses the "_R" gravity variant: 2 = x center, 4 = x right, 16 = y center, 32 = y bottom
    if g & 1: parts.append("x_left")
    if g & 2: parts.append("x_center")
    if g & 4: parts.append("x_right")
    if g & 8: parts.append("y_top")
    if g & 16: parts.append("y_center")
    if g & 32: parts.append("y_bottom")
    return "|".join(parts) or "none"


def unpack(path, outdir):
    data = open(path, "rb").read()
    version, els, blobs = wf.parse(data)
    os.makedirs(outdir, exist_ok=True)
    layout = {"format": "sma-jl-am05", "version": version, "screen": [466, 466],
              "source_size": len(data), "elements": []}
    expect_first = 0
    for n, e in enumerate(els):
        if e["first"] != expect_first:
            raise ValueError("element %d image index not sequential" % n)
        expect_first += e["count"]
        bpp = 3 if e["alpha"] else 2
        name = wf.type_name(e["type"])
        sub = "e%02d_%s" % (n, name)
        os.makedirs(os.path.join(outdir, sub), exist_ok=True)
        files = []
        for k in range(e["count"]):
            blob = blobs[e["first"] + k]
            if e["mode"] == 0:
                w, h = e["w"], e["h"]
                pix = wf.raw_decode(blob, w, h, bpp)
            else:
                w, h, pix = wf.rle_decode(blob, bpp)
            img = wf.pixels_to_image(pix, w, h, bpp)
            rel = "%s/%02d.png" % (sub, k)
            img.save(os.path.join(outdir, rel))
            files.append(rel)
        el = {"type": name, "alpha": e["alpha"], "x": e["x"], "y": e["y"],
              "w": e["w"], "h": e["h"], "gravity": e["gravity"],
              "gravity_desc": gravity_desc(e["gravity"]), "mode": e["mode"],
              "encoding": "raw" if e["mode"] == 0 else "rle",
              "b18": e["b18"], "b19": e["b19"], "images": files}
        if e["type"] in (3, 4, 5):
            el["note"] = "b18=pivot distance from image bottom, b19=pivot x inside image; x,y=screen pivot"
        elif e["type"] in (23, 44):
            el["note"] = "b18=frame interval"
        layout["elements"].append(el)
    with open(os.path.join(outdir, "layout.json"), "w") as f:
        json.dump(layout, f, indent=1)
    return layout


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    lay = unpack(sys.argv[1], sys.argv[2])
    print("%d elements, %d images -> %s" % (len(lay["elements"]),
          sum(len(e["images"]) for e in lay["elements"]), sys.argv[2]))
