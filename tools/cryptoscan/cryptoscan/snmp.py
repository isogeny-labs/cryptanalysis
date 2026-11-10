"""Minimal SNMP BER codec: just enough for a sysDescr GET and an SNMPv3 discovery.

Supported: SEQUENCE, INTEGER, OCTET STRING, OBJECT IDENTIFIER, NULL, the
GetRequest (0xa0) / GetResponse (0xa2) / Report (0xa8) PDUs.  Nothing here
touches the network; `collectors/netdev.py` sends the packets.  Community
strings are inputs only and are never stored by callers.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

SYS_DESCR = "1.3.6.1.2.1.1.1.0"

T_INT, T_OCTETS, T_NULL, T_OID, T_SEQ = 0x02, 0x04, 0x05, 0x06, 0x30
PDU_GET, PDU_RESPONSE, PDU_REPORT = 0xA0, 0xA2, 0xA8

VERSION_V1, VERSION_V2C, VERSION_V3 = 0, 1, 3


class SnmpError(ValueError):
    """Malformed or unsupported BER."""


# ---------------------------------------------------------------------------
# encoding
# ---------------------------------------------------------------------------

def enc_len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def enc_tlv(tag: int, content: bytes) -> bytes:
    return bytes([tag]) + enc_len(len(content)) + content


def enc_int(v: int) -> bytes:
    if v == 0:
        body = b"\x00"
    else:
        length = (v.bit_length() + 8) // 8 if v > 0 else ((-v - 1).bit_length() + 8) // 8
        body = v.to_bytes(length, "big", signed=True)
    return enc_tlv(T_INT, body)


def enc_octets(b: bytes) -> bytes:
    return enc_tlv(T_OCTETS, b)


def enc_null() -> bytes:
    return enc_tlv(T_NULL, b"")


def enc_oid(oid: str) -> bytes:
    arcs = [int(x) for x in oid.strip(".").split(".")]
    if len(arcs) < 2:
        raise SnmpError("OID needs at least two arcs")
    body = bytearray([arcs[0] * 40 + arcs[1]])
    for a in arcs[2:]:
        chunk = [a & 0x7F]
        a >>= 7
        while a:
            chunk.append(0x80 | (a & 0x7F))
            a >>= 7
        body.extend(reversed(chunk))
    return enc_tlv(T_OID, bytes(body))


def enc_seq(*parts: bytes, tag: int = T_SEQ) -> bytes:
    return enc_tlv(tag, b"".join(parts))


def new_request_id() -> int:
    return struct.unpack(">I", os.urandom(4))[0] & 0x7FFFFFFF


def build_get_request(version: int, community: str, oid: str = SYS_DESCR, request_id: Optional[int] = None) -> bytes:
    """SNMPv1 (version=0) or v2c (version=1) GetRequest for one OID."""
    rid = new_request_id() if request_id is None else request_id
    varbind = enc_seq(enc_oid(oid), enc_null())
    pdu = enc_seq(enc_int(rid), enc_int(0), enc_int(0), enc_seq(varbind), tag=PDU_GET)
    return enc_seq(enc_int(version), enc_octets(community.encode()), pdu)


def build_v3_discovery(msg_id: Optional[int] = None) -> bytes:
    """SNMPv3 engine-discovery request: reportable, noAuthNoPriv, empty engine id and user."""
    mid = new_request_id() if msg_id is None else msg_id
    header = enc_seq(enc_int(mid), enc_int(65507), enc_octets(b"\x04"), enc_int(3))
    usm = enc_seq(enc_octets(b""), enc_int(0), enc_int(0), enc_octets(b""), enc_octets(b""), enc_octets(b""))
    pdu = enc_seq(enc_int(new_request_id()), enc_int(0), enc_int(0), enc_seq(), tag=PDU_GET)
    scoped = enc_seq(enc_octets(b""), enc_octets(b""), pdu)
    return enc_seq(enc_int(VERSION_V3), header, enc_octets(usm), scoped)


# ---------------------------------------------------------------------------
# decoding
# ---------------------------------------------------------------------------

@dataclass
class TLV:
    tag: int
    value: bytes

    @property
    def constructed(self) -> bool:
        return bool(self.tag & 0x20)

    def children(self) -> List[TLV]:
        return decode_all(self.value)


def decode_tlv(data: bytes, pos: int = 0) -> Tuple[TLV, int]:
    if pos + 2 > len(data):
        raise SnmpError("truncated TLV header")
    tag = data[pos]
    if tag & 0x1F == 0x1F:
        raise SnmpError("multi-byte tags unsupported")
    ln = data[pos + 1]
    pos += 2
    if ln & 0x80:
        k = ln & 0x7F
        if k == 0 or k > 4 or pos + k > len(data):
            raise SnmpError("bad length")
        ln = int.from_bytes(data[pos:pos + k], "big")
        pos += k
    if pos + ln > len(data):
        raise SnmpError("truncated TLV body")
    return TLV(tag, data[pos:pos + ln]), pos + ln


def decode_all(data: bytes) -> List[TLV]:
    out: List[TLV] = []
    pos = 0
    while pos < len(data):
        tlv, pos = decode_tlv(data, pos)
        out.append(tlv)
    return out


def decode_int(v: bytes) -> int:
    return int.from_bytes(v, "big", signed=True) if v else 0


def decode_oid(v: bytes) -> str:
    if not v:
        raise SnmpError("empty OID")
    arcs = [v[0] // 40, v[0] % 40]
    acc = 0
    for b in v[1:]:
        acc = (acc << 7) | (b & 0x7F)
        if not b & 0x80:
            arcs.append(acc)
            acc = 0
    return ".".join(str(a) for a in arcs)


@dataclass
class SnmpMessage:
    version: int
    community: Optional[bytes] = None
    pdu_type: Optional[int] = None
    request_id: Optional[int] = None
    error_status: int = 0
    varbinds: List[Tuple[str, int, bytes]] = field(default_factory=list)   # (oid, tag, raw value)
    # v3 only
    msg_id: Optional[int] = None
    flags: Optional[int] = None
    engine_id: Optional[bytes] = None
    engine_boots: Optional[int] = None
    engine_time: Optional[int] = None

    def value_text(self, oid: str) -> Optional[str]:
        for o, tag, val in self.varbinds:
            if o == oid and tag == T_OCTETS:
                return val.decode("utf-8", "replace")
        return None


def _parse_pdu(pdu: TLV, msg: SnmpMessage) -> None:
    kids = pdu.children()
    msg.pdu_type = pdu.tag
    if len(kids) < 4:
        raise SnmpError("short PDU")
    msg.request_id = decode_int(kids[0].value)
    msg.error_status = decode_int(kids[1].value)
    for vb in kids[3].children():
        parts = vb.children()
        if len(parts) == 2 and parts[0].tag == T_OID:
            msg.varbinds.append((decode_oid(parts[0].value), parts[1].tag, parts[1].value))


def parse_message(data: bytes) -> SnmpMessage:
    """Decode a v1/v2c message or an SNMPv3 message (header, USM parameters, scoped PDU)."""
    outer, _ = decode_tlv(data)
    if outer.tag != T_SEQ:
        raise SnmpError("not a SEQUENCE")
    parts = outer.children()
    if len(parts) < 3 or parts[0].tag != T_INT:
        raise SnmpError("bad message layout")
    version = decode_int(parts[0].value)
    msg = SnmpMessage(version=version)
    if version in (VERSION_V1, VERSION_V2C):
        if parts[1].tag != T_OCTETS or not (0xA0 <= parts[2].tag <= 0xA8):
            raise SnmpError("bad v1/v2c layout")
        msg.community = parts[1].value
        _parse_pdu(parts[2], msg)
    elif version == VERSION_V3:
        hdr = parts[1].children()
        if len(hdr) >= 3:
            msg.msg_id = decode_int(hdr[0].value)
            msg.flags = hdr[2].value[0] if hdr[2].value else 0
        if parts[2].tag == T_OCTETS and parts[2].value:
            try:
                usm, _ = decode_tlv(parts[2].value)
                u = usm.children()
                if len(u) >= 3:
                    msg.engine_id = u[0].value
                    msg.engine_boots = decode_int(u[1].value)
                    msg.engine_time = decode_int(u[2].value)
            except SnmpError:
                pass
        if len(parts) > 3 and parts[3].tag == T_SEQ:
            sc = parts[3].children()
            if len(sc) >= 3 and 0xA0 <= sc[2].tag <= 0xA8:
                _parse_pdu(sc[2], msg)
    else:
        raise SnmpError(f"unsupported SNMP version {version}")
    return msg


def build_response(request: bytes, sys_descr: str, version_ok: Tuple[int, ...] = (VERSION_V2C,),
                   communities: Tuple[str, ...] = ("public",)) -> Optional[bytes]:
    """GetResponse for a GET of sysDescr (used by the test agent); None when the request is not acceptable."""
    msg = parse_message(request)
    if msg.version not in version_ok or msg.community is None or msg.community.decode("utf-8", "replace") not in communities:
        return None
    vb = enc_seq(enc_oid(SYS_DESCR), enc_octets(sys_descr.encode()))
    pdu = enc_seq(enc_int(msg.request_id or 0), enc_int(0), enc_int(0), enc_seq(vb), tag=PDU_RESPONSE)
    return enc_seq(enc_int(msg.version), enc_octets(msg.community), pdu)
