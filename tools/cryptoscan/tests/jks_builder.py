"""Test helper: encode JKS / JCEKS keystores from DER certificates (no keytool needed)."""

import hashlib
import struct
from typing import List, Tuple

JKS = 0xFEEDFEED
JCEKS = 0xCECECECE


def _utf(s: str) -> bytes:
    b = s.encode()
    return struct.pack(">H", len(b)) + b


def _epki(oid_der: bytes) -> bytes:
    """EncryptedPrivateKeyInfo with the given AlgorithmIdentifier OID and a dummy payload."""
    alg = b"\x30" + bytes([len(oid_der) + 2]) + oid_der + b"\x05\x00"
    payload = b"\x04\x08" + b"\x00" * 8
    body = alg + payload
    return b"\x30" + bytes([len(body)]) + body


JAVASOFT_PROTECTOR_OID = bytes.fromhex("060a2b060104012a02110101")     # 1.3.6.1.4.1.42.2.17.1.1


def build(entries: List[Tuple], version: int = 2, magic: int = JKS) -> bytes:
    """entries: ("trusted", alias, der) | ("key", alias, [der, ...]) | ("secret", alias)."""
    out = struct.pack(">III", magic, version, len(entries))
    for e in entries:
        kind, alias = e[0], e[1]
        if kind == "trusted":
            out += struct.pack(">I", 2) + _utf(alias) + struct.pack(">Q", 1700000000000)
            if version == 2:
                out += _utf("X.509")
            out += struct.pack(">I", len(e[2])) + e[2]
        elif kind == "key":
            blob = _epki(JAVASOFT_PROTECTOR_OID)
            out += struct.pack(">I", 1) + _utf(alias) + struct.pack(">Q", 1700000000000)
            out += struct.pack(">I", len(blob)) + blob + struct.pack(">I", len(e[2]))
            for der in e[2]:
                if version == 2:
                    out += _utf("X.509")
                out += struct.pack(">I", len(der)) + der
        elif kind == "secret":
            out += struct.pack(">I", 3) + _utf(alias) + struct.pack(">Q", 1700000000000) + b"\xac\xed\x00\x05"
    return out + hashlib.sha1(out).digest()
