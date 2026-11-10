"""SSH public-key blob parsing (RFC 4253 §6.6, RFC 5656, RFC 8709) and the
OpenSSH private-key container (PROTOCOL.key)."""

from __future__ import annotations

import base64
import struct
from typing import Optional, Tuple

from .x509 import KeyFileInfo, PublicKeyInfo

_CURVES = {"nistp256": ("p-256", 256), "nistp384": ("p-384", 384), "nistp521": ("p-521", 521)}


class SSHBlobError(ValueError):
    pass


def read_string(b: bytes, off: int) -> Tuple[bytes, int]:
    if off + 4 > len(b):
        raise SSHBlobError("truncated string length")
    (n,) = struct.unpack(">I", b[off:off + 4])
    off += 4
    if off + n > len(b):
        raise SSHBlobError("truncated string")
    return b[off:off + n], off + n


def read_mpint(b: bytes, off: int) -> Tuple[int, int]:
    s, off = read_string(b, off)
    return int.from_bytes(s, "big", signed=True), off


def parse_public_blob(blob: bytes) -> PublicKeyInfo:
    """Parse an SSH wire-format public key blob."""
    ktype, off = read_string(blob, 0)
    t = ktype.decode("ascii", "replace")
    base = t.split("-cert-v01@openssh.com")[0]
    if base in ("ssh-rsa", "rsa-sha2-256", "rsa-sha2-512", "ssh-rsa1"):
        if t.endswith("-cert-v01@openssh.com"):
            _nonce, off = read_string(blob, off)
        _e, off = read_mpint(blob, off)
        n, _ = read_mpint(blob, off)
        return PublicKeyInfo("rsa", n.bit_length(), rsa_exponent=_e)
    if base == "ssh-dss":
        if t.endswith("-cert-v01@openssh.com"):
            _nonce, off = read_string(blob, off)
        p, _ = read_mpint(blob, off)
        return PublicKeyInfo("dsa", p.bit_length())
    if base.startswith("ecdsa-sha2-"):
        if t.endswith("-cert-v01@openssh.com"):
            _nonce, off = read_string(blob, off)
        curve, off = read_string(blob, off)
        cname, bits = _CURVES.get(curve.decode("ascii", "replace"), (curve.decode("ascii", "replace"), None))
        return PublicKeyInfo("ecdsa", bits, cname)
    if base.startswith("sk-ecdsa-sha2-"):
        curve, off = read_string(blob, off)
        cname, bits = _CURVES.get(curve.decode("ascii", "replace"), (curve.decode("ascii", "replace"), None))
        return PublicKeyInfo("ecdsa-sk", bits, cname)
    if base == "ssh-ed25519":
        return PublicKeyInfo("ed25519", 256, "curve25519")
    if base == "sk-ssh-ed25519@openssh.com":
        return PublicKeyInfo("ed25519-sk", 256, "curve25519")
    if base == "ssh-ed448":
        return PublicKeyInfo("ed448", 448, "curve448")
    if base.startswith("x509v3-"):
        return PublicKeyInfo(base, None)
    return PublicKeyInfo(t, None)


def parse_public_line(line: str) -> Optional[Tuple[str, PublicKeyInfo, str]]:
    """Parse an authorized_keys / known_hosts / .pub line.

    Returns (key_type, info, comment) or None for comments/blank lines.
    Handles option prefixes in authorized_keys and the hostname column in
    known_hosts (including hashed and @cert-authority/@revoked markers).
    """
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    tokens = line.split()
    for i, tok in enumerate(tokens):
        if _is_key_type(tok) and i + 1 < len(tokens):
            try:
                blob = base64.b64decode(tokens[i + 1], validate=False)
                info = parse_public_blob(blob)
            except (SSHBlobError, ValueError):
                return None
            comment = " ".join(tokens[i + 2:])
            return tok, info, comment
    return None


def _is_key_type(tok: str) -> bool:
    return (tok.startswith(("ssh-", "ecdsa-sha2-", "sk-", "rsa-sha2-", "x509v3-"))
            or tok.endswith("@openssh.com") and "-" in tok)


def parse_openssh_private_blob(blob: bytes) -> KeyFileInfo:
    """Parse the body of an OPENSSH PRIVATE KEY PEM block (public part only)."""
    magic = b"openssh-key-v1\x00"
    if not blob.startswith(magic):
        raise SSHBlobError("bad openssh-key-v1 magic")
    off = len(magic)
    cipher, off = read_string(blob, off)
    kdf, off = read_string(blob, off)
    kdfopts, off = read_string(blob, off)
    (nkeys,) = struct.unpack(">I", blob[off:off + 4])
    off += 4
    pub, off = read_string(blob, off)
    info = parse_public_blob(pub)
    encrypted = cipher != b"none"
    rounds = None
    if kdf == b"bcrypt" and len(kdfopts) >= 8:
        salt, o2 = read_string(kdfopts, 0)
        (rounds,) = struct.unpack(">I", kdfopts[o2:o2 + 4])
    note = f"cipher={cipher.decode()} kdf={kdf.decode()}" + (f" rounds={rounds}" if rounds else "")
    return KeyFileInfo("encrypted-private" if encrypted else "private", "openssh", info, encrypted, note)
