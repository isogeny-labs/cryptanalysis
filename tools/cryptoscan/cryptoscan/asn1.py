"""Minimal DER decoder: enough for X.509 certificates, SubjectPublicKeyInfo,
PKCS#1 / PKCS#8 / SEC1 keys and PKCS#7 bundles.  Not a general ASN.1 library:
it decodes the TLV structure and leaves interpretation to the caller.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class DERError(ValueError):
    pass


# Universal tags we care about
BOOLEAN = 0x01
INTEGER = 0x02
BIT_STRING = 0x03
OCTET_STRING = 0x04
NULL = 0x05
OID = 0x06
UTF8STRING = 0x0C
SEQUENCE = 0x10
SET = 0x11
PRINTABLESTRING = 0x13
T61STRING = 0x14
IA5STRING = 0x16
UTCTIME = 0x17
GENERALIZEDTIME = 0x18
BMPSTRING = 0x1E


@dataclass
class Node:
    tag_class: int          # 0 universal, 1 application, 2 context, 3 private
    constructed: bool
    tag: int
    header_len: int
    value: bytes            # content octets
    raw: bytes              # full TLV
    children: List[Node] = field(default_factory=list)

    # ---- convenience ---------------------------------------------------
    @property
    def is_sequence(self) -> bool:
        return self.tag_class == 0 and self.tag == SEQUENCE

    @property
    def is_set(self) -> bool:
        return self.tag_class == 0 and self.tag == SET

    def context(self, n: int) -> Optional[Node]:
        """First child with context-specific tag [n]."""
        for c in self.children:
            if c.tag_class == 2 and c.tag == n:
                return c
        return None

    def as_int(self) -> int:
        if self.tag != INTEGER:
            raise DERError(f"expected INTEGER, got tag {self.tag}")
        return int.from_bytes(self.value, "big", signed=True)

    def as_oid(self) -> str:
        if self.tag != OID:
            raise DERError(f"expected OID, got tag {self.tag}")
        return decode_oid(self.value)

    def as_bitstring(self) -> Tuple[int, bytes]:
        if self.tag != BIT_STRING:
            raise DERError(f"expected BIT STRING, got tag {self.tag}")
        if not self.value:
            raise DERError("empty BIT STRING")
        return self.value[0], self.value[1:]

    def as_str(self) -> str:
        if self.tag == BMPSTRING:
            return self.value.decode("utf-16-be", "replace")
        if self.tag in (UTF8STRING,):
            return self.value.decode("utf-8", "replace")
        return self.value.decode("latin-1", "replace")

    def as_time(self) -> _dt.datetime:
        s = self.value.decode("ascii", "replace")
        try:
            if self.tag == UTCTIME:
                # YYMMDDHHMM[SS]Z   (RFC 5280: seconds mandatory, 50..99 -> 19xx)
                if len(s) == 11:
                    s = s[:10] + "00" + s[10:]
                t = _dt.datetime.strptime(s, "%y%m%d%H%M%SZ")
                if t.year >= 2050:
                    t = t.replace(year=t.year - 100)
                return t.replace(tzinfo=_dt.timezone.utc)
            if self.tag == GENERALIZEDTIME:
                if "." in s:
                    s = s.split(".")[0] + "Z"
                if len(s) == 11:
                    s = s[:10] + "00" + s[10:]
                return _dt.datetime.strptime(s, "%Y%m%d%H%M%SZ").replace(tzinfo=_dt.timezone.utc)
        except ValueError as e:
            raise DERError(f"bad time {s!r}: {e}") from e
        raise DERError(f"not a time tag: {self.tag}")


def decode_oid(b: bytes) -> str:
    if not b:
        raise DERError("empty OID")
    arcs = []
    first = b[0]
    arcs.append(first // 40 if first < 80 else 2)
    arcs.append(first % 40 if first < 80 else first - 80)
    v = 0
    for byte in b[1:]:
        v = (v << 7) | (byte & 0x7F)
        if not byte & 0x80:
            arcs.append(v)
            v = 0
    if v:
        raise DERError("truncated OID arc")
    return ".".join(str(a) for a in arcs)


def _read_tlv(data: bytes, off: int) -> Tuple[Node, int]:
    if off >= len(data):
        raise DERError("unexpected end of data")
    b0 = data[off]
    tag_class = b0 >> 6
    constructed = bool(b0 & 0x20)
    tag = b0 & 0x1F
    p = off + 1
    if tag == 0x1F:
        tag = 0
        while True:
            if p >= len(data):
                raise DERError("truncated high tag")
            tag = (tag << 7) | (data[p] & 0x7F)
            more = data[p] & 0x80
            p += 1
            if not more:
                break
    if p >= len(data):
        raise DERError("truncated length")
    l0 = data[p]
    p += 1
    if l0 < 0x80:
        length = l0
    elif l0 == 0x80:
        raise DERError("indefinite length not allowed in DER")
    else:
        n = l0 & 0x7F
        if n > 4 or p + n > len(data):
            raise DERError("bad long-form length")
        length = int.from_bytes(data[p:p + n], "big")
        p += n
    end = p + length
    if end > len(data):
        raise DERError("value runs past end of data")
    node = Node(tag_class, constructed, tag, p - off, data[p:end], data[off:end])
    if constructed:
        node.children = decode_all(node.value)
    return node, end


def decode(data: bytes) -> Node:
    """Decode exactly one DER element (trailing bytes are an error)."""
    node, end = _read_tlv(data, 0)
    if end != len(data):
        raise DERError(f"{len(data) - end} trailing bytes after DER element")
    return node


def decode_prefix(data: bytes) -> Tuple[Node, bytes]:
    """Decode one element and return (node, remaining bytes)."""
    node, end = _read_tlv(data, 0)
    return node, data[end:]


def decode_all(data: bytes) -> List[Node]:
    out = []
    off = 0
    while off < len(data):
        node, off = _read_tlv(data, off)
        out.append(node)
    return out
