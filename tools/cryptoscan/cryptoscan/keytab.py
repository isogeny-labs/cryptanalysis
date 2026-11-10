"""Parser for MIT/Heimdal Kerberos keytab files (read-only, never exposes keys).

File layout (all integers big-endian for version 0x0502; *native* byte order for
the legacy version 0x0501)::

    uint16  file format version (0x0502 or 0x0501)
    entry*  int32 size            (negative: a deleted slot of |size| bytes)
            uint16 num_components (v1: counts the realm as well)
            counted-string realm  (uint16 length + bytes)
            counted-string component * num_components
            uint32 name_type      (absent in v1)
            uint32 timestamp
            uint8  vno8           (low 8 bits of the key version number)
            uint16 enctype
            uint16 key length ; key bytes
            [uint32 vno]          (only when room remains in the entry)

The key bytes are *skipped*: only their length is returned, so no key material
can leak into reports, logs or JSON output.
"""

from __future__ import annotations

import struct
import sys
from dataclasses import dataclass, field
from typing import List, Optional

MAGIC_V2 = 0x0502
MAGIC_V1 = 0x0501


class KeytabError(ValueError):
    """The data is not a keytab (bad magic number)."""


@dataclass
class KeytabEntry:
    principal: str            # "comp1/comp2@REALM"
    realm: str
    components: List[str]
    name_type: Optional[int]  # None for v1 keytabs
    timestamp: int            # seconds since the epoch
    kvno: int
    enctype: int              # Kerberos etype number (RFC 3961 registry)
    key_length: int           # length in bytes only; the key itself is never kept


@dataclass
class KeytabResult:
    version: int
    entries: List[KeytabEntry] = field(default_factory=list)
    deleted_slots: int = 0
    truncated: bool = False


class _Reader:
    def __init__(self, data: bytes, endian: str) -> None:
        self.d, self.p, self.e = data, 0, endian

    def left(self) -> int:
        return len(self.d) - self.p

    def take(self, n: int) -> bytes:
        if n < 0 or self.p + n > len(self.d):
            raise struct.error("short read")
        b = self.d[self.p:self.p + n]
        self.p += n
        return b

    def u8(self) -> int:
        return self.take(1)[0]

    def u16(self) -> int:
        return struct.unpack(self.e + "H", self.take(2))[0]

    def u32(self) -> int:
        return struct.unpack(self.e + "I", self.take(4))[0]

    def counted(self) -> str:
        return self.take(self.u16()).decode("utf-8", "replace")


def parse_keytab_ex(data: bytes) -> KeytabResult:
    """Parse a keytab; raises KeytabError on a bad header, tolerates truncation."""
    if len(data) < 2:
        raise KeytabError("file too short for a keytab header")
    if data[0] == 0x05 and data[1] in (0x01, 0x02):
        version = 0x0500 | data[1]
    else:
        raise KeytabError("bad keytab magic %02x%02x" % (data[0], data[1]))
    # v2 is always big-endian; v1 is stored in the writer's native order.  The
    # two header bytes are 05 01, so the file itself cannot tell us the order:
    # assume native (as MIT does) and fall back to the other order if entries
    # do not parse.
    if version == MAGIC_V2:
        return _parse_entries(data, ">", version)
    native = "<" if sys.byteorder == "little" else ">"
    other = ">" if native == "<" else "<"
    res = _parse_entries(data, native, version)
    if res.truncated and not res.entries:
        alt = _parse_entries(data, other, version)
        if alt.entries:
            return alt
    return res


def _parse_entries(data: bytes, endian: str, version: int) -> KeytabResult:
    res = KeytabResult(version=version)
    r = _Reader(data, endian)
    r.p = 2
    sizefmt = endian + "i"
    while r.left() >= 4:
        size = struct.unpack(sizefmt, r.take(4))[0]
        if size < 0:
            res.deleted_slots += 1
            if r.left() < -size:
                res.truncated = True
                break
            r.p += -size
            continue
        if size == 0:
            continue
        if r.left() < size:
            res.truncated = True
            break
        body = _Reader(r.take(size), endian)
        try:
            ncomp = body.u16()
            if version == MAGIC_V1:
                ncomp -= 1                      # v1 counts the realm in num_components
            realm = body.counted()
            comps = [body.counted() for _ in range(max(ncomp, 0))]
            name_type = body.u32() if version == MAGIC_V2 else None
            ts = body.u32()
            vno = body.u8()
            etype = body.u16()
            klen = body.u16()
            body.take(klen)                     # key bytes are discarded on purpose
            if body.left() >= 4:
                vno = body.u32()
        except struct.error:
            res.truncated = True
            continue
        princ = "/".join(comps) + "@" + realm
        res.entries.append(KeytabEntry(principal=princ, realm=realm, components=comps, name_type=name_type,
                                       timestamp=ts, kvno=vno, enctype=etype, key_length=klen))
    if r.left():
        res.truncated = True
    return res


def parse_keytab(data: bytes) -> List[KeytabEntry]:
    """Return the live (non-deleted) entries of a keytab."""
    return parse_keytab_ex(data).entries
