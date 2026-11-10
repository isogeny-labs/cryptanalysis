"""System-wide crypto policy collector (Linux): crypto-policies, FIPS, OpenSSL, GnuTLS, Java, password hashing, LUKS.

One SYSTEM_POLICY asset per source:

* RHEL/Fedora ``/etc/crypto-policies/config`` and ``state/current`` (CONFIG
  ``crypto-policy``); ``/proc/sys/crypto/fips_enabled`` (CONFIG ``fips-mode``)
  plus a summary of ``/proc/crypto``.
* OpenSSL: ``openssl version`` (CONFIG ``openssl-version``), every openssl.cnf
  (``@SECLEVEL``, ``MinProtocol``, ``Options``, legacy provider), the runtime
  provider list and the compiled-in ``DEFAULT`` cipher list.
* GnuTLS: ``/etc/gnutls/config`` and the crypto-policies GnuTLS back end.
* Java: every ``java.security`` of the JDKs found; missing default
  ``jdk.tls.disabledAlgorithms`` entries (CONFIG ``java-disabled-algorithms-missing``).
* Password hashing: ``login.defs`` ENCRYPT_METHOD, PAM ``pam_unix`` options and,
  when readable, a histogram of ``/etc/shadow`` hash types (counts only; no hash,
  user name or salt is ever recorded).
* LUKS (opt-in: ``ctx.options["luks"]``, root only): ``cryptsetup luksDump`` of
  the devices in ``/etc/crypttab``.

Windows is out of scope and macOS is skipped.  Collectors never grade; the
policy engine turns these records into findings.
"""

from __future__ import annotations

import os
import re
import sys
from typing import Dict, List, Optional, Set, Tuple

from . import register
from ._confparse import ctx_glob, file_attrs, is_root_host, logical, parse_properties, real
from .base import Collector, ScanContext
from .. import names, util
from ..model import Asset, AssetKind, CryptoUse, Primitive

# Entries the stock JDK disables in jdk.tls.disabledAlgorithms (JDK 17/21 defaults).
JAVA_DEFAULT_TLS_DISABLED = ("SSLv3", "TLSv1", "TLSv1.1", "RC4", "DES", "MD5withRSA", "DH keySize < 1024",
                             "EC keySize < 224", "3DES_EDE_CBC", "anon", "NULL")

_HASH_PREFIXES = (("$1$", "md5crypt"), ("$apr1$", "md5crypt"), ("$5$", "sha256crypt"), ("$6$", "sha512crypt"),
                  ("$y$", "yescrypt"), ("$gy$", "yescrypt"), ("$7$", "scrypt"), ("$2a$", "bcrypt"), ("$2b$", "bcrypt"),
                  ("$2y$", "bcrypt"), ("$2x$", "bcrypt"), ("$sha1$", "sha1crypt"), ("$md5$", "md5crypt"))
_WEAK_HASHES = ("descrypt", "md5crypt", "sha1crypt")


# ---------------------------------------------------------------------------
# Pure parsers (unit-tested)
# ---------------------------------------------------------------------------

def normalise_java_item(item: str) -> str:
    return re.sub(r"\s*<\s*", " < ", re.sub(r"\s+", " ", item.strip())).lower()


def java_missing_disabled(value: Optional[str]) -> List[str]:
    """Which JDK-default jdk.tls.disabledAlgorithms entries are absent from `value`."""
    items = [normalise_java_item(i) for i in (value or "").split(",") if i.strip()]
    plain = set(items)
    sizes: Dict[str, int] = {}
    for it in items:
        m = re.fullmatch(r"(\w+) keysize < (\d+)", it)
        if m:
            sizes[m.group(1)] = max(sizes.get(m.group(1), 0), int(m.group(2)))
    missing = []
    for want in JAVA_DEFAULT_TLS_DISABLED:
        w = normalise_java_item(want)
        m = re.fullmatch(r"(\w+) keysize < (\d+)", w)
        if m:
            if sizes.get(m.group(1), 0) < int(m.group(2)):
                missing.append(want)
        elif w not in plain:
            missing.append(want)
    return missing


def parse_openssl_ciphers(text: str) -> List[Tuple[str, Optional[str]]]:
    """`openssl ciphers -v` output -> [(suite name, protocol)]."""
    out = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and re.match(r"(SSL|TLS)v?[\d.]+$", parts[1], re.I):
            proto = parts[1].lower().replace("tlsv", "tls").replace("sslv", "sslv")
            out.append((parts[0], proto))
    return out


def parse_openssl_cnf(text: str) -> Dict[str, Dict[str, str]]:
    """OpenSSL config -> {section: {lower-key: value}} (top-level in section '')."""
    secs: Dict[str, Dict[str, str]] = {"": {}}
    cur = ""
    for line in text.splitlines():
        s = line.strip()
        if not s or s[0] == "#":
            continue
        s = re.sub(r"\s+#.*$", "", s)
        m = re.match(r"\[\s*([^\]]+?)\s*\]$", s)
        if m:
            cur = m.group(1)
            secs.setdefault(cur, {})
            continue
        m = re.match(r"([^=\s]+)\s*=\s*(.*)$", s)
        if m:
            secs[cur][m.group(1).lower()] = m.group(2).strip()
    return secs


def parse_luks_dump(text: str) -> Dict[str, object]:
    """Tolerant parser for `cryptsetup luksDump` (LUKS1 and LUKS2)."""
    info: Dict[str, object] = {}
    m = re.search(r"^Version:\s*(\d+)", text, re.M)
    if m:
        info["version"] = int(m.group(1))
    m = re.search(r"^\s*Cipher:\s+(\S+)", text, re.M)               # LUKS2 keyslot cipher
    if m:
        info["cipher"] = m.group(1)
    m1 = re.search(r"^Cipher name:\s*(\S+)", text, re.M)
    m2 = re.search(r"^Cipher mode:\s*(\S+)", text, re.M)
    if m1 and m2:
        info["cipher"] = f"{m1.group(1)}-{m2.group(1)}"
    m = re.search(r"^\s*Cipher key:\s+(\d+) bits", text, re.M) or re.search(r"^MK bits:\s*(\d+)", text, re.M)
    if m:
        info["key_bits"] = int(m.group(1))
    m = re.search(r"^\s*PBKDF:\s+(\S+)", text, re.M)
    if m:
        info["pbkdf"] = m.group(1)
    m = re.search(r"^\s*Hash:\s+(\S+)", text, re.M) or re.search(r"^Hash spec:\s*(\S+)", text, re.M)
    if m:
        info["hash"] = m.group(1)
    return info


def classify_shadow_hash(field: str) -> str:
    """Classify the password field of a shadow entry into a coarse type (never keeps the hash)."""
    if field == "":
        return "empty"
    if field in ("*", "!", "!!", "x", "*LK*", "NP"):
        return "locked"
    f = field[1:] if field.startswith("!") else field
    for pre, name in _HASH_PREFIXES:
        if f.startswith(pre):
            return name
    if re.fullmatch(r"[./0-9A-Za-z]{13}", f):
        return "descrypt"
    if f.startswith("_"):
        return "bsdi-extended-des"
    return "other"


def parse_login_defs(text: str) -> Dict[str, str]:
    out = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = s.split(None, 1)
        if len(p) == 2:
            out[p[0].upper()] = p[1].strip()
    return out


def parse_pam_unix(text: str) -> List[Dict[str, object]]:
    """`password ... pam_unix.so opts` lines -> [{algo, options}]."""
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "pam_unix" not in s:
            continue
        toks = s.split()
        if not toks or toks[0] != "password":
            continue
        opts = toks[toks.index(next(t for t in toks if "pam_unix" in t)) + 1:]
        algo = None
        for o in opts:
            if o in ("md5", "sha256", "sha512", "yescrypt", "blowfish", "bigcrypt", "gost_yescrypt"):
                algo = o
        out.append({"algo": algo, "options": opts, "nullok": any(o in ("nullok", "nullok_secure") for o in opts)})
    return out


_GNUTLS_TOKENS = (
    (r"\+VERS-SSL3\.0", "protocol", "sslv3"), (r"\+VERS-TLS1\.0", "protocol", "tls1.0"),
    (r"\+VERS-TLS1\.1", "protocol", "tls1.1"), (r"\+3DES-CBC", "cipher", "3des"), (r"\+ARCFOUR-128", "cipher", "rc4"),
    (r"\+SIGN-RSA-SHA1", "sig", "rsa"), (r"\+SIGN-ECDSA-SHA1", "sig", "ecdsa"), (r"\+SIGN-DSA-SHA1", "sig", "dsa"),
    (r"\+SIGN-RSA-MD5", "sigmd5", "rsa"), (r"\+MD5\b", "mac", "md5"),
)


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

@register
class SystemPolicyCollector(Collector):
    name = "system_policy"
    description = "System crypto policy: crypto-policies, FIPS, OpenSSL, GnuTLS, Java, password hashing, LUKS"

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        if is_root_host(ctx):
            if sys.platform.startswith("win"):
                return False, "Windows is out of scope"
            if sys.platform == "darwin":
                return False, "macOS is not supported by this collector"
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        for step in (self._crypto_policies, self._fips, self._openssl, self._gnutls, self._java, self._login_defs,
                     self._pam, self._shadow, self._luks):
            try:
                out.extend(step(ctx))
            except Exception as e:
                ctx.warn(f"system_policy: {step.__name__} failed: {type(e).__name__}: {e}")
        return out

    def _asset(self, ctx: ScanContext, name: str, location: str, **attrs) -> Asset:
        return Asset(AssetKind.SYSTEM_POLICY, name, location, self.name, ctx.hostname, attributes=dict(attrs))

    # -- crypto-policies ------------------------------------------------------

    def _crypto_policies(self, ctx: ScanContext) -> List[Asset]:
        cfg = ctx.path("/etc/crypto-policies/config")
        cur = ctx.path("/etc/crypto-policies/state/current")
        if not os.path.isfile(cfg) and not os.path.isfile(cur):
            return []
        a = self._asset(ctx, "crypto-policies", "/etc/crypto-policies")
        seen: Set[str] = set()
        for path, context in ((cfg, "crypto-policies-config"), (cur, "crypto-policies-state")):
            if not os.path.isfile(path):
                continue
            text = util.read_text(path)
            if text is None:
                a.errors.append(f"cannot read {path}")
                continue
            val = next((l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")), "")
            if val and val not in seen:
                seen.add(val)
                a.add(CryptoUse(Primitive.CONFIG, "crypto-policy", raw=val, context=context))
            a.attributes[context.replace("-", "_")] = val
        backends = [os.path.basename(p) for p in ctx_glob(ctx, "/etc/crypto-policies/back-ends/*.config")]
        if backends:
            a.attributes["backends"] = backends
        return [a]

    def _fips(self, ctx: ScanContext) -> List[Asset]:
        p = ctx.path("/proc/sys/crypto/fips_enabled")
        text = util.read_text(p, 64) if os.path.exists(p) else None
        if text is None:
            return []
        a = self._asset(ctx, "FIPS mode", "/proc/sys/crypto/fips_enabled")
        val = text.strip() or "0"
        a.add(CryptoUse(Primitive.CONFIG, "fips-mode", raw=val, context="fips_enabled"))
        a.attributes["system_fips_marker"] = os.path.exists(ctx.path("/etc/system-fips"))
        crypto = util.read_text(ctx.path("/proc/crypto"), 4 * 1024 * 1024)
        if crypto:
            algs = re.findall(r"^name\s*:\s*(\S+)", crypto, re.M)
            a.attributes["proc_crypto_algorithms"] = len(set(algs))
            fl = set(re.findall(r"^fips\s*:\s*(\S+)", crypto, re.M))
            if fl:
                a.attributes["proc_crypto_fips_flags"] = sorted(fl)
        a.attributes["fips_on"] = val == "1"
        return [a]

    # -- OpenSSL --------------------------------------------------------------

    def _openssl(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        live = is_root_host(ctx) and util.which("openssl") is not None
        cands = [ctx.path("/etc/ssl/openssl.cnf"), ctx.path("/etc/pki/tls/openssl.cnf")]
        if live:
            r = util.run_cmd(["openssl", "version"], timeout=ctx.cmd_timeout)
            if r.ok and r.stdout.strip():
                a = self._asset(ctx, "OpenSSL version", "openssl version")
                a.add(CryptoUse(Primitive.CONFIG, "openssl-version", raw=r.stdout.strip().splitlines()[0], context="openssl version"))
                out.append(a)
            d = util.run_cmd(["openssl", "version", "-d"], timeout=ctx.cmd_timeout)
            m = re.search(r'OPENSSLDIR:\s*"([^"]+)"', d.stdout) if d.ok else None
            if m:
                cands.append(os.path.join(m.group(1), "openssl.cnf"))
        seen: Set[str] = set()
        runtime_legacy: Optional[bool] = None
        if live:
            r = util.run_cmd(["openssl", "list", "-providers"], timeout=ctx.cmd_timeout)
            if r.ok:
                runtime_legacy = bool(re.search(r"^\s*legacy\b", r.stdout, re.M | re.I))
        for path in cands:
            rp = real(path)
            if rp in seen or not os.path.isfile(path):
                continue
            seen.add(rp)
            out.append(self._openssl_cnf(ctx, path, runtime_legacy))
        if live:
            r = util.run_cmd(["openssl", "ciphers", "-v", "DEFAULT"], timeout=ctx.cmd_timeout)
            if r.ok:
                suites = parse_openssl_ciphers(r.stdout)
                if suites:
                    a = self._asset(ctx, "openssl default cipher list", "openssl ciphers -v DEFAULT", suite_count=len(suites))
                    for name, proto in suites:
                        a.add(names.tls_cipher_suite(name, protocol=proto, negotiated=False))
                    out.append(a)
        return out

    def _openssl_cnf(self, ctx: ScanContext, path: str, runtime_legacy: Optional[bool]) -> Asset:
        a = self._asset(ctx, f"openssl.cnf {logical(ctx, path)}", logical(ctx, path), **file_attrs(path))
        text = util.read_text(path)
        if text is None:
            a.errors.append(f"cannot read {path}")
            return a
        secs = parse_openssl_cnf(text)
        opts: List[str] = []
        for sname, kv in secs.items():
            for key in ("cipherstring",):
                if key in kv:
                    m = re.search(r"@SECLEVEL=(\d+)", kv[key], re.I)
                    a.attributes.setdefault("cipher_strings", []).append(kv[key])
                    if m:
                        a.add(CryptoUse(Primitive.CONFIG, "openssl-seclevel", raw=m.group(1), context=f"CipherString [{sname}]"))
            if "minprotocol" in kv:
                v = kv["minprotocol"]
                v2 = "DTLSv1.0" if v.upper() == "DTLSV1" else v
                u = names.tls_protocol(v2, negotiated=None)
                u.context = "openssl-min-protocol"
                a.add(u)
            if "maxprotocol" in kv:
                a.attributes["max_protocol"] = kv["maxprotocol"]
            if "options" in kv:
                opts.extend(t.strip() for t in re.split(r"[,:]", kv["options"]) if t.strip())
        if opts:
            a.attributes["options"] = opts
        legacy = False
        for init in {v for kv in secs.values() for k, v in kv.items() if k == "providers"}:
            for pname, psect in secs.get(init, {}).items():
                if pname == "legacy" or psect == "legacy_sect":
                    if secs.get(psect, {}).get("activate", "").lower() in ("1", "yes", "true", "on"):
                        legacy = True
        a.attributes["legacy_provider_configured"] = legacy
        if runtime_legacy is not None:
            a.attributes["legacy_provider_loaded"] = runtime_legacy
        return a

    # -- GnuTLS ---------------------------------------------------------------

    def _gnutls(self, ctx: ScanContext) -> List[Asset]:
        out = []
        for p in ("/etc/gnutls/config", "/etc/crypto-policies/back-ends/gnutls.config"):
            path = ctx.path(p)
            if not os.path.isfile(path):
                continue
            a = self._asset(ctx, f"GnuTLS config {p}", p, **file_attrs(path))
            text = util.read_text(path)
            if text is None:
                a.errors.append(f"cannot read {path}")
                out.append(a)
                continue
            prios = []
            section = ""
            for line in text.splitlines():
                s = line.strip()
                if not s or s[0] in "#;":
                    continue
                if s.startswith("["):
                    section = s.strip("[] ").lower()
                    continue
                if section in ("priorities", "overrides") and "=" in s:
                    prios.append(s)
            if prios:
                a.attributes["priorities"] = prios[:20]
            joined = "\n".join(prios).upper()
            seen: Set[Tuple[str, str]] = set()
            for pat, kind, val in _GNUTLS_TOKENS:
                m = re.search(pat, joined)
                if not m or (kind, val) in seen:
                    continue
                seen.add((kind, val))
                raw = m.group(0).lstrip("+")
                if kind == "protocol":
                    a.add(CryptoUse(Primitive.PROTOCOL, val, raw=raw, context="gnutls-priority"))
                elif kind == "cipher":
                    a.add(CryptoUse(Primitive.CIPHER, val, key_bits=168 if val == "3des" else 128,
                                    mode="cbc" if val == "3des" else None, raw=raw, context="gnutls-priority"))
                elif kind == "sig":
                    a.add(CryptoUse(Primitive.SIGNATURE, val, hash_algorithm="sha1", raw=raw, context="gnutls-priority"))
                elif kind == "sigmd5":
                    a.add(CryptoUse(Primitive.SIGNATURE, val, hash_algorithm="md5", raw=raw, context="gnutls-priority"))
                elif kind == "mac":
                    a.add(CryptoUse(Primitive.HASH, "md5", raw=raw, context="gnutls-priority"))
            out.append(a)
        return out

    # -- Java -----------------------------------------------------------------

    def _jdk_homes(self, ctx: ScanContext) -> List[str]:
        cand = [d for d in ctx_glob(ctx, "/usr/lib/jvm/*") if os.path.isdir(d)]
        cand += [d for d in ctx_glob(ctx, "/usr/java/*") if os.path.isdir(d)]
        if is_root_host(ctx) and os.environ.get("JAVA_HOME"):
            cand.append(os.environ["JAVA_HOME"])
        out, seen = [], set()
        for d in cand:
            rd = real(d)
            if rd not in seen:
                seen.add(rd)
                out.append(d)
        return out

    def _java(self, ctx: ScanContext) -> List[Asset]:
        out = []
        for home in self._jdk_homes(ctx):
            sec = None
            for rel in ("conf/security/java.security", "lib/security/java.security", "jre/lib/security/java.security"):
                p = os.path.join(home, rel)
                if os.path.isfile(p):
                    sec = p
                    break
            if sec is None:
                continue
            a = self._asset(ctx, f"java.security ({logical(ctx, home)})", logical(ctx, sec), java_home=logical(ctx, home),
                            **file_attrs(sec))
            text = util.read_text(sec)
            if text is None:
                a.errors.append(f"cannot read {sec}")
                out.append(a)
                continue
            props = parse_properties(text)
            rel = util.read_text(os.path.join(home, "release"), 4096)
            if rel:
                m = re.search(r'JAVA_VERSION="?([^"\n]+)', rel)
                if m:
                    a.attributes["java_version"] = m.group(1)
            for key, attr in (("jdk.tls.disabledAlgorithms", "tls_disabled"), ("jdk.certpath.disabledAlgorithms", "certpath_disabled"),
                              ("jdk.jar.disabledAlgorithms", "jar_disabled")):
                if key in props:
                    a.attributes[attr] = [i.strip() for i in props[key].split(",") if i.strip()][:60]
            for key, attr in (("keystore.type", "keystore_type"), ("jdk.tls.keyLimits", "tls_key_limits"),
                              ("crypto.policy", "crypto_policy"), ("keystore.type.compat", "keystore_type_compat")):
                if key in props:
                    a.attributes[attr] = props[key]
            missing = java_missing_disabled(props.get("jdk.tls.disabledAlgorithms"))
            if missing:
                a.add(CryptoUse(Primitive.CONFIG, "java-disabled-algorithms-missing", raw=", ".join(missing),
                                context="jdk.tls.disabledAlgorithms"))
            out.append(a)
        return out

    # -- password hashing -------------------------------------------------------

    def _login_defs(self, ctx: ScanContext) -> List[Asset]:
        path = ctx.path("/etc/login.defs")
        text = util.read_text(path) if os.path.isfile(path) else None
        if text is None:
            return []
        d = parse_login_defs(text)
        a = self._asset(ctx, "login.defs", "/etc/login.defs", **file_attrs(path))
        method = d.get("ENCRYPT_METHOD", "").upper()
        raw = {"DES": "descrypt", "MD5": "md5crypt", "SHA256": "sha256crypt", "SHA512": "sha512crypt",
               "YESCRYPT": "yescrypt", "BCRYPT": "bcrypt"}.get(method)
        if raw is None and d.get("MD5_CRYPT_ENAB", "").lower() == "yes" and not method:
            raw = "md5crypt"
        if raw:
            a.add(CryptoUse(Primitive.CONFIG, "password-hash", raw=raw, context="login.defs"))
        for k in ("ENCRYPT_METHOD", "SHA_CRYPT_MIN_ROUNDS", "SHA_CRYPT_MAX_ROUNDS", "YESCRYPT_COST_FACTOR"):
            if k in d:
                a.attributes[k.lower()] = d[k]
        return [a] if (a.uses or a.attributes.get("encrypt_method")) else []

    def _pam(self, ctx: ScanContext) -> List[Asset]:
        out = []
        for p in ("/etc/pam.d/common-password", "/etc/pam.d/system-auth", "/etc/pam.d/password-auth",
                  "/etc/pam.d/system-auth-ac", "/etc/pam.d/password-auth-ac"):
            path = ctx.path(p)
            text = util.read_text(path) if os.path.isfile(path) else None
            if text is None:
                continue
            lines = parse_pam_unix(text)
            if not lines:
                continue
            a = self._asset(ctx, f"PAM {p}", p, **file_attrs(path))
            for ln in lines:
                algo = ln["algo"]
                if algo:
                    raw = {"md5": "md5crypt", "sha256": "sha256crypt", "sha512": "sha512crypt", "yescrypt": "yescrypt",
                           "gost_yescrypt": "yescrypt", "blowfish": "bcrypt", "bigcrypt": "descrypt"}[algo]
                    a.add(CryptoUse(Primitive.CONFIG, "password-hash", raw=raw, context=f"pam_unix:{os.path.basename(p)}"))
                if ln["nullok"]:
                    a.attributes["nullok"] = True
                for o in ln["options"]:
                    if o.startswith(("rounds=", "minlen=")):
                        a.attributes[o.split("=")[0]] = o.split("=")[1]
            out.append(a)
        return out

    def _shadow(self, ctx: ScanContext) -> List[Asset]:
        path = ctx.path("/etc/shadow")
        if not os.path.isfile(path):
            return []
        a = self._asset(ctx, "/etc/shadow hash types", "/etc/shadow", **file_attrs(path))
        text = util.read_text(path)
        if text is None:
            a.errors.append("cannot read /etc/shadow (run as root to inventory password hash types)")
            return [a]
        hist: Dict[str, int] = {}
        for line in text.splitlines():
            parts = line.split(":")
            if len(parts) < 2 or not parts[0] or parts[0][0] in "+-#":
                continue
            kind = classify_shadow_hash(parts[1])
            hist[kind] = hist.get(kind, 0) + 1
        a.attributes["hash_histogram"] = dict(sorted(hist.items()))
        for kind in _WEAK_HASHES + ("empty",):
            if hist.get(kind):
                raw = "empty-password" if kind == "empty" else kind
                a.add(CryptoUse(Primitive.CONFIG, "password-hash", raw=raw, context="shadow", extra={"count": hist[kind]}))
        return [a]

    # -- LUKS -------------------------------------------------------------------

    def _luks(self, ctx: ScanContext) -> List[Asset]:
        if not ctx.opt("luks") or not is_root_host(ctx):
            return []
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            ctx.warn("system_policy: luks inventory needs root")
            return []
        if util.which("cryptsetup") is None:
            return []
        text = util.read_text("/etc/crypttab") or ""
        out = []
        for line in text.splitlines():
            parts = line.split()
            if len(parts) < 2 or parts[0].startswith("#"):
                continue
            dev = parts[1]
            for pre, d in (("UUID=", "/dev/disk/by-uuid/"), ("PARTUUID=", "/dev/disk/by-partuuid/"),
                           ("LABEL=", "/dev/disk/by-label/")):
                if dev.startswith(pre):
                    dev = d + dev[len(pre):]
            r = util.run_cmd(["cryptsetup", "luksDump", dev], timeout=ctx.cmd_timeout)
            a = self._asset(ctx, f"LUKS {parts[0]}", dev)
            if not r.ok:
                a.errors.append(f"cryptsetup luksDump {dev} failed: {(r.error or r.stderr).strip()[:200]}")
                out.append(a)
                continue
            info = parse_luks_dump(r.stdout)
            a.attributes.update({k: v for k, v in info.items()})
            a.attributes["format"] = f"luks{info.get('version', '?')}"
            cipher = str(info.get("cipher", ""))
            if cipher:
                parts_c = cipher.split("-")
                alg = parts_c[0].lower()
                mode = parts_c[1].lower() if len(parts_c) > 1 else None
                bits = info.get("key_bits")
                if mode == "xts" and isinstance(bits, int):
                    bits //= 2
                a.add(CryptoUse(Primitive.CIPHER, alg, key_bits=bits if isinstance(bits, int) else None, mode=mode,
                                raw=cipher, context="luks"))
            if info.get("hash"):
                a.add(CryptoUse(Primitive.HASH, names.hash_name(str(info["hash"])), raw=str(info["hash"]), context="luks"))
            if info.get("pbkdf"):
                a.add(CryptoUse(Primitive.KDF, str(info["pbkdf"]).lower(), raw=str(info["pbkdf"]), context="luks",
                                hash_algorithm=names.hash_name(str(info["hash"])) if info.get("hash") else None))
            out.append(a)
        return out
