"""Private keys, DH parameters and EC parameters on disk.

Scans the same service directories as ``certs_local`` plus user home
directories (``~/.ssh`` identity files and ``*.pub`` are left to ``ssh_local``)
and, with ``deep_fs_scan``, the whole root.  Emits PRIVATE_KEY assets with
``mode``, ``owner``, ``encrypted``, ``fmt``, ``encryption_note``,
``service_key`` (True under /etc, /var, /opt, /srv, /usr/local so the policy only
INFOs unencrypted service keys) and a ``public-key`` use for the public part.
Keys are paired with certificates found in the scanned files by SPKI SHA-256
(RSA and EC keys; the public part is re-encoded with a tiny DER writer);
unpaired keys are not an error.

Key material is only parsed for its public properties; nothing is written,
copied or printed.
"""

from __future__ import annotations

import hashlib
import os
import re
from typing import Dict, List, Optional, Tuple

from .. import asn1, x509
from ..model import Asset, AssetKind, CryptoUse, Primitive
from ..util import file_mode, file_owner, read_bytes
from . import register
from ._certassets import CERT_EXTS, host_home_dirs, iter_candidate_files
from .base import Collector, ScanContext
from .certs_local import SERVICE_DIRS

KEY_EXTS = CERT_EXTS + (".key", ".pk8", ".pkcs8", ".priv", ".private", ".rsa", ".ec", ".dsa", ".dh", ".params")
_HOME_SKIP = {".cache", ".npm", ".cargo", ".rustup", ".local", ".gradle", ".m2", ".docker", "Downloads", ".mozilla",
              ".config", "go", ".nvm", ".pyenv", "venv", ".venv", "snap"}
EXTRA_KEY_DIR_GLOBS = ["/var/lib/*/ssl", "/var/lib/*/pki", "/var/lib/*/tls"]

_RSA_OID = "1.2.840.113549.1.1.1"
_EC_OID = "1.2.840.10045.2.1"


# ---- tiny DER writer -------------------------------------------------------

def _len(n: int) -> bytes:
    if n < 0x80:
        return bytes([n])
    b = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(b)]) + b


def _tlv(tag: int, body: bytes) -> bytes:
    return bytes([tag]) + _len(len(body)) + body


def _int(n: int) -> bytes:
    b = n.to_bytes(max(1, (n.bit_length() + 8) // 8), "big")
    return _tlv(0x02, b)


def _oid(oid: str) -> bytes:
    from ..jks import _oid_der
    return _oid_der(oid)


def rsa_spki(n: int, e: int) -> bytes:
    """SubjectPublicKeyInfo DER of an RSA public key."""
    alg = _tlv(0x30, _oid(_RSA_OID) + b"\x05\x00")
    pub = _tlv(0x30, _int(n) + _int(e))
    return _tlv(0x30, alg + _tlv(0x03, b"\x00" + pub))


def ec_spki(curve_oid: str, point: bytes) -> bytes:
    alg = _tlv(0x30, _oid(_EC_OID) + _oid(curve_oid))
    return _tlv(0x30, alg + _tlv(0x03, b"\x00" + point))


def private_spki_sha256(label: str, der: bytes) -> Optional[str]:
    """SPKI SHA-256 of the public half of an unencrypted RSA/EC private key (None if not derivable)."""
    try:
        seq = asn1.decode(der)
        curve_oid: Optional[str] = None
        if label == "PRIVATE KEY":                       # PKCS#8: unwrap
            alg_id = seq.children[1]
            alg = alg_id.children[0].as_oid()
            inner = asn1.decode(seq.children[2].value)
            if alg == _RSA_OID:
                label, seq = "RSA PRIVATE KEY", inner
            elif alg == _EC_OID:
                label, seq = "EC PRIVATE KEY", inner
                if len(alg_id.children) > 1 and alg_id.children[1].tag == asn1.OID:
                    curve_oid = alg_id.children[1].as_oid()
            else:
                return None
        if label == "RSA PRIVATE KEY":
            return hashlib.sha256(rsa_spki(seq.children[1].as_int(), seq.children[2].as_int())).hexdigest()
        if label == "EC PRIVATE KEY":
            return _ec_from_sec1(seq, curve_oid)
    except Exception:
        return None
    return None


def _ec_from_sec1(seq, curve_oid_fallback: Optional[str]) -> Optional[str]:
    params = seq.context(0)
    pub = seq.context(1)
    if pub is None or not pub.children:
        return None
    oid = curve_oid_fallback
    if params is not None and params.children and params.children[0].tag == asn1.OID:
        oid = params.children[0].as_oid()
    if oid is None:
        return None
    _, point = pub.children[0].as_bitstring()
    return hashlib.sha256(ec_spki(oid, point)).hexdigest()


def _dek_info(data: bytes) -> Optional[str]:
    m = re.search(rb"DEK-Info:\s*([A-Za-z0-9-]+)", data)
    return m.group(1).decode().lower() if m else None


def _is_service_path(path: str, root: str) -> bool:
    rel = path[len(root.rstrip("/")):] if root not in ("", "/") and path.startswith(root.rstrip("/")) else path
    return rel.startswith(("/etc/", "/var/", "/opt/", "/srv/", "/usr/local/"))


def _skip_for_ssh_local(path: str) -> bool:
    base = os.path.basename(path)
    if base.endswith(".pub") or base.startswith("ssh_host_"):
        return True
    if os.path.basename(os.path.dirname(path)) == ".ssh" and (base.startswith("id_") or base in (
            "authorized_keys", "known_hosts", "config")):
        return True
    return False


def _magic(head: bytes) -> bool:
    return head.startswith(b"-----BEGIN") or head[:2] == b"\x30\x82"


@register
class KeysLocalCollector(Collector):
    name = "keys_local"
    description = "Private keys, DH and EC parameter files on disk (permissions, encryption, key size)"
    needs_network = False

    def collect(self, ctx: ScanContext) -> List[Asset]:
        roots = [ctx.path(d) for d in SERVICE_DIRS]
        import glob
        for g in EXTRA_KEY_DIR_GLOBS:
            roots.extend(sorted(glob.glob(ctx.path(g))))
        roots.extend(ctx.extra_paths)
        budget = [ctx.max_files]
        files: List[str] = []
        seen: set = set()
        for path in iter_candidate_files(ctx, list(dict.fromkeys(roots)), exts=KEY_EXTS, magic=_magic, budget=budget):
            files.append(path)
        # Home directories can hold whole source trees; stay shallow unless --deep.
        home_depth = 6 if ctx.deep_fs_scan else int(ctx.opt("home_scan_depth", 2))
        for h in host_home_dirs(ctx):
            for path in iter_candidate_files(ctx, [h], exts=KEY_EXTS, magic=_magic, budget=budget, max_depth=home_depth,
                                             skip_dirs=_HOME_SKIP):
                files.append(path)
        if ctx.deep_fs_scan:
            for path in iter_candidate_files(ctx, [ctx.root or "/"], exts=KEY_EXTS, magic=_magic, budget=budget):
                files.append(path)

        assets: List[Asset] = []
        cert_spki: Dict[str, str] = {}
        key_assets: List[Tuple[Asset, Optional[str]]] = []
        for path in files:
            rp = os.path.realpath(path)
            if rp in seen or _skip_for_ssh_local(path):
                continue
            seen.add(rp)
            data = read_bytes(path, 8 * 1024 * 1024)
            if not data or (b"-----BEGIN" not in data and data[:2] != b"\x30\x82"):
                continue
            loc = path
            if ctx.root not in ("", "/") and path.startswith(ctx.root.rstrip("/") + "/"):
                loc = "/" + os.path.relpath(path, ctx.root)
            if b"-----BEGIN CERTIFICATE" in data:
                for c in x509.load_certificates(data):
                    if c.public_key.spki_sha256:
                        cert_spki.setdefault(c.public_key.spki_sha256, loc)
            infos = x509.parse_key_data(data)
            labels = [(lb, d) for lb, d in x509.iter_pem(data)] if b"-----BEGIN" in data else []
            priv_labels = [(lb, d) for lb, d in labels if lb.endswith("PRIVATE KEY")]
            idx = 0
            for info in infos:
                if info.kind in ("private", "encrypted-private") and info.fmt != "pkcs12":
                    a = self._private_key_asset(ctx, path, loc, info, data, len(infos) > 1, idx)
                    spki = None
                    if idx < len(priv_labels) and not info.encrypted:
                        spki = private_spki_sha256(priv_labels[idx][0], priv_labels[idx][1])
                    key_assets.append((a, spki))
                    idx += 1
                elif info.kind == "parameters":
                    assets.append(self._param_asset(ctx, loc, info, path))
        for a, spki in key_assets:
            if spki:
                a.attributes["spki_sha256"] = spki
                if spki in cert_spki:
                    a.attributes["paired_certificate"] = cert_spki[spki]
            assets.append(a)
        return assets

    def _private_key_asset(self, ctx: ScanContext, path: str, loc: str, info: x509.KeyFileInfo, data: bytes,
                           multi: bool, idx: int) -> Asset:
        note = info.note
        if info.encrypted and info.fmt in ("pkcs1", "sec1", "dsa") and not note:
            cipher = _dek_info(data)
            note = (f"legacy PEM encryption DEK-Info {cipher}, key derived with a single MD5 round"
                    if cipher else "legacy PEM encryption")
        attrs = {"mode": file_mode(path), "owner": file_owner(path), "encrypted": bool(info.encrypted),
                 "fmt": info.fmt, "encryption_note": note,
                 "service_key": _is_service_path(path, ctx.root)}
        pk = info.public_key
        name = f"private key {loc}" + (f" #{idx + 1}" if multi else "")
        a = Asset(AssetKind.PRIVATE_KEY, name, loc, "keys_local", host=ctx.hostname, attributes=attrs)
        if pk is not None:
            attrs["key_algorithm"] = pk.algorithm
            attrs["key_bits"] = pk.key_bits
            if pk.rsa_exponent is not None:
                attrs["rsa_exponent"] = pk.rsa_exponent
            if pk.curve:
                attrs["curve"] = pk.curve
            a.add(CryptoUse(Primitive.PUBLIC_KEY, pk.algorithm, key_bits=pk.key_bits, curve=pk.curve,
                            context="public-key", extra={"rsa_exponent": pk.rsa_exponent} if pk.rsa_exponent else {}))
        elif not info.encrypted:
            a.errors.append(f"could not determine the key algorithm ({info.note or info.fmt})")
        return a

    def _param_asset(self, ctx: ScanContext, loc: str, info: x509.KeyFileInfo, path: str) -> Asset:
        pk = info.public_key
        kind = info.fmt
        a = Asset(AssetKind.OTHER, f"{'DH' if kind == 'dhparam' else 'EC'} parameters {loc}", loc, "keys_local",
                  host=ctx.hostname, attributes={"fmt": kind, "mode": file_mode(path), "owner": file_owner(path)})
        if pk is not None:
            if kind == "dhparam":
                a.attributes["key_bits"] = pk.key_bits
                a.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=pk.key_bits, raw=f"DH {pk.key_bits} bits",
                                context="dhparam"))
            else:
                a.attributes["curve"] = pk.curve
                a.add(CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=pk.key_bits, curve=pk.curve,
                                raw=pk.curve, context="ecparam"))
        return a
