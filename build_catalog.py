"""Gabungkan katalog watch face resmi yang cocok untuk itel ISW-O43 (JL, 466x466) jadi catalog.json.

Sumber = folder varian prototype AM05 (hardware sama, merek lain) + AM22 (JL, 466x466).
Duplikat dibuang berdasarkan ETag (= MD5 file .bin) dari request HEAD, tanpa mengunduh isinya.

Jalankan:  python build_catalog.py
"""
import json
import os
import re
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

UPSTREAM = "https://api-oss.iot-solution.net/watchFace/"
SOURCES = [
    ("JL/AM05/default", "Resmi itel"),
    ("JL/AM05/GS3", "AM05 · GS3"),
    ("JL/AM05/RTER", "AM05 · RTER"),
    ("JL/AM05/KW17", "AM05 · KW17"),
    ("JL/AM05/KW18", "AM05 · KW18"),
    ("JL/AM05/HAYLOU", "AM05 · Haylou"),
    ("JL/AM05/IT_WATCH_WR02", "AM05 · IT Watch"),
    ("JL/AM05/FireBoltt", "AM05 · FireBoltt"),
    ("JL/AM22/default", "AM22"),
]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog.json")


def fetch(url, method="GET"):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "okhttp/4.12.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read() if method == "GET" else r.headers
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
        except Exception:  # noqa: BLE001
            pass
        time.sleep(1 + attempt)
    return None


def list_items(path, label):
    raw = fetch(UPSTREAM + path + "/info.txt")
    if not raw:
        print("tidak ada info.txt:", path)
        return []
    info = json.loads(re.sub(rb",\s*([\]}])", rb"\1", raw))
    items = []
    if info.get("categorys"):
        for c in info["categorys"]:
            ext = "gif" if c["type"] == 1 else "png"
            cat = re.sub(r"\d+$", "", c["dir"])
            for n in range(1, c["total"] + 1):
                i = c["type"] * 10000 + n
                items.append({"src": label, "cat": cat,
                              "preview": f"{path}/category/{c['dir']}/{i}.{ext}",
                              "bin": f"{path}/category/{c['dir']}/{i}.bin"})
    else:
        for n in range(1, info["total"] + 1):
            items.append({"src": label, "cat": "lainnya",
                          "preview": f"{path}/preview/{n}.png", "bin": f"{path}/bin/{n}.bin"})
    return items


def head(item):
    h = fetch(UPSTREAM + item["bin"], "HEAD")
    if h is None:
        return None
    item["etag"] = (h.get("ETag") or "").strip('"')
    item["size"] = int(h.get("Content-Length") or 0)
    return item


def main():
    all_items = []
    for path, label in SOURCES:
        items = list_items(path, label)
        print(f"{label}: {len(items)} item, cek ETag…")
        with ThreadPoolExecutor(8) as ex:
            all_items += [it for it in ex.map(head, items) if it]
    seen, result = set(), []
    for it in all_items:  # urutan SOURCES = prioritas; yang pertama dipertahankan
        if it["etag"] in seen:
            continue
        seen.add(it["etag"])
        result.append(it)
    for idx, it in enumerate(result, 1):
        it["id"] = idx
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"generated": time.strftime("%Y-%m-%d %H:%M"), "items": result}, f, ensure_ascii=False)
    by_src = {}
    for it in result:
        by_src[it["src"]] = by_src.get(it["src"], 0) + 1
    print(f"Total unik: {len(result)} dari {len(all_items)}")
    for k, v in by_src.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
