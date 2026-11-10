"""OpenSSL-style cipher-string expansion and TLS protocol-list helpers.

Shared by the `netdev` collector (F5, ASA, ...) and the `web_servers` collector
(nginx, Apache, HAProxy, Postfix, ...).  Two jobs:

* `openssl_cipher_string_expand(spec)` turns an OpenSSL cipher string
  (`ALL:!aNULL`, `HIGH:MEDIUM:RC4-SHA`, `ECDHE+AESGCM`) into the concrete suite
  list by running `openssl ciphers -v` when the binary exists.  When it does
  not (or rejects the string) the result is flagged `expanded=False` and a
  conservative keyword heuristic stands in.
* `cipher_string_uses(spec)` turns that into CryptoUses through
  `names.tls_cipher_suite`, adding explicit suite names the local OpenSSL build
  does not know (RC4-SHA on a build without weak ciphers) and keyword
  heuristics for weak families, so the weak-suite findings do not depend on
  which OpenSSL happens to be installed on the scanning host.

Expansion always appends `@SECLEVEL=0` (unless the string sets a level) so the
local security level does not hide suites the audited server would offer.
Nothing here is graded; the policy engine does that.
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from . import names
from .model import CryptoUse
from .util import run_cmd, which

PROTO_ORDER = ["SSLv2", "SSLv3", "TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"]
_PROTO_RE = re.compile(r"^(ssl|tls)v?(\d)(?:[._\-]?(\d))?$")


def normalize_proto(token: str) -> Optional[str]:
    """Canonical display name ("TLSv1", "TLSv1.2", "SSLv3") for many spellings, else None.

    Accepts TLSv1, TLSv1.1, TLSv1_2, tls1-3, tlsv1-0, VersionTLS12, TLS1.2, SSLv3.
    """
    t = token.strip().lower().replace("version", "").strip("+-,;'\" ")
    m = _PROTO_RE.match(t)
    if not m:
        return None
    fam, a, b = m.groups()
    if fam == "ssl":
        return {"2": "SSLv2", "3": "SSLv3"}.get(a)
    if a != "1":
        return None
    if b is None or b == "0":
        return "TLSv1"
    return {"1": "TLSv1.1", "2": "TLSv1.2", "3": "TLSv1.3"}.get(b)


def proto_range(lo: Optional[str], hi: Optional[str] = None) -> List[str]:
    """Protocols from `lo` up to `hi` (inclusive); open-ended ends default to TLSv1.3."""
    lo_i = PROTO_ORDER.index(lo) if lo in PROTO_ORDER else 0
    hi_i = PROTO_ORDER.index(hi) if hi in PROTO_ORDER else len(PROTO_ORDER) - 1
    return PROTO_ORDER[lo_i:hi_i + 1]


def sort_protos(protos: Iterable[str]) -> List[str]:
    return [p for p in PROTO_ORDER if p in set(protos)]


def protocol_use(display: str, **extra) -> CryptoUse:
    """PROTOCOL use for a canonical display name; negotiated stays None (configured, not observed)."""
    return names.tls_protocol(display, negotiated=None, extra=dict(extra))


# ---------------------------------------------------------------------------
# cipher strings
# ---------------------------------------------------------------------------

@dataclass
class CipherExpansion:
    spec: str
    suites: List[Tuple[str, str]] = field(default_factory=list)     # (openssl name, protocol column)
    expanded: bool = False                                          # True when openssl produced the list
    error: Optional[str] = None
    openssl_version: Optional[str] = None


@functools.lru_cache(maxsize=1)
def _openssl_version() -> Optional[str]:
    r = run_cmd(["openssl", "version"], timeout=5)
    return r.stdout.strip() if r.ok else None


_LINE = re.compile(r"^(\S+)\s+(\S+)\s+Kx=")


@functools.lru_cache(maxsize=512)
def _expand_cached(spec: str, timeout: float) -> CipherExpansion:
    exp = CipherExpansion(spec=spec)
    if not spec or which("openssl") is None:
        exp.error = "openssl not installed" if spec else "empty cipher string"
        return exp
    full = spec if "@SECLEVEL" in spec.upper() else spec + ":@SECLEVEL=0"
    for argv in (["openssl", "ciphers", "-v", "-ciphersuites", "", full], ["openssl", "ciphers", "-v", full]):
        r = run_cmd(argv, timeout=timeout)
        if not r.ok:
            exp.error = (r.stderr or r.error or "openssl ciphers failed").strip().splitlines()[0][:200] if (r.stderr or r.error) else "openssl ciphers failed"
            continue
        suites: List[Tuple[str, str]] = []
        for line in r.stdout.splitlines():
            m = _LINE.match(line)
            if m:
                name, proto = m.groups()
                if name.startswith("TLS_") and name not in spec:      # TLS 1.3 suites are listed unconditionally
                    continue
                suites.append((name, proto))
        exp.suites, exp.expanded, exp.error = suites, True, None
        exp.openssl_version = _openssl_version()
        return exp
    return exp


def openssl_cipher_string_expand(spec: str, timeout: float = 10.0) -> CipherExpansion:
    """Expand an OpenSSL cipher string with `openssl ciphers -v`; `.expanded` is False when that was impossible."""
    return _expand_cached((spec or "").strip().strip("'\""), timeout)


_KEYWORDS_SKIP = {"@STRENGTH", "DEFAULT", "ALL", "COMPLEMENTOFALL", "COMPLEMENTOFDEFAULT"}

# keyword -> synthetic OpenSSL suite names that stand for the family when nothing better is known
_HEUR = {
    "RC4": ["RC4-SHA"], "3DES": ["DES-CBC3-SHA"], "DES-CBC3": ["DES-CBC3-SHA"], "DES": ["DES-CBC-SHA", "DES-CBC3-SHA"],
    "LOW": ["DES-CBC-SHA"], "EXP": ["EXP-RC4-MD5", "EXP-DES-CBC-SHA"], "EXPORT": ["EXP-RC4-MD5", "EXP-DES-CBC-SHA"],
    "EXPORT40": ["EXP-RC4-MD5"], "EXPORT56": ["EXP-DES-CBC-SHA"], "MD5": ["RC4-MD5"],
    "NULL": ["NULL-SHA"], "ENULL": ["NULL-SHA"], "ANULL": ["ADH-AES128-SHA"], "ADH": ["ADH-AES128-SHA"],
    "AECDH": ["AECDH-AES128-SHA"], "MEDIUM": ["DES-CBC3-SHA"],
    "HIGH": ["ECDHE-RSA-AES256-GCM-SHA384", "DHE-RSA-AES256-SHA", "AES256-SHA"],
    "KEDH": ["DHE-RSA-AES128-SHA"], "DHE": ["DHE-RSA-AES128-SHA"], "EDH": ["DHE-RSA-AES128-SHA"],
}
_ALL_HEUR = ["RC4-SHA", "DES-CBC3-SHA", "AES128-SHA", "DHE-RSA-AES128-SHA"]
_DEFAULT_HEUR = ["AES128-SHA", "DHE-RSA-AES128-SHA", "ECDHE-RSA-AES128-GCM-SHA256"]
_NAME_RE = re.compile(r"^[A-Z0-9]+(?:-[A-Z0-9]+)+$")
_NON_NAMES = {"ECDHE-RSA", "ECDHE-ECDSA", "DHE-RSA", "DHE-DSS"}


def _tokens(spec: str) -> List[str]:
    return [t for t in re.split(r"[:,;\s]+", spec) if t]


def _looks_like_suite(tok: str) -> bool:
    if tok.startswith("TLS_"):
        return True
    return bool(_NAME_RE.match(tok)) and tok not in _NON_NAMES and "+" not in tok and not tok.startswith("SECLEVEL")


def _suite_matches(name: str, token: str) -> bool:
    """Does an OpenSSL/IANA suite name match an exclusion keyword (RC4, 3DES, aNULL, MD5, ...)?"""
    n, t = name.upper(), token.upper().lstrip("!+-")
    if t in ("3DES", "DES-CBC3"):
        return "3DES" in n or "DES-CBC3" in n
    if t == "DES":
        return bool(re.search(r"(^|[-_])DES([-_]|$)", n)) or "3DES" in n or "DES-CBC3" in n
    if t in ("ANULL", "ADH", "AECDH"):
        return n.startswith(("ADH-", "AECDH-")) or "_ANON_" in n
    if t in ("ENULL", "NULL"):
        return n.startswith("NULL-") or "_NULL_" in n
    if t in ("EXP", "EXPORT", "EXPORT40", "EXPORT56"):
        return n.startswith("EXP") or "_EXPORT_" in n
    if t == "LOW":
        return bool(re.search(r"(^|[-_])DES([-_]|$)", n)) and "3DES" not in n and "CBC3" not in n
    return t in n


_SRP_DSS = re.compile(r"^SRP-DSS-AES-(128|256)-CBC-SHA$")


def canonical_openssl_name(name: str) -> str:
    """Rewrite OpenSSL suite spellings that `names.tls_cipher_suite` would mis-parse.

    OpenSSL 1.1+/3.x spell PSK suites `PSK-AES128-CBC-SHA`, the RSA-authenticated
    ARIA suites `ECDHE-ARIA128-GCM-SHA256` and SRP-DSS `SRP-DSS-AES-128-CBC-SHA`;
    the names heuristic expects `AES128` / `ECDHE-RSA-ARIA...`.
    """
    m = _SRP_DSS.match(name)
    if m:
        return f"TLS_SRP_SHA_DSS_WITH_AES_{m.group(1)}_CBC_SHA"
    n = re.sub(r"(^|-)AES(128|256)-CBC-", r"\1AES\2-", name)
    if n.startswith("ECDHE-ARIA"):
        n = "ECDHE-RSA-" + n[len("ECDHE-"):]
    return n


def _mk_suite(name: str, proto: Optional[str], negotiated: Optional[bool], extra: Dict) -> CryptoUse:
    p = proto.lower().replace("tlsv", "tls") if proto else None
    u = names.tls_cipher_suite(canonical_openssl_name(name), protocol=p, negotiated=negotiated, extra=dict(extra))
    u.raw = name
    return u


@dataclass
class CipherStringInfo:
    uses: List[CryptoUse] = field(default_factory=list)
    expanded: bool = False
    openssl_version: Optional[str] = None
    flags: Set[str] = field(default_factory=set)       # "ALL", "DEFAULT", "no-seclevel", "heuristic"
    seclevel: Optional[int] = None
    error: Optional[str] = None


def cipher_string_uses(spec: str, negotiated: Optional[bool] = False, extra: Optional[Dict] = None,
                       exclude: Sequence[str] = ()) -> CipherStringInfo:
    """CryptoUses for an OpenSSL cipher string (see module docstring).

    `exclude` lists extra keywords/suite names to drop (Postfix `*_tls_exclude_ciphers`).
    """
    extra = dict(extra or {})
    spec = (spec or "").strip().strip("'\"")
    info = CipherStringInfo()
    toks = _tokens(spec)
    negated = {t[1:].upper() for t in toks if t.startswith("!")}
    for t in toks:
        m = re.match(r"@SECLEVEL=(\d)", t, re.I)
        if m:
            info.seclevel = int(m.group(1))
    upper = {t.lstrip("+").upper() for t in toks if not t.startswith(("!", "-"))}
    if "ALL" in upper:
        info.flags.add("ALL")
    if "DEFAULT" in upper:
        info.flags.add("DEFAULT")
    if ("ALL" in upper or "DEFAULT" in upper) and info.seclevel is None:
        info.flags.add("no-seclevel")
    exp = openssl_cipher_string_expand(spec)
    info.expanded, info.openssl_version, info.error = exp.expanded, exp.openssl_version, exp.error
    seen: Set[str] = set()

    def add(name: str, proto: Optional[str], src_extra: Dict) -> None:
        if name in seen or any(_suite_matches(name, x) for x in exclude):
            return
        seen.add(name)
        info.uses.append(_mk_suite(name, proto, negotiated, {**extra, **src_extra}))

    for name, proto in exp.suites:
        add(name, proto, {})
    # explicit suite names that this OpenSSL build does not know (e.g. RC4-SHA)
    for t in toks:
        if t.startswith(("!", "-", "@")):
            continue
        t2 = t.lstrip("+")
        if _looks_like_suite(t2) and t2 not in seen and t2.upper() not in negated:
            add(t2, None, {"explicit": True, **({} if exp.expanded else {"unexpanded": True, "heuristic": True})})
    # keyword heuristics: always for weak families, ALL/DEFAULT/HIGH only when the string was not expanded
    for t in toks:
        if t.startswith(("!", "-", "@")):
            continue
        k = t.lstrip("+").upper()
        if k in negated:
            continue
        if k in _HEUR and (k not in ("HIGH", "MEDIUM", "DHE", "EDH", "KEDH") or not exp.expanded):
            if exp.expanded and any(_suite_matches(n, k) for n, _ in exp.suites):
                continue
            for name in _HEUR[k]:
                if not any(n.upper() == name for n in seen):
                    add(name, None, {"heuristic": True, "keyword": k, "unexpanded": not exp.expanded})
        elif k == "ALL" and not exp.expanded:
            for name in _ALL_HEUR + (["ADH-AES128-SHA"] if "ANULL" not in negated else []):
                add(name, None, {"heuristic": True, "keyword": k, "unexpanded": True})
        elif k == "DEFAULT" and not exp.expanded:
            for name in _DEFAULT_HEUR:
                add(name, None, {"heuristic": True, "keyword": k, "unexpanded": True})
    if any(u.extra.get("heuristic") for u in info.uses) or not exp.expanded:
        info.flags.add("heuristic")
    return info


def dhe_allowed(uses: Iterable[CryptoUse]) -> bool:
    """True when any suite in `uses` does finite-field (EC-less) Diffie-Hellman key exchange."""
    for u in uses:
        if u.extra.get("kx") in ("dhe", "dh-anon", "dh-static"):
            return True
    return False


def iana_suite_uses(suite_names: Iterable[str], negotiated: Optional[bool] = False, extra: Optional[Dict] = None) -> List[CryptoUse]:
    """CryptoUses for explicit suite names (IANA, JSSE, Go, or OpenSSL spellings)."""
    out: List[CryptoUse] = []
    seen: Set[str] = set()
    for n in suite_names:
        n = n.strip().strip("'\"")
        if not n or n in seen:
            continue
        seen.add(n)
        out.append(names.tls_cipher_suite(n, negotiated=negotiated, extra=dict(extra or {})))
    return out


def resolve_protocol_expr(expr: str, all_set: Optional[Sequence[str]] = None) -> List[str]:
    """Resolve an Apache-style protocol expression (`all -SSLv3 -TLSv1 +TLSv1.2`) to canonical names.

    A token without sign starts a fresh set (`all` expands to `all_set`, default SSLv3..TLSv1.3);
    `+X` adds and `-X` removes, applied in order.
    """
    universe = list(all_set) if all_set else ["SSLv3", "TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"]
    result: Set[str] = set(universe)
    seen_abs = False
    for tok in re.split(r"[\s,]+", expr.strip()):
        if not tok:
            continue
        sign = tok[0] if tok[0] in "+-" else ""
        body = tok[1:] if sign else tok
        if body.lower() == "all":
            members = set(universe)
        else:
            p = normalize_proto(body)
            members = {p} if p else set()
        if not sign:
            if not seen_abs:
                result, seen_abs = set(), True
            result |= members
        elif sign == "+":
            result |= members
        else:
            result -= members
    return sort_protos(result)
