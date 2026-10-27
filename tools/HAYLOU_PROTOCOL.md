# Haylou Solar Plus (RT3 / LS16): BLE protocol notes for Web Bluetooth

Source: static reading of the jadx output of Haylou Fun (`com.yingsheng.hayloufun`).
Paths below are relative to `scratchpad/haylou/src/sources/` unless they start with `q/`
(classes I re-decompiled with `--show-bad-code`, in `scratchpad/haylou/q/`).
Nothing was sent to any device and no vendor server was contacted.

---

## 1. Platform / SDK selection

| Step | Where | What |
|---|---|---|
| Advertisement | `com/liesheng/haylou/bluetooth/watch/BleDeviceFactory.java:66-77` | Manufacturer data with **company id 21324 = 0x534C**. The payload starts with `3C` (`BleDataInfo.HAYOU_SPECIFICVALUE`), followed by pType, pId, check, color, battery and MAC (`com/liesheng/blescan/bean/WatchBleDataInfo.java:43-66`). The check byte is the sum of the 5 bytes after it, `& 0xFF`. |
| Model table | `com/liesheng/blescan/constant/BleDeviceFactory$2.java:20` | `new FilterDeviceBean("Watch", "LS16", "2", String.valueOf(137), "0534C", "")`, so **pType = 2 (watch), pId = 137 = 0x89** |
| Name map | `com/liesheng/haylou/utils/CommonUtil.java:77` | `put("Watch137", "LS16")` |
| SDK dispatch | `WatchComService.connectDevice()` (the original fails to decompile at line 377; see `q/wcs/sources/com/liesheng/haylou/service/watch/WatchComService.java`) | `switch (boundedDeviceTable.getPid())`: **pid 137 (and 151/153/162) builds `HuaWoWatchControl` (`huawo/d0`)** and calls `BluetoothSDK.addConnectionStateListener` and `SFWatchfaceFilePushManager.init` (SiFli). Other pids map to Youcy (2), Dongxin (155), FitCloud (158), CRP (165-168, 174), Nadal (172) and Haylou (default). |
| Sub-variant | `HuaWoWatchControlHelper.java:3583` | `f5546u = projectNo contains "LS20" or "LS23"`. **LS16 has f5546u = false**, so it uses the Huawo "OTA-style" face path. LS20/LS23 use the SiFli watchface-zip path instead. `projectNo` comes from firmware (`utils/e.java:16`, with an "LS16…002" special case). |

The chip vendor is SiFli: the `com.sifli.*` libraries are present (`libezip.so`, `libsfwatchface.so`), and the SDK has a `huawo/sdk/bluetoothsdk/slifi` package. The application protocol is the **"Huawo" BluetoothSDK** (`com/huawo/sdk/bluetoothsdk/`). The **JieLi RCSP, Realtek AES and mbedtls code is not used for LS16.** `MbedtlsJni` is only used by `com/yingsheng/protocol/haylou/task/HaylouCmdTask.java:36`, which is the older in-house Haylou protocol.

## 2. GATT services and characteristics

`com/huawo/sdk/bluetoothsdk/core/model/BleUUID.java:5-19` (all on the SIG base `-0000-1000-8000-00805f9b34fb`):

| Service | Char | Direction | Use |
|---|---|---|---|
| **0x6006** | 0x8001 | write (app to watch) | command tasks (`DataManager.java:388`) |
| | 0x8002 | notify | command responses |
| | 0x8003 / 0x8004 | write / notify | "void" tasks without a reply (`DataManager.java:324`) and events |
| | 0x8005 / 0x8006 | write / notify | bulk file sender (`files/BleFileSender.java:110`) |
| **0x1530** | 0x1531 | write and notify | OTA/picture control. The SDK calls it `OTA_WRITE_ID`; responses arrive here (`BluetoothSDK.java:3360`). |
| | 0x1532 | write (no reply needed) | OTA/picture data (the SDK calls it `OTA_READ_ID`; the name is misleading) |
| 0xFD35 | – | – | used as a scan filter (`BluetoothSDK.java:4291`) |
| 0x1630 | 0x1631 / 0x1632 | write / notify | "WL" channel (OTA, media, watchface for other chips) |
| SiFli serial | `00000000-0000-0000-6473-5f696c666973` service, char `00000000-0000-0200-6473-5f696c666973` (write and notify) | | SiFli watchface push (`com/sifli/siflicore/blecore/SFBLEManager.java:36-38`) |

Web Bluetooth `optionalServices` should include:
`[0x6006, 0x1530, 0xfd35, 0x1630, '00000000-0000-0000-6473-5f696c666973', 0x180a, 0x180f]`.
The probe that was already run did not include any of these, which explains why only 0x1800 was visible.
Possible `requestDevice` filter: `{manufacturerData:[{companyIdentifier:0x534C, dataPrefix:new Uint8Array([0x3C,0x02,0x89])}]}` or `{namePrefix:'HAYLOU'}`.

Connect sequence in the SDK (`BluetoothSDK.java:3405-3640`, `640-650`, `1291-1310`):
enable notifications on **every** characteristic that has the notify property, request MTU (the app passes 247 at `huawo/d0.java:226`), then set the split size to MTU-3 (`BluetoothSDK.java:5113`). There is no crypto handshake. Chrome negotiates the MTU on its own, so writes should stay at 20 bytes or another conservative size, or the frame should be split.

## 3. Bind and authentication

There is no challenge-response and no AES. The bind is identity-by-hash plus a confirm tap on the watch:

1. `GetUID`: `6F 93 70 01 00 00 8F`. The reply payload is an ASCII string. If it equals `md5_16(userId)`, the watch is already bound to this user (`huawo/f.java`, `ops/BindHandler.java`).
2. Otherwise send `StartConfirmBind`: `6F 93 71 11 00 00 <16 ASCII bytes of md5_16(userId)> 8F` (`ops/StartConfirmBind.java`, 63 s timeout). The watch shows a confirm prompt and the user taps it. Fail code 62 means a factory reset during the bind; 63 means already bound.
3. `SetUserInfo` (height, weight, birthday and so on).
4. `EndBind`: `6F 94 71 01 00 01 8F`.

`md5_16(s)` = `hex(md5(utf8(s))).substring(8,24)` (`interfaces/utils/SecurityUtils.java:28-34`). The userId is the Haylou cloud user id (`huawo/d0.java:241-300`), but **any string works for a local client**. Binding to a new id probably unbinds the phone app (the app then sees a mismatch and offers to rebind).
Other bind variants: `StartSifliBind` `6F 92 71 01 00 01 8F` and `StartSifliBindWithoutConfirm` (cmd 0x92 with a TLV time payload).
Classic BT bonding (`createBond`, `requestLS16Bond`) is only needed for calls and audio. GATT does not need it.
**Nothing native or secret is needed. All of it can be done in JS.**

## 4. Framing (Huawo command channel, 0x6006/0x8001 to 0x8002)

```
6F | cmd | type | len_lo len_hi | payload[len] | 8F
type: 0x70 = get, 0x71 = set      (all multi-byte ints little-endian)
```
`interfaces/task/DataParser.java:33-46`, `ops/base/GetTask.java`, `ops/base/SetTask.java`.
There is no CRC on command frames. Writes use `BleManager.write(…, split=true)`, so a frame is cut into MTU-3 pieces with no extra header. The reply is reassembled until `len+6` bytes have arrived.

* **Set ACK**: 8 bytes, `6F ?? ?? 02 00 <echoed cmd> <status> 8F`. Status 0 means OK (`SetTask.parse`).
* **Get reply**: same cmd byte, payload = business bytes. Cmd 0xBF means a multi-packet reply with index/count at offsets 8 and 10.
* Many payloads use TLV: `type(1) len(1) data` (`ops/models/inners/ValueUnit.java`).

| Purpose | Bytes |
|---|---|
| Device type | `6F 03 70 01 00 00 8F` |
| Firmware version | `6F 03 70 01 00 07 8F` |
| Device info | `6F 03 70 01 00 08 8F` |
| Battery | `6F 08 70 01 00 01 8F` |
| Current face id | `6F 0F 70 01 00 02 8F` |
| Face id list | `6F 1E 70 01 00 00 8F` |
| **Set time** | `6F 04 71 0C 00 YYYY(le16) MM DD hh mm ss fmt 00 tzSign tzH tzM 8F`. fmt: 1 = 24h, 2 = 12h. tzSign: 1 = east. (`ops/SetDeviceTime.java`, bad-code dump) |
| Switch face | `6F 42 71 05 00 01 id(le32) 8F` |
| Delete face | `6F 42 71 05 00 02 id(le32) 8F` |
| **Get OTA address for face id** | `6F 1E 70 05 00 01 id(le32) 8F`. Reply payload: `[x] addr(4)`. `FF FF FF FF` means no slot or unknown (`ops/GetOtaAddress.java`). |
| **Enter OTA** | `6F 0E 71 05 00 00 addr(4) 8F` (`ops/EnterOta.java`) |

## 5. Watch-face pipeline for LS16

### Download (app side)
`POST app/watch/plateList` and `POST app/watch/plateDetail` (`com/liesheng/module_device/repository/DeviceService.java:43,76`).
`DialDetail.plateFile` is the file URL and `plateId` is a hex string.
`DialDetailViewModel$synDialFile$1` fetches the raw bytes into a DiskLruCache keyed by md5(url) (`v7/b.java`). **The app does no decryption and no signature check.** It passes the bytes straight to `sendPlate(plateId, bytes)`.

### Transfer (`HuaWoWatchControlHelper.sendPlate`, `:3718-3724`, and `BluetoothSDK.setOnlineWatchfaceForLS`, `BluetoothSDK.java:4722`)
1. `GetOtaAddress(parseLong(plateId,16))` returns a 4-byte flash address.
2. `blob = addr(4) || faceFile`, sent as `OtaData(type=Picture=4)`.
3. `OtaControl` (`interfaces/ota/OtaControl.java`):
   * Command 0x8001: `EnterOta(addr)`, then wait for the ACK.
   * Write to 0x1531: `01 totalLen(le32)`. The reply on 0x1531 is `[01, status]`. Status 0 means start failed, 0x3A (58) is an error and 0xFF is an error.
   * Write to 0x1531: `02 04 addr(4) len(le32) crc(4) 14`. Here `len` = face file length without the address and `crc` = **CRC-16/CCITT-FALSE** (init 0xFFFF) of the face file, zero-extended to 4 bytes (`BytesUtils.crc32`, `BytesUtils.java:118`, which is mis-named). The reply is `[02, ok]`.
   * Data: the face is cut into **2048-byte pieces** (`OtaData.java`, `sizeOfPiece`). Each piece is written to **0x1532** in ≤ min(128, MTU-3) byte packets, at most 20 packets per burst. The watch replies on 0x1531 with `[03, ?, 02]` = send the next piece, or `[03, ?, 04]` = all received.
   * Write `04` (check CRC) to 0x1531. The reply is `[04, …]`.
   * Write `05` (end) to 0x1531. The reply `[05, …]` means done.
4. After that the app sets the current face id (`SetWatchfaceID` `6F 0F 71 06 00 02 04 id(le32) 8F` / `SwitchWatchface`).

### Custom / DIY face (built on the phone, no server file needed)
`sendDiyPlate` (`HuaWoWatchControlHelper.java:3693-3705`) builds `SimpleCustomWatchface(bg 466x466, thumb 264x264, time/date colour)` with `id = parseLong(plateId,16)` and calls `CustomWatchfaceHandler` (`interfaces/ops/CustomWatchfaceHandler.java`):
1. `SetCustomWatchface` on 0x8001: `6F 1E 71 len 02 id(le32) {idx type 02 04 colorRGBA-bytes-reversed}… 8F`. Widgets are Time (13) and Date (4), with optional position `{idx type 00 04 x(le16) y(le16)}` (`ops/SetCustomWatchface.java`).
2. `GetOtaAddress(id)`. If the result is null, the SDK treats it as success with no image.
3. Image blob: `addr(4) || hdr(le32 = (w<<10 | h<<21) + 4) || RGB565-BE(bg) || hdr(thumb) || RGB565-BE(thumb) || crc16(bgPixels)(2) || (byte)id || "UFACE"`. The RGB565 is written big-endian, row-major, with an 8x8 ordered dither (`interfaces/utils/ImageUtil.java:261-277`).
4. The blob is sent with the same OTA procedure, type Picture.

### SiFli zip path (LS20/LS23 only; not LS16 per `f5546u`)
`com/sifli/watchfacesdk/*`: the zip is unpacked and each file is pushed by relative path. Frames go over the SiFli serial characteristic `cateID(4) flag len(le16) payload`, with flags 0 = single, 1 = first, 2 = middle, 3 = last. Commands: 0 EntireStart(type le16, phone=2, totalLen le32), 13 Space, 2 FileStart(len le32, nameLen le16, name), 4 FileData(index le32 starting at 1, ≤ min(4096, device maxDataLen)) acked per slice, 6 FileEnd, 8 EntireEnd, 10/11 LoseCheck. Optional 4-byte padding plus CRC32-MPEG2 (`siflicore/util/FileUtil.java:20-70`). This path is documented here in case `getProjectNo` on this unit turns out to be LS20 or LS23.

## 6. Feasibility (Web Bluetooth on Windows Chrome)

| Goal | Verdict | Notes |
|---|---|---|
| (a) Connect and read info | **Easy** | Add 0x6006 (and 0x1530) to optionalServices, start notifications on 0x8002, send plain frames. No auth is needed for gets; binding is only md5 of an arbitrary string plus a tap on the watch. |
| (b) Push an official face file | **Medium** | The face files are raw blobs with no app-side encryption, and the OTA-like protocol is fully visible in Java. Risks: you need the file and its `plateId` (both come from the vendor API, which I did not touch), and firmware may reject an id it does not know (GetOtaAddress returns FFFFFFFF). The chunk and ACK flow on 0x1531/0x1532 must be matched exactly, and Chrome does not expose the MTU, so use small packets (≤ 20 bytes is safe; 128 if the negotiated MTU is large). |
| (c) Own faces | **Medium (background/DIY), Hard (fully custom layouts)** | A DIY face (any 466x466 background, 264x264 thumbnail, time and date colours and positions) can be built entirely in JS from `CustomWatchfaceHandler` and needs only a valid DIY `plateId`. The binary format of the official online faces is not documented in the APK (no builder for LS16), so a fully custom layout would mean reverse-engineering a downloaded face file. |

**Main blocker:** none of it is cryptographic. The practical unknowns are (1) which face ids the LS16 firmware accepts in `GetOtaAddress`, and (2) the internal format of server face files if you want more than the DIY background-plus-widgets face. Everything above is static analysis and has not been tested against the live watch.

---

## 7. DIY implementation details (follow-up)

The coordinator's live read-only test matched the framing in section 4: device type "LS16002", face id 10097 = 0x2771, and UID is a 16-hex string. 0x8006 does not exist on this unit.

### 7.1 How the DIY plateId is chosen (LS16 / pid 137)
* `DialDiyFragment.java:107` picks `HuaWoDiyWatchFaceViewModel` when the model is LS16 or LS18.
* `HuaWoDiyWatchFaceViewModel$synData$1` uses `id = f7001v`. That field is empty by default and is reset to "" when the user changes the background (`f7003y`). An empty id is replaced by `DiyWatchFaceViewModel.p(pngBytes)` (`DiyWatchFaceViewModel.java:188-197`):
  `id = 20000 + CRC16_XMODEM(pngBytesOfThumbnail)` (poly 0x1021, init 0, MSB-first, `service/watch/youcy/b.java:22-37`). It is formatted with `Integer.toString(id,16)` and parsed back with `parseLong(hex,16)` in `sendDiyPlate`. **The range is 20000..85535 (0x4E20..0x14E1F).** The id is never fetched from the server.
* `f7001v` is only set to a non-computed value when the user re-selects an earlier DIY entry from the local "recent" list (`DialDiyFragment.o()`, `:469-475`). That entry is stored locally as type "custom" (`DiyWatchFaceViewModel.java:369`).
* No other literal DIY ids exist. The literal "20000" is the only one. The server `plateList`/`plateDetail` are not used for DIY.

### 7.2 EnterOta, GetOtaAddress, and what happens after the transfer
* `GetOtaAddress(id)` sends `6F 1E 70 05 00 01 id0 id1 id2 id3 8F` (id little-endian 32-bit). The reply payload is `P = frame[5 .. 5+len)` and must be at least 5 bytes. The address is `P[1..]`: everything after the first byte, which is a sub-command or status. **The whole of `P[1..]` is prepended to the image.** `OtaData` then treats data[0..3] as the address and data[4..] as the image, so the payload should be exactly 5 bytes. If `P[1..4] == FF FF FF FF`, the address is null. For DIY (`CustomWatchfaceHandler`) a null address means the SDK reports success and sends no image. For online faces a null address would crash the app.
* `EnterOta(addr)` sends `6F 0E 71 05 00 00 a0 a1 a2 a3 8F`. The address bytes are copied raw from the reply with no endian swap. The ACK has the generic SetTask form: 8 bytes, with `ack[5] == 0x0E` and `ack[6]` = status (0 = OK). The timeout is 10 s.
* **After the transfer the app sends neither SetWatchfaceID nor SwitchWatchface.** For both DIY (`w0.onSuccess`, `HuaWoWatchControlHelper.java:2477`) and online faces (`x0`, `:2562`) it waits 2000 ms and calls `onCompleted()`. Grep finds no switch or setID call in `com/liesheng`, so the watch presumably activates the face itself. `SwitchWatchface` `6F 42 71 05 00 01 id(le32) 8F` is available if it is needed.

### 7.3 SetCustomWatchface (cmd 0x1E, set) worked example
The frame is `6F 1E 71`, then **a 2-byte little-endian length**, then the payload, then `8F` (`ops/SetCustomWatchface.java`). Payload:
```
02 id(le32)                                   sub-cmd 2 + face id
per widget i (idx = position in widget list):
  [if position and type not hand/dial: i type 00 04 x(le16) y(le16)]
  i type                                      always written
  [if color: i.e. always for simple face: 02 04 R G B A]
  [if style>=0: i type 03 01 style]
```
`setSimpleCustomWatchface` builds the list [Time (13, idx 0), Date (4, idx 1)] with no position and no style.
**Colour bytes.** The app packs `c = A | R<<24 | G<<16 | B<<8` (`module_device/util/ext/a.java`). The SDK writes `intToBytes(c,4)` reversed, which puts **`R G B A` on the wire**. Alpha is `Color.alpha(pickedColor)`, normally 0xFF. The default colour -1 gives `FF FF FF FF`. The app uses one font colour for both widgets; the protocol allows them to differ.
Example with id = 0x4E20, time white, date yellow (len = 0x15 = 21):
```
6F 1E 71 15 00  02 20 4E 00 00  00 0D 02 04 FF FF FF FF  01 04 02 04 FF FF 00 FF  8F
```
The ACK is the generic 8-byte SetTask ACK with `[5] = 0x1E`.

### 7.4 Image blob, CRC and OTA transfer
**Building the blob:**
```
addr(4)
le32(((466<<10)|(466<<21))+4) = 04 48 47 3A
bgPix  466*466*2
le32(((264<<10)|(264<<21))+4) = 04 20 04 21
thPix  264*264*2
crcLo crcHi (byte)id 55 46 41 43 45 ("UFACE")
```
* **Header.** The header is an LVGL v7 `lv_img_header_t` (little-endian): bits 0-4 are cf and 4 = LV_IMG_CF_TRUE_COLOR, bits 10-20 are w and bits 21-31 are h. The `+4` is the colour-format code.
* **Pixels.** RGB565, **big-endian (hi byte first)**, row-major (`(y*w+x)*2`). Images are centre-cropped and scaled (`ThumbnailUtils.extractThumbnail`).
* **Dither.** An 8x8 ordered dither is applied before truncation, using `k=((y&7)<<3)+(x&7)`. Each channel is `min(channel+table[k],255)>>bits`. R uses `iArr` (values 0..8), G uses `iArr2` (0..4) and B uses `iArr3` (0..8) (`interfaces/utils/ImageUtil.java:262-264`; copy the tables verbatim). The dither is cosmetic.
* **Footer CRC.** `crc16` = CRC-16/CCITT-FALSE (poly 0x1021, init 0xFFFF, not reflected, no xorout) over **bgPix only** (the big-endian bytes, without the header), stored low byte first. The id byte is the low byte of the id.
* **Size.** 573,720 bytes plus 4, which is 281 pieces of 2048 bytes.

**OTA.** Commands go to 0x1531 and replies are notified on 0x1531. Data goes to 0x1532 (`interfaces/ota/OtaControl.java`).

| Step | Write on 0x1531 | Reply on 0x1531 |
|---|---|---|
| start | `01 totalLen(le32)`. totalLen **includes** the 4-byte address prefix. | `01 st` |
| settings | `02 04 addr(4) imgLen(le32) crc16(le16) 00 00 14`. imgLen and crc exclude the address. `0x14` = 20 packets per piece. | `02 st`, then the app sends piece 0 |
| piece | data on 0x1532 | `03 st 02` = send the next piece; `03 st 04` = all received |
| check | `04` | `04 st` |
| end | `05` | `05 st`, then done (the app waits 1 s) |

**Errors.** `st` (byte 1) must be non-zero. `00` means start failed and `3A` (58) means fail. The SDK's 0xFF check never fires, because a Java byte cannot equal 255. No abort command exists. Stop on error and let the timeout or a reconnect clean up.
**Data packets.** Piece k = image[k*2048, +2048]. It is sent as sequential writes of `min(128, MTU-3)` bytes to 0x1532. Each write waits for the previous one to complete; there is no extra delay, and writes use the characteristic's default type (with response). **The SDK sends at most 20 packets per piece and never continues inside a piece, so packets must be at least 103 bytes; use 128.** Smaller writes totalling 2048 might also work, but that is unverified.
**Timeouts.** Start, piece and end replies: `10 + 20*(MB-1)/12` s. Settings and check replies: `15 + 90*(MB-1)/12` s. MB is the total size in MiB, minimum 1, so for DIY that is 10 s and 15 s.

### 7.5 Brick and data-loss risks
* Use only the address returned by `GetOtaAddress`. **Never invent one.**
* `settings[1]` must be **4 (Picture)**. 1 = Platform firmware, 2 = touch panel, 3 = HR sensor, 10 = Patch and 11 = Bootloader write firmware regions and could brick the watch (`OtaDataType.java`).
* App and SDK guards:
  * An `FF FF FF FF` address skips or aborts the transfer.
  * The CRC check (`04`) lets the watch reject a corrupt image.
  * Commands on 0x6006 are refused while OTA runs.
* There is no slot-size check and no rollback on the phone side. Keep exactly 466/264.
* `StartConfirmBind` with a new id unbinds the official app. `ResetDevice` and `removeBond` exist; do not send them.
