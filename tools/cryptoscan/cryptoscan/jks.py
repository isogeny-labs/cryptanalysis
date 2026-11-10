"""Readers for Java keystores (JKS, JCEKS) and a PKCS#12 sniffer.

Only metadata that is readable without the store password is extracted:

* JKS  (magic 0xFEEDFEED, versions 1 and 2): trusted-certificate entries (tag 2)
  and the certificate chains of private-key entries (tag 1).  The encrypted key
  blob is skipped, but the algorithm OID of its EncryptedPrivateKeyInfo is kept
  (1.3.6.1.4.1.42.2.17.1.1 is the weak proprietary JavaSoft key protector).
* JCEKS (magic 0xCECECECE): the same two entry kinds.  Secret-key entries
  (tag 3) hold a Java-serialised SealedObject and cannot be skipped without
  parsing the serialisation stream, so parsing stops there with a note.
* PKCS#12: detected, never decrypted.  The PBE algorithm OIDs and the MAC digest
  that are visible in the DER are reported.

Standard library only; never raises on malformed input (returns notes/errors).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import asn1

JKS_MAGIC = 0xFEEDFEED
JCEKS_MAGIC = 0xCECECECE

KEY_PROTECTOR_OIDS = {
    "1.3.6.1.4.1.42.2.17.1.1": "JavaSoft proprietary key protector (SHA-1 keystream XOR)",
    "1.3.6.1.4.1.42.2.19.1": "PBEWithMD5AndTripleDES (JCEKS)",
}

PBE_OIDS = {
    "1.2.840.113549.1.12.1.1": ("pbeWithSHAAnd128BitRC4", "rc4", 128),
    "1.2.840.113549.1.12.1.2": ("pbeWithSHAAnd40BitRC4", "rc4", 40),
    "1.2.840.113549.1.12.1.3": ("pbeWithSHAAnd3-KeyTripleDES-CBC", "3des", 168),
    "1.2.840.113549.1.12.1.4": ("pbeWithSHAAnd2-KeyTripleDES-CBC", "3des", 112),
    "1.2.840.113549.1.12.1.5": ("pbeWithSHAAnd128BitRC2-CBC", "rc2", 128),
    "1.2.840.113549.1.12.1.6": ("pbeWithSHAAnd40BitRC2-CBC", "rc2", 40),
    "1.2.840.113549.1.5.13": ("PBES2", None, None),
    "1.2.840.113549.1.5.3": ("pbeWithMD5AndDES-CBC", "des", 56),
    "1.2.840.113549.1.5.10": ("pbeWithSHA1AndDES-CBC", "des", 56),
}
PKCS7_DATA_OID = "1.2.840.113549.1.7.1"
_MAC_HASH_OIDS = {"1.3.14.3.2.26": "sha1", "2.16.840.1.101.3.4.2.1": "sha256", "2.16.840.1.101.3.4.2.2": "sha384",
                  "2.16.840.1.101.3.4.2.3": "sha512", "1.2.840.113549.2.5": "md5"}


@dataclass
class JksEntry:
    alias: str
    kind: str                                   # "trusted" | "key"
    certs: List[bytes] = field(default_factory=list)    # DER
    created_ms: Optional[int] = None
    key_protector_oid: Optional[str] = None


@dataclass
class JksStore:
    format: str                                 # "jks" | "jceks"
    version: int
    entries: List[JksEntry] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.d = data
        self.o = 0

    def need(self, n: int) -> None:
        if n < 0 or self.o + n > len(self.d):
            raise ValueError("truncated keystore")

    def u2(self) -> int:
        self.need(2)
        v = struct.unpack_from(">H", self.d, self.o)[0]
        self.o += 2
        return v

    def u4(self) -> int:
        self.need(4)
        v = struct.unpack_from(">I", self.d, self.o)[0]
        self.o += 4
        return v

    def u8(self) -> int:
        self.need(8)
        v = struct.unpack_from(">Q", self.d, self.o)[0]
        self.o += 8
        return v

    def raw(self, n: int) -> bytes:
        self.need(n)
        b = self.d[self.o:self.o + n]
        self.o += n
        return b

    def utf(self) -> str:
        return self.raw(self.u2()).decode("utf-8", "replace")


def sniff(data: bytes) -> Optional[str]:
    """'jks' | 'jceks' | 'pkcs12' | None."""
    if len(data) >= 4:
        m = struct.unpack(">I", data[:4])[0]
        if m == JKS_MAGIC:
            return "jks"
        if m == JCEKS_MAGIC:
            return "jceks"
    if looks_like_pkcs12(data):
        return "pkcs12"
    return None


def parse_jks(data: bytes) -> JksStore:
    """Parse a JKS or JCEKS keystore without the password."""
    r = _Reader(data)
    magic = r.u4()
    fmt = "jks" if magic == JKS_MAGIC else "jceks"
    if magic not in (JKS_MAGIC, JCEKS_MAGIC):
        raise ValueError("not a Java keystore")
    version = r.u4()
    store = JksStore(fmt, version)
    if version not in (1, 2):
        store.notes.append(f"unknown keystore version {version}")
        return store
    count = r.u4()
    if count > 100000:
        store.notes.append("implausible entry count")
        return store
    try:
        for _ in range(count):
            tag = r.u4()
            alias = r.utf()
            created = r.u8()
            if tag == 1:
                key_len = r.u4()
                blob = r.raw(key_len)
                oid = _epki_oid(blob)
                n = r.u4()
                certs = [_read_cert(r, version) for _ in range(min(n, 1000))]
                store.entries.append(JksEntry(alias, "key", certs, created, oid))
            elif tag == 2:
                store.entries.append(JksEntry(alias, "trusted", [_read_cert(r, version)], created))
            elif tag == 3 and fmt == "jceks":
                store.notes.append("secret-key entry (serialised SealedObject): remaining entries not parsed")
                break
            else:
                store.notes.append(f"unknown entry tag {tag}")
                break
    except ValueError as e:
        store.notes.append(str(e))
    return store


def _read_cert(r: _Reader, version: int) -> bytes:
    if version == 2:
        r.utf()                     # certificate type, normally "X.509"
    return r.raw(r.u4())


def _epki_oid(blob: bytes) -> Optional[str]:
    try:
        seq = asn1.decode(blob)
        return seq.children[0].children[0].as_oid()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# PKCS#12
# ---------------------------------------------------------------------------

def looks_like_pkcs12(der: bytes) -> bool:
    if not der[:1] == b"\x30":
        return False
    try:
        root, _ = asn1.decode_prefix(der)
        return bool(root.is_sequence and len(root.children) >= 2 and root.children[0].tag == asn1.INTEGER
                    and root.children[0].as_int() == 3 and root.children[1].is_sequence
                    and root.children[1].children and root.children[1].children[0].tag == asn1.OID
                    and root.children[1].children[0].as_oid() == PKCS7_DATA_OID)
    except Exception:
        return False


def _oid_der(oid: str) -> bytes:
    parts = [int(x) for x in oid.split(".")]
    body = bytearray([parts[0] * 40 + parts[1]])
    for p in parts[2:]:
        chunk = [p & 0x7F]
        p >>= 7
        while p:
            chunk.append(0x80 | (p & 0x7F))
            p >>= 7
        body.extend(reversed(chunk))
    return b"\x06" + bytes([len(body)]) + bytes(body)


_PBE_DER = {oid: _oid_der(oid) for oid in PBE_OIDS}


def pkcs12_info(der: bytes) -> Dict[str, object]:
    """PBE algorithm OIDs and MAC digest visible in a PKCS#12 file (no password needed)."""
    found: List[str] = [oid for oid, enc in _PBE_DER.items() if enc in der]
    info: Dict[str, object] = {"pbe_oids": sorted(found),
                               "pbe_names": [PBE_OIDS[o][0] for o in sorted(found)]}
    try:
        root, _ = asn1.decode_prefix(der)
        mac = root.children[2]
        digest_info = mac.children[0]
        info["mac_hash"] = _MAC_HASH_OIDS.get(digest_info.children[0].children[0].as_oid(), "unknown")
        if len(mac.children) >= 3:
            info["mac_iterations"] = mac.children[2].as_int()
    except Exception:
        info["mac_hash"] = None
    return info
