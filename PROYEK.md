# Dial Loader: watch face untuk itel ISW-O43

Web app lokal untuk mengirim watch face ke jam **itel ISW-O43** lewat Bluetooth laptop (Web Bluetooth di Chrome/Edge), ditambah alat Python untuk membuat watch face sendiri.

Status per 2026-10-27:
- Kirim watch face resmi dan buatan sendiri ke itel: **terbukti jalan**.
- Ada 54 desain di `D:\watch`.
- Dukungan Haylou Solar Plus: **dihentikan sementara** (fokus itel), lihat bagian 8.

---

## 1. Menjalankan

```
cd D:\APP\SRC\laragon\www\itel-watchface
python server.py
```

1. Buka **http://localhost:8765** di **Chrome atau Edge laptop**. Firefox tidak mendukung Web Bluetooth.
2. Matikan Bluetooth HP (atau tutup paksa CO FIT). Jam hanya mau satu koneksi BLE.
3. Klik **Konek ke jam**, pilih "itel ISW-O43", lalu tunggu status **terhubung & siap**.
4. Klik watch face di katalog. Pengiriman ±100–400 KB butuh sekitar 20–60 detik.

Kebutuhan: Windows dengan Bluetooth LE, **Python 3** + **Pillow** (`pip install pillow`), dan Chrome/Edge.

## 2. Struktur

```
itel-watchface/
  index.html          web app: Web Bluetooth, katalog, tab kategori, kirim
  server.py           server lokal :8765: file statis, /oss/ = proxy+cache katalog resmi,
                      /mine/ = koleksi D:\watch (WATCH_DIR bisa diganti lewat env)
  build_catalog.py    bangun catalog.json (katalog resmi gabungan 619 face, tanpa duplikat)
  catalog.json        hasil build_catalog.py
  cache/              cache unduhan katalog resmi (bisa dihapus, terisi lagi otomatis)
  PROYEK.md           dokumen ini
  tools/
    FORMAT.md         spesifikasi format .bin watch face itel (JL/AM05)
    HAYLOU_PROTOCOL.md protokol Haylou Solar Plus (hasil bongkar app, sebagian teruji)
    wfformat.py       codec format .bin
    wfunpack.py       .bin -> PNG + layout.json
    wfpack.py         layout.json + PNG -> .bin
    wfrender.py       render pratinjau tanpa jam
    fonts/            DSEG7 (lisensi OFL)
    _work/            hasil bongkar sampel resmi (referensi, boleh dihapus)
    designs/
      wflib.py        pustaka desain (Design, glyph, jarum, animasi, autocenter)
      koleksi.py      PINTU UTAMA: bangun semua desain -> D:\watch + koleksi.json
      koleksi_*.py    desain per seri (it, it2, anim, game, op, anime, anime2, orbit, wall, wall2, wall3)
      taktis.py       generator seri Taktis
      export_haylou.py latar untuk Haylou DIY (*.hbg.png), dipanggil otomatis oleh koleksi.py
      assets/         wallpaper sumber (milik user, untuk dipakai sendiri)
      out/            folder kerja per desain (layout.json + PNG), hasil build
D:\watch\             KOLEKSI SIAP PAKAI: <nama>.bin, <nama>.png (pratinjau), koleksi.json, README.txt
```

## 3. Membuat ulang atau menambah desain

```
cd D:\APP\SRC\laragon\www\itel-watchface\tools\designs
python -I koleksi.py D:/watch
```

Perintah ini membangun ulang semua desain, menulis `koleksi.json` (judul, kategori, animasi), lalu mengekspor latar Haylou.

Menambah desain baru:
1. Buat fungsi yang mengembalikan `Design(...)` di salah satu `koleksi_*.py` (contoh paling sederhana: `koleksi_it2.py`), lalu masukkan ke tuple `ALL` modul itu.
2. Kalau modulnya baru, daftarkan di `koleksi.py` → `main()`.
3. Atur kategori di `koleksi.py` → `category_of()` (set `ANALOG`/`GAMING`/`IT`, atau `ANIME_PREFIX`).
4. **Aturan nama:** desain beranimasi **wajib berakhiran `_anim`**.
5. Untuk desain dari wallpaper: salin gambar ke `designs/assets/`, lalu contoh caranya ada di `koleksi_wall2.py` (`crop_square`, `time_row`/`time_stack`, `anim_embers`/`anim_lightning`/`anim_pulse`/`anim_flame`).

## 4. Aturan desain (hasil uji di jam)

- **Ringan = lancar.** Versi dengan 12 elemen dan banyak sensor (suhu, cuaca, detak, kalori) membuat buka notifikasi lag. Versi ±10 elemen tanpa alpha lancar.
- Angka **tanpa alpha**: glyph opaque di atas warna polos (latar hitam, atau inti hitam lewat `shadow()` untuk foto).
- Jarum jam tetap RGBA raw, seperti watch face resmi.
- Animasi (`bg_dynamic`): 6–8 frame, area sedang, sebagian besar hitam. Nilai `interval` belum pasti satuannya (kemungkinan 10 ms).
- Batas aman file: ≤ ~886 KB, ≤ ~124 gambar (watch face resmi terbesar).
- Preferensi user: **latar hitam pekat, jam besar, ada detik, isi di tengah**.
- Elemen **persen baterai (tipe 18)** belum terbukti. Uji dulu `zz_tes_baterai.bin` sebelum memakai versi `*_info_anim`.

## 5. Protokol itel (ringkas, terbukti)

- Chip JL, prototype `AM05`, firmwareFlag `itel_ISW_O43`, layar 466×466, ioBufferSize 1018.
- GATT Nordic UART `6e400001-…` (tulis `…0002`, notify `…0003`).
- Frame: `AB | flags|1 | len BE (payload+3) | CRC16-ARC BE dari byte 6 | cmd | key | keyFlag | payload`. Reply flag 0x10, NACK 0x20. Setiap pesan dari jam di-ACK dengan frame reply kosong.
- Bind: `IDENTITY 03 01` CREATE + int32 → jam mengirim info perangkat.
- Kirim watch face: `WATCH_FACE 07 01` UPDATE, payload `slot(1) | total BE32 | offset BE32 | data (≤1018)`. **Progres datang sebagai REPLY** `status | total | completed`, lalu potongan berikutnya dikirim mulai `completed`.
- Katalog resmi: `https://api-oss.iot-solution.net/watchFace/JL/AM05/default/info.txt` (tanpa login, tanpa CORS, sehingga lewat proxy `/oss/`).
- Format file .bin: `tools/FORMAT.md`.

## 6. Pindah ke perangkat (laptop) baru

**Wajib disalin:**

| Salin | Ukuran | Keterangan |
|---|---|---|
| `D:\APP\SRC\laragon\www\itel-watchface\` (tanpa `cache\`) | ±55 MB | web app + semua alat & sumber desain |
| `D:\watch\` | ±19 MB | koleksi watch face siap kirim |

**Boleh tidak disalin:**
- `itel-watchface\cache\` (±94 MB): cache katalog resmi, terisi lagi otomatis.
- `tools\_work\` (±16 MB): sampel referensi hasil bongkar.
- `tools\designs\out\` (±20 MB): dibuat ulang oleh `koleksi.py`. Watch face `taktis` diambil dari `out\taktis_mini_sec.*`, jadi kalau folder ini tidak disalin, jalankan dulu `python -I taktis.py --mini --sec`.

**Di perangkat baru:**
1. Pasang Python 3, lalu `pip install pillow`.
2. Pastikan Chrome/Edge terbaru dan Bluetooth LE aktif.
3. Kalau path `D:\watch` berbeda, jalankan server dengan `set WATCH_DIR=E:\path\watch` lalu `python server.py`. Untuk build, `koleksi.py <folder>`.
4. Font yang dipakai generator desain adalah bawaan Windows 10/11: Bahnschrift, Consolas, Georgia, Segoe UI, Impact, Yu Gothic, dan MS Gothic. DSEG7 sudah ada di `tools/fonts`.
5. Jam itel tidak perlu disetel ulang. Bind dari laptop baru otomatis saat konek pertama, dan Haylou Fun/CO FIT di HP tetap bisa dipakai bergantian.

**Opsional (untuk Claude Code):** catatan memori proyek ini ada di
`C:\Users\Pongo\.claude\projects\d--APP-SRC-laragon-www-rc\memory\project_itel_watchface_webapp.md`.
Salin ke lokasi yang sama di perangkat baru kalau mau sesi Claude berikutnya langsung paham konteksnya. Dokumen ini sendiri sudah cukup sebagai pegangan.

## 7. Ide lanjutan (belum dikerjakan)

- Fitur kontrol jam: cari jam, kirim cuaca, notifikasi dari laptop atau webhook, dashboard kesehatan + export CSV. Daftar perintah ada di `BleKey` milik SDK CO FIT. Masih tahap perencanaan.
- APK Android (WebView + BLE native) supaya bisa jalan tanpa laptop. Masih ide.
- Koleksi khusus Haylou terpisah (lihat bagian 8).

## 8. Haylou Solar Plus (DIHENTIKAN SEMENTARA)

- Protokol sudah dibongkar: `tools/HAYLOU_PROTOCOL.md`. Kode di `index.html` (bagian "Haylou Solar Plus").
- Sudah teruji: konek dan baca info (LS16002, firmware V1.0.0R0.8T0.9H0.0B45, UID bind `4a1750e8d7db6f78`, **jangan bind baru**).
- Kirim watch face DIY: sudah diimplementasikan (latar 466 + thumbnail 264 + widget jam/tanggal firmware), lengkap dengan pengaman (tipe OTA 4 saja, alamat dari jam). Hasil di jam: posisi jam/tanggal belum pas, jadi ada panel penggeser posisi.
- Rencana kalau dilanjutkan: ukur posisi widget firmware dengan panel penggeser, lalu buat koleksi Haylou terpisah (`D:\watch\haylou\`) yang dirancang untuk posisi jam firmware.
