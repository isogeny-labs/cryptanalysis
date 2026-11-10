"""Inventory of X.509 certificates, trust stores and Java/NSS keystores on disk.

Produces
* TRUST_STORE assets (system CA bundles / anchor directories / JDK cacerts / NSS
  databases) with a summary: count, key-algorithm histogram, expired, SHA-1
  signed roots, RSA-1024 roots, weakest key;
* one CA_CERTIFICATE asset per trust anchor (deduplicated by SHA-256, all places
  it was seen are listed in ``attributes["locations"]``; ``locally_added`` marks
  enterprise/user anchors);
* CERTIFICATE / CA_CERTIFICATE assets for service certificates found in well-known
  directories, ``ctx.extra_paths`` and (with ``deep_fs_scan``) the whole root;
* JAVA_KEYSTORE assets for JKS / JCEKS / PKCS#12 files (PKCS#12 is never decrypted,
  only its PBE OIDs and MAC digest are read).

Read-only; nothing here grades.  ``ctx.extra_paths`` entries are used verbatim
(they are host paths the user named), well-known locations go through ``ctx.path``.
"""

from __future__ import annotations

import datetime as _dt
import glob
import os
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

from .. import jks, x509
from ..model import Asset, AssetKind, CryptoUse, Primitive
from ..util import file_mode, file_owner, read_bytes, run_cmd, which
from . import register
from ._certassets import cert_attributes, cert_label, cert_uses, host_home_dirs, iter_candidate_files, looks_like_pem_or_der
from .base import Collector, ScanContext

# (path, kind) kind: "bundle" file with many PEMs, "dir" directory of certs
SYSTEM_STORES: List[Tuple[str, str, bool]] = [
    ("/etc/ssl/certs/ca-certificates.crt", "bundle", False),
    ("/usr/share/ca-certificates", "dir", False),
    ("/usr/local/share/ca-certificates", "dir", True),
    ("/etc/pki/ca-trust/source/anchors", "dir", True),
    ("/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", "bundle", False),
    ("/etc/pki/tls/certs/ca-bundle.crt", "bundle", False),
    ("/etc/ssl/cert.pem", "bundle", False),
    ("/etc/pki/trust/anchors", "dir", True),
    ("/var/lib/ca-certificates/ca-bundle.pem", "bundle", False),
]
JAVA_CACERTS = ["/etc/ssl/certs/java/cacerts", "/etc/pki/java/cacerts"]
JAVA_CACERTS_GLOBS = ["/usr/lib/jvm/*/lib/security/cacerts", "/usr/lib/jvm/*/jre/lib/security/cacerts",
                      "/usr/java/*/lib/security/cacerts", "/opt/*/lib/security/cacerts"]
NSS_DIRS = ["/etc/pki/nssdb"]
SERVICE_DIRS = ["/etc/ssl/private", "/etc/ssl/certs", "/etc/pki/tls/certs", "/etc/pki/tls/private",
                "/etc/letsencrypt/live", "/etc/letsencrypt/archive", "/etc/nginx", "/etc/apache2", "/etc/httpd",
                "/etc/haproxy", "/etc/postfix", "/etc/dovecot", "/etc/exim4", "/etc/openvpn", "/etc/ipsec.d",
                "/etc/strongswan", "/etc/kubernetes/pki", "/var/lib/kubelet/pki", "/etc/etcd", "/etc/docker",
                "/etc/rancher", "/etc/cockpit/ws-certs.d", "/opt", "/srv", "/usr/local/etc"]


def _now() -> _dt.datetime:
    return _dt.datetime.now(_dt.timezone.utc)


class _Inventory:
    """Deduplicating collection of certificate assets for one scan."""

    def __init__(self, ctx: ScanContext) -> None:
        self.ctx = ctx
        self.by_sha: Dict[str, Asset] = {}
        self.assets: List[Asset] = []

    def add_cert(self, cert: x509.Certificate, location: str, *, anchor: bool, locally_added: bool = False,
                 role: str = "", extra: Optional[Dict[str, object]] = None,
                 file_for_perms: Optional[str] = None) -> Asset:
        sha = cert.fingerprint_sha256
        existing = self.by_sha.get(sha)
        if existing is not None:
            locs = existing.attributes.setdefault("locations", [])
            if location not in locs:
                locs.append(location)
            if anchor and not existing.attributes.get("trust_anchor"):
                existing.attributes["trust_anchor"] = True
                existing.kind = AssetKind.CA_CERTIFICATE
            if locally_added:
                existing.attributes["locally_added"] = True
            if extra:
                for k, v in extra.items():
                    existing.attributes.setdefault(k, v)
            return existing
        attrs = cert_attributes(cert)
        attrs["trust_anchor"] = anchor
        attrs["locations"] = [location]
        attrs["locally_added"] = locally_added
        if file_for_perms:
            attrs["mode"] = file_mode(file_for_perms)
            attrs["owner"] = file_owner(file_for_perms)
        if extra:
            attrs.update(extra)
        kind = AssetKind.CA_CERTIFICATE if (anchor or cert.is_ca) else AssetKind.CERTIFICATE
        label = cert_label(cert)
        a = Asset(kind, f"{label}{' (' + role + ')' if role else ''}", location, "certs_local",
                  host=self.ctx.hostname, uses=cert_uses(cert), attributes=attrs)
        self.by_sha[sha] = a
        self.assets.append(a)
        return a


def _security_bits(alg: str, bits: Optional[int]) -> Optional[int]:
    """Rough classical security strength (SP 800-57 table) used only to pick the weakest key."""
    if not bits:
        return None
    if alg in ("rsa", "dsa", "dh", "rsa-pss"):
        for limit, sec in ((2048, 80), (3072, 112), (7680, 128), (15360, 192)):
            if bits < limit:
                return sec
        return 256
    return bits // 2


def trust_store_summary(certs: List[x509.Certificate], now: Optional[_dt.datetime] = None) -> Dict[str, object]:
    """count / by_key_algorithm / expired / sha1_roots / rsa1024 / weakest_key for a set of anchors."""
    now = now or _now()
    hist: Counter = Counter()
    weakest: Optional[Tuple[int, str]] = None
    expired = sha1 = rsa1024 = 0
    for c in certs:
        pk = c.public_key
        if pk.algorithm == "rsa":
            tag = f"rsa-{pk.key_bits}"
        elif pk.curve:
            tag = f"{pk.algorithm}-{pk.curve}"
        else:
            tag = pk.algorithm
        hist[tag] += 1
        if c.not_after < now:
            expired += 1
        if c.signature_hash in ("sha1", "md5", "md2", "md4"):
            sha1 += 1
        if pk.algorithm == "rsa" and (pk.key_bits or 0) <= 1024:
            rsa1024 += 1
        sec = _security_bits(pk.algorithm, pk.key_bits)
        if sec is not None and (weakest is None or sec < weakest[0]):
            weakest = (sec, f"{tag} ({cert_label(c)})")
    return {"count": len(certs), "by_key_algorithm": dict(sorted(hist.items())), "expired": expired,
            "sha1_roots": sha1, "rsa1024": rsa1024, "weakest_key": weakest[1] if weakest else None}


# ---------------------------------------------------------------------------
# NSS
# ---------------------------------------------------------------------------

_NSS_FLAGS = re.compile(r"^[pPcCTuw]*,[pPcCTuw]*,[pPcCTuw]*$")


def parse_nss_list(text: str) -> List[Tuple[str, str]]:
    """Parse `certutil -L` output into [(nickname, trust flags)]."""
    out: List[Tuple[str, str]] = []
    for line in text.splitlines():
        line = line.rstrip()
        if not line.strip() or line.lstrip().lower().startswith(("certificate nickname", "nickname")):
            continue
        parts = line.rsplit(None, 1)
        if len(parts) == 2 and _NSS_FLAGS.match(parts[1]):
            out.append((parts[0].strip(), parts[1]))
    return out


@register
class CertsLocalCollector(Collector):
    name = "certs_local"
    description = "Certificates on disk: system trust stores, service certificates, Java keystores, NSS databases"
    needs_network = False

    # ---- public entry --------------------------------------------------
    def collect(self, ctx: ScanContext) -> List[Asset]:
        inv = _Inventory(ctx)
        stores: List[Asset] = []
        done_files: set = set()
        budget = [ctx.max_files]

        stores.extend(self._system_stores(ctx, inv, done_files))
        stores.extend(self._java_stores(ctx, inv, done_files))
        stores.extend(self._nss(ctx, inv))
        extra = self._service_certs(ctx, inv, done_files, budget)
        return stores + inv.assets + extra

    # ---- system trust stores ---------------------------------------------
    def _system_stores(self, ctx: ScanContext, inv: _Inventory, done: set) -> List[Asset]:
        out: List[Asset] = []
        for path, kind, local in SYSTEM_STORES:
            real = ctx.path(path)
            if not os.path.exists(real):
                continue
            files = [real] if kind == "bundle" else [p for p in iter_candidate_files(
                ctx, [real], exts=(".crt", ".pem", ".cer", ".cert"), budget=[ctx.max_files], follow_symlinks=True)]
            certs: List[x509.Certificate] = []
            store = Asset(AssetKind.TRUST_STORE, f"trust store {path}", path, "certs_local", host=ctx.hostname,
                          attributes={"store_type": "pem-bundle" if kind == "bundle" else "pem-directory",
                                      "locally_added": local})
            for f in files:
                done.add(os.path.realpath(f))
                data = read_bytes(f, 16 * 1024 * 1024)
                if data is None:
                    store.errors.append(f"cannot read {f}")
                    continue
                for c in x509.load_certificates(data):
                    certs.append(c)
                    inv.add_cert(c, f if kind == "dir" else path, anchor=True, locally_added=local,
                                 extra={"store_type": store.attributes["store_type"]})
            store.attributes.update(trust_store_summary(certs))
            out.append(store)
        return out

    # ---- Java stores ---------------------------------------------------------
    def _java_stores(self, ctx: ScanContext, inv: _Inventory, done: set) -> List[Asset]:
        paths: List[str] = [ctx.path(p) for p in JAVA_CACERTS]
        jh = os.environ.get("JAVA_HOME") if ctx.root in ("", "/") else None
        if jh:
            paths.append(os.path.join(jh, "lib", "security", "cacerts"))
            paths.append(os.path.join(jh, "jre", "lib", "security", "cacerts"))
        for g in JAVA_CACERTS_GLOBS:
            paths.extend(sorted(glob.glob(ctx.path(g))))
        out: List[Asset] = []
        seen: set = set()
        for p in paths:
            rp = os.path.realpath(p)
            if rp in seen or not os.path.isfile(rp):
                continue
            seen.add(rp)
            done.add(rp)
            out.extend(self.read_keystore_file(ctx, inv, p, force_trust=True))
        return out

    def read_keystore_file(self, ctx: ScanContext, inv: _Inventory, path: str, force_trust: bool = False) -> List[Asset]:
        """Handle one JKS / JCEKS / PKCS#12 file; returns the store asset (cert assets go to `inv`)."""
        data = read_bytes(path, 8 * 1024 * 1024)
        if data is None:
            return []
        kind = jks.sniff(data)
        if kind is None:
            return []
        loc = path
        if ctx.root not in ("", "/") and path.startswith(ctx.root):
            loc = "/" + os.path.relpath(path, ctx.root)
        attrs: Dict[str, object] = {"format": kind, "mode": file_mode(path), "owner": file_owner(path),
                                    "store_type": kind}
        if kind == "pkcs12":
            return [self._pkcs12_asset(ctx, loc, data, attrs)]
        try:
            st = jks.parse_jks(data)
        except ValueError as e:
            a = Asset(AssetKind.JAVA_KEYSTORE, f"Java keystore {loc}", loc, "certs_local", host=ctx.hostname, attributes=attrs)
            a.errors.append(f"cannot parse keystore: {e}")
            return [a]
        certs: List[x509.Certificate] = []
        trusted = [e for e in st.entries if e.kind == "trusted"]
        keys = [e for e in st.entries if e.kind == "key"]
        for e in st.entries:
            for i, der in enumerate(e.certs):
                try:
                    c = x509.parse_certificate(der)
                except Exception:
                    continue
                is_anchor = e.kind == "trusted"
                if is_anchor:
                    certs.append(c)
                inv.add_cert(c, f"{loc}#{e.alias}", anchor=is_anchor, extra={
                    "store_type": st.format, "keystore_alias": e.alias,
                    "chain_position": i if e.kind == "key" else None})
        all_trusted = bool(st.entries) and not keys
        kindv = AssetKind.TRUST_STORE if (force_trust or all_trusted) else AssetKind.JAVA_KEYSTORE
        a = Asset(kindv, f"{'trust store' if kindv == AssetKind.TRUST_STORE else 'Java keystore'} {loc}", loc,
                  "certs_local", host=ctx.hostname, attributes=attrs)
        attrs.update({"keystore_version": st.version, "entries": len(st.entries), "trusted_entries": len(trusted),
                      "key_entries": len(keys), "encrypted": bool(keys)})
        protectors = sorted({e.key_protector_oid for e in keys if e.key_protector_oid})
        if protectors:
            attrs["key_protectors"] = [jks.KEY_PROTECTOR_OIDS.get(o, o) for o in protectors]
        attrs.update(trust_store_summary(certs))
        a.errors.extend(st.notes)
        return [a]

    def _pkcs12_asset(self, ctx: ScanContext, loc: str, data: bytes, attrs: Dict[str, object]) -> Asset:
        info = jks.pkcs12_info(data)
        attrs.update({"encrypted": True, "pbe_oids": info["pbe_oids"], "pbe_names": info["pbe_names"],
                      "mac_hash": info.get("mac_hash")})
        a = Asset(AssetKind.JAVA_KEYSTORE, f"PKCS#12 keystore {loc}", loc, "certs_local", host=ctx.hostname, attributes=attrs)
        for oid in info["pbe_oids"]:
            name, alg, bits = jks.PBE_OIDS[oid]
            if alg:
                a.add(CryptoUse(Primitive.CIPHER, alg, key_bits=bits, raw=name, context="pkcs12-pbe",
                                mode="cbc" if alg in ("3des", "rc2", "des") else None))
        mh = info.get("mac_hash")
        if mh in ("sha1", "md5"):
            a.add(CryptoUse(Primitive.MAC, "hmac", hash_algorithm=mh, raw=f"hmac-{mh}", context="pkcs12-mac"))
        return a

    # ---- NSS ---------------------------------------------------------------
    def _nss(self, ctx: ScanContext, inv: _Inventory) -> List[Asset]:
        dirs = [ctx.path(d) for d in NSS_DIRS]
        for h in host_home_dirs(ctx):
            dirs.append(os.path.join(h, ".pki", "nssdb"))
            for pat in (".mozilla/firefox/*", "snap/firefox/common/.mozilla/firefox/*", ".thunderbird/*"):
                dirs.extend(sorted(glob.glob(os.path.join(h, pat))))
        dirs = [d for d in dict.fromkeys(dirs) if os.path.isfile(os.path.join(d, "cert9.db"))]
        if not dirs:
            return []
        out: List[Asset] = []
        if which("certutil") is None:
            for d in dirs:
                a = Asset(AssetKind.TRUST_STORE, f"NSS database {d}", d, "certs_local", host=ctx.hostname,
                          attributes={"store_type": "nss", "skipped": "certutil not installed"})
                out.append(a)
            return out
        for d in dirs:
            spec = f"sql:{d}"
            a = Asset(AssetKind.TRUST_STORE, f"NSS database {d}", d, "certs_local", host=ctx.hostname,
                      attributes={"store_type": "nss"})
            r = run_cmd(["certutil", "-L", "-d", spec], timeout=ctx.cmd_timeout)
            if not r.ok:
                a.attributes["skipped"] = (r.error or r.stderr.strip() or "certutil failed")[:200]
                out.append(a)
                continue
            certs: List[x509.Certificate] = []
            for nick, flags in parse_nss_list(r.stdout)[:500]:
                rr = run_cmd(["certutil", "-L", "-d", spec, "-n", nick, "-a"], timeout=ctx.cmd_timeout)
                if not rr.ok:
                    a.errors.append(f"certutil -n {nick!r}: {(rr.error or rr.stderr.strip())[:100]}")
                    continue
                for c in x509.load_certificates(rr.stdout.encode()):
                    anchor = "C" in flags.split(",")[0] or "T" in flags.split(",")[0]
                    if anchor:
                        certs.append(c)
                    inv.add_cert(c, f"{d}#{nick}", anchor=anchor, locally_added=True,
                                 extra={"store_type": "nss", "nss_trust": flags, "nss_nickname": nick})
            a.attributes.update(trust_store_summary(certs))
            out.append(a)
        return out

    # ---- service certificates --------------------------------------------------
    def _service_certs(self, ctx: ScanContext, inv: _Inventory, done: set, budget: List[int]) -> List[Asset]:
        roots = [ctx.path(d) for d in SERVICE_DIRS]
        roots.extend(p for p in ctx.extra_paths)
        if ctx.deep_fs_scan:
            roots.append(ctx.root or "/")
        keystores: List[Asset] = []
        seen_files: set = set()
        for path in iter_candidate_files(ctx, list(dict.fromkeys(roots)), magic=looks_like_pem_or_der, budget=budget):
            rp = os.path.realpath(path)
            if rp in done or rp in seen_files:
                continue
            seen_files.add(rp)
            data = read_bytes(path, 8 * 1024 * 1024)
            if not data:
                continue
            loc = path
            if ctx.root not in ("", "/") and path.startswith(ctx.root.rstrip("/") + "/"):
                loc = "/" + os.path.relpath(path, ctx.root)
            kind = jks.sniff(data)
            if kind:
                keystores.extend(self.read_keystore_file(ctx, inv, path))
                continue
            for c in x509.load_certificates(data):
                inv.add_cert(c, loc, anchor=False, file_for_perms=path)
        return keystores
