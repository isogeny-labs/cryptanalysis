"""OpenPGP key inventory: APT/RPM keyrings, GnuPG home directories.

Keyring *files* (``/etc/apt/trusted.gpg*``, ``/etc/apt/keyrings``,
``/usr/share/keyrings``, ``/etc/pki/rpm-gpg``) are always read with the built-in
OpenPGP packet parser (RFC 4880 old/new packet headers; v3, v4, v5 and v6 (RFC
9580) public keys; ASCII armor; GnuPG ``pubring.kbx`` key blocks).  It yields
algorithm, size and curve of the primary key and every subkey, plus the digest
algorithm of the key self-signatures (SHA-1 or MD5 self-signatures are classic
findings).  Only the *public* part of a key packet is parsed; secret key
material is never read into any structure.

GnuPG home directories are listed with ``gpg --with-colons --list-keys`` when
``gpg`` is installed and the live root is scanned.  To keep the scan read-only
(gpg writes lock files and trust databases) the keyrings are first copied to a
private temporary home directory and listed there.  Without gpg, or for an
offline root, the same files are parsed directly.  Secret keys are only
counted (``private-keys-v1.d``) or read from legacy ``secring.gpg`` public
parts, never copied.

One PGP_KEY asset is produced per primary key with PUBLIC_KEY uses for the
primary key (context ``pgp-primary``) and each subkey (``pgp-subkey``) and HASH
uses (context ``pgp-selfsig``).  Collectors never grade.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import os
import re
import shutil
import struct
import tempfile
import time
from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional, Set, Tuple

from .. import util
from ..model import Asset, AssetKind, CryptoUse, Primitive
from . import register
from ._confparse import ctx_glob, file_attrs, is_root_host, logical
from .base import Collector, ScanContext

HASH_NAMES = {1: "md5", 2: "sha1", 3: "ripemd160", 8: "sha256", 9: "sha384", 10: "sha512", 11: "sha224",
              12: "sha3-256", 14: "sha3-512"}

# curve OID (hex of the DER content bytes) -> (canonical curve, bits)
CURVE_OIDS = {
    "2a8648ce3d030101": ("p-192", 192), "2b81040021": ("p-224", 224), "2a8648ce3d030107": ("p-256", 256),
    "2b81040022": ("p-384", 384), "2b81040023": ("p-521", 521), "2b8104000a": ("secp256k1", 256),
    "2b2403030208010107": ("brainpoolp256r1", 256), "2b240303020801010b": ("brainpoolp384r1", 384),
    "2b240303020801010d": ("brainpoolp512r1", 512), "2b06010401da470f01": ("curve25519", 256),   # Ed25519 (legacy EdDSA)
    "2b060104019755010501": ("curve25519", 256),                                                 # Curve25519 (ECDH)
}

SELFSIG_TYPES = (0x10, 0x11, 0x12, 0x13, 0x1F)


def algo_name(algo_id: int, curve: Optional[str] = None) -> str:
    if algo_id in (1, 2, 3):
        return "rsa"
    if algo_id in (16, 20):
        return "elgamal"
    if algo_id == 17:
        return "dsa"
    if algo_id == 18 or algo_id in (25, 26):
        return "ecdh"
    if algo_id == 19:
        return "ecdsa"
    if algo_id in (22, 27):
        return "ed25519"
    if algo_id == 28:
        return "ed448"
    if algo_id == 21:
        return "dh"
    return "unknown"


def pgp_curve(name: Optional[str]) -> Optional[str]:
    """GnuPG / OpenPGP curve name -> canonical curve name."""
    if not name:
        return None
    n = name.strip().lower()
    return {"nistp192": "p-192", "nistp224": "p-224", "nistp256": "p-256", "nistp384": "p-384", "nistp521": "p-521",
            "ed25519": "curve25519", "cv25519": "curve25519", "curve25519": "curve25519", "x25519": "curve25519",
            "ed448": "curve448", "cv448": "curve448", "x448": "curve448"}.get(n, n)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class KeyPart:
    algo_id: int
    algorithm: str
    key_bits: Optional[int] = None
    curve: Optional[str] = None
    created: Optional[int] = None
    expires: Optional[int] = None
    version: Optional[int] = None
    fingerprint: Optional[str] = None
    keyid: Optional[str] = None
    caps: str = ""
    revoked: bool = False
    expired_flag: bool = False       # validity 'e' reported by gpg
    secret: bool = False
    sig_created: int = 0             # creation time of the self-signature that gave caps/expires


@dataclass
class PgpKey:
    primary: KeyPart
    subkeys: List[KeyPart] = field(default_factory=list)
    uids: List[str] = field(default_factory=list)
    selfsig_hashes: Dict[str, Set[str]] = field(default_factory=dict)   # hash name -> {sigtype labels}
    source: str = ""


# ---------------------------------------------------------------------------
# Armor and packets
# ---------------------------------------------------------------------------

def crc24(data: bytes) -> int:
    crc = 0xB704CE
    for b in data:
        crc ^= b << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def dearmor(data: bytes) -> bytes:
    """Concatenate the payloads of all ASCII-armored blocks (CRC and headers ignored)."""
    out = bytearray()
    for m in re.finditer(rb"-----BEGIN PGP [A-Z ]+-----[ \t]*\r?\n(.*?)-----END PGP [A-Z ]+-----", data, re.S):
        body = m.group(1).replace(b"\r", b"")
        lines = body.split(b"\n")
        i = 0
        while i < len(lines) and lines[i].strip() and b":" in lines[i]:      # armor headers
            i += 1
        payload = []
        for ln in lines[i:]:
            ln = ln.strip()
            if not ln:
                continue
            if ln.startswith(b"="):                                          # CRC-24 line
                break
            payload.append(ln)
        try:
            out += base64.b64decode(b"".join(payload) + b"=" * (-len(b"".join(payload)) % 4))
        except (ValueError, base64.binascii.Error):
            continue
    return bytes(out)


def iter_packets(data: bytes) -> Iterator[Tuple[int, bytes]]:
    """Yield (tag, body) for each OpenPGP packet; stops quietly on malformed data."""
    p, n = 0, len(data)
    while p < n:
        b = data[p]
        p += 1
        if not b & 0x80:
            return
        if b & 0x40:                                   # new format
            tag = b & 0x3F
            body = bytearray()
            while True:
                if p >= n:
                    return
                o = data[p]
                p += 1
                partial = False
                if o < 192:
                    ln = o
                elif o < 224:
                    if p >= n:
                        return
                    ln = ((o - 192) << 8) + data[p] + 192
                    p += 1
                elif o == 255:
                    if p + 4 > n:
                        return
                    ln = struct.unpack(">I", data[p:p + 4])[0]
                    p += 4
                else:
                    ln = 1 << (o & 0x1F)
                    partial = True
                if p + ln > n:
                    return
                body += data[p:p + ln]
                p += ln
                if not partial:
                    break
            yield tag, bytes(body)
        else:                                          # old format
            tag = (b >> 2) & 0x0F
            lt = b & 3
            if lt == 3:
                ln = n - p
            else:
                w = (1, 2, 4)[lt]
                if p + w > n:
                    return
                ln = int.from_bytes(data[p:p + w], "big")
                p += w
            if p + ln > n:
                return
            yield tag, data[p:p + ln]
            p += ln


def _mpi(body: bytes, p: int) -> Tuple[int, bytes, int]:
    bits = struct.unpack(">H", body[p:p + 2])[0]
    nb = (bits + 7) // 8
    if p + 2 + nb > len(body):
        raise ValueError("short MPI")
    return bits, body[p + 2:p + 2 + nb], p + 2 + nb


def parse_public_key_packet(body: bytes, tag: int = 6) -> KeyPart:
    """Parse the public part of a key packet (tags 5, 6, 7, 14)."""
    ver = body[0]
    created = struct.unpack(">I", body[1:5])[0]
    part = KeyPart(algo_id=0, algorithm="unknown", created=created, version=ver)
    if ver == 3:
        validity_days = struct.unpack(">H", body[5:7])[0]
        part.algo_id = body[7]
        bits_n, n, p = _mpi(body, 8)
        bits_e, e, p = _mpi(body, p)
        part.algorithm, part.key_bits = "rsa", bits_n
        if validity_days:
            part.expires = created + validity_days * 86400
        try:
            fp = hashlib.md5(n + e, usedforsecurity=False).hexdigest().upper()    # v3 fingerprint is MD5 by definition
        except TypeError:
            fp = hashlib.md5(n + e).hexdigest().upper()
        part.fingerprint, part.keyid = fp, n[-8:].hex().upper()
        return part
    if ver not in (4, 5, 6):
        return part
    part.algo_id = body[5]
    if ver == 4:
        start = 6
        end = len(body)
    else:
        mlen = struct.unpack(">I", body[6:10])[0]
        start, end = 10, 10 + mlen
    a = part.algo_id
    p = start
    try:
        if a in (1, 2, 3):
            part.key_bits, _, p = _mpi(body, p)
            _, _, p = _mpi(body, p)
        elif a in (16, 20, 21):
            part.key_bits, _, p = _mpi(body, p)
            _, _, p = _mpi(body, p)
            _, _, p = _mpi(body, p)
        elif a == 17:
            part.key_bits, _, p = _mpi(body, p)
            for _i in range(3):
                _, _, p = _mpi(body, p)
        elif a in (18, 19, 22):
            ol = body[p]
            oid = body[p + 1:p + 1 + ol].hex()
            p += 1 + ol
            _, _, p = _mpi(body, p)
            if a == 18 and p < len(body):
                kl = body[p]
                p += 1 + kl
            curve, bits = CURVE_OIDS.get(oid, (oid, None))
            part.curve, part.key_bits = curve, bits
            if a == 22 and curve == "curve25519":
                part.key_bits = 256
        elif a in (25, 27):
            part.curve, part.key_bits, p = "curve25519", 256, start + 32
        elif a in (26, 28):
            part.curve, part.key_bits = "curve448", 448
            p = start + (56 if a == 26 else 57)
        else:
            p = end
    except (ValueError, struct.error, IndexError):
        p = end
    part.algorithm = algo_name(a, part.curve)
    pub = body[:p] if ver == 4 else body[:end]
    if ver == 4:
        fp = hashlib.sha1(b"\x99" + struct.pack(">H", len(pub)) + pub).hexdigest().upper()
        part.fingerprint, part.keyid = fp, fp[-16:]
    else:
        hdr = b"\x9a" if ver == 5 else b"\x9b"
        fp = hashlib.sha256(hdr + struct.pack(">I", len(pub)) + pub).hexdigest().upper()
        part.fingerprint, part.keyid = fp, fp[:16]
    return part


@dataclass
class Sig:
    version: int
    sigtype: int
    pubalgo: int
    hashalgo: int
    created: int = 0
    issuer_keyid: Optional[str] = None
    issuer_fp: Optional[str] = None
    key_expires: Optional[int] = None      # seconds after key creation (0 = never)
    key_flags: Optional[int] = None


def _subpackets(area: bytes, sig: Sig) -> None:
    p = 0
    while p < len(area):
        o = area[p]
        p += 1
        if o < 192:
            ln = o
        elif o < 255:
            if p >= len(area):
                return
            ln = ((o - 192) << 8) + area[p] + 192
            p += 1
        else:
            if p + 4 > len(area):
                return
            ln = struct.unpack(">I", area[p:p + 4])[0]
            p += 4
        if ln < 1 or p + ln > len(area):
            return
        t = area[p] & 0x7F
        d = area[p + 1:p + ln]
        p += ln
        if t == 2 and len(d) == 4:
            sig.created = struct.unpack(">I", d)[0]
        elif t == 9 and len(d) == 4:
            sig.key_expires = struct.unpack(">I", d)[0]
        elif t == 16 and len(d) == 8:
            sig.issuer_keyid = d.hex().upper()
        elif t == 33 and len(d) >= 21:
            sig.issuer_fp = d[1:].hex().upper()
        elif t == 27 and d:
            sig.key_flags = d[0]


def parse_signature_packet(body: bytes) -> Optional[Sig]:
    try:
        ver = body[0]
        if ver == 3:
            s = Sig(3, body[2], body[15], body[16])
            s.created = struct.unpack(">I", body[3:7])[0]
            s.issuer_keyid = body[7:15].hex().upper()
            return s
        if ver not in (4, 5, 6):
            return None
        s = Sig(ver, body[1], body[2], body[3])
        w = 2 if ver == 4 else 4
        p = 4
        hl = int.from_bytes(body[p:p + w], "big")
        p += w
        _subpackets(body[p:p + hl], s)
        p += hl
        ul = int.from_bytes(body[p:p + w], "big")
        p += w
        _subpackets(body[p:p + ul], s)
        return s
    except (IndexError, struct.error):
        return None


def _caps(flags: Optional[int]) -> str:
    if flags is None:
        return ""
    out = ""
    if flags & 0x01:
        out += "C"
    if flags & 0x02:
        out += "S"
    if flags & 0x0C:
        out += "E"
    if flags & 0x20:
        out += "A"
    return out


def parse_keyring(data: bytes, source: str = "") -> List[PgpKey]:
    """Parse armored or binary OpenPGP key data into primary keys with subkeys."""
    if b"-----BEGIN PGP" in data:
        data = dearmor(data)
    keys: List[PgpKey] = []
    cur: Optional[PgpKey] = None
    target: Optional[KeyPart] = None
    for tag, body in iter_packets(data):
        try:
            if tag in (5, 6):
                part = parse_public_key_packet(body, tag)
                part.secret = tag == 5
                cur = PgpKey(primary=part, source=source)
                keys.append(cur)
                target = part
            elif tag in (7, 14) and cur is not None:
                part = parse_public_key_packet(body, tag)
                part.secret = tag == 7
                cur.subkeys.append(part)
                target = part
            elif tag == 13 and cur is not None:
                cur.uids.append(body.decode("utf-8", "replace"))
                target = cur.primary
            elif tag == 2 and cur is not None:
                sig = parse_signature_packet(body)
                if sig is not None:
                    _apply_sig(cur, target, sig)
        except (IndexError, ValueError, struct.error):
            continue
        if len(keys) > 5000:
            break
    return keys


def _apply_sig(key: PgpKey, target: Optional[KeyPart], sig: Sig) -> None:
    prim = key.primary
    if sig.issuer_fp and prim.fingerprint:
        mine = prim.fingerprint.endswith(sig.issuer_fp[-16:]) or prim.fingerprint.startswith(sig.issuer_fp[:16])
    elif sig.issuer_keyid and prim.keyid:
        mine = sig.issuer_keyid == prim.keyid
    else:
        mine = True                                   # issuer unknown: assume a self-signature
    if not mine:
        return
    hname = HASH_NAMES.get(sig.hashalgo, f"hash-{sig.hashalgo}")
    if sig.sigtype in SELFSIG_TYPES:
        key.selfsig_hashes.setdefault(hname, set()).add(f"0x{sig.sigtype:02x}")
        _update(prim, sig)
    elif sig.sigtype == 0x18 and target is not None and target is not prim:
        key.selfsig_hashes.setdefault(hname, set()).add("0x18")
        _update(target, sig)
    elif sig.sigtype == 0x20:
        prim.revoked = True
    elif sig.sigtype == 0x28 and target is not None and target is not prim:
        target.revoked = True


def _update(part: KeyPart, sig: Sig) -> None:
    if sig.created and sig.created >= part.sig_created:
        part.sig_created = sig.created
        if sig.key_flags is not None:
            part.caps = _caps(sig.key_flags)
        if sig.key_expires is not None:
            part.expires = (part.created or 0) + sig.key_expires if sig.key_expires else None


def kbx_keyblocks(data: bytes) -> List[bytes]:
    """Extract the OpenPGP key blocks of a GnuPG keybox (pubring.kbx)."""
    out = []
    p = 0
    while p + 16 <= len(data):
        ln = struct.unpack(">I", data[p:p + 4])[0]
        if ln < 16 or p + ln > len(data):
            break
        if data[p + 4] == 2:                          # OpenPGP blob
            off, klen = struct.unpack(">II", data[p + 8:p + 16])
            if off + klen <= ln:
                out.append(data[p + off:p + off + klen])
        p += ln
    return out


def parse_key_file(data: bytes, source: str = "") -> List[PgpKey]:
    if data[8:12] == b"KBXf":
        keys: List[PgpKey] = []
        for blk in kbx_keyblocks(data):
            keys.extend(parse_keyring(blk, source))
        return keys
    return parse_keyring(data, source)


# ---------------------------------------------------------------------------
# gpg --with-colons
# ---------------------------------------------------------------------------

def _unescape(s: str) -> str:
    return re.sub(r"\\x([0-9a-fA-F]{2})", lambda m: chr(int(m.group(1), 16)), s)


def _int(s: str) -> Optional[int]:
    return int(s) if s.isdigit() else None


def parse_colons(text: str) -> List[PgpKey]:
    """Parse `gpg --with-colons --list-keys/--list-secret-keys` output."""
    keys: List[PgpKey] = []
    cur: Optional[PgpKey] = None
    last: Optional[KeyPart] = None
    for line in text.splitlines():
        f = line.split(":")
        rt = f[0]
        if rt in ("pub", "sec", "sub", "ssb"):
            f += [""] * (18 - len(f))
            algo = _int(f[3]) or 0
            curve = pgp_curve(f[16]) if f[16] else None
            bits = _int(f[2])
            if curve == "curve25519":
                bits = 256
            elif curve == "curve448":
                bits = 448
            elif curve in ("p-256", "p-384", "p-521") and (bits is None or bits == 0):
                bits = int(curve[2:])
            part = KeyPart(algo_id=algo, algorithm=algo_name(algo), key_bits=bits, curve=curve, created=_int(f[5]),
                           expires=_int(f[6]), caps="".join(ch for ch in f[11] if ch.islower()).upper(), revoked=f[1] == "r", expired_flag=f[1] == "e",
                           secret=rt in ("sec", "ssb"))
            if rt in ("pub", "sec"):
                cur = PgpKey(primary=part, source="gpg")
                keys.append(cur)
            elif cur is not None:
                cur.subkeys.append(part)
            last = part
        elif rt == "fpr" and last is not None and len(f) > 9:
            last.fingerprint = f[9].upper()
            last.keyid = last.fingerprint[-16:]
        elif rt == "uid" and cur is not None and len(f) > 9:
            cur.uids.append(_unescape(f[9]))
    return keys


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

def _iso(ts: Optional[int]) -> Optional[str]:
    if ts is None:
        return None
    try:
        return _dt.datetime.fromtimestamp(ts, _dt.timezone.utc).date().isoformat()
    except (OverflowError, OSError, ValueError):
        return None


@register
class PgpCollector(Collector):
    name = "pgp"
    description = "OpenPGP keys: APT/RPM keyrings and GnuPG home directories"

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        assets: List[Asset] = []
        for path in self._keyring_files(ctx):
            assets.extend(self._file_assets(ctx, path, "keyring"))
        for home in self._gnupg_homes(ctx):
            try:
                assets.extend(self._home_assets(ctx, home))
            except Exception as e:
                ctx.warn(f"pgp: {home}: {type(e).__name__}: {e}")
        return assets

    # -- keyring files --------------------------------------------------------

    def _keyring_files(self, ctx: ScanContext) -> List[str]:
        pats = ["/etc/apt/trusted.gpg", "/etc/apt/trusted.gpg.d/*.gpg", "/etc/apt/trusted.gpg.d/*.asc",
                "/etc/apt/keyrings/*", "/etc/pki/rpm-gpg/*", "/usr/share/keyrings/*.gpg", "/usr/share/keyrings/*.asc",
                "/usr/share/keyrings/*.pgp"]
        out, seen = [], set()
        for pat in pats:
            for p in ctx_glob(ctx, pat):
                rp = os.path.realpath(p)
                if rp not in seen and os.path.isfile(p):
                    seen.add(rp)
                    out.append(p)
        for ep in ctx.extra_paths:
            if os.path.isfile(ep) and ep.endswith((".gpg", ".asc", ".pgp", ".kbx")) and os.path.realpath(ep) not in seen:
                out.append(ep)
        return out

    def _file_assets(self, ctx: ScanContext, path: str, origin: str) -> List[Asset]:
        data = util.read_bytes(path)
        if data is None:
            a = Asset(AssetKind.PGP_KEY, f"PGP keyring {logical(ctx, path)}", logical(ctx, path), self.name, ctx.hostname,
                      attributes={"origin": origin, **file_attrs(path)})
            a.errors.append(f"cannot read {path}")
            return [a]
        keys = parse_key_file(data, logical(ctx, path))
        return [self._key_asset(ctx, k, logical(ctx, path), origin, file_attrs(path)) for k in keys]

    # -- GnuPG homes ----------------------------------------------------------

    def _gnupg_homes(self, ctx: ScanContext) -> List[str]:
        if is_root_host(ctx):
            homes = [os.path.join(h, ".gnupg") for h in util.home_dirs()]
        else:
            homes = ctx_glob(ctx, "/home/*/.gnupg") + ctx_glob(ctx, "/root/.gnupg")
        out, seen = [], set()
        for h in homes:
            rh = os.path.realpath(h)
            if os.path.isdir(h) and rh not in seen:
                seen.add(rh)
                out.append(h)
        return out

    def _home_assets(self, ctx: ScanContext, home: str) -> List[Asset]:
        ring_names = ("pubring.kbx", "pubring.gpg", "trustedkeys.gpg", "secring.gpg")
        rings = [os.path.join(home, n) for n in ring_names if os.path.isfile(os.path.join(home, n))]
        priv_dir = os.path.join(home, "private-keys-v1.d")
        secret_files = len([f for f in os.listdir(priv_dir) if f.endswith(".key")]) if os.path.isdir(priv_dir) else 0
        attrs = {"origin": "gnupg-home", "gnupg_home": logical(ctx, home), "secret_key_files": secret_files}
        keys: Optional[List[PgpKey]] = None
        used_gpg = False
        if is_root_host(ctx) and util.which("gpg") and rings:
            keys = self._gpg_list(ctx, rings)
            used_gpg = keys is not None
        if keys is None:
            keys = []
            for r in rings:
                data = util.read_bytes(r)
                if data:
                    keys.extend(parse_key_file(data, logical(ctx, r)))
        attrs["parsed_with"] = "gpg" if used_gpg else "builtin"
        out = []
        seen: Set[str] = set()
        for k in keys:
            fp = k.primary.fingerprint or id(k)
            if fp in seen:
                continue
            seen.add(fp)
            out.append(self._key_asset(ctx, k, logical(ctx, home), "gnupg-home", dict(attrs, **file_attrs(home))))
        return out

    def _gpg_list(self, ctx: ScanContext, rings: List[str]) -> Optional[List[PgpKey]]:
        """List keys with gpg on a private copy of the public keyrings (never touches the real homedir)."""
        tmp = tempfile.mkdtemp(prefix="cryptoscan-gpg-")
        try:
            os.chmod(tmp, 0o700)
            copied = 0
            for r in rings:
                if os.path.basename(r) == "secring.gpg":
                    continue                                   # secret keyring is never copied
                try:
                    shutil.copy(r, os.path.join(tmp, os.path.basename(r)))
                    copied += 1
                except OSError:
                    continue
            if not copied:
                return None
            res = util.run_cmd(["gpg", "--batch", "--no-tty", "--no-auto-check-trustdb", "--no-permission-warning",
                                "--homedir", tmp, "--with-colons", "--list-keys"], timeout=ctx.cmd_timeout)
            util.run_cmd(["gpgconf", "--homedir", tmp, "--kill", "all"], timeout=5)
            if not res.ok or not res.stdout.strip():
                return None
            keys = parse_colons(res.stdout)
            for k in keys:
                k.source = "gpg"
            return keys
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # -- asset building -----------------------------------------------------------

    def _key_asset(self, ctx: ScanContext, k: PgpKey, location: str, origin: str, attrs: Dict[str, object]) -> Asset:
        p = k.primary
        fp = p.fingerprint or ""
        uid0 = k.uids[0] if k.uids else ""
        a = Asset(AssetKind.PGP_KEY, f"PGP key {fp[-16:] or '?'} {uid0}".strip(), location, self.name, ctx.hostname,
                  attributes=dict(attrs))
        now = int(time.time())
        a.attributes.update({"fingerprint": fp, "key_id": p.keyid, "version": p.version,
                             "created": _iso(p.created), "expires": _iso(p.expires), "subkey_count": len(k.subkeys),
                             "user_ids": k.uids[:3], "secret": p.secret or any(s.secret for s in k.subkeys),
                             "revoked": p.revoked, "expired": bool(p.expired_flag or (p.expires and p.expires < now))})
        if p.version == 3:
            a.attributes["legacy_v3_key"] = True
        for part, ctxname in [(p, "pgp-primary")] + [(s, "pgp-subkey") for s in k.subkeys]:
            expired = bool(part.expired_flag or (part.expires and part.expires < now))
            a.add(CryptoUse(Primitive.PUBLIC_KEY, part.algorithm, key_bits=part.key_bits, curve=part.curve,
                            raw=f"{part.algorithm}{part.key_bits or ''}", context=ctxname,
                            extra={"capabilities": part.caps, "expired": expired, "revoked": part.revoked,
                                   "fingerprint": part.fingerprint, "algo_id": part.algo_id}))
        for h, kinds in sorted(k.selfsig_hashes.items()):
            a.add(CryptoUse(Primitive.HASH, h, raw=h, context="pgp-selfsig", extra={"sigtypes": sorted(kinds)}))
        return a
