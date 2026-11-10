"""Shared helpers that turn parsed X.509 certificates into Assets.

Not a collector (it is not listed in the registry); imported by tls_remote,
certs_local and keys_local so all three describe certificates identically.
"""

from __future__ import annotations

import os
import re
import stat
from typing import Callable, Dict, Iterator, List, Optional, Sequence

from ..model import CryptoUse, Primitive
from ..util import home_dirs, walk_files
from ..x509 import Certificate

_SNAKEOIL = re.compile(r"snakeoil|localhost(\.localdomain)?$|CN=localhost|ssl-cert", re.I)


def serial_bits(cert: Certificate) -> int:
    return cert.serial.bit_length()


def cert_attributes(cert: Certificate) -> Dict[str, object]:
    """Certificate.summary() plus serial_bits, rsa_exponent and snakeoil detection."""
    attrs: Dict[str, object] = dict(cert.summary())
    attrs["serial_bits"] = serial_bits(cert)
    pk = cert.public_key
    if pk.rsa_exponent is not None:
        attrs["rsa_exponent"] = pk.rsa_exponent
    if pk.explicit_curve_params:
        attrs["explicit_curve_params"] = True
    attrs["spki_sha256"] = pk.spki_sha256
    attrs["sha1"] = cert.fingerprint_sha1
    attrs["is_default_snakeoil"] = bool(_SNAKEOIL.search(cert.subject))
    if cert.parse_warnings:
        attrs["parse_warnings"] = list(cert.parse_warnings)
    return attrs


def cert_uses(cert: Certificate) -> List[CryptoUse]:
    """PUBLIC_KEY + SIGNATURE uses of a certificate (the brief's contract)."""
    pk = cert.public_key
    uses = [CryptoUse(Primitive.PUBLIC_KEY, pk.algorithm, key_bits=pk.key_bits, curve=pk.curve,
                      context="public-key", extra={"rsa_exponent": pk.rsa_exponent} if pk.rsa_exponent else {})]
    uses.append(CryptoUse(Primitive.SIGNATURE, cert.signature_algorithm, hash_algorithm=cert.signature_hash,
                          raw=cert.signature_oid, context="certificate-signature"))
    return uses


def cert_label(cert: Certificate) -> str:
    """CN of the subject, else the first SAN, else the whole subject."""
    for part in cert.subject.split(","):
        if part.startswith("CN="):
            return part[3:]
    if cert.sans:
        return cert.sans[0].split(":", 1)[-1]
    return cert.subject or "(empty subject)"


def hostname_matches(cert: Certificate, host: str) -> bool:
    """RFC 6125-ish match: SAN DNS/IP entries, CN only when there is no SAN; one-label wildcards."""
    host = host.lower().rstrip(".")
    dns = [s[4:].lower() for s in cert.sans if s.startswith("DNS:")]
    ips = [s[3:] for s in cert.sans if s.startswith("IP:")]
    if not dns and not ips:
        dns = [p[3:].lower() for p in cert.subject.split(",") if p.startswith("CN=")]
    try:
        import ipaddress
        ip = ipaddress.ip_address(host)
        return any(_same_ip(i, ip) for i in ips)
    except ValueError:
        pass
    for pat in dns:
        pat = pat.rstrip(".")
        if pat == host:
            return True
        if pat.startswith("*.") and host.count(".") == pat.count(".") and host.split(".", 1)[1] == pat[2:] \
                and not host.startswith("."):
            return True
    return False


def _same_ip(text: str, ip) -> bool:
    import ipaddress
    try:
        return ipaddress.ip_address(text) == ip
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# File discovery shared by certs_local and keys_local
# ---------------------------------------------------------------------------

CERT_EXTS = (".pem", ".crt", ".cer", ".der", ".p7b", ".p7c", ".pfx", ".p12", ".jks", ".keystore", ".bks",
             ".jceks", ".truststore", ".cert", ".ca-bundle")
_NOISE_EXTS = {".py", ".pyc", ".so", ".js", ".json", ".html", ".css", ".png", ".jpg", ".gif", ".svg", ".txt",
               ".md", ".gz", ".xz", ".zip", ".jar", ".class", ".h", ".c", ".o", ".a", ".log", ".sample",
               ".conf", ".cnf", ".template", ".map", ".ttf", ".woff", ".woff2", ".mo", ".po", ".ko", ".rpm", ".deb"}


def host_home_dirs(ctx) -> List[str]:
    """Home directories of the inspected system (root-relative for offline images)."""
    if ctx.root in ("", "/"):
        return home_dirs()
    out = []
    for base in ("root", "home"):
        p = ctx.path("/" + base)
        if not os.path.isdir(p):
            continue
        if base == "root":
            out.append(p)
        else:
            try:
                out.extend(os.path.join(p, d) for d in sorted(os.listdir(p)) if os.path.isdir(os.path.join(p, d)))
            except OSError:
                pass
    return out


def iter_candidate_files(ctx, roots: Sequence[str], exts: Sequence[str] = CERT_EXTS,
                         magic: Optional[Callable[[bytes], bool]] = None, budget: Optional[List[int]] = None,
                         follow_symlinks: bool = False, max_depth: int = 12,
                         skip_dirs: Optional[set] = None) -> Iterator[str]:
    """Yield regular files that look like key/cert material: by extension, or by first bytes.

    `budget` is a one-element list holding the remaining file allowance (shared across roots).
    Symlinks are skipped (the targets are scanned under their own path).
    """
    left = budget if budget is not None else [ctx.max_files]
    for path in walk_files([r for r in roots if os.path.exists(r)], max_files=max(left[0], 0),
                           max_depth=max_depth, skip_dirs=skip_dirs):
        if left[0] <= 0:
            return
        left[0] -= 1
        if not follow_symlinks and os.path.islink(path):
            continue
        ext = os.path.splitext(path)[1].lower()
        if ext in exts:
            yield path
            continue
        if magic is None or ext in _NOISE_EXTS:
            continue
        try:
            st = os.lstat(path)
            if not stat.S_ISREG(st.st_mode) or st.st_size > 65536 or st.st_size < 16:
                continue        # never open devices, FIFOs or sockets: a tty read blocks forever
            with open(path, "rb") as fh:
                head = fh.read(16)
        except OSError:
            continue
        if magic(head):
            yield path


def looks_like_pem_or_der(head: bytes) -> bool:
    return head.startswith(b"-----BEGIN") or head[:2] == b"\x30\x82" or head[:4] in (b"\xfe\xed\xfe\xed", b"\xce\xce\xce\xce")
