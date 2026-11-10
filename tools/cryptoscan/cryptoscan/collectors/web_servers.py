"""Local TLS server configuration: nginx, Apache httpd, HAProxy, Postfix, Dovecot,
Exim, lighttpd, Tomcat, Spring Boot, Traefik, Envoy, Kubernetes components and etcd.

One TLS_ENDPOINT asset per server block / virtual host / bind line, with
attributes ``software``, ``config_file``, ``server_names``, ``listen``,
``protocols``, ``defaults_assumed`` and uses:

* configured protocols -> ``names.tls_protocol`` (negotiated=None); when TLS 1.3
  is enabled ``attributes["tls1.3"] = True`` so the TLS-1.2-only rule stays quiet;
* cipher strings -> ``ciphers.cipher_string_uses`` (OpenSSL syntax, expanded with
  the local ``openssl ciphers -v`` when available, keyword heuristics otherwise)
  or ``ciphers.iana_suite_uses`` (Java/Go/IANA names); every suite negotiated=False;
* ECDH groups -> ``names.tls_group``;
* Diffie-Hellman: a KEY_EXCHANGE ``dh`` use with the size of the configured
  dhparam file (or HAProxy ``tune.ssl.default-dh-param``), or CONFIG
  ``dh-param-missing`` when DHE suites are allowed and no group is configured;
* certificate / key files -> separate CERTIFICATE assets (described exactly like
  ``certs_local`` through ``_certassets``) and PRIVATE_KEY assets (mode, owner,
  encrypted, fmt), deduplicated across blocks (attribute ``used_by``).

When a directive is absent the software default is recorded with
``extra["source"] = "default"`` (or ``"default-unknown-version"`` when the
default depends on a version that could not be determined) and the asset gets
``attributes["defaults_assumed"] = True``.  Versions come from ``nginx -v``,
``haproxy -v``, ``dovecot --version`` and ``lighttpd -v`` on a live root only,
or from ``ctx.opt("<software>_version")``.

Defaults used (from the vendor documentation):
  nginx      ssl_protocols "TLSv1.2 TLSv1.3" since 1.23.4, "TLSv1 TLSv1.1 TLSv1.2" before
             (TLS 1.3 joined the default list in 1.23.4); ssl_ciphers "HIGH:!aNULL:!MD5"
  Apache     SSLProtocol "all -SSLv3" (TLS 1.0-1.3)
  HAProxy    ssl-min-ver TLSv1.2 since 2.2, TLSv1.0 before
  Postfix    smtpd/smtp_tls_(mandatory_)protocols TLSv1+ ("!SSLv2, !SSLv3" / ">=TLSv1");
             cipher grade "medium"; grade -> cipher list mapping below
  Dovecot    ssl_min_protocol TLSv1.2 since 2.3.15 (approximate), TLSv1 before;
             ssl_cipher_list ALL:!kRSA:!SRP:!kDHd:!DSS:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK:!RC4:!ADH:!LOW@STRENGTH
  Exim       openssl_options "+no_sslv2 +no_sslv3" (TLS 1.0-1.3)
  lighttpd   MinProtocol TLSv1.2 since 1.4.56, TLSv1 before
  Tomcat     protocols "TLSv1.2+TLSv1.3"
  Traefik    minVersion VersionTLS12;  Envoy (server) TLSv1_2..TLSv1_3
  Spring / Kubernetes / etcd: runtime (JSSE / Go crypto/tls) defaults, not recorded.

Postfix grade heuristic (Postfix's own tls_*_cipherlist defaults; "+RC4" is
dropped because OpenSSL >= 1.1 builds no longer contain RC4 in MEDIUM, and an
explicit RC4 in an override still counts):
  high   aNULL:-aNULL:HIGH:@STRENGTH
  medium aNULL:-aNULL:HIGH:MEDIUM:@STRENGTH
  low    aNULL:-aNULL:HIGH:MEDIUM:LOW:@STRENGTH
  export aNULL:-aNULL:HIGH:MEDIUM:LOW:EXPORT:@STRENGTH
  null   eNULL:!aNULL

Every host path goes through ``ctx.path`` so offline roots work; Include /
include / !include globs are followed (bounded depth and file count).  Only
TLS-relevant directives are read: passwords (keystorePass, key-store-password,
...) are never looked at or stored.  Nothing here grades.
"""

from __future__ import annotations

import glob
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .. import names, x509
from ..ciphers import PROTO_ORDER, cipher_string_uses, dhe_allowed, iana_suite_uses, normalize_proto, proto_range, resolve_protocol_expr, sort_protos
from ..confparse import tokenize
from ..model import Asset, AssetKind, CryptoUse, Primitive
from ..util import file_mode, file_owner, read_bytes, read_text, run_cmd, which
from . import register
from ._certassets import cert_attributes, cert_label, cert_uses
from .base import Collector, ScanContext

MAX_INCLUDE_DEPTH = 8
MAX_CONF_FILES = 2000
TLS_ALL = ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"]


# ---------------------------------------------------------------------------
# block model and the shared emitter
# ---------------------------------------------------------------------------

@dataclass
class CipherSpec:
    spec: str
    directive: str
    kind: str = "openssl"             # "openssl" | "iana" (comma/colon list of explicit names)
    source: Optional[str] = None      # None (configured) | "default" | "default-unknown-version"


@dataclass
class Block:
    """One TLS server (or client) configuration, as read from a config file."""

    software: str
    config_file: str                              # logical (host) path
    label: str
    role: str = "server"
    server_names: List[str] = field(default_factory=list)
    listen: List[str] = field(default_factory=list)
    protocols: Optional[List[str]] = None         # canonical display names
    proto_directive: str = ""
    proto_source: Optional[str] = None
    ciphers: List[CipherSpec] = field(default_factory=list)
    exclude: List[str] = field(default_factory=list)
    groups: List[Tuple[str, str, Optional[str]]] = field(default_factory=list)   # (name, directive, source)
    dhparam_file: Optional[str] = None            # logical path
    dhparam_directive: str = "dhparam"
    dh_bits: Optional[Tuple[int, str]] = None     # (bits, raw)
    dhe_check: bool = True
    certs: List[str] = field(default_factory=list)
    keys: List[str] = field(default_factory=list)
    attrs: Dict[str, object] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


def _src(source: Optional[str]) -> Dict[str, object]:
    return {"source": source} if source else {}


class _Emitter:
    """Turns Blocks into assets; certificate and key assets are shared between blocks."""

    def __init__(self, ctx: ScanContext, collector: str):
        self.ctx = ctx
        self.collector = collector
        self.assets: List[Asset] = []
        self._certs: Dict[str, Asset] = {}
        self._keys: Dict[Tuple[str, int], Asset] = {}
        self._labels: Dict[str, int] = {}

    # ---- endpoint -------------------------------------------------------
    def emit(self, b: Block) -> Asset:
        ctx = self.ctx
        label = f"{b.software} {b.label}"
        n = self._labels.get(label, 0) + 1
        self._labels[label] = n
        if n > 1:
            label = f"{label} #{n}"
        attrs: Dict[str, object] = {"software": b.software, "config_file": b.config_file, "server_names": b.server_names,
                                    "listen": b.listen, "role": b.role, "defaults_assumed": False}
        attrs.update(b.attrs)
        a = Asset(AssetKind.TLS_ENDPOINT, label, b.config_file, self.collector, host=ctx.hostname, attributes=attrs)
        a.errors.extend(b.errors)
        seen: set = set()

        def add(u: CryptoUse) -> None:
            key = (u.primitive, u.raw, u.context, u.algorithm, u.key_bits)
            if key in seen:
                return
            seen.add(key)
            a.add(u)
            if u.extra.get("source") in ("default", "default-unknown-version"):
                attrs["defaults_assumed"] = True

        if b.protocols is not None:
            protos = sort_protos(b.protocols)
            attrs["protocols"] = protos
            if b.proto_source:
                attrs["protocols_source"] = b.proto_source
            for p in protos:
                add(names.tls_protocol(p, negotiated=None, extra={"directive": b.proto_directive, **_src(b.proto_source)}))
            if "TLSv1.3" in protos:
                attrs["tls1.3"] = True
        cipher_uses: List[CryptoUse] = []
        for cs in b.ciphers:
            extra = {"directive": cs.directive, **_src(cs.source)}
            if cs.kind == "iana":
                uses = iana_suite_uses([x for x in re.split(r"[\s,:|\[\]]+", cs.spec) if x], negotiated=False, extra=extra)
            else:
                info = cipher_string_uses(cs.spec, negotiated=False, extra=extra, exclude=b.exclude)
                uses = info.uses
                attrs.setdefault("cipher_strings", {})[cs.directive] = cs.spec
                if info.flags:
                    attrs.setdefault("cipher_string_flags", {})[cs.directive] = sorted(info.flags)
                attrs["ciphers_expanded"] = bool(attrs.get("ciphers_expanded", True)) and info.expanded
                if info.openssl_version:
                    attrs["openssl_used_for_expansion"] = info.openssl_version
            for u in uses:
                cipher_uses.append(u)
                add(u)
        for g, directive, source in b.groups:
            g = g.strip()
            if not g or g.lower() in ("auto", "default"):
                continue
            add(names.tls_group(_group_alias(g), negotiated=None, extra={"directive": directive, **_src(source)}))
        # Diffie-Hellman parameters
        if b.dh_bits:
            bits, raw = b.dh_bits
            add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=bits, raw=raw, context="dhparam", negotiated=None,
                          extra={"directive": b.dhparam_directive}))
            attrs["dh_bits"] = bits
        elif b.dhparam_file:
            attrs["dhparam_file"] = b.dhparam_file
            bits = self._dh_bits_from_file(b.dhparam_file, a)
            if bits:
                add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=bits, raw=f"{b.dhparam_directive} {b.dhparam_file}",
                              context="dhparam", negotiated=None, extra={"directive": b.dhparam_directive, "file": b.dhparam_file}))
                attrs["dh_bits"] = bits
        elif b.dhe_check and dhe_allowed(cipher_uses):
            add(CryptoUse(Primitive.CONFIG, "dh-param-missing",
                          raw=f"{b.software}: DHE cipher suites are enabled but {b.dhparam_directive} is not set "
                              f"(the built-in/default group of this software version is used)",
                          context="dhparam", negotiated=None, extra={"directive": b.dhparam_directive}))
        # certificates and keys
        if b.certs:
            attrs["cert_files"] = list(dict.fromkeys(b.certs))
        if b.keys:
            attrs["key_files"] = list(dict.fromkeys(b.keys))
        key_paths = list(dict.fromkeys(b.keys))
        for c in dict.fromkeys(b.certs):
            self._cert_file(c, label, a, also_keys=c not in key_paths)
        for k in key_paths:
            self._key_file(k, label, a)
        self.assets.append(a)
        return a

    # ---- helpers --------------------------------------------------------
    def _dh_bits_from_file(self, logical: str, a: Asset) -> Optional[int]:
        data = read_bytes(self.ctx.path(logical))
        if data is None:
            a.errors.append(f"cannot read DH parameter file {logical}")
            return None
        for info in x509.parse_key_data(data):
            if info.fmt == "dhparam" and info.public_key is not None:
                return info.public_key.key_bits
        a.errors.append(f"no DH PARAMETERS block in {logical}")
        return None

    def _cert_file(self, logical: str, used_by: str, endpoint: Asset, also_keys: bool) -> None:
        path = self.ctx.path(logical)
        data = read_bytes(path, 16 * 1024 * 1024)
        if data is None:
            endpoint.errors.append(f"cannot read certificate file {logical}")
            return
        certs = x509.load_certificates(data)
        if not certs and b"-----BEGIN" not in data and data[:1] != b"\x30":
            endpoint.errors.append(f"no certificate found in {logical}")
        for i, c in enumerate(certs):
            sha = c.fingerprint_sha256
            ex = self._certs.get(sha)
            if ex is not None:
                ub = ex.attributes.setdefault("used_by", [])
                if used_by not in ub:
                    ub.append(used_by)
                locs = ex.attributes.setdefault("locations", [])
                if logical not in locs:
                    locs.append(logical)
                continue
            attrs = cert_attributes(c)
            attrs.update({"trust_anchor": False, "locations": [logical], "mode": file_mode(path), "owner": file_owner(path),
                          "used_by": [used_by], "chain_position": i, "source_config": endpoint.attributes.get("config_file")})
            kind = AssetKind.CA_CERTIFICATE if c.is_ca else AssetKind.CERTIFICATE
            role = "server certificate" if i == 0 else "chain certificate"
            ca = Asset(kind, f"{cert_label(c)} ({role})", logical, self.collector, host=self.ctx.hostname,
                       uses=cert_uses(c), attributes=attrs)
            self._certs[sha] = ca
            self.assets.append(ca)
        dh_infos = [k for k in x509.parse_key_data(data) if k.fmt == "dhparam" and k.public_key] if b"DH PARAMETERS" in data else []
        if dh_infos:
            # Apache / HAProxy read DH parameters appended to the certificate file
            bits = dh_infos[0].public_key.key_bits
            if not any(u.context == "dhparam" and u.primitive == Primitive.KEY_EXCHANGE for u in endpoint.uses):
                endpoint.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=bits, raw=f"DH PARAMETERS in {logical}",
                                       context="dhparam", negotiated=None, extra={"file": logical}))
                endpoint.uses[:] = [u for u in endpoint.uses if u.algorithm != "dh-param-missing"]
                endpoint.attributes["dh_bits"] = bits
        if also_keys and b"PRIVATE KEY" in data:
            self._key_file(logical, used_by, endpoint, data=data)

    def _key_file(self, logical: str, used_by: str, endpoint: Asset, data: Optional[bytes] = None) -> None:
        path = self.ctx.path(logical)
        if data is None:
            data = read_bytes(path)
        if data is None:
            endpoint.errors.append(f"cannot read private key file {logical}")
            return
        infos = [k for k in x509.parse_key_data(data) if k.kind in ("private", "encrypted-private")]
        for idx, info in enumerate(infos):
            key = (os.path.realpath(path), idx)
            ex = self._keys.get(key)
            if ex is not None:
                ub = ex.attributes.setdefault("used_by", [])
                if used_by not in ub:
                    ub.append(used_by)
                continue
            note = info.note
            attrs = {"mode": file_mode(path), "owner": file_owner(path), "encrypted": bool(info.encrypted), "fmt": info.fmt,
                     "encryption_note": note, "service_key": True, "used_by": [used_by]}
            pk = info.public_key
            name = f"private key {logical}" + (f" #{idx + 1}" if len(infos) > 1 else "")
            ka = Asset(AssetKind.PRIVATE_KEY, name, logical, self.collector, host=self.ctx.hostname, attributes=attrs)
            if pk is not None:
                attrs["key_algorithm"] = pk.algorithm
                attrs["key_bits"] = pk.key_bits
                if pk.curve:
                    attrs["curve"] = pk.curve
                ka.add(CryptoUse(Primitive.PUBLIC_KEY, pk.algorithm, key_bits=pk.key_bits, curve=pk.curve, context="public-key",
                                 extra={"rsa_exponent": pk.rsa_exponent} if pk.rsa_exponent else {}))
            self._keys[key] = ka
            self.assets.append(ka)


_GROUP_ALIASES = {"p-256": "secp256r1", "p-384": "secp384r1", "p-521": "secp521r1", "curvep256": "secp256r1",
                  "curvep384": "secp384r1", "curvep521": "secp521r1", "x25519": "x25519", "x448": "x448"}


def _group_alias(g: str) -> str:
    return _GROUP_ALIASES.get(g.lower().replace("_", ""), g)


# ---------------------------------------------------------------------------
# small shared helpers
# ---------------------------------------------------------------------------

def _version_tuple(text: Optional[str]) -> Optional[Tuple[int, ...]]:
    if not text:
        return None
    m = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", str(text))
    if not m:
        return None
    return tuple(int(x) for x in m.groups() if x is not None)


def live_version(ctx: ScanContext, software: str, argv: Sequence[str], pattern: str) -> Optional[Tuple[int, ...]]:
    """Version from ctx.opt("<software>_version") or, on a live root, from the binary."""
    v = ctx.opt(f"{software}_version")
    if v:
        return _version_tuple(str(v))
    if ctx.root not in ("", "/") or which(argv[0]) is None:
        return None
    r = run_cmd(list(argv), timeout=min(ctx.cmd_timeout, 10))
    m = re.search(pattern, (r.stdout or "") + (r.stderr or ""))
    return _version_tuple(m.group(1)) if m else None


def _exists(ctx: ScanContext, logical: str) -> bool:
    return os.path.isfile(ctx.path(logical))


def _glob(ctx: ScanContext, pattern: str) -> List[str]:
    """Glob a logical pattern under the root; returns logical paths, sorted."""
    real = ctx.path(pattern)
    out = []
    for p in sorted(glob.glob(real, recursive="**" in pattern)):
        if not os.path.isfile(p):
            continue
        if ctx.root in ("", "/"):
            out.append(p)
        else:
            out.append("/" + os.path.relpath(p, ctx.root))
    return out[:MAX_CONF_FILES]


def _resolve(base_dir: str, p: str) -> str:
    p = p.strip().strip("'\"")
    if not p:
        return p
    return p if p.startswith("/") else os.path.normpath(os.path.join(base_dir, p))


def _proto_min(lo: Optional[str], hi: Optional[str] = None) -> List[str]:
    return [p for p in proto_range(lo or "TLSv1", hi or "TLSv1.3") if p != "SSLv2"]


def _apply_minmax(protos: List[str], lo: Optional[str], hi: Optional[str]) -> List[str]:
    lo_i = PROTO_ORDER.index(lo) if lo in PROTO_ORDER else 0
    hi_i = PROTO_ORDER.index(hi) if hi in PROTO_ORDER else len(PROTO_ORDER) - 1
    return [p for p in protos if lo_i <= PROTO_ORDER.index(p) <= hi_i]


def _openssl_conf_protocol(value: str, base: List[str]) -> List[str]:
    """OpenSSL SSL_CONF `Protocol` command: `-ALL,TLSv1.2,TLSv1.3` / `-TLSv1,-TLSv1.1`."""
    result = list(base)
    for tok in re.split(r"[,\s]+", value.strip()):
        if not tok:
            continue
        sign = "-" if tok.startswith("-") else "+"
        body = tok.lstrip("+-")
        members = PROTO_ORDER[1:] if body.upper() == "ALL" else ([normalize_proto(body)] if normalize_proto(body) else [])
        if sign == "-":
            result = [p for p in result if p not in members]
        else:
            result = sort_protos(set(result) | set(members))
    return result


def _is_openssl_spec(spec: str) -> bool:
    """True for an OpenSSL cipher string, False for a plain list of IANA/JSSE suite names."""
    toks = [t for t in re.split(r"[\s,:]+", spec.strip()) if t]
    if not toks:
        return True
    return not all(t.startswith(("TLS_", "SSL_")) for t in toks)


def _yaml_flatten(text: str) -> List[Tuple[Tuple[str, ...], str]]:
    """Tolerant YAML-ish flattener: (key path, scalar value) for `key: value` and `- item` lines.

    Inline lists `[a, b]` are split into one entry per item; `- key: value` list items
    contribute their keys under the list's parent path.  Anchors, multi-line scalars and
    flow maps are not supported (they are not needed for the keys read here).
    """
    out: List[Tuple[Tuple[str, ...], str]] = []
    stack: List[Tuple[int, str]] = []
    for raw in text.splitlines():
        if raw.lstrip().startswith("#"):
            continue
        line = re.sub(r"\s+#.*$", "", raw).rstrip()
        if not line.strip() or line.strip() in ("---", "..."):
            continue
        indent = len(line) - len(line.lstrip(" "))
        s = line.strip()
        item = s == "-" or s.startswith("- ")
        if item:
            s = s[1:].strip()
            while stack and stack[-1][0] > indent:       # `key:` followed by `- x` at the same indent
                stack.pop()
            content_indent = indent + 2
        else:
            while stack and stack[-1][0] >= indent:
                stack.pop()
            content_indent = indent
        if not s:
            continue
        path = tuple(k for _, k in stack)
        m = re.match(r"^([\"']?)([^:\"']+)\1\s*:(?:\s+(.*))?$", s)
        if m and not s.startswith(("[", "{")):
            key, val = m.group(2).strip(), (m.group(3) or "").strip()
            if val in ("", "|", ">", "|-", ">-"):
                stack.append((content_indent, key))
                continue
            out.extend((path + (key,), v) for v in _yaml_values(val))
        else:
            out.extend((path, v) for v in _yaml_values(s))
    return out


def _yaml_values(val: str) -> List[str]:
    val = val.strip()
    if val.startswith("[") and val.endswith("]"):
        return [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
    return [val.strip("'\"")]


def _yaml_get(flat: List[Tuple[Tuple[str, ...], str]], *suffix: str) -> List[str]:
    n = len(suffix)
    return [v for p, v in flat if p[-n:] == suffix]


# ---------------------------------------------------------------------------
# nginx
# ---------------------------------------------------------------------------

@dataclass
class NgxDir:
    name: str
    args: List[str]
    file: str
    line: int
    children: Optional[List[NgxDir]] = None


def _ngx_lex(text: str) -> List[Tuple[str, int, bool]]:
    """Tokens (text, line, is_word) with comments removed; quotes kept as words."""
    toks: List[Tuple[str, int, bool]] = []
    i, n, line = 0, len(text), 1
    while i < n:
        c = text[i]
        if c == "\n":
            line += 1
            i += 1
        elif c.isspace():
            i += 1
        elif c == "#":
            while i < n and text[i] != "\n":
                i += 1
        elif c in "{};":
            toks.append((c, line, False))
            i += 1
        elif c in "\"'":
            j, buf = i + 1, []
            while j < n and text[j] != c:
                if text[j] == "\\" and j + 1 < n:
                    j += 1
                if text[j] == "\n":
                    line += 1
                buf.append(text[j])
                j += 1
            toks.append(("".join(buf), line, True))
            i = j + 1
        else:
            j = i
            while j < n and not text[j].isspace() and text[j] not in "{};":
                if text[j] == "\\" and j + 1 < n:
                    j += 1
                j += 1
            toks.append((text[i:j], line, True))
            i = j
    return toks


class _NginxReader:
    def __init__(self, ctx: ScanContext, conf_dir: str):
        self.ctx = ctx
        self.conf_dir = conf_dir
        self.files: List[str] = []

    def parse_file(self, logical: str, depth: int = 0) -> List[NgxDir]:
        if depth > MAX_INCLUDE_DEPTH or len(self.files) > MAX_CONF_FILES:
            return []
        text = read_text(self.ctx.path(logical))
        if text is None:
            return []
        self.files.append(logical)
        toks = _ngx_lex(text)
        pos = [0]
        return self._block(toks, pos, logical, depth)

    def _block(self, toks, pos, file: str, depth: int) -> List[NgxDir]:
        out: List[NgxDir] = []
        cur: List[Tuple[str, int, bool]] = []
        while pos[0] < len(toks):
            t, line, word = toks[pos[0]]
            pos[0] += 1
            if not word and t == ";":
                if cur:
                    d = NgxDir(cur[0][0], [x[0] for x in cur[1:]], file, cur[0][1])
                    if d.name == "include" and d.args:
                        for inc in _glob(self.ctx, _resolve(self.conf_dir, d.args[0])):
                            out.extend(self.parse_file(inc, depth + 1))
                    else:
                        out.append(d)
                cur = []
            elif not word and t == "{":
                name = cur[0][0] if cur else ""
                d = NgxDir(name, [x[0] for x in cur[1:]], file, cur[0][1] if cur else line, [])
                d.children = self._block(toks, pos, file, depth)
                out.append(d)
                cur = []
            elif not word and t == "}":
                return out
            else:
                cur.append((t, line, word))
        return out


def _ngx_last(dirs: Iterable[NgxDir], name: str) -> Optional[NgxDir]:
    found = None
    for d in dirs:
        if d.name == name and d.children is None:
            found = d
    return found


def _ngx_all(dirs: Iterable[NgxDir], name: str) -> List[NgxDir]:
    return [d for d in dirs if d.name == name and d.children is None]


def nginx_blocks(ctx: ScanContext) -> List[Block]:
    out: List[Block] = []
    for main in ("/etc/nginx/nginx.conf", "/usr/local/nginx/conf/nginx.conf", "/usr/local/etc/nginx/nginx.conf",
                 "/etc/openresty/nginx.conf", "/usr/local/openresty/nginx/conf/nginx.conf"):
        if not _exists(ctx, main):
            continue
        reader = _NginxReader(ctx, os.path.dirname(main))
        tree = reader.parse_file(main)
        ver = live_version(ctx, "nginx", ["nginx", "-v"], r"nginx/(\d+\.\d+\.\d+)")
        for ctxname in ("http", "stream", "mail"):
            for top in (d for d in tree if d.name == ctxname and d.children is not None):
                inherited = [d for d in top.children if d.children is None]
                for srv in (d for d in top.children if d.name == "server" and d.children is not None):
                    b = _nginx_server(ctx, srv, inherited, ver, ctxname, os.path.dirname(main))
                    if b is not None:
                        out.append(b)
        break
    return out


def _nginx_server(ctx: ScanContext, srv: NgxDir, inherited: List[NgxDir], ver: Optional[Tuple[int, ...]], ctxname: str,
                  conf_dir: str) -> Optional[Block]:
    own = [d for d in srv.children or [] if d.children is None]
    listens = _ngx_all(own, "listen")
    ssl_listen = [d for d in listens if any(a in ("ssl", "quic") for a in d.args[1:])]
    ssl_on = any(d.args[:1] == ["on"] for d in _ngx_all(own + inherited, "ssl"))
    if not ssl_listen and not ssl_on:
        return None

    def get(name: str) -> Optional[NgxDir]:
        return _ngx_last(own, name) or _ngx_last(inherited, name)

    def get_all(name: str) -> List[NgxDir]:
        mine = _ngx_all(own, name)
        return mine if mine else _ngx_all(inherited, name)

    names_ = [a for d in _ngx_all(own, "server_name") for a in d.args]
    b = Block("nginx", srv.file, f"server {names_[0] if names_ else '_'} (line {srv.line})", server_names=names_,
              listen=[" ".join(d.args) for d in (ssl_listen or listens)])
    b.attrs["context"] = ctxname
    if any("http2" in d.args for d in listens) or any(d.args[:1] == ["on"] for d in _ngx_all(own, "http2")):
        b.attrs["http2"] = True
    if any("quic" in d.args for d in listens):
        b.attrs["quic"] = True
    p = get("ssl_protocols")
    if p:
        b.protocols = [x for x in (normalize_proto(a) for a in p.args) if x]
        b.proto_directive = "ssl_protocols"
    else:
        b.proto_directive = "ssl_protocols (default)"
        if ver is None:
            b.protocols, b.proto_source = ["TLSv1", "TLSv1.1", "TLSv1.2"], "default-unknown-version"
        elif ver >= (1, 23, 4):
            b.protocols, b.proto_source = ["TLSv1.2", "TLSv1.3"], "default"
        else:
            b.protocols, b.proto_source = ["TLSv1", "TLSv1.1", "TLSv1.2"], "default"
    c = get("ssl_ciphers")
    if c and c.args:
        b.ciphers.append(CipherSpec(" ".join(c.args), "ssl_ciphers"))
    else:
        b.ciphers.append(CipherSpec("HIGH:!aNULL:!MD5", "ssl_ciphers (default)", source="default"))
    for cc in get_all("ssl_conf_command"):
        if len(cc.args) < 2:
            continue
        cmd, val = cc.args[0].lower(), " ".join(cc.args[1:])
        if cmd == "ciphersuites":
            b.ciphers.append(CipherSpec(val, "ssl_conf_command Ciphersuites", kind="iana"))
        elif cmd == "cipherstring":
            b.ciphers.append(CipherSpec(val, "ssl_conf_command CipherString"))
        elif cmd in ("groups", "curves"):
            b.groups.extend((g, f"ssl_conf_command {cc.args[0]}", None) for g in val.split(":"))
        elif cmd == "minprotocol" and normalize_proto(val):
            b.protocols = _apply_minmax(b.protocols or [], normalize_proto(val), None)
            b.attrs["min_protocol"] = normalize_proto(val)
        elif cmd == "maxprotocol" and normalize_proto(val):
            b.protocols = _apply_minmax(b.protocols or [], None, normalize_proto(val))
        elif cmd == "protocol":
            b.protocols = _openssl_conf_protocol(val, b.protocols or [])
        elif cmd == "options":
            b.attrs.setdefault("openssl_options", []).append(val)
    e = get("ssl_ecdh_curve")
    if e and e.args:
        b.groups.extend((g, "ssl_ecdh_curve", None) for g in e.args[0].split(":"))
    d = get("ssl_dhparam")
    b.dhparam_directive = "ssl_dhparam"
    if d and d.args:
        b.dhparam_file = _resolve(conf_dir, d.args[0])
    psc = get("ssl_prefer_server_ciphers")
    b.attrs["prefer_server_ciphers"] = bool(psc and psc.args[:1] == ["on"])
    st = get("ssl_stapling")
    b.attrs["ocsp_stapling"] = bool(st and st.args[:1] == ["on"])
    tk = get("ssl_session_tickets")
    if tk:
        b.attrs["session_tickets"] = tk.args[:1] == ["on"]
    for cd in get_all("ssl_certificate"):
        if cd.args and not cd.args[0].startswith(("data:", "engine:", "$")):
            b.certs.append(_resolve(conf_dir, cd.args[0]))
    for kd in get_all("ssl_certificate_key"):
        if kd.args and not kd.args[0].startswith(("data:", "engine:", "$")):
            b.keys.append(_resolve(conf_dir, kd.args[0]))
    return b


# ---------------------------------------------------------------------------
# Apache httpd
# ---------------------------------------------------------------------------

@dataclass
class ApDir:
    name: str            # lower-case directive name
    args: List[str]
    file: str
    line: int
    vhost: Optional[int]  # index of the enclosing <VirtualHost>, None = server config
    vhost_args: List[str] = field(default_factory=list)
    scoped: bool = False  # inside <Directory>/<Location>/<Files>


class _ApacheReader:
    def __init__(self, ctx: ScanContext, server_root: str):
        self.ctx = ctx
        self.server_root = server_root
        self.dirs: List[ApDir] = []
        self.files: List[str] = []
        self._vh = 0

    def read(self, logical: str, depth: int = 0, stack: Optional[List[Tuple[str, str, Optional[int]]]] = None) -> None:
        if depth > MAX_INCLUDE_DEPTH or len(self.files) > MAX_CONF_FILES or logical in self.files:
            return
        text = read_text(self.ctx.path(logical))
        if text is None:
            return
        self.files.append(logical)
        stack = stack if stack is not None else []
        skip_depth: Optional[int] = None
        buf, start = "", 0
        for no, raw in enumerate(text.splitlines(), 1):
            if raw.rstrip().endswith("\\"):
                if not buf:
                    start = no
                buf += raw.rstrip()[:-1] + " "
                continue
            line = (buf + raw).strip()
            lineno = start if buf else no
            buf = ""
            if not line or line.startswith("#"):
                continue
            if line.startswith("</"):
                if stack:
                    stack.pop()
                if skip_depth is not None and len(stack) < skip_depth:
                    skip_depth = None
                continue
            if line.startswith("<"):
                m = re.match(r"<\s*(\S+)\s*(.*?)\s*>$", line)
                if not m:
                    continue
                sec, arg = m.group(1).lower(), m.group(2)
                vh = None
                if sec == "virtualhost":
                    self._vh += 1
                    vh = self._vh
                stack.append((sec, arg, vh))
                if skip_depth is None and sec in ("ifmodule", "ifdefine") and arg.startswith("!"):
                    skip_depth = len(stack)
                continue
            if skip_depth is not None:
                continue
            toks = tokenize(line)
            if not toks:
                continue
            name = toks[0].lower()
            if name in ("include", "includeoptional") and len(toks) > 1:
                for inc in _glob(self.ctx, _resolve(self.server_root, toks[1])):
                    self.read(inc, depth + 1, stack)
                continue
            vhs = [(s, a, v) for s, a, v in stack if s == "virtualhost"]
            scoped = any(s in ("directory", "directorymatch", "location", "locationmatch", "files", "filesmatch") for s, _, _ in stack)
            self.dirs.append(ApDir(name, toks[1:], logical, lineno, vhs[-1][2] if vhs else None,
                                   tokenize(vhs[-1][1]) if vhs else [], scoped))


def apache_blocks(ctx: ScanContext) -> List[Block]:
    for main, root in (("/etc/apache2/apache2.conf", "/etc/apache2"), ("/etc/httpd/conf/httpd.conf", "/etc/httpd"),
                       ("/usr/local/apache2/conf/httpd.conf", "/usr/local/apache2"), ("/etc/apache2/httpd.conf", "/etc/apache2"),
                       ("/usr/local/etc/apache24/httpd.conf", "/usr/local/etc/apache24")):
        if not _exists(ctx, main):
            continue
        text = read_text(ctx.path(main)) or ""
        m = re.search(r"^\s*ServerRoot\s+\"?([^\"\s]+)", text, re.M | re.I)
        reader = _ApacheReader(ctx, m.group(1) if m else root)
        reader.read(main)
        return _apache_assemble(reader, main)
    return []


def _apache_assemble(reader: _ApacheReader, main: str) -> List[Block]:
    dirs = [d for d in reader.dirs if not d.scoped]
    glob_dirs = [d for d in dirs if d.vhost is None]
    vhosts: Dict[int, List[ApDir]] = {}
    for d in dirs:
        if d.vhost is not None:
            vhosts.setdefault(d.vhost, []).append(d)
    any_proto = any(d.name == "sslprotocol" for d in dirs)
    out: List[Block] = []

    def last(ds: List[ApDir], name: str) -> Optional[ApDir]:
        f = None
        for d in ds:
            if d.name == name:
                f = d
        return f

    candidates: List[Tuple[str, List[ApDir], List[ApDir]]] = []
    for vh, ds in sorted(vhosts.items()):
        candidates.append((f"vhost {' '.join(ds[0].vhost_args)}", ds, glob_dirs))
    geng = last(glob_dirs, "sslengine")
    if not candidates or (geng is not None and geng.args[:1] and geng.args[0].lower() == "on"):
        candidates.insert(0, ("server config", glob_dirs, []))
    for label, own, inh in candidates:
        eng = last(own, "sslengine") or (last(inh, "sslengine") if inh else None)
        if not eng or not eng.args or eng.args[0].lower() not in ("on", "optional"):
            continue

        def get(name: str, own: List[ApDir] = own, inh: List[ApDir] = inh) -> Optional[ApDir]:
            return last(own, name) or (last(inh, name) if inh else None)

        def get_all(name: str, own: List[ApDir] = own, inh: List[ApDir] = inh) -> List[ApDir]:
            mine = [d for d in own if d.name == name]
            return mine if mine else [d for d in inh if d.name == name]

        sn = [a for d in own if d.name in ("servername", "serveralias") for a in d.args]
        b = Block("apache", own[0].file if own else main, f"{label} ({sn[0]})" if sn else label, server_names=sn,
                  listen=list(own[0].vhost_args) if own and own[0].vhost is not None else [])
        p = get("sslprotocol")
        if p:
            b.protocols, b.proto_directive = resolve_protocol_expr(" ".join(p.args)), "SSLProtocol"
        else:
            b.protocols, b.proto_directive, b.proto_source = TLS_ALL[:], "SSLProtocol (default: all -SSLv3)", "default"
            b.attrs["sslprotocol_absent_everywhere"] = not any_proto
        for cs in get_all("sslciphersuite"):
            if not cs.args:
                continue
            if cs.args[0].upper() in ("TLSV1.3", "SSL") and len(cs.args) > 1:
                kind = "iana" if cs.args[0].upper() == "TLSV1.3" else "openssl"
                b.ciphers.append(CipherSpec(" ".join(cs.args[1:]), f"SSLCipherSuite {cs.args[0]}", kind=kind))
            else:
                b.ciphers.append(CipherSpec(" ".join(cs.args), "SSLCipherSuite"))
        for cc in get_all("sslopensslconfcmd"):
            if len(cc.args) < 2:
                continue
            cmd, val = cc.args[0].lower(), " ".join(cc.args[1:])
            if cmd == "dhparameters":
                b.dhparam_file = _resolve(reader.server_root, val)
            elif cmd in ("curves", "groups", "ecdhparameters"):
                b.groups.extend((g, f"SSLOpenSSLConfCmd {cc.args[0]}", None) for g in val.split(":"))
            elif cmd == "minprotocol" and normalize_proto(val):
                b.protocols = _apply_minmax(b.protocols or [], normalize_proto(val), None)
            elif cmd == "maxprotocol" and normalize_proto(val):
                b.protocols = _apply_minmax(b.protocols or [], None, normalize_proto(val))
            elif cmd == "protocol":
                b.protocols = _openssl_conf_protocol(val, b.protocols or [])
            elif cmd == "ciphersuites":
                b.ciphers.append(CipherSpec(val, "SSLOpenSSLConfCmd Ciphersuites", kind="iana"))
            elif cmd == "cipherstring":
                b.ciphers.append(CipherSpec(val, "SSLOpenSSLConfCmd CipherString"))
        b.dhparam_directive = "SSLOpenSSLConfCmd DHParameters"
        for key, attr in (("sslhonorcipherorder", "honor_cipher_order"), ("sslusestapling", "ocsp_stapling"),
                          ("sslcompression", "compression"), ("sslinsecurerenegotiation", "insecure_renegotiation"),
                          ("sslsessiontickets", "session_tickets")):
            d = get(key)
            if d and d.args:
                b.attrs[attr] = d.args[0].lower() == "on"
        for d in get_all("sslcertificatefile") + get_all("sslcertificatechainfile"):
            if d.args:
                b.certs.append(_resolve(reader.server_root, d.args[0]))
        for d in get_all("sslcertificatekeyfile"):
            if d.args:
                b.keys.append(_resolve(reader.server_root, d.args[0]))
        out.append(b)
    return out


# ---------------------------------------------------------------------------
# HAProxy
# ---------------------------------------------------------------------------

_HAP_NO = {"no-sslv3": "SSLv3", "no-tlsv10": "TLSv1", "no-tlsv11": "TLSv1.1", "no-tlsv12": "TLSv1.2", "no-tlsv13": "TLSv1.3"}
_HAP_FORCE = {"force-sslv3": "SSLv3", "force-tlsv10": "TLSv1", "force-tlsv11": "TLSv1.1", "force-tlsv12": "TLSv1.2",
              "force-tlsv13": "TLSv1.3"}


def _hap_options(toks: List[str]) -> Dict[str, object]:
    """Parse HAProxy ssl options (bind line or ssl-default-*-options)."""
    o: Dict[str, object] = {"no": set(), "force": None, "min": None, "max": None, "tickets": None}
    i = 0
    while i < len(toks):
        t = toks[i]
        nxt = toks[i + 1] if i + 1 < len(toks) else None
        if t in _HAP_NO:
            o["no"].add(_HAP_NO[t])
        elif t in _HAP_FORCE:
            o["force"] = _HAP_FORCE[t]
        elif t == "ssl-min-ver" and nxt:
            o["min"] = normalize_proto(nxt)
            i += 1
        elif t == "ssl-max-ver" and nxt:
            o["max"] = normalize_proto(nxt)
            i += 1
        elif t == "no-tls-tickets":
            o["tickets"] = False
        i += 1
    return o


def _hap_protocols(opts: List[Dict[str, object]], default_min: str) -> Tuple[List[str], bool]:
    """Effective protocols from option dicts (later wins); returns (protocols, explicitly_configured)."""
    explicit = False
    mn, mx, force, no = None, None, None, set()
    for o in opts:
        if o["min"] or o["max"] or o["force"] or o["no"]:
            explicit = True
        if o["force"]:
            force = o["force"]
        if o["min"]:
            mn = o["min"]
        if o["max"]:
            mx = o["max"]
        no |= o["no"]
    if force:
        return [force], True
    if mn or mx:
        protos = [p for p in proto_range(mn or "SSLv3", mx or "TLSv1.3") if p != "SSLv2"]
    else:
        protos = [p for p in proto_range(default_min, "TLSv1.3")]
    return [p for p in protos if p not in no], explicit


def haproxy_blocks(ctx: ScanContext) -> List[Block]:
    files = [f for f in ("/etc/haproxy/haproxy.cfg",) if _exists(ctx, f)] + _glob(ctx, "/etc/haproxy/conf.d/*.cfg")
    if not files:
        return []
    ver = live_version(ctx, "haproxy", ["haproxy", "-v"], r"HA-?Proxy version (\d+\.\d+(?:\.\d+)?)")
    if ver is None:
        default_min, dsrc = "TLSv1", "default-unknown-version"
    elif ver >= (2, 2):
        default_min, dsrc = "TLSv1.2", "default"
    else:
        default_min, dsrc = "TLSv1", "default"
    glob_: Dict[str, List[str]] = {}
    sections: List[Tuple[str, str, str, List[Tuple[int, List[str]]]]] = []      # (type, name, file, lines)
    for f in files:
        text = read_text(ctx.path(f)) or ""
        cur: Optional[Tuple[str, str, str, List[Tuple[int, List[str]]]]] = None
        for no, raw in enumerate(text.splitlines(), 1):
            s = raw.split("#", 1)[0].strip() if not raw.strip().startswith("#") else ""
            if not s:
                continue
            toks = tokenize(s)
            if toks[0] in ("global", "defaults", "frontend", "backend", "listen", "peers", "resolvers", "userlist",
                           "program", "http-errors", "ring", "cache", "mailers"):
                cur = (toks[0], toks[1] if len(toks) > 1 else "", f, [])
                sections.append(cur)
                continue
            if cur is None:
                continue
            if cur[0] == "global":
                glob_[toks[0]] = toks[1:]
            else:
                cur[3].append((no, toks))
    dh = glob_.get("tune.ssl.default-dh-param")
    dh_file = glob_.get("ssl-dh-param-file")
    crt_base = (glob_.get("crt-base") or [os.path.dirname(files[0])])[0]
    out: List[Block] = []
    for stype, sname, f, lines in sections:
        if stype not in ("frontend", "listen", "backend"):
            continue
        for no, toks in lines:
            if toks[0] == "bind" and "ssl" in toks[2:]:
                b = Block("haproxy", f, f"{stype} {sname} bind {toks[1] if len(toks) > 1 else ''}", listen=[toks[1]] if len(toks) > 1 else [])
                _hap_fill(b, toks[2:], glob_, "bind", default_min, dsrc, crt_base, ctx)
            elif toks[0] in ("server", "default-server") and "ssl" in toks[3:]:
                b = Block("haproxy", f, f"{stype} {sname} server {toks[1] if len(toks) > 1 else ''}", role="client",
                          listen=[toks[2]] if len(toks) > 2 else [])
                _hap_fill(b, toks[2:], glob_, "server", default_min, dsrc, crt_base, ctx)
                b.dhe_check = False
            else:
                continue
            if dh and dh[0].isdigit():
                b.dh_bits = (int(dh[0]), f"tune.ssl.default-dh-param {dh[0]}")
                b.dhparam_directive = "tune.ssl.default-dh-param"
            elif dh_file:
                b.dhparam_file, b.dhparam_directive = _resolve(crt_base, dh_file[0]), "ssl-dh-param-file"
            else:
                b.dhparam_directive = "tune.ssl.default-dh-param"
            out.append(b)
    return out


def _hap_fill(b: Block, toks: List[str], glob_: Dict[str, List[str]], side: str, default_min: str, dsrc: str,
              crt_base: str, ctx: ScanContext) -> None:
    pre = f"ssl-default-{side}"
    gopts = _hap_options(glob_.get(f"{pre}-options", []))
    lopts = _hap_options(toks)
    protos, explicit = _hap_protocols([gopts, lopts], default_min)
    b.protocols = protos
    b.proto_directive = f"{side} options / {pre}-options"
    if not (gopts["min"] or gopts["max"] or gopts["force"] or lopts["min"] or lopts["max"] or lopts["force"]):
        b.proto_source = dsrc       # the lower bound is the software default
    b.attrs["options"] = sorted(set(glob_.get(f"{pre}-options", [])) | {t for t in toks if t.startswith(("no-", "force-"))})
    if lopts["tickets"] is False or gopts["tickets"] is False:
        b.attrs["session_tickets"] = False

    def opt(name: str) -> Optional[str]:
        if name in toks and toks.index(name) + 1 < len(toks):
            return toks[toks.index(name) + 1]
        return None

    c = opt("ciphers") or (glob_.get(f"{pre}-ciphers") or [None])[0]
    if c:
        b.ciphers.append(CipherSpec(c, "ciphers" if opt("ciphers") else f"{pre}-ciphers"))
    cs = opt("ciphersuites") or (glob_.get(f"{pre}-ciphersuites") or [None])[0]
    if cs:
        b.ciphers.append(CipherSpec(cs, "ciphersuites" if opt("ciphersuites") else f"{pre}-ciphersuites", kind="iana"))
    cv = opt("curves") or opt("ecdhe") or (glob_.get(f"{pre}-curves") or [None])[0]
    if cv:
        b.groups.extend((g, "curves", None) for g in cv.split(":"))
    for i, t in enumerate(toks):
        if t == "crt" and i + 1 < len(toks):
            p = _resolve(crt_base, toks[i + 1])
            if os.path.isdir(ctx.path(p)):
                for f in _glob(ctx, p.rstrip("/") + "/*.pem"):
                    b.certs.append(f)
            else:
                b.certs.append(p)
        elif t == "crt-list" and i + 1 < len(toks):
            lst = _resolve(crt_base, toks[i + 1])
            txt = read_text(ctx.path(lst))
            if txt is None:
                b.errors.append(f"cannot read crt-list {lst}")
                continue
            for ln in txt.splitlines():
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    b.certs.append(_resolve(crt_base, tokenize(ln)[0]))


# ---------------------------------------------------------------------------
# Postfix
# ---------------------------------------------------------------------------

POSTFIX_GRADES = {
    "high": "aNULL:-aNULL:HIGH:@STRENGTH",
    "medium": "aNULL:-aNULL:HIGH:MEDIUM:@STRENGTH",
    "low": "aNULL:-aNULL:HIGH:MEDIUM:LOW:@STRENGTH",
    "export": "aNULL:-aNULL:HIGH:MEDIUM:LOW:EXPORT:@STRENGTH",
    "null": "eNULL:!aNULL",
}


def parse_postfix_main(text: str) -> Dict[str, str]:
    """main.cf -> {name: value} with continuation lines joined and $name expanded once."""
    raw: Dict[str, str] = {}
    key = None
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace() and key:
            raw[key] += " " + line.strip()
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$", line)
        if m:
            key = m.group(1)
            raw[key] = m.group(2).strip()
    defaults = {"config_directory": "/etc/postfix"}

    def expand(v: str) -> str:
        return re.sub(r"\$\{?([A-Za-z0-9_]+)\}?", lambda m: raw.get(m.group(1), defaults.get(m.group(1), m.group(0))), v)
    return {k: expand(v) for k, v in raw.items()}


def parse_postfix_protocols(value: str) -> List[str]:
    """`!SSLv2, !SSLv3` | `>=TLSv1.2` | `<=TLSv1.2` | `TLSv1.2 TLSv1.3` -> canonical protocol list."""
    universe = ["SSLv3"] + TLS_ALL
    toks = [t for t in re.split(r"[\s,:]+", value.strip()) if t]
    if not toks:
        return TLS_ALL[:]
    incl: List[str] = []
    excl: set = set()
    lo = hi = None
    for t in toks:
        if t.startswith(">="):
            lo = normalize_proto(t[2:])
        elif t.startswith("<="):
            hi = normalize_proto(t[2:])
        elif t.startswith("!"):
            p = normalize_proto(t[1:])
            if p:
                excl.add(p)
        else:
            p = normalize_proto(t)
            if p:
                incl.append(p)
    base = incl if incl else universe
    if not incl and not lo and excl:
        base = [p for p in universe if p not in excl]
    elif lo or hi:
        base = _apply_minmax(base, lo, hi)
    return [p for p in sort_protos(base) if p not in excl]


def postfix_blocks(ctx: ScanContext) -> List[Block]:
    main = "/etc/postfix/main.cf"
    text = read_text(ctx.path(main))
    if text is None:
        return []
    cf = parse_postfix_main(text)
    out: List[Block] = []
    for side, prefix in (("server", "smtpd"), ("client", "smtp")):
        level = cf.get(f"{prefix}_tls_security_level", "").lower()
        use = cf.get(f"{prefix}_use_tls", "no").lower() == "yes" or cf.get(f"{prefix}_enforce_tls", "no").lower() == "yes"
        has_cert = bool(cf.get(f"{prefix}_tls_cert_file") or cf.get(f"{prefix}_tls_chain_files") or cf.get(f"{prefix}_tls_eccert_file"))
        if level in ("none",) or not (level or use or (has_cert and side == "server")):
            continue
        b = Block("postfix", main, f"{prefix} ({'smtp server' if side == 'server' else 'smtp client'})", role=side)
        b.attrs["security_level"] = level or ("may" if use else "")
        protos: List[str] = []
        srcs = []
        for key in (f"{prefix}_tls_protocols", f"{prefix}_tls_mandatory_protocols"):
            if key in cf:
                protos += parse_postfix_protocols(cf[key])
                srcs.append(None)
            else:
                protos += TLS_ALL
                srcs.append("default")
        b.protocols = sort_protos(set(protos))
        b.proto_directive = f"{prefix}_tls_protocols + {prefix}_tls_mandatory_protocols"
        b.proto_source = "default" if all(s == "default" for s in srcs) else None
        mandatory = level in ("encrypt", "dane", "fingerprint", "verify", "secure")
        for key, excl_key in ((f"{prefix}_tls_ciphers", f"{prefix}_tls_exclude_ciphers"),
                              (f"{prefix}_tls_mandatory_ciphers", f"{prefix}_tls_mandatory_exclude_ciphers")):
            if key.endswith("mandatory_ciphers") and not mandatory and key not in cf:
                continue
            grade = cf.get(key, "medium").lower()
            spec = cf.get(f"tls_{grade}_cipherlist") or POSTFIX_GRADES.get(grade, POSTFIX_GRADES["medium"])
            src = None if key in cf else "default"
            b.ciphers.append(CipherSpec(spec, f"{key} = {grade}", source=src))
            b.attrs.setdefault("cipher_grades", {})[key] = grade
            for e in cf.get(excl_key, "").replace(",", " ").split():
                if e not in b.exclude:
                    b.exclude.append(e)
        if side == "server":
            b.dhparam_directive = "smtpd_tls_dh1024_param_file"
            if cf.get("smtpd_tls_dh1024_param_file"):
                b.dhparam_file = cf["smtpd_tls_dh1024_param_file"]
            if cf.get("smtpd_tls_dh512_param_file"):
                b.attrs["dh512_param_file"] = cf["smtpd_tls_dh512_param_file"]
            eg = cf.get("smtpd_tls_eecdh_grade", "").lower()
            if eg:
                b.attrs["eecdh_grade"] = eg
                if eg == "strong":
                    b.groups.append((cf.get("tls_eecdh_strong_curve", "prime256v1"), "smtpd_tls_eecdh_grade strong", None))
                elif eg == "ultra":
                    b.groups.append((cf.get("tls_eecdh_ultra_curve", "secp384r1"), "smtpd_tls_eecdh_grade ultra", None))
            if cf.get("tls_eecdh_auto_curves") and eg in ("", "auto"):
                b.groups.extend((g, "tls_eecdh_auto_curves", None) for g in re.split(r"[\s,:]+", cf["tls_eecdh_auto_curves"]) if g)
        else:
            b.dhe_check = False
        for k in ("cert_file", "eccert_file", "dcert_file"):
            if cf.get(f"{prefix}_tls_{k}"):
                b.certs.append(cf[f"{prefix}_tls_{k}"])
        for f in cf.get(f"{prefix}_tls_chain_files", "").replace(",", " ").split():
            b.certs.append(f)
        for k, ck in (("key_file", "cert_file"), ("eckey_file", "eccert_file"), ("dkey_file", "dcert_file")):
            if cf.get(f"{prefix}_tls_{k}"):
                b.keys.append(cf[f"{prefix}_tls_{k}"])
        out.append(b)
    return out


# ---------------------------------------------------------------------------
# Dovecot
# ---------------------------------------------------------------------------

DOVECOT_DEFAULT_CIPHERS = "ALL:!kRSA:!SRP:!kDHd:!DSS:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK:!RC4:!ADH:!LOW@STRENGTH"


def _dovecot_read(ctx: ScanContext, logical: str, out: List[Tuple[str, str, str, int]], files: List[str], depth: int = 0) -> None:
    if depth > MAX_INCLUDE_DEPTH or logical in files or len(files) > MAX_CONF_FILES:
        return
    text = read_text(ctx.path(logical))
    if text is None:
        return
    files.append(logical)
    level = 0
    for raw in text.splitlines():
        s = raw.split("#", 1)[0].strip()
        if not s:
            continue
        m = re.match(r"^!include(?:_try)?\s+(\S+)", s)
        if m:
            for inc in _glob(ctx, _resolve(os.path.dirname(logical), m.group(1))):
                _dovecot_read(ctx, inc, out, files, depth + 1)
            continue
        if s.endswith("{"):
            level += 1
            continue
        if s == "}":
            level = max(level - 1, 0)
            continue
        m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$", s)
        if m:
            out.append((m.group(1), m.group(2).strip(), logical, level))


def dovecot_blocks(ctx: ScanContext) -> List[Block]:
    main = "/etc/dovecot/dovecot.conf"
    settings: List[Tuple[str, str, str, int]] = []
    files: List[str] = []
    if _exists(ctx, main):
        _dovecot_read(ctx, main, settings, files)
    for f in ("/etc/dovecot/conf.d/10-ssl.conf",):
        if _exists(ctx, f) and f not in files:
            _dovecot_read(ctx, f, settings, files)
    if not settings:
        return []
    top: Dict[str, Tuple[str, str]] = {}
    for k, v, f, lvl in settings:
        if lvl == 0:
            top[k] = (v, f)
    ssl = top.get("ssl", ("yes", ""))[0].lower()
    if ssl == "no" or not any(k.startswith("ssl") for k in top):
        return []
    cfg_file = top.get("ssl_cert", top.get("ssl", ("", files[0])))[1] or files[0]
    b = Block("dovecot", cfg_file, "imap/pop3 (ssl = " + ssl + ")", attrs={"ssl": ssl})
    ver = live_version(ctx, "dovecot", ["dovecot", "--version"], r"^(\d+\.\d+(?:\.\d+)?)")
    mp = top.get("ssl_min_protocol")
    if mp and normalize_proto(mp[0]):
        b.protocols, b.proto_directive = _proto_min(normalize_proto(mp[0])), "ssl_min_protocol"
    elif "ssl_protocols" in top:
        b.protocols = parse_postfix_protocols(top["ssl_protocols"][0])
        b.proto_directive = "ssl_protocols"
    else:
        b.proto_directive = "ssl_min_protocol (default)"
        if ver is None:
            b.protocols, b.proto_source = TLS_ALL[:], "default-unknown-version"
        elif ver >= (2, 3, 15):
            b.protocols, b.proto_source = ["TLSv1.2", "TLSv1.3"], "default"
        else:
            b.protocols, b.proto_source = TLS_ALL[:], "default"
    if "ssl_cipher_list" in top:
        b.ciphers.append(CipherSpec(top["ssl_cipher_list"][0], "ssl_cipher_list"))
    else:
        b.ciphers.append(CipherSpec(DOVECOT_DEFAULT_CIPHERS, "ssl_cipher_list (default)", source="default"))
    if "ssl_cipher_suites" in top:
        b.ciphers.append(CipherSpec(top["ssl_cipher_suites"][0], "ssl_cipher_suites", kind="iana"))
    if "ssl_curve_list" in top:
        b.groups.extend((g, "ssl_curve_list", None) for g in top["ssl_curve_list"][0].split(":"))
    b.dhparam_directive = "ssl_dh"
    if "ssl_dh" in top:
        b.dhparam_file = top["ssl_dh"][0].lstrip("<").strip()
    if "ssl_dh_parameters_length" in top and top["ssl_dh_parameters_length"][0].isdigit():
        n = int(top["ssl_dh_parameters_length"][0])
        b.dh_bits = (n, f"ssl_dh_parameters_length = {n}")
    if "ssl_prefer_server_ciphers" in top:
        b.attrs["prefer_server_ciphers"] = top["ssl_prefer_server_ciphers"][0].lower() == "yes"
    for k, v, f, lvl in settings:
        if k in ("ssl_cert", "ssl_alt_cert") and v.startswith("<"):
            b.certs.append(v[1:].strip())
        elif k in ("ssl_key", "ssl_alt_key") and v.startswith("<"):
            b.keys.append(v[1:].strip())
    return [b]


# ---------------------------------------------------------------------------
# Exim
# ---------------------------------------------------------------------------

def exim_blocks(ctx: ScanContext) -> List[Block]:
    files = [f for f in ("/etc/exim4/exim4.conf", "/etc/exim/exim.conf", "/etc/exim4/exim4.conf.template",
                         "/usr/local/etc/exim/configure", "/etc/exim/configure") if _exists(ctx, f)]
    files += _glob(ctx, "/etc/exim4/conf.d/main/*")
    if not files:
        return []
    settings: Dict[str, Tuple[str, str]] = {}
    for f in files:
        text = read_text(ctx.path(f)) or ""
        for line in text.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if re.match(r"^begin\s+\S+", s):
                break                                   # only the main section holds TLS options
            m = re.match(r"^([A-Za-z0-9_]+)\s*=\s*(.*)$", s)
            if m and (m.group(1).startswith("tls_") or m.group(1) in ("openssl_options",)) or \
                    (m and m.group(1).startswith(("MAIN_TLS", "TLS_"))):
                settings.setdefault(m.group(1), (m.group(2).strip(), f))
    tls_keys = {k for k in settings if k.startswith("tls_") or k == "openssl_options"}
    if not tls_keys:
        return []
    cfg = next(iter(settings.values()))[1]
    b = Block("exim", cfg, "smtp (main section)")
    opts = settings.get("openssl_options", ("", ""))[0]
    req = settings.get("tls_require_ciphers", ("", ""))[0].strip().strip('"')
    gnutls = bool(re.match(r"^(NORMAL|SECURE\d*|PERFORMANCE|NONE|PFS|LEGACY|SUITEB\d+)\b", req)) or "VERS-" in req
    if gnutls:
        protos = set(TLS_ALL)
        for m in re.finditer(r"([+-])VERS-(TLS1\.\d|SSL3\.0|TLS-ALL)", req):
            members = TLS_ALL if m.group(2) == "TLS-ALL" else [normalize_proto(m.group(2).replace("SSL3.0", "SSLv3").replace("TLS", "TLSv"))]
            protos = protos - set(members) if m.group(1) == "-" else protos | {x for x in members if x}
        b.protocols, b.proto_directive = sort_protos(protos), "tls_require_ciphers (GnuTLS priority)"
        b.attrs["tls_library"] = "gnutls"
        b.attrs["gnutls_priority"] = req
    else:
        protos = TLS_ALL[:]
        no = {"+no_sslv3": "SSLv3", "+no_tlsv1": "TLSv1", "+no_tlsv1_1": "TLSv1.1", "+no_tlsv1_2": "TLSv1.2", "+no_tlsv1_3": "TLSv1.3"}
        toks = opts.split()
        if "-no_sslv3" in toks:
            protos = ["SSLv3"] + protos
        protos = [p for p in protos if p not in {v for k, v in no.items() if k in toks}]
        b.protocols, b.proto_directive = protos, "openssl_options"
        if not opts:
            b.proto_source = "default"
            b.proto_directive = "openssl_options (default +no_sslv2 +no_sslv3)"
        if req:
            b.ciphers.append(CipherSpec(req, "tls_require_ciphers"))
    b.dhparam_directive = "tls_dhparam"
    dh = settings.get("tls_dhparam", ("", ""))[0].strip('"')
    if dh.startswith("/"):
        b.dhparam_file = dh
    elif dh:
        b.attrs["tls_dhparam"] = dh
        m = re.match(r"ffdhe(\d+)", dh)
        if m:
            b.dh_bits = (int(m.group(1)), f"tls_dhparam = {dh}")
        b.dhe_check = dh != "none"
    for k, lst in (("tls_certificate", b.certs), ("tls_privatekey", b.keys)):
        v = settings.get(k, ("", ""))[0].strip('"')
        if v.startswith("/") and "$" not in v:
            lst.append(v)
    return [b]


# ---------------------------------------------------------------------------
# lighttpd
# ---------------------------------------------------------------------------

def _lighttpd_read(ctx: ScanContext, logical: str, lines: List[Tuple[str, str, int]], files: List[str], depth: int = 0) -> None:
    if depth > MAX_INCLUDE_DEPTH or logical in files:
        return
    text = read_text(ctx.path(logical))
    if text is None:
        return
    files.append(logical)
    for no, raw in enumerate(text.splitlines(), 1):
        s = raw.split("#", 1)[0].strip() if not raw.strip().startswith("#") else ""
        if not s:
            continue
        m = re.match(r'^include\s+"([^"]+)"', s)
        if m:
            for inc in _glob(ctx, _resolve(os.path.dirname(logical), m.group(1))):
                _lighttpd_read(ctx, inc, lines, files, depth + 1)
            continue
        lines.append((s, logical, no))


def lighttpd_blocks(ctx: ScanContext) -> List[Block]:
    main = "/etc/lighttpd/lighttpd.conf"
    if not _exists(ctx, main):
        return []
    lines: List[Tuple[str, str, int]] = []
    _lighttpd_read(ctx, main, lines, [])
    ver = live_version(ctx, "lighttpd", ["lighttpd", "-v"], r"lighttpd/(\d+\.\d+\.\d+)")
    scopes: List[Tuple[str, Dict[str, Tuple[str, str]]]] = [("global", {})]
    stack: List[int] = []
    buf = ""
    for s, f, _no in lines:
        # join multi-line ( ... ) values
        if buf:
            buf += " " + s
            if buf.count("(") <= buf.count(")"):
                s, buf = buf, ""
            else:
                continue
        elif "(" in s and s.count("(") > s.count(")"):
            buf = s
            continue
        m = re.match(r'^\$SERVER\["socket"\]\s*==\s*"([^"]*)"\s*\{\s*$', s)
        if m:
            scopes.append((m.group(1), {}))
            stack.append(len(scopes) - 1)
            continue
        if s.endswith("{"):
            stack.append(-1)
            continue
        if s == "}":
            if stack:
                stack.pop()
            continue
        m = re.match(r"^(ssl\.[A-Za-z0-9._-]+)\s*(\+?=)\s*(.+)$", s)
        if not m:
            continue
        target = next((i for i in reversed(stack) if i >= 0), 0)
        scopes[target][1][m.group(1)] = (m.group(3).strip(), f)
    out: List[Block] = []
    glob_settings = scopes[0][1]
    for label, own in scopes:
        merged = dict(glob_settings)
        merged.update(own)
        eng = merged.get("ssl.engine", ("", ""))[0].strip('"')
        if eng != "enable" or (label == "global" and len(scopes) > 1 and "ssl.engine" not in glob_settings):
            continue
        if label == "global" and len(scopes) > 1 and all("ssl.engine" in o for _, o in scopes[1:]):
            continue
        f = next((v[1] for v in own.values()), main)
        b = Block("lighttpd", f, f"socket {label}" if label != "global" else "server config",
                  listen=[label] if label != "global" else [])
        conf_cmd = merged.get("ssl.openssl.ssl-conf-cmd", ("", ""))[0]
        cmds = dict(re.findall(r'"([^"]+)"\s*=>\s*"([^"]*)"', conf_cmd))
        mp = cmds.get("MinProtocol")
        if mp and normalize_proto(mp):
            b.protocols, b.proto_directive = _proto_min(normalize_proto(mp)), "ssl.openssl.ssl-conf-cmd MinProtocol"
        else:
            b.proto_directive = "MinProtocol (default)"
            if ver is None:
                b.protocols, b.proto_source = TLS_ALL[:], "default-unknown-version"
            elif ver >= (1, 4, 56):
                b.protocols, b.proto_source = ["TLSv1.2", "TLSv1.3"], "default"
            else:
                b.protocols, b.proto_source = TLS_ALL[:], "default"
        if "Protocol" in cmds:
            b.protocols = _openssl_conf_protocol(cmds["Protocol"], b.protocols)
        if merged.get("ssl.use-sslv3", ("", ""))[0].strip('"') == "enable":
            b.protocols = sort_protos(set(b.protocols) | {"SSLv3"})
        if merged.get("ssl.use-sslv2", ("", ""))[0].strip('"') == "enable":
            b.attrs["sslv2_enabled"] = True
            b.protocols = sort_protos(set(b.protocols) | {"SSLv2"})
        cl = merged.get("ssl.cipher-list", ("", ""))[0].strip('"')
        if cmds.get("CipherString"):
            b.ciphers.append(CipherSpec(cmds["CipherString"], "ssl.openssl.ssl-conf-cmd CipherString"))
        elif cl:
            b.ciphers.append(CipherSpec(cl, "ssl.cipher-list"))
        if cmds.get("Ciphersuites"):
            b.ciphers.append(CipherSpec(cmds["Ciphersuites"], "ssl.openssl.ssl-conf-cmd Ciphersuites", kind="iana"))
        for key in ("Curves", "Groups"):
            if cmds.get(key):
                b.groups.extend((g, f"ssl.openssl.ssl-conf-cmd {key}", None) for g in cmds[key].split(":"))
        ec = merged.get("ssl.ec-curve", ("", ""))[0].strip('"')
        if ec:
            b.groups.append((ec, "ssl.ec-curve", None))
        b.dhparam_directive = "ssl.dh-file"
        dhf = merged.get("ssl.dh-file", ("", ""))[0].strip('"')
        if dhf:
            b.dhparam_file = dhf
        for key, lst in (("ssl.pemfile", b.certs), ("ssl.ca-file", b.certs), ("ssl.privkey", b.keys)):
            v = merged.get(key, ("", ""))[0].strip('"')
            if v:
                lst.append(v)
        if b.certs and not b.keys:
            b.keys.append(b.certs[0])          # lighttpd: ssl.pemfile holds the key when ssl.privkey is absent
        out.append(b)
    return out


# ---------------------------------------------------------------------------
# Tomcat
# ---------------------------------------------------------------------------

def tomcat_protocols(expr: str) -> List[str]:
    """Tomcat protocols attribute (`TLSv1.2+TLSv1.3`, `all`, `+TLSv1.2 -TLSv1`, `TLSv1,TLSv1.1`)."""
    toks = re.findall(r"([+-]?)([A-Za-z][A-Za-z0-9.]*)", expr)
    parts = []
    for i, (sign, body) in enumerate(toks):
        if body.lower() == "sslv2hello":
            continue
        if i > 0 and not sign and "+" in expr and "," not in expr:
            sign = "+"
        parts.append(sign + body)
    return [p for p in resolve_protocol_expr(" ".join(parts), all_set=TLS_ALL) if p != "SSLv2"]


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1]


def tomcat_blocks(ctx: ScanContext) -> List[Block]:
    files = [f for f in ("/etc/tomcat/server.xml", "/usr/share/tomcat/conf/server.xml") if _exists(ctx, f)]
    files += _glob(ctx, "/etc/tomcat*/server.xml") + _glob(ctx, "/opt/tomcat*/conf/server.xml") + \
        _glob(ctx, "/opt/*/conf/server.xml") + _glob(ctx, "/var/lib/tomcat*/conf/server.xml")
    out: List[Block] = []
    for f in dict.fromkeys(files):
        text = read_text(ctx.path(f))
        if text is None:
            continue
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            b = Block("tomcat", f, "server.xml (unparseable)")
            b.errors.append(f"XML parse error: {e}")
            b.protocols = None
            out.append(b)
            continue
        base = os.path.dirname(os.path.dirname(f))               # CATALINA_BASE (conf/..)
        for conn in (e for e in root.iter() if _local(e.tag) == "Connector"):
            a = {k: v for k, v in conn.attrib.items()}
            hosts = [e for e in conn if _local(e.tag) == "SSLHostConfig"]
            if a.get("SSLEnabled", "").lower() != "true" and a.get("secure", "").lower() != "true" and not hosts:
                continue
            port = a.get("port", "?")
            units = hosts or [None]
            for h in units:
                ha = dict(h.attrib) if h is not None else {}
                label = f"Connector port {port}" + (f" host {ha.get('hostName', '_default_')}" if h is not None else "")
                b = Block("tomcat", f, label, listen=[port], server_names=[ha.get("hostName", "_default_")] if h is not None else [])
                pdir = next((k for k in ("protocols", "sslEnabledProtocols", "SSLProtocol") if (ha if k == "protocols" else a).get(k)), None)
                pexpr = (ha if pdir == "protocols" else a).get(pdir) if pdir else None
                if pexpr:
                    b.protocols, b.proto_directive = tomcat_protocols(pexpr), pdir
                else:
                    b.protocols, b.proto_directive, b.proto_source = ["TLSv1.2", "TLSv1.3"], "protocols (default)", "default"
                if a.get("sslProtocol"):
                    b.attrs["sslProtocol"] = a["sslProtocol"]
                ciphers = ha.get("ciphers") or a.get("ciphers") or a.get("SSLCipherSuite")
                if ciphers:
                    b.ciphers.append(CipherSpec(ciphers, "ciphers", kind="openssl" if _is_openssl_spec(ciphers) else "iana"))
                hco = ha.get("honorCipherOrder") or a.get("honorCipherOrder") or a.get("useServerCipherSuitesOrder")
                if hco:
                    b.attrs["honor_cipher_order"] = hco.lower() == "true"
                certs = [c for c in h if _local(c.tag) == "Certificate"] if h is not None else []
                srcs = [dict(c.attrib) for c in certs] or [a]
                for ca in srcs:
                    ks = ca.get("certificateKeystoreFile") or ca.get("keystoreFile")
                    if ks:
                        b.attrs.setdefault("keystores", []).append(ks)
                        b.attrs["keystore_type"] = ca.get("certificateKeystoreType") or ca.get("keystoreType") or "JKS"
                    for k in ("certificateFile", "SSLCertificateFile", "certificateChainFile", "SSLCertificateChainFile"):
                        if ca.get(k):
                            b.certs.append(_resolve(base, ca[k].replace("${catalina.base}", base)))
                    for k in ("certificateKeyFile", "SSLCertificateKeyFile"):
                        if ca.get(k):
                            b.keys.append(_resolve(base, ca[k].replace("${catalina.base}", base)))
                b.dhe_check = bool(ciphers)
                b.dhparam_directive = "jdk.tls.ephemeralDHKeySize / SSLHostConfig"
                out.append(b)
    return out


# ---------------------------------------------------------------------------
# Spring Boot
# ---------------------------------------------------------------------------

def spring_blocks(ctx: ScanContext) -> List[Block]:
    pats = list(ctx.opt("spring_config_paths", []) or [])
    for base in ("/etc/*", "/opt/*", "/opt/*/config", "/srv/*", "/srv/*/config", "/usr/local/*/config"):
        for ext in ("properties", "yml", "yaml"):
            pats.append(f"{base}/application.{ext}")
            pats.append(f"{base}/application-*.{ext}")
    out: List[Block] = []
    seen = set()
    for pat in pats:
        for f in _glob(ctx, pat):
            if f in seen:
                continue
            seen.add(f)
            text = read_text(ctx.path(f)) or ""
            props: Dict[str, List[str]] = {}
            if f.endswith(".properties"):
                for line in text.splitlines():
                    m = re.match(r"^\s*(server\.ssl\.[A-Za-z0-9.\-\[\]]+)\s*[=:]\s*(.*)$", line)
                    if m:
                        key = re.sub(r"\[\d+\]$", "", m.group(1))
                        props.setdefault(key, []).extend(x.strip() for x in m.group(2).split(",") if x.strip())
            else:
                for path, v in _yaml_flatten(text):
                    if path[:2] == ("server", "ssl") and len(path) > 2:
                        props.setdefault("server.ssl." + ".".join(path[2:]), []).extend(x.strip() for x in v.split(",") if x.strip())
            if not props:
                continue
            if (props.get("server.ssl.enabled") or ["true"])[0].lower() == "false":
                continue
            b = Block("spring-boot", f, "server.ssl")
            protos = props.get("server.ssl.enabled-protocols")
            if protos:
                b.protocols = [p for p in (normalize_proto(x) for x in protos) if p]
                b.proto_directive = "server.ssl.enabled-protocols"
            else:
                b.attrs["protocols_default"] = "JSSE runtime default"
            if props.get("server.ssl.protocol"):
                b.attrs["sslProtocol"] = props["server.ssl.protocol"][0]
            if props.get("server.ssl.ciphers"):
                spec = ",".join(props["server.ssl.ciphers"])
                b.ciphers.append(CipherSpec(spec, "server.ssl.ciphers", kind="openssl" if _is_openssl_spec(spec) else "iana"))
            b.dhe_check = False
            for k in ("server.ssl.key-store", "server.ssl.trust-store"):
                if props.get(k):
                    b.attrs.setdefault("keystores", []).append(props[k][0])
            for k in ("server.ssl.certificate", "server.ssl.certificate-chain"):
                if props.get(k) and props[k][0].startswith(("/", "file:")):
                    b.certs.append(props[k][0].replace("file:", "", 1))
            if props.get("server.ssl.certificate-private-key") and props["server.ssl.certificate-private-key"][0].startswith(("/", "file:")):
                b.keys.append(props["server.ssl.certificate-private-key"][0].replace("file:", "", 1))
            out.append(b)
    return out


# ---------------------------------------------------------------------------
# Traefik
# ---------------------------------------------------------------------------

def _toml_flatten(text: str) -> List[Tuple[Tuple[str, ...], str]]:
    """Tolerant TOML scanner: [table] / [[array-table]] headers, key = value, multi-line arrays."""
    out: List[Tuple[Tuple[str, ...], str]] = []
    table: Tuple[str, ...] = ()
    pending: Optional[Tuple[Tuple[str, ...], str]] = None
    for raw in text.splitlines():
        s = raw.split("#", 1)[0].strip() if not raw.strip().startswith("#") else ""
        if not s:
            continue
        if pending:
            path, buf = pending
            buf += " " + s
            if "]" in s:
                out.extend((path, v) for v in _yaml_values(buf))
                pending = None
            else:
                pending = (path, buf)
            continue
        m = re.match(r"^\[\[?\s*([^\]]+?)\s*\]\]?$", s)
        if m:
            table = tuple(p.strip().strip('"') for p in m.group(1).split("."))
            continue
        m = re.match(r"^([A-Za-z0-9_.\"-]+)\s*=\s*(.*)$", s)
        if m:
            path = table + tuple(p.strip('"') for p in m.group(1).split("."))
            val = m.group(2).strip()
            if val.startswith("[") and "]" not in val:
                pending = (path, val)
                continue
            out.extend((path, v) for v in _yaml_values(val))
    return out


def traefik_blocks(ctx: ScanContext) -> List[Block]:
    files = [f for f in ("/etc/traefik/traefik.yml", "/etc/traefik/traefik.yaml", "/etc/traefik/traefik.toml") if _exists(ctx, f)]
    for d in ("/etc/traefik/dynamic", "/etc/traefik/conf.d", "/etc/traefik/conf", "/etc/traefik/rules"):
        for ext in ("yml", "yaml", "toml"):
            files += _glob(ctx, f"{d}/*.{ext}")
    out: List[Block] = []
    for f in dict.fromkeys(files):
        text = read_text(ctx.path(f)) or ""
        flat = _toml_flatten(text) if f.endswith(".toml") else _yaml_flatten(text)
        opts: Dict[str, Dict[str, List[str]]] = {}
        certs: List[str] = []
        keys: List[str] = []
        for path, v in flat:
            if len(path) >= 4 and path[0] == "tls" and path[1] == "options":
                opts.setdefault(path[2], {}).setdefault(path[3], []).append(v)
            elif len(path) >= 2 and path[0] == "tls" and path[-1] == "certFile":
                certs.append(v)
            elif len(path) >= 2 and path[0] == "tls" and path[-1] == "keyFile":
                keys.append(v)
        if certs and "default" not in opts:
            opts["default"] = {}
        for name, o in opts.items():
            b = Block("traefik", f, f"tls.options.{name}")
            lo = normalize_proto((o.get("minVersion") or [""])[0])
            hi = normalize_proto((o.get("maxVersion") or [""])[0])
            if lo or hi:
                b.protocols, b.proto_directive = _proto_min(lo or "TLSv1", hi), "minVersion/maxVersion"
            else:
                b.protocols, b.proto_directive, b.proto_source = ["TLSv1.2", "TLSv1.3"], "minVersion (default VersionTLS12)", "default"
            if o.get("cipherSuites"):
                b.ciphers.append(CipherSpec(",".join(o["cipherSuites"]), "cipherSuites", kind="iana"))
            for g in o.get("curvePreferences", []):
                b.groups.append((g, "curvePreferences", None))
            b.dhe_check = False
            if name == "default":
                b.certs.extend(certs)
                b.keys.extend(keys)
            out.append(b)
    return out


# ---------------------------------------------------------------------------
# Envoy
# ---------------------------------------------------------------------------

_ENVOY_PROTO = {"TLSv1_0": "TLSv1", "TLSv1_1": "TLSv1.1", "TLSv1_2": "TLSv1.2", "TLSv1_3": "TLSv1.3"}


def envoy_blocks(ctx: ScanContext) -> List[Block]:
    files = [f for f in ("/etc/envoy/envoy.yaml", "/etc/envoy/envoy.yml") if _exists(ctx, f)] + _glob(ctx, "/etc/envoy/*.yaml")
    out: List[Block] = []
    for f in dict.fromkeys(files):
        text = read_text(ctx.path(f)) or ""
        lines = text.splitlines()
        i = 0
        while i < len(lines):
            m = re.match(r"^(\s*)(?:-\s+)?tls_params:\s*$", lines[i])
            if not m:
                i += 1
                continue
            indent = len(m.group(1))
            body = []
            j = i + 1
            while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indent):
                body.append(lines[j])
                j += 1
            flat = _yaml_flatten("\n".join(body))
            b = Block("envoy", f, f"tls_params (line {i + 1})")
            lo = _ENVOY_PROTO.get((_yaml_get(flat, "tls_minimum_protocol_version") or [""])[0])
            hi = _ENVOY_PROTO.get((_yaml_get(flat, "tls_maximum_protocol_version") or [""])[0])
            if lo or hi:
                b.protocols, b.proto_directive = _proto_min(lo or "TLSv1.2", hi), "tls_minimum_protocol_version"
            else:
                b.protocols, b.proto_directive, b.proto_source = ["TLSv1.2", "TLSv1.3"], "tls_params (default)", "default"
            suites = _yaml_get(flat, "cipher_suites")
            if suites:
                names_ = [x for s in suites for x in re.split(r"[|\[\]]", s) if x.strip()]
                b.ciphers.append(CipherSpec(",".join(names_), "cipher_suites", kind="iana"))
            for g in _yaml_get(flat, "ecdh_curves"):
                b.groups.append((g, "ecdh_curves", None))
            b.dhe_check = False
            out.append(b)
            i = j
    return out


# ---------------------------------------------------------------------------
# Kubernetes components, kubelet, etcd
# ---------------------------------------------------------------------------

_K8S_FLAG = re.compile(r"--(tls-min-version|tls-cipher-suites|cipher-suites|tls-cert-file|tls-private-key-file|cert-file|key-file)"
                       r"(?:=|\s+)[\"']?([^\s\"']+)")


def _k8s_block(software: str, f: str, label: str, flags: Dict[str, List[str]]) -> Optional[Block]:
    if not any(k in flags for k in ("tls-min-version", "tls-cipher-suites", "cipher-suites")):
        return None
    b = Block(software, f, label)
    mv = (flags.get("tls-min-version") or [""])[0]
    if mv and normalize_proto(mv):
        b.protocols, b.proto_directive = _proto_min(normalize_proto(mv)), "--tls-min-version"
    else:
        b.attrs["protocols_default"] = "Go crypto/tls runtime default"
    for k in ("tls-cipher-suites", "cipher-suites"):
        for v in flags.get(k, []):
            b.ciphers.append(CipherSpec(v, f"--{k}", kind="iana"))
    b.dhe_check = False
    for k in ("tls-cert-file", "cert-file"):
        b.certs.extend(v for v in flags.get(k, []) if v.startswith("/"))
    for k in ("tls-private-key-file", "key-file"):
        b.keys.extend(v for v in flags.get(k, []) if v.startswith("/"))
    return b


def _flags(text: str) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for m in _K8S_FLAG.finditer(text):
        out.setdefault(m.group(1), []).append(m.group(2).rstrip(",\\"))
    return out


def kubernetes_blocks(ctx: ScanContext) -> List[Block]:
    out: List[Block] = []
    for f in _glob(ctx, "/etc/kubernetes/manifests/*.yaml") + _glob(ctx, "/etc/kubernetes/manifests/*.yml") + \
            _glob(ctx, "/etc/kubernetes/manifests/*.json"):
        text = read_text(ctx.path(f)) or ""
        comp = os.path.splitext(os.path.basename(f))[0]
        b = _k8s_block("etcd" if comp.startswith("etcd") else "kubernetes", f, comp, _flags(text))
        if b:
            out.append(b)
    for f in ("/var/lib/kubelet/config.yaml", "/etc/kubernetes/kubelet/config.yaml", "/etc/kubernetes/kubelet-config.yaml",
              "/etc/kubernetes/kubelet.conf.yaml"):
        if not _exists(ctx, f):
            continue
        flat = _yaml_flatten(read_text(ctx.path(f)) or "")
        mv = _yaml_get(flat, "tlsMinVersion")
        cs = _yaml_get(flat, "tlsCipherSuites")
        flags = {}
        if mv:
            flags["tls-min-version"] = mv[:1]
        if cs:
            flags["tls-cipher-suites"] = [",".join(cs)]
        flags["tls-cert-file"] = _yaml_get(flat, "tlsCertFile")[:1]
        flags["tls-private-key-file"] = _yaml_get(flat, "tlsPrivateKeyFile")[:1]
        b = _k8s_block("kubelet", f, "KubeletConfiguration", flags)
        if b:
            out.append(b)
    units = _glob(ctx, "/etc/systemd/system/**/*.conf") + _glob(ctx, "/etc/systemd/system/*.service") + \
        [f for f in ("/etc/default/kubelet", "/etc/sysconfig/kubelet") if _exists(ctx, f)]
    for f in dict.fromkeys(units):
        text = read_text(ctx.path(f)) or ""
        flags = _flags(text)
        name = os.path.basename(os.path.dirname(f)) if f.endswith(".conf") else os.path.basename(f)
        b = _k8s_block("etcd" if "etcd" in f else "kubernetes" if "kube" in f else "systemd-unit", f, name, flags)
        if b:
            out.append(b)
    for f in ("/etc/etcd/etcd.conf", "/etc/etcd/etcd.conf.yml", "/etc/etcd/etcd.yaml"):
        if not _exists(ctx, f):
            continue
        text = read_text(ctx.path(f)) or ""
        flags: Dict[str, List[str]] = {}
        for key, flag in (("CIPHER_SUITES", "cipher-suites"), ("TLS_MIN_VERSION", "tls-min-version"),
                          ("CERT_FILE", "cert-file"), ("KEY_FILE", "key-file")):
            m = re.search(rf"^\s*ETCD_{key}\s*=\s*\"?([^\"\n]+)", text, re.M) or \
                re.search(rf"^\s*{flag}:\s*\"?([^\"\n]+)", text, re.M)
            if m:
                flags[flag] = [m.group(1).strip().strip("'\"[]")]
        b = _k8s_block("etcd", f, "etcd", flags)
        if b:
            out.append(b)
    return out


# ---------------------------------------------------------------------------
# collector
# ---------------------------------------------------------------------------

PARSERS = (("nginx", nginx_blocks), ("apache", apache_blocks), ("haproxy", haproxy_blocks), ("postfix", postfix_blocks),
           ("dovecot", dovecot_blocks), ("exim", exim_blocks), ("lighttpd", lighttpd_blocks), ("tomcat", tomcat_blocks),
           ("spring-boot", spring_blocks), ("traefik", traefik_blocks), ("envoy", envoy_blocks),
           ("kubernetes", kubernetes_blocks))


@register
class WebServersCollector(Collector):
    name = "web_servers"
    description = ("Local TLS server configuration: nginx, Apache, HAProxy, Postfix, Dovecot, Exim, lighttpd, Tomcat, "
                   "Spring Boot, Traefik, Envoy, Kubernetes/etcd (protocols, cipher strings, DH groups, certificates, keys)")
    needs_network = False

    def collect(self, ctx: ScanContext) -> List[Asset]:
        em = _Emitter(ctx, self.name)
        only = ctx.opt("web_servers_only")
        for name, fn in PARSERS:
            if only and name not in str(only).split(","):
                continue
            try:
                blocks = fn(ctx)
            except Exception as e:      # one broken parser must not hide the others
                ctx.warn(f"web_servers: {name} parser failed: {type(e).__name__}: {e}")
                continue
            for b in blocks:
                try:
                    em.emit(b)
                except Exception as e:
                    ctx.warn(f"web_servers: {name} {b.label}: {type(e).__name__}: {e}")
        return em.assets


__all__ = ["WebServersCollector", "Block", "CipherSpec", "parse_postfix_main", "parse_postfix_protocols", "tomcat_protocols",
           "nginx_blocks", "apache_blocks", "haproxy_blocks", "postfix_blocks", "dovecot_blocks", "exim_blocks",
           "lighttpd_blocks", "tomcat_blocks", "spring_blocks", "traefik_blocks", "envoy_blocks", "kubernetes_blocks",
           "POSTFIX_GRADES", "live_version"]
