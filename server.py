"""Server lokal: file statis + proxy (dengan cache disk) ke katalog watch face resmi.

Jalankan:  python server.py   lalu buka http://localhost:8765
"""
import json
import os
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, "cache")
UPSTREAM = "https://api-oss.iot-solution.net/watchFace/"
PREFIX = "/oss/"
# Watch face buatan sendiri: setiap <nama>.bin (+ <nama>.png sebagai pratinjau) di folder ini.
MINE_DIR = os.environ.get("WATCH_DIR", "D:/watch")
MINE = "/mine/"


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def end_headers(self):
        # Halaman & file koleksi sering berubah: jangan dipakai dari cache browser.
        if not self.path.startswith(PREFIX):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith(PREFIX):
            return self.proxy(self.path[len(PREFIX):].split("?")[0])
        if self.path.startswith(MINE):
            return self.mine(urllib.parse.unquote(self.path[len(MINE):].split("?")[0]))
        return super().do_GET()

    def mine(self, name):
        if name == "list.json":
            items = []
            # koleksi.json (dari tools/designs/koleksi.py) memberi judul + kategori; file lain tetap tampil.
            meta = {}
            try:
                with open(os.path.join(MINE_DIR, "koleksi.json"), encoding="utf-8") as fh:
                    meta = {m["name"]: m for m in json.load(fh)}
            except (OSError, ValueError, KeyError, TypeError):
                pass
            if os.path.isdir(MINE_DIR):
                for f in sorted(os.listdir(MINE_DIR)):
                    if f.lower().endswith(".bin"):
                        base = f[:-4]
                        m = meta.get(base, {})
                        items.append({"name": base, "bin": f, "size": os.path.getsize(os.path.join(MINE_DIR, f)),
                                      "preview": base + ".png" if os.path.exists(os.path.join(MINE_DIR, base + ".png")) else None,
                                      "title": m.get("title"), "category": m.get("category"),
                                      "anim": bool(m.get("anim", base.lower().endswith("_anim"))),
                                      "haylou": m.get("haylou")})
            data = json.dumps({"dir": MINE_DIR, "items": items}).encode()
            ctype = "application/json"
        else:
            path = os.path.join(MINE_DIR, os.path.basename(name))
            if not os.path.isfile(path):
                return self.send_error(404)
            with open(path, "rb") as f:
                data = f.read()
            ctype = "image/png" if name.lower().endswith(".png") else "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def proxy(self, rel):
        if ".." in rel or rel.startswith("/"):
            return self.send_error(400)
        # info.txt bisa berubah, jadi tidak di-cache; preview dan .bin di-cache.
        cached = os.path.join(CACHE, *rel.split("/"))
        use_cache = not rel.endswith("info.txt")
        try:
            if use_cache and os.path.exists(cached):
                with open(cached, "rb") as f:
                    data = f.read()
            else:
                req = urllib.request.Request(UPSTREAM + rel, headers={"User-Agent": "okhttp/4.12.0"})
                with urllib.request.urlopen(req, timeout=60) as r:
                    data = r.read()
                if use_cache:
                    os.makedirs(os.path.dirname(cached), exist_ok=True)
                    with open(cached, "wb") as f:
                        f.write(data)
        except urllib.error.HTTPError as e:
            return self.send_error(e.code)
        except Exception as e:  # noqa: BLE001
            return self.send_error(502, str(e))
        self.send_response(200)
        ctype = {"png": "image/png", "gif": "image/gif", "txt": "text/plain"}.get(rel.rsplit(".", 1)[-1], "application/octet-stream")
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print("Buka http://localhost:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
