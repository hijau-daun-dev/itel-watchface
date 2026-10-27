# itel ISW-O43 (SMA smable3, platform JL, prototype AM05) watch-face `.bin` format

Status legend: **[C]** confirmed (byte-exact rebuild of 29 official dials and/or seen in app code),
**[S]** strongly supported by samples, **[G]** guess.

Screen: 466x466 round AMOLED. All integers are little-endian unless stated otherwise.

## 1. File layout

```
+0                header (4 bytes)
+4                element table: nel * 20 bytes
+4+20*nel         image size table: nimg * u32
+4+20*nel+4*nimg  image blobs, concatenated in index order, no gaps
EOF               (no trailer, no checksum, no global padding)
```

No checksum or CRC anywhere in the file **[C]** (any bytes we change rebuild fine, and the file size
equals header + tables + sum(sizes) exactly).

### 1.1 Header (4 bytes)

| off | type | meaning |
|----:|------|---------|
| 0 | u16 | `nimg`: total number of images **[C]** |
| 2 | u8  | `nel`: number of elements **[C]** (so at most 255) |
| 3 | u8  | format version, always `2` in every sample **[S]** |

### 1.2 Element record (20 bytes)

| off | type | field | notes |
|----:|------|-------|-------|
| 0  | u32 | `offset` | absolute file offset of this element's first image blob **[C]** |
| 4  | u16 | `first`  | index of the element's first image in the size table **[C]** |
| 6  | u16 | `w` | glyph/image width (for groups: width of image 0) **[C]** |
| 8  | u16 | `h` | glyph/image height **[C]** |
| 10 | u16 | `x` | anchor x on screen (see gravity) **[C]** |
| 12 | u16 | `y` | anchor y on screen **[C]** |
| 14 | u8  | `count` | number of images in this element **[C]** |
| 15 | u8  | `type` | bits 0-6 = element type id (table below); **bit 7 = has alpha** (pixels are A8+RGB565) **[C]** |
| 16 | u8  | `gravity` | anchor flags, see 1.3 **[S]** |
| 17 | u8  | `mode` | the SDK field `ignoreBlack`. `0` = raw pixels, `4` = JL block-RLE (the app sets 4 when images go through `BmpConvert.bitmapConvertBlock`), `5`/`6` also RLE (extra low bits' meaning unknown **[G]**) |
| 18 | u8  | `b18` | needles: `bottomOffset` = pivot distance from image bottom; `bg_dynamic`: frame interval (units unknown, 10..30 seen) **[S]** |
| 19 | u8  | `b19` | needles: `leftOffset` = pivot x inside image (always w/2 in samples) **[S]** |

Images of an element are consecutive: element *n* uses images `first .. first+count-1`, and elements
appear in image order (`first` of element n+1 = first+count of element n) in every sample **[C]**.
The packer recomputes `offset`/`first`.

This is the same field set as `com.szabh.smable3.watchface.Element(type, hasAlpha, w, h, gravity,
ignoreBlack, x, y, playInterval, bottomOffset, leftOffset, imageBuffers)`; the native
`WatchFaceBuilder.build()` (libsmawatchface.so) serializes it into this layout. Element order in the
file = draw order (back to front) **[S]**.

### 1.3 Gravity (byte 16)

JL/AM05 uses the `_R` bit variant of `WatchFaceBuilder` (the app calls `setX_CENTER(2)`,
`setY_CENTER(16)` for these devices) **[S]**:

| bit | meaning |
|----:|---------|
| 0x01 | x = left edge |
| 0x02 | x = horizontal centre |
| 0x04 | x = right edge |
| 0x08 | y = top edge |
| 0x10 | y = vertical centre |
| 0x20 | y = bottom edge |

Observed values: `0x09` (left/top, almost everything), `0x0a` (centre/top, sensor numbers, centred on
x), `0x0c` (right/top), `0x00` (preview, needles). Renders match the official previews with this
reading: e.g. 30001 steps `x=232, g=0x0a` is centred on the dial axis.

### 1.4 Element type ids

Ids 1-23 and 44 are named constants in `WatchFaceBuilder.java` **[C]**; the others were identified
from the images in official dials **[S]**.

| id | name (tools) | count | meaning / glyph order |
|---:|------|------|------|
| 1 | preview | 1 | 280x280 thumbnail shown in the watch's dial picker, not drawn on the face |
| 2 | background | 1 | full background (usually 466x466 at 0,0; can be smaller, placed at x,y) |
| 3 | needle_hour | 1 | hour hand, image points to 12 o'clock, raw mode |
| 4 | needle_min | 1 | minute hand |
| 5 | needle_sec | 1 | second hand |
| 6 | year | 10 | digits (not seen in samples) |
| 7 | month | 10 or 12 | 10 = digits 0-9 (2 drawn, zero padded); 12 = month names Jan..Dec |
| 8 | day | 10 | digits, 2 drawn |
| 9 | hour | 10 | digits, 2 drawn |
| 10 | min | 10 | digits, 2 drawn |
| 11 | sec | 10 | digits, 2 drawn |
| 12 | ampm | 2 | AM, PM |
| 13 | weekday | 7 | SUN, MON, ... SAT |
| 14 | step | 10 | digits 0-9, variable length |
| 15 | heart | 10/11 | digits; index 10 = "--" (no reading) |
| 16 | calorie | 10 | digits |
| 17 | distance | 10/11 | digits; index 10 = "." |
| 18 | battery | 10 | digits (SDK constant; not seen) |
| 19 | bt | - | Bluetooth status (SDK constant; not seen) |
| 20 | div_hour | 1 | time separator (SDK constant; not seen) |
| 21 | div_month | 1 | date separator (SDK constant; not seen) |
| 22 | icon | 1 | static image overlay |
| 23 | bg_dynamic | n | animation frames, `b18` = frame interval |
| 24 | battery_level | 6 | battery gauge pictures, empty -> full |
| 25 | weather_icon | 12 | weather pictures; order in 20055 looks like unknown, sunny, cloudy, partly cloudy, rain, thunder, thunder+rain, wind, snow, fog, sand/dust, ... (index-to-condition mapping **[G]**) |
| 26 | temperature | 12 | digits 0-9, 10 = "-", 11 = "°" |
| 30 | step_progress | 11 | step-goal ring 0%,10%..100% |
| 37 | distance_unit | 2 | "KM", "MI" |
| 39 | hour_tens | 10 | single digit, individually positioned |
| 40 | hour_units | 10 | " |
| 41 | min_tens | 10 | " |
| 42 | min_units | 10 | " |
| 44 | bg_image_array | n | SDK constant; not seen |

Bit 7 of the type byte is independent of the id: the same id appears with and without alpha
(e.g. hour = 9 or 137, needles always 131/132/133 in samples).

## 2. Image size table

`nimg` x u32 = byte length of each blob, **including** its 4-byte alignment padding **[C]**.
Blob *i* starts at `4 + 20*nel + 4*nimg + sum(size[0..i-1])`; every blob length is a multiple of 4.

## 3. Pixel formats

* No alpha (type bit 7 = 0): 2 bytes/pixel, **RGB565 big-endian** (`RRRRRGGG GGGBBBBB`, high byte
  first) **[C]**.
* Alpha (type bit 7 = 1): 3 bytes/pixel, **A8, then RGB565 big-endian** **[C]** (app:
  `XA8IAXI(argb) = A<<16 | 565`, written as bytes `[A, hi, lo]`). Colour is NOT premultiplied;
  fully transparent pixels still carry a colour (often 0xFFFF) that must be preserved for byte
  exactness.
* 8->5/6 bit conversion is plain truncation (`r>>3, g>>2, b>>3`) **[C]**. The tools expand back with
  bit replication (`v<<3 | v>>2`, `v<<2 | v>>4`), which round-trips exactly.

## 4. Blob encodings

### 4.1 Raw (`mode == 0`; all needles in the samples)

`h` rows; each row = `w * bpp` pixel bytes, then zero padding up to a multiple of 4 bytes. Blob size =
`align4(w*bpp) * h` **[C]**. w,h come from the element record. (The app's `getPointer2` builds exactly
this, cropping the hand to the top 60% of its bitmap and setting `bottomOffset = h - fullHeight/2`,
`leftOffset = w/2`.)

### 4.2 JL block RLE (`mode != 0`; everything else) **[C]**

```
u32 row_table[h]          ; entry = (row_len << 21) | row_offset
                          ; row_offset: 21 bits, from blob start; row_len: 11 bits (max 2047 bytes)
row data ...              ; rows back to back, row 0 at offset 4*h
zero padding to 4 bytes
```

* `h = (row_table[0] & 0x1FFFFF) / 4` and the width is the decoded pixel count of a row, so every
  RLE blob is self-describing. Images inside one element may differ in size (e.g. heart "--" is
  28 px wide while the digits are 14).
* Row data is a sequence of packets:
  * `c & 0x80` -> **run**: `n = c & 0x7F` (1..127) copies of the single following pixel (bpp bytes).
  * else -> **literal**: `n = c` (1..127) pixels follow verbatim.
  * Packets never span rows; each row decodes to exactly `w` pixels.
* Exact encoder used for the official files (reproduced byte for byte in `wfformat._rle_row`):
  ```
  i = 0
  while i < w:
      r = length of run of px[i] (capped at 127)
      if r >= 3: emit run(r); i += r; continue
      j = i
      while j < w and j-i < 127:
          if j-i <= 124 and px[j] == px[j+1] == px[j+2]: break   # run check only while lit <= 124
          j += 1
      emit literal(px[i:j]); i = j
  ```
  The `j-i <= 124` detail (a run starting inside the last 3 slots of a full literal gets absorbed
  into it) was needed for 100% exactness. Runs of 1-2 never appear; literals may contain pairs.

## 5. Conventions seen in official dials

* Element 0 is always the 280x280 preview (RLE, no alpha). Element 1 is the background in 28 of 29
  samples; 10030 uses a full-screen `bg_dynamic` (2 frames, b18=100) instead.
* Typical files: 110-890 KB, 5-17 elements, 5-124 images. Needles are always raw ARGB8565 and come
  last (drawn on top).
* `mode` is constant per file (4 or 6) except needles (0) and one step_progress element (5).

## 6. Things not known / risks for brand-new dials

* Limits enforced by the firmware (max file size, max images, RAM for decoding) are unknown. Largest
  official sample seen: 885,832 bytes; most images: 124; most elements: 17. Staying inside these
  is the safe envelope.
* Whether the firmware requires the preview element / a background element: every official file has
  both, keep them.
* Exact firmware layout rules for variable-length numbers (spacing, whether centring uses the real
  string width), the battery_level / step_progress index mapping, and the frame interval unit are
  inferred, not verified on hardware.
* Meaning of `mode` bits 0/1 (values 5, 6) is unknown; 4 is what the CO FIT app itself emits.
* Type ids 24-42 are inferred from sample artwork; ids not listed have not been observed.
