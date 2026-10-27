"""Shared codec for SMA / JL "AM05" watch-face .bin files (itel ISW-O43).

See FORMAT.md for the specification. Pure Python + Pillow.
"""
import struct

HEADER_SIZE = 4
ELEMENT_SIZE = 20
ALPHA_FLAG = 0x80

# element type ids (low 7 bits of the type byte). Ids 1..23, 44 come from
# com.szabh.smable3.watchface.WatchFaceBuilder; 24, 25, 26, 30, 37, 39-42 were inferred
# from official samples (see FORMAT.md).
TYPE_NAMES = {
    1: "preview", 2: "background", 3: "needle_hour", 4: "needle_min", 5: "needle_sec",
    6: "year", 7: "month", 8: "day", 9: "hour", 10: "min", 11: "sec", 12: "ampm",
    13: "weekday", 14: "step", 15: "heart", 16: "calorie", 17: "distance",
    18: "battery", 19: "bt", 20: "div_hour", 21: "div_month", 22: "icon",
    23: "bg_dynamic", 24: "battery_level", 25: "weather_icon", 26: "temperature",
    30: "step_progress", 37: "distance_unit", 39: "hour_tens", 40: "hour_units",
    41: "min_tens", 42: "min_units", 44: "bg_image_array",
}
TYPE_IDS = {v: k for k, v in TYPE_NAMES.items()}


def type_name(t):
    return TYPE_NAMES.get(t, "type_%d" % t)


def type_id(v):
    if isinstance(v, int):
        return v
    if v in TYPE_IDS:
        return TYPE_IDS[v]
    if v.startswith("type_"):
        return int(v[5:])
    raise ValueError("unknown element type %r" % v)


def align4(n):
    return (n + 3) & ~3


# ---------------------------------------------------------------- pixels
# 16-bit pixels are RGB565 stored BIG-endian; alpha pixels are A8 followed by RGB565 BE.
_E5 = [(v << 3) | (v >> 2) for v in range(32)]
_E6 = [(v << 2) | (v >> 4) for v in range(64)]


def px565_to_rgb(hi, lo):
    v = (hi << 8) | lo
    return _E5[v >> 11], _E6[(v >> 5) & 63], _E5[v & 31]


def rgb_to_565(r, g, b):
    v = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
    return bytes((v >> 8, v & 255))


def pixels_to_image(pix, w, h, bpp):
    """pix: bytes of w*h*bpp device pixels -> PIL Image (RGB or RGBA)."""
    from PIL import Image
    out = bytearray()
    if bpp == 2:
        lut = {}
        for i in range(0, len(pix), 2):
            k = pix[i:i + 2]
            t = lut.get(k)
            if t is None:
                t = lut[k] = bytes(px565_to_rgb(k[0], k[1]))
            out += t
        return Image.frombytes("RGB", (w, h), bytes(out))
    lut = {}
    for i in range(0, len(pix), 3):
        k = pix[i:i + 3]
        t = lut.get(k)
        if t is None:
            r, g, b = px565_to_rgb(k[1], k[2])
            t = lut[k] = bytes((r, g, b, k[0]))
        out += t
    return Image.frombytes("RGBA", (w, h), bytes(out))


def image_to_pixels(img, bpp):
    """PIL Image -> (w, h, device pixel bytes). bpp 2 = RGB565, 3 = A8+RGB565."""
    w, h = img.size
    out = bytearray()
    if bpp == 2:
        if img.mode == "RGBA" or img.mode == "LA" or (img.mode == "P" and "transparency" in img.info):
            from PIL import Image
            bg = Image.new("RGBA", img.size, (0, 0, 0, 255))
            img = Image.alpha_composite(bg, img.convert("RGBA"))
        data = img.convert("RGB").tobytes()
        lut = {}
        for i in range(0, len(data), 3):
            k = data[i:i + 3]
            t = lut.get(k)
            if t is None:
                t = lut[k] = rgb_to_565(*k)
            out += t
    else:
        data = img.convert("RGBA").tobytes()
        lut = {}
        for i in range(0, len(data), 4):
            k = data[i:i + 4]
            t = lut.get(k)
            if t is None:
                t = lut[k] = bytes((k[3],)) + rgb_to_565(k[0], k[1], k[2])
            out += t
    return w, h, bytes(out)


# ---------------------------------------------------------------- RLE codec
def rle_decode(blob, bpp):
    """Decode one compressed image blob. Returns (w, h, pixel bytes)."""
    first = struct.unpack_from("<I", blob, 0)[0]
    h = (first & 0x1FFFFF) // 4
    rows = struct.unpack_from("<%dI" % h, blob, 0)
    out = bytearray()
    w = None
    expect = 4 * h
    for r, v in enumerate(rows):
        off, ln = v & 0x1FFFFF, v >> 21
        if off != expect:
            raise ValueError("row %d offset %d != %d" % (r, off, expect))
        expect += ln
        p, e = off, off + ln
        start = len(out)
        while p < e:
            c = blob[p]
            p += 1
            if c & 0x80:
                out += blob[p:p + bpp] * (c & 0x7F)
                p += bpp
            else:
                out += blob[p:p + bpp * c]
                p += bpp * c
        if p != e:
            raise ValueError("row %d overruns its length" % r)
        rw = (len(out) - start) // bpp
        if w is None:
            w = rw
        elif rw != w:
            raise ValueError("row %d width %d != %d" % (r, rw, w))
    if align4(expect) != len(blob):
        raise ValueError("blob size %d != align4(%d)" % (len(blob), expect))
    return w, h, bytes(out)


def _rle_row(px):
    """px: list of pixel byte-strings. Reproduces the official encoder exactly."""
    out = bytearray()
    n = len(px)
    i = 0
    while i < n:
        r = 1
        while i + r < n and r < 127 and px[i + r] == px[i]:
            r += 1
        if r >= 3:
            out.append(0x80 | r)
            out += px[i]
            i += r
            continue
        j = i
        # literal: stop before a run of >=3, but only while the literal is <=124 long
        while j < n and j - i < 127:
            if j - i <= 124 and j + 2 < n and px[j] == px[j + 1] == px[j + 2]:
                break
            j += 1
        out.append(j - i)
        out += b"".join(px[i:j])
        i = j
    return bytes(out)


def rle_encode(w, h, pix, bpp):
    rows = []
    stride = w * bpp
    for y in range(h):
        line = pix[y * stride:(y + 1) * stride]
        rows.append(_rle_row([line[k:k + bpp] for k in range(0, stride, bpp)]))
    table = bytearray()
    off = 4 * h
    for r in rows:
        if len(r) > 0x7FF:
            raise ValueError("compressed row too long (%d > 2047 bytes)" % len(r))
        table += struct.pack("<I", (len(r) << 21) | off)
        off += len(r)
    if off > 0x1FFFFF:
        raise ValueError("image too large for 21-bit row offsets")
    blob = bytes(table) + b"".join(rows)
    return blob + b"\0" * (align4(len(blob)) - len(blob))


def raw_decode(blob, w, h, bpp):
    stride = align4(w * bpp)
    if len(blob) != stride * h:
        raise ValueError("raw size %d != %d" % (len(blob), stride * h))
    return b"".join(blob[y * stride:y * stride + w * bpp] for y in range(h))


def raw_encode(w, h, pix, bpp):
    pad = align4(w * bpp) - w * bpp
    return b"".join(pix[y * w * bpp:(y + 1) * w * bpp] + b"\0" * pad for y in range(h))


# ---------------------------------------------------------------- container
def parse(data):
    nimg, nel, version = struct.unpack_from("<HBB", data, 0)
    els = []
    for i in range(nel):
        (off, idx, w, h, x, y, cnt, traw, grav, mode, b18, b19) = struct.unpack_from(
            "<IHHHHHBBBBBB", data, HEADER_SIZE + ELEMENT_SIZE * i)
        els.append(dict(offset=off, first=idx, w=w, h=h, x=x, y=y, count=cnt,
                        type=traw & 0x7F, alpha=bool(traw & ALPHA_FLAG), gravity=grav,
                        mode=mode, b18=b18, b19=b19))
    t = HEADER_SIZE + ELEMENT_SIZE * nel
    sizes = struct.unpack_from("<%dI" % nimg, data, t)
    pos = t + 4 * nimg
    blobs = []
    for s in sizes:
        blobs.append(data[pos:pos + s])
        pos += s
    if pos != len(data):
        raise ValueError("trailing data: %d != %d" % (pos, len(data)))
    return version, els, blobs


def build(version, els, blobs):
    """els: list of dicts as returned by parse (offset/first recomputed)."""
    nimg = len(blobs)
    if nimg > 0xFFFF or len(els) > 0xFF:
        raise ValueError("too many images/elements")
    t = HEADER_SIZE + ELEMENT_SIZE * len(els) + 4 * nimg
    starts = []
    pos = t
    for b in blobs:
        starts.append(pos)
        pos += len(b)
    out = bytearray(struct.pack("<HBB", nimg, len(els), version))
    for e in els:
        traw = (e["type"] & 0x7F) | (ALPHA_FLAG if e["alpha"] else 0)
        out += struct.pack("<IHHHHHBBBBBB", starts[e["first"]], e["first"], e["w"], e["h"],
                           e["x"], e["y"], e["count"], traw, e["gravity"], e["mode"],
                           e["b18"], e["b19"])
    for b in blobs:
        out += struct.pack("<I", len(b))
    for b in blobs:
        out += b
    return bytes(out)
