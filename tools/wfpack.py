"""Build an AM05 watch-face .bin from layout.json + PNG images.

usage: python -I wfpack.py indir/ out.bin
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wfformat as wf
from PIL import Image


def pack(indir, outpath):
    layout = json.load(open(os.path.join(indir, "layout.json")))
    els, blobs = [], []
    for n, el in enumerate(layout["elements"]):
        bpp = 3 if el.get("alpha") else 2
        mode = el.get("mode", 4)
        first = len(blobs)
        dims = []
        for rel in el["images"]:
            img = Image.open(os.path.join(indir, rel))
            img.load()
            w, h, pix = wf.image_to_pixels(img, bpp)
            dims.append((w, h))
            blobs.append(wf.raw_encode(w, h, pix, bpp) if mode == 0 else wf.rle_encode(w, h, pix, bpp))
        if mode == 0 and any(d != (el.get("w", dims[0][0]), el.get("h", dims[0][1])) for d in dims):
            raise ValueError("element %d: raw images must all match w,h" % n)
        w = el.get("w", dims[0][0]); h = el.get("h", dims[0][1])
        els.append(dict(first=first, count=len(el["images"]), w=w, h=h, x=el["x"], y=el["y"],
                        type=wf.type_id(el["type"]), alpha=bool(el.get("alpha")),
                        gravity=el.get("gravity", 9), mode=mode,
                        b18=el.get("b18", 0), b19=el.get("b19", 0)))
    data = wf.build(layout.get("version", 2), els, blobs)
    open(outpath, "wb").write(data)
    return data


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    d = pack(sys.argv[1], sys.argv[2])
    print("wrote %s (%d bytes)" % (sys.argv[2], len(d)))
