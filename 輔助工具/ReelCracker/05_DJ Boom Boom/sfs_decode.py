"""SmartFoxServer 2X 二進位封包解碼（FA CHAI 遊戲走 wss://gs.fcg666.net/BlueBox/websocket）

封包格式：
  1 byte header  (0x80=binary, 0x20=zlib 壓縮, 0x08=長度用 4 bytes)
  2/4 bytes 長度
  SFSObject：0x12 + uint16 欄位數 + (uint16 key 長 + key + 型別 byte + 值)...
"""
import struct
import zlib
import json


class _Reader:
    def __init__(self, b):
        self.b, self.i = b, 0

    def take(self, n):
        v = self.b[self.i:self.i + n]
        self.i += n
        return v

    def u8(self):
        return self.take(1)[0]

    def fmt(self, f):
        n = struct.calcsize(f)
        return struct.unpack(">" + f, self.take(n))[0]

    def utf(self):
        return self.take(self.fmt("H")).decode("utf-8", errors="replace")

    def text(self):
        return self.take(self.fmt("i")).decode("utf-8", errors="replace")


_ARR = {9: "?", 11: "h", 12: "i", 13: "q", 14: "f", 15: "d"}


def _value(r):
    t = r.u8()
    if t == 0:
        return None
    if t == 1:
        return r.u8() != 0
    if t == 2:
        return r.fmt("b")
    if t == 3:
        return r.fmt("h")
    if t == 4:
        return r.fmt("i")
    if t == 5:
        return r.fmt("q")
    if t == 6:
        return r.fmt("f")
    if t == 7:
        return r.fmt("d")
    if t == 8:
        return r.utf()
    if t == 10:  # byte array：FA CHAI 把 JSON 放這裡
        raw = r.take(r.fmt("i"))
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                return raw.hex()
    if t in _ARR:
        n = r.fmt("H")
        return [r.fmt(_ARR[t]) for _ in range(n)]
    if t == 16:
        return [r.utf() for _ in range(r.fmt("H"))]
    if t == 17:
        return [_value(r) for _ in range(r.fmt("H"))]
    if t == 18:
        return _object(r)
    if t == 20:
        return r.text()
    raise ValueError(f"未知 SFS 型別 {t} @ {r.i}")


def _object(r):
    out = {}
    for _ in range(r.fmt("H")):
        k = r.utf()
        out[k] = _value(r)
    return out


def decode_packet(data: bytes):
    """回傳解出的 dict（含 c/a/p 欄位）。"""
    hdr = data[0]
    size_len = 4 if hdr & 0x08 else 2
    body = data[1 + size_len:]
    if hdr & 0x20:
        body = zlib.decompress(body)
    r = _Reader(body)
    t = r.u8()
    if t == 18:
        return _object(r)
    r.i = 0
    return _value(r)
