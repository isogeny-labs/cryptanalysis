"""IPsec / VPN collector: strongSwan, libreswan, racoon, OpenVPN, WireGuard, PPTP, L2TP.

* strongSwan / libreswan ``ipsec.conf`` (+ ``include``, ``ipsec.d/*.conf``): one
  IPSEC_CONFIG asset per ``conn``.  ``keyexchange=ikev1`` / ``ikev2=never`` ->
  PROTOCOL ``ikev1`` (``aggressive=yes``/``aggrmode=yes`` -> ``ikev1-aggressive``);
  ``ike=`` / ``esp=`` / ``ah=`` proposal strings such as
  ``aes128-sha1-modp1024,3des-md5-modp768!`` become CIPHER, MAC and KEY_EXCHANGE
  uses (context ``ike-proposal`` / ``esp-proposal`` / ``ah-proposal``).
* strongSwan ``swanctl.conf`` (+ ``conf.d``): ``version``, ``proposals``,
  ``esp_proposals``.
* racoon ``racoon.conf``: IKEv1 only; ``remote`` / ``sainfo`` blocks.
* OpenVPN ``/etc/openvpn/**/*.conf|*.ovpn`` -> VPN_CONFIG; inline ``<ca>`` /
  ``<cert>`` blocks become CERTIFICATE assets, ``dh`` files are measured.
* WireGuard ``/etc/wireguard/*.conf`` -> Curve25519 key exchange; keys are never
  recorded, only whether a PresharedKey exists.
* PPTP and L2TP/IPsec-PSK -> PROTOCOL ``pptp`` / ``l2tp-ipsec-psk``.

Collectors do not grade; PSK secrets and private keys are never read into
assets.
"""

from __future__ import annotations

import os
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .. import names, util, x509
from ..model import Asset, AssetKind, CryptoUse, Primitive
from . import register
from ._confparse import blocks, ctx_glob, file_attrs, first, is_root_host, logical, parse_braces, real, strip_quotes, values
from .base import Collector, ScanContext

# IKE transform id -> (algorithm, key_bits, curve)
IKE_DH_GROUPS: Dict[int, Tuple[str, int, Optional[str]]] = {
    1: ("dh", 768, None), 2: ("dh", 1024, None), 5: ("dh", 1536, None), 14: ("dh", 2048, None), 15: ("dh", 3072, None),
    16: ("dh", 4096, None), 17: ("dh", 6144, None), 18: ("dh", 8192, None), 19: ("ecdh", 256, "p-256"),
    20: ("ecdh", 384, "p-384"), 21: ("ecdh", 521, "p-521"), 22: ("dh", 1024, None), 23: ("dh", 2048, None),
    24: ("dh", 2048, None), 25: ("ecdh", 192, "p-192"), 26: ("ecdh", 224, "p-224"), 27: ("ecdh", 224, "brainpoolp224r1"),
    28: ("ecdh", 256, "brainpoolp256r1"), 29: ("ecdh", 384, "brainpoolp384r1"), 30: ("ecdh", 512, "brainpoolp512r1"),
    31: ("ecdh", 256, "curve25519"), 32: ("ecdh", 448, "curve448"),
}
_BP = {224: "brainpoolp224r1", 256: "brainpoolp256r1", 384: "brainpoolp384r1", 512: "brainpoolp512r1"}


# ---------------------------------------------------------------------------
# Proposal token -> CryptoUse (shared by strongSwan, libreswan, swanctl, racoon)
# ---------------------------------------------------------------------------

def dh_use(token: str, context: str) -> Optional[CryptoUse]:
    t = token.lower().replace("_", "")
    m = re.fullmatch(r"modp(\d+)(?:s\d+)?", t)
    if m:
        extra = {"subgroup": True} if "s" in t[4:] else {}
        return CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=int(m.group(1)), raw=token, context=context, extra=extra)
    m = re.fullmatch(r"ecp(\d+)bp", t)
    if m:
        bits = int(m.group(1))
        return CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=bits, curve=_BP.get(bits, f"brainpoolp{bits}r1"),
                         raw=token, context=context)
    m = re.fullmatch(r"ecp(\d+)", t)
    if m:
        bits = int(m.group(1))
        return CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=bits, curve=f"p-{bits}", raw=token, context=context)
    if t in ("curve25519", "x25519"):
        return CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=256, curve="curve25519", raw=token, context=context)
    if t in ("curve448", "x448"):
        return CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=448, curve="curve448", raw=token, context=context)
    m = re.fullmatch(r"(?:mlkem|kyber)(\d+)", t)
    if m:
        return CryptoUse(Primitive.KEY_EXCHANGE, "ml-kem", key_bits=int(m.group(1)), raw=token, context=context)
    m = re.fullmatch(r"dh(\d+)", t)
    if m and int(m.group(1)) in IKE_DH_GROUPS:
        alg, bits, curve = IKE_DH_GROUPS[int(m.group(1))]
        return CryptoUse(Primitive.KEY_EXCHANGE, alg, key_bits=bits, curve=curve, raw=token, context=context)
    return None


def cipher_use(token: str, context: str) -> Optional[CryptoUse]:
    t = token.lower().replace("_", "")
    kw = dict(raw=token, context=context)
    if t == "null":
        return CryptoUse(Primitive.CIPHER, "null", **kw)
    m = re.fullmatch(r"aes(\d{3})?(cbc|ctr|gcm|ccm)?(\d+)?", t)
    if m and (m.group(1) or m.group(2) or t == "aes"):
        bits = int(m.group(1)) if m.group(1) else None
        mode = m.group(2) or "cbc"
        extra = {}
        if mode in ("gcm", "ccm") and bits is None and m.group(3) in ("128", "192", "256"):
            bits = int(m.group(3))                      # libreswan aes_gcm256 spelling
        elif mode in ("gcm", "ccm") and m.group(3):
            icv = int(m.group(3))
            icv = icv * 8 if icv <= 16 else icv
            extra["icv_bits"] = icv
            if mode == "ccm" and icv == 64:
                mode = "ccm-8"
        return CryptoUse(Primitive.CIPHER, "aes", key_bits=bits, mode=mode, extra=extra, **kw)
    m = re.fullmatch(r"aesgcmc?(\d{3})?", t)                  # libreswan aes_gcm_c-256 style
    if m:
        return CryptoUse(Primitive.CIPHER, "aes", key_bits=int(m.group(1)) if m.group(1) else None, mode="gcm", **kw)
    if t in ("3des", "des3", "3desede"):
        return CryptoUse(Primitive.CIPHER, "3des", key_bits=168, mode="cbc", **kw)
    if t == "des":
        return CryptoUse(Primitive.CIPHER, "des", key_bits=56, mode="cbc", **kw)
    m = re.fullmatch(r"blowfish(\d+)?", t)
    if m:
        return CryptoUse(Primitive.CIPHER, "blowfish", key_bits=int(m.group(1) or 128), mode="cbc", **kw)
    m = re.fullmatch(r"camellia(\d{3})?(ctr|cbc)?", t)
    if m:
        return CryptoUse(Primitive.CIPHER, "camellia", key_bits=int(m.group(1)) if m.group(1) else None,
                         mode=m.group(2) or "cbc", **kw)
    if t in ("chacha20poly1305", "chacha20"):
        return CryptoUse(Primitive.CIPHER, "chacha20-poly1305", key_bits=256, mode="aead", **kw)
    m = re.fullmatch(r"(cast|cast128)", t)
    if m:
        return CryptoUse(Primitive.CIPHER, "cast5", key_bits=128, mode="cbc", **kw)
    m = re.fullmatch(r"(twofish|serpent)(\d+)?", t)
    if m:
        return CryptoUse(Primitive.CIPHER, m.group(1), key_bits=int(m.group(2) or 128), mode="cbc", **kw)
    return None


_HASHES = {"sha2": "sha256", "sha1": "sha1", "sha1160": "sha1", "md5": "md5", "md5128": "md5", "sha256": "sha256", "sha2256": "sha256",
           "sha256128": "sha256", "sha2256128": "sha256", "sha384": "sha384", "sha2384": "sha384", "sha384192": "sha384",
           "sha2384192": "sha384", "sha512": "sha512", "sha2512": "sha512", "sha512256": "sha512", "sha2512256": "sha512"}


def mac_use(token: str, context: str, prf: bool = False) -> Optional[CryptoUse]:
    t = token.lower().replace("_", "")
    if t.startswith("hmac"):
        t = t[4:]
    if prf and t.startswith("prf"):
        t = t[3:]
    extra = {"prf": True} if prf else {}
    m = re.fullmatch(r"(sha1|md5|sha256|sha2256)(96)", t)
    if m and not prf:
        return CryptoUse(Primitive.MAC, "hmac", hash_algorithm=_HASHES[m.group(1)], key_bits=96,
                         extra={"truncated": True}, raw=token, context=context)
    if t in _HASHES:
        return CryptoUse(Primitive.MAC, "hmac", hash_algorithm=_HASHES[t], raw=token, context=context, extra=extra)
    if t in ("aesxcbc", "aescmac") and not prf:
        return CryptoUse(Primitive.MAC, "aes-xcbc" if t == "aesxcbc" else "aes-cmac", raw=token, context=context)
    if prf and t in ("aesxcbc", "aescmac"):
        return CryptoUse(Primitive.MAC, "aes-xcbc" if t == "aesxcbc" else "aes-cmac", raw=token, context=context, extra=extra)
    return None


def parse_proposals(value: str, context: str) -> Tuple[List[CryptoUse], List[str]]:
    """'aes128-sha1-modp1024,3des-md5-modp768!' -> (uses, unparsed tokens)."""
    uses: List[CryptoUse] = []
    unparsed: List[str] = []
    for prop in re.split(r"[,\s]+", value.strip().rstrip("!")):
        prop = prop.strip().rstrip("!")
        if not prop or prop.lower() == "default":
            continue
        toks = [t for t in re.split(r"[-;]", prop) if t]
        for tok in toks:
            low = tok.lower()
            if low in ("none", "noke", "default") or re.fullmatch(r"\d+", low):
                continue
            u = None
            if low.startswith("prf"):
                u = mac_use(tok, context, prf=True)
            if u is None:
                u = dh_use(tok, context) or cipher_use(tok, context) or mac_use(tok, context)
            if u is None:
                unparsed.append(tok)
                continue
            uses.append(u)
    return uses, unparsed


def _add_unique(asset: Asset, uses: Iterable[CryptoUse]) -> None:
    seen = {(u.primitive, u.algorithm, u.key_bits, u.curve, u.hash_algorithm, u.mode, u.raw, u.context) for u in asset.uses}
    for u in uses:
        key = (u.primitive, u.algorithm, u.key_bits, u.curve, u.hash_algorithm, u.mode, u.raw, u.context)
        if key not in seen:
            seen.add(key)
            asset.add(u)


# ---------------------------------------------------------------------------
# ipsec.conf (strongSwan / libreswan)
# ---------------------------------------------------------------------------

def parse_ipsec_conf(text: str) -> Tuple[List[Tuple[str, str, Dict[str, str]]], List[str]]:
    """-> ([(section kind, name, {lower-key: value})], include patterns)."""
    sections: List[Tuple[str, str, Dict[str, str]]] = []
    includes: List[str] = []
    cur: Optional[Dict[str, str]] = None
    for raw in text.splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).rstrip()
        if not line.strip():
            continue
        if not raw[:1].isspace():
            parts = line.split(None, 1)
            head = parts[0].lower()
            if head == "include" and len(parts) == 2:
                includes.append(parts[1].strip())
                cur = None
            elif head in ("conn", "config", "ca") and len(parts) == 2:
                cur = {}
                sections.append((head, parts[1].strip(), cur))
            else:
                cur = None
            continue
        if cur is not None and "=" in line:
            k, v = line.strip().split("=", 1)
            cur[k.strip().lower()] = strip_quotes(v.strip())
    return sections, includes


def _truthy(v: Optional[str]) -> bool:
    return (v or "").strip().lower() in ("yes", "true", "1", "on", "insist")


def _auth_uses(authby: str) -> List[CryptoUse]:
    out = []
    for tok in re.split(r"[,\s]+", authby.strip()):
        m = re.fullmatch(r"(rsa|ecdsa)-sha1", tok.lower().replace("_", ""))
        if m:
            out.append(CryptoUse(Primitive.SIGNATURE, m.group(1), hash_algorithm="sha1", raw=tok, context="ike-auth"))
    return out


# ---------------------------------------------------------------------------
# racoon.conf
# ---------------------------------------------------------------------------

def parse_racoon(text: str) -> List[Tuple[List[str], list]]:
    """racoon.conf -> [(header tokens, children)] where a child is ('stmt', tokens) or ('block', header, children)."""
    text = re.sub(r"#.*", "", text)
    toks = re.findall(r"[^\s{};]+|[{};]", text)

    def block(i: int) -> Tuple[list, int]:
        items: list = []
        stmt: List[str] = []
        while i < len(toks):
            t = toks[i]
            if t == ";":
                if stmt:
                    items.append(("stmt", stmt))
                stmt = []
            elif t == "{":
                sub, i = block(i + 1)
                items.append(("block", stmt, sub))
                stmt = []
                continue
            elif t == "}":
                return items, i + 1
            else:
                stmt.append(t)
            i += 1
        return items, i

    items, _ = block(0)
    return [(it[1], it[2]) for it in items if it[0] == "block"]


# ---------------------------------------------------------------------------
# OpenVPN
# ---------------------------------------------------------------------------

_OVPN_CURVES = {"secp384r1": ("p-384", 384), "prime256v1": ("p-256", 256), "secp256r1": ("p-256", 256),
                "secp521r1": ("p-521", 521), "x25519": ("curve25519", 256), "x448": ("curve448", 448)}
_TLS_ALIASES = {"DEFAULT", "ALL", "HIGH", "MEDIUM", "LOW", "NULL", "ENULL", "ANULL", "EXPORT", "EXP", "COMPLEMENTOFDEFAULT",
                "COMPLEMENTOFALL", "FIPS"}


def openvpn_cipher(name: str, context: str) -> CryptoUse:
    n = name.strip().upper()
    kw = dict(raw=name, context=context)
    if n == "NONE":
        return CryptoUse(Primitive.CIPHER, "null", **kw)
    if n == "CHACHA20-POLY1305":
        return CryptoUse(Primitive.CIPHER, "chacha20-poly1305", key_bits=256, mode="aead", **kw)
    m = re.fullmatch(r"(AES|CAMELLIA|ARIA)-(\d{3})-([A-Z0-9]+)", n)
    if m:
        return CryptoUse(Primitive.CIPHER, m.group(1).lower(), key_bits=int(m.group(2)), mode=m.group(3).lower(), **kw)
    m = re.fullmatch(r"BF(?:-([A-Z0-9]+))?", n)
    if m:
        return CryptoUse(Primitive.CIPHER, "blowfish", key_bits=128, mode=(m.group(1) or "cbc").lower(), **kw)
    m = re.fullmatch(r"DES-EDE3(?:-([A-Z0-9]+))?", n)
    if m:
        return CryptoUse(Primitive.CIPHER, "3des", key_bits=168, mode=(m.group(1) or "cbc").lower(), **kw)
    m = re.fullmatch(r"DES-EDE(?:-([A-Z0-9]+))?", n)
    if m:
        return CryptoUse(Primitive.CIPHER, "3des", key_bits=112, mode=(m.group(1) or "ecb").lower(), **kw)
    m = re.fullmatch(r"(DESX|DES)(?:-([A-Z0-9]+))?", n)
    if m:
        return CryptoUse(Primitive.CIPHER, "des", key_bits=56, mode=(m.group(2) or "cbc").lower(), **kw)
    m = re.fullmatch(r"(CAST5|RC2|IDEA|SEED)(?:-([A-Z0-9]+))?", n)
    if m:
        alg = m.group(1).lower()
        return CryptoUse(Primitive.CIPHER, alg, key_bits=128, mode=(m.group(2) or "cbc").lower(), **kw)
    if n.startswith("RC4"):
        return CryptoUse(Primitive.CIPHER, "rc4", key_bits=128, **kw)
    return CryptoUse(Primitive.CIPHER, n.lower(), **kw)


def _is_aead(u: CryptoUse) -> bool:
    return u.mode in ("gcm", "ccm", "aead")


def parse_openvpn(text: str) -> Tuple[Dict[str, List[List[str]]], Dict[str, str]]:
    """-> ({directive: [args...]} (all occurrences), {inline block name: body})."""
    inline: Dict[str, str] = {}

    def grab(m):
        inline[m.group(1).lower()] = m.group(2)
        return ""

    body = re.sub(r"<([A-Za-z][\w-]*)>[ \t]*\r?\n(.*?)</\1>", grab, text, flags=re.S)
    d: Dict[str, List[List[str]]] = {}
    for raw in body.splitlines():
        s = raw.strip()
        if not s or s[0] in "#;":
            continue
        parts = [strip_quotes(p) for p in s.split()]
        d.setdefault(parts[0].lower(), []).append(parts[1:])
    return d, inline


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

@register
class IpsecCollector(Collector):
    name = "ipsec"
    description = "IPsec and VPN configuration: strongSwan, libreswan, racoon, OpenVPN, WireGuard, PPTP, L2TP"

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        self._psk_conns = False
        for step in (self._ipsec_conf, self._swanctl, self._racoon, self._openvpn, self._wireguard, self._pptp, self._l2tp):
            try:
                out.extend(step(ctx))
            except Exception as e:
                ctx.warn(f"ipsec: {step.__name__} failed: {type(e).__name__}: {e}")
        return out

    def _asset(self, ctx: ScanContext, kind: AssetKind, name: str, location: str, path: Optional[str] = None, **attrs) -> Asset:
        a = Asset(kind, name, location, self.name, ctx.hostname, attributes=dict(attrs))
        if path:
            a.attributes.update(file_attrs(path))
        return a

    # -- ipsec.conf -----------------------------------------------------------

    def _ipsec_files(self, ctx: ScanContext) -> List[str]:
        files = [ctx.path("/etc/ipsec.conf")] + [f for f in ctx_glob(ctx, "/etc/ipsec.d/*.conf")]
        return files

    def _ipsec_conf(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        queue = [(p, 0) for p in self._ipsec_files(ctx)]
        seen: Set[str] = set()
        sections: List[Tuple[str, str, Dict[str, str], str]] = []     # + source file
        while queue:
            path, depth = queue.pop(0)
            rp = real(path)
            if rp in seen or not os.path.isfile(path):
                continue
            seen.add(rp)
            text = util.read_text(path)
            if text is None:
                a = self._asset(ctx, AssetKind.IPSEC_CONFIG, f"ipsec config {logical(ctx, path)}", logical(ctx, path), path)
                a.errors.append(f"cannot read {path}")
                out.append(a)
                continue
            secs, incs = parse_ipsec_conf(text)
            sections.extend((k, n, d, path) for k, n, d in secs)
            if depth < 4:
                for inc in incs:
                    pat = inc if inc.startswith("/") else os.path.join(os.path.dirname(logical(ctx, path)), inc)
                    queue.extend((f, depth + 1) for f in ctx_glob(ctx, pat))
        defaults: Dict[str, str] = {}
        conns: Dict[str, Dict[str, str]] = {}
        for kind, name, d, _ in sections:
            if kind == "conn":
                if name == "%default":
                    defaults.update(d)
                else:
                    conns.setdefault(name, {}).update(d)
        for kind, name, d, path in sections:
            if kind != "conn" or name == "%default":
                continue
            merged = dict(defaults)
            for also in re.split(r"\s+", d.get("also", "").strip()):
                if also and also in conns:
                    merged.update(conns[also])
            merged.update(d)
            out.append(self._conn_asset(ctx, name, merged, path))
        return out

    def _conn_asset(self, ctx: ScanContext, name: str, c: Dict[str, str], path: str) -> Asset:
        a = self._asset(ctx, AssetKind.IPSEC_CONFIG, f"ipsec conn {name}", logical(ctx, path), path, conn=name,
                        implementation="ipsec.conf")
        kx = c.get("keyexchange", "").lower()
        ikev2 = c.get("ikev2", "").lower()
        aggressive = _truthy(c.get("aggressive")) or _truthy(c.get("aggrmode"))
        if kx:
            a.attributes["keyexchange"] = kx
        if ikev2:
            a.attributes["ikev2"] = ikev2
        v1_only = kx == "ikev1" or ikev2 in ("never", "no")
        if aggressive:
            a.add(CryptoUse(Primitive.PROTOCOL, "ikev1-aggressive", raw="aggressive=yes", context="ike-version"))
            a.attributes["aggressive"] = True
        elif v1_only:
            a.add(CryptoUse(Primitive.PROTOCOL, "ikev1", raw=f"keyexchange={kx}" if kx else f"ikev2={ikev2}", context="ike-version"))
        unparsed: List[str] = []
        for key, ctxname in (("ike", "ike-proposal"), ("esp", "esp-proposal"), ("ah", "ah-proposal")):
            if key in c:
                uses, bad = parse_proposals(c[key], ctxname)
                _add_unique(a, uses)
                unparsed.extend(bad)
                a.attributes[key] = c[key]
        if unparsed:
            a.attributes["unparsed_tokens"] = sorted(set(unparsed))
        authby = c.get("authby") or c.get("leftauth") or ""
        if authby:
            a.attributes["authby"] = authby
            psk = any(t in ("psk", "secret") for t in re.split(r"[,\s|]+", authby.lower()))
            a.attributes["psk"] = psk
            if psk:
                self._psk_conns = True
            _add_unique(a, _auth_uses(authby))
        for k in ("left", "right", "type", "auto", "leftprotoport", "rightprotoport"):
            if k in c:
                a.attributes[k] = c[k]
        if "17/1701" in (c.get("leftprotoport", "") + c.get("rightprotoport", "")) and a.attributes.get("psk"):
            a.add(CryptoUse(Primitive.PROTOCOL, "l2tp-ipsec-psk", raw="L2TP over IPsec with PSK", context="l2tp"))
        return a

    # -- swanctl.conf ---------------------------------------------------------

    def _swanctl(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        queue = [ctx.path("/etc/swanctl/swanctl.conf")] + ctx_glob(ctx, "/etc/swanctl/conf.d/*.conf")
        seen: Set[str] = set()
        depth = 0
        while queue and depth < 100:
            depth += 1
            path = queue.pop(0)
            rp = real(path)
            if rp in seen or not os.path.isfile(path):
                continue
            seen.add(rp)
            text = util.read_text(path)
            if text is None:
                continue
            tree, incs = parse_braces(text, inline_comments=True, directives=("include",))
            base = os.path.dirname(logical(ctx, path))
            for _, pat in incs:
                queue.extend(ctx_glob(ctx, pat if pat.startswith("/") else os.path.join(base, pat)))
            for _, cb in blocks(tree, "connections"):
                for cname, body in blocks(cb):
                    out.append(self._swan_conn(ctx, cname, body, path))
            for _, sb in blocks(tree, "secrets"):
                for sname, _b in blocks(sb):
                    if sname.lower().startswith("ike"):
                        self._psk_conns = True
        return out

    def _swan_conn(self, ctx: ScanContext, name: str, body, path: str) -> Asset:
        a = self._asset(ctx, AssetKind.IPSEC_CONFIG, f"swanctl connection {name}", logical(ctx, path), path, conn=name,
                        implementation="swanctl")
        version = first(body, "version")
        aggressive = _truthy(first(body, "aggressive"))
        if version:
            a.attributes["version"] = version
        if aggressive:
            a.add(CryptoUse(Primitive.PROTOCOL, "ikev1-aggressive", raw="aggressive = yes", context="ike-version"))
        elif version and version.strip() == "1":
            a.add(CryptoUse(Primitive.PROTOCOL, "ikev1", raw="version = 1", context="ike-version"))
        unparsed: List[str] = []
        for v in values(body, "proposals"):
            uses, bad = parse_proposals(v, "ike-proposal")
            _add_unique(a, uses)
            unparsed += bad
            a.attributes["proposals"] = v
        for _, ch in blocks(body, "children"):
            for chname, chbody in blocks(ch):
                for key, ctxname in (("esp_proposals", "esp-proposal"), ("ah_proposals", "ah-proposal")):
                    for v in values(chbody, key):
                        uses, bad = parse_proposals(v, ctxname)
                        for u in uses:
                            u.extra["child"] = chname
                        _add_unique(a, uses)
                        unparsed += bad
        auths = []
        for side in ("local", "remote"):
            for _, sb in blocks(body, side):
                v = first(sb, "auth")
                if v:
                    auths.append(f"{side}:{v}")
                    if v.lower() == "psk":
                        a.attributes["psk"] = True
                        self._psk_conns = True
        if auths:
            a.attributes["auth"] = auths
        if unparsed:
            a.attributes["unparsed_tokens"] = sorted(set(unparsed))
        return a

    # -- racoon ---------------------------------------------------------------

    def _racoon(self, ctx: ScanContext) -> List[Asset]:
        path = ctx.path("/etc/racoon/racoon.conf")
        if not os.path.isfile(path):
            return []
        text = util.read_text(path)
        if text is None:
            a = self._asset(ctx, AssetKind.IPSEC_CONFIG, "racoon", "/etc/racoon/racoon.conf", path)
            a.errors.append(f"cannot read {path}")
            return [a]
        out = []
        for header, items in parse_racoon(text):
            kind = header[0].lower() if header else ""
            if kind not in ("remote", "sainfo"):
                continue
            label = " ".join(header)
            a = self._asset(ctx, AssetKind.IPSEC_CONFIG, f"racoon {label}", "/etc/racoon/racoon.conf", path, implementation="racoon")
            if kind == "remote":
                a.add(CryptoUse(Primitive.PROTOCOL, "ikev1", raw="racoon (IKEv1 only)", context="ike-version"))
            self._racoon_items(a, items, kind)
            out.append(a)
        return out

    def _racoon_items(self, a: Asset, items: list, kind: str) -> None:
        for it in items:
            if it[0] == "block":
                head = it[1][0].lower() if it[1] else ""
                self._racoon_items(a, it[2], "proposal" if head == "proposal" else kind)
                continue
            toks = it[1]
            if not toks:
                continue
            key, args = toks[0].lower(), toks[1:]
            ctxname = "esp-proposal" if kind == "sainfo" else "ike-proposal"
            if key == "exchange_mode":
                modes = [m.strip().lower() for t in args for m in t.split(",") if m.strip()]
                a.attributes["exchange_mode"] = modes
                if "aggressive" in modes:
                    a.add(CryptoUse(Primitive.PROTOCOL, "ikev1-aggressive", raw="exchange_mode aggressive", context="ike-version"))
            elif key == "encryption_algorithm":
                joined = " ".join(args)
                for part in joined.split(","):
                    w = part.split()
                    if not w:
                        continue
                    name = w[0]
                    if name.lower() in ("aes", "camellia") and len(w) > 1 and w[1].isdigit():
                        name += w[1]
                    u = cipher_use(name, ctxname)
                    if u:
                        _add_unique(a, [u])
            elif key in ("hash_algorithm", "authentication_algorithm"):
                for part in " ".join(args).split(","):
                    w = part.strip()
                    if w and w != "non_auth":
                        u = mac_use(w.replace("hmac_", ""), ctxname)
                        if u:
                            _add_unique(a, [u])
                    elif w == "non_auth":
                        _add_unique(a, [CryptoUse(Primitive.MAC, "null", raw=w, context=ctxname)])
            elif key in ("dh_group", "pfs_group"):
                for w in " ".join(args).replace(",", " ").split():
                    u = dh_use(w, ctxname)
                    if u is None and w.isdigit() and int(w) in IKE_DH_GROUPS:
                        alg, bits, curve = IKE_DH_GROUPS[int(w)]
                        u = CryptoUse(Primitive.KEY_EXCHANGE, alg, key_bits=bits, curve=curve, raw=w, context=ctxname)
                    if u:
                        _add_unique(a, [u])
            elif key == "authentication_method":
                a.attributes["authentication_method"] = " ".join(args)
                if "pre_shared_key" in args or "xauth_psk_server" in args:
                    a.attributes["psk"] = True

    # -- OpenVPN ----------------------------------------------------------------

    def _openvpn_version(self, ctx: ScanContext) -> Optional[Tuple[int, int]]:
        forced = ctx.opt("openvpn_version")
        text = str(forced) if forced else ""
        if not text and is_root_host(ctx) and util.which("openvpn"):
            r = util.run_cmd(["openvpn", "--version"], timeout=ctx.cmd_timeout)
            text = (r.stdout or r.stderr).splitlines()[0] if (r.stdout or r.stderr) else ""
        m = re.search(r"(\d+)\.(\d+)", text)
        return (int(m.group(1)), int(m.group(2))) if m else None

    def _openvpn(self, ctx: ScanContext) -> List[Asset]:
        root = ctx.path("/etc/openvpn")
        if not os.path.isdir(root):
            return []
        files = [f for f in util.walk_files([root], max_files=min(ctx.max_files, 5000), max_depth=6)
                 if f.endswith((".conf", ".ovpn"))]
        version = self._openvpn_version(ctx)
        out: List[Asset] = []
        for path in sorted(files):
            out.extend(self._openvpn_file(ctx, path, version))
        return out

    def _openvpn_file(self, ctx: ScanContext, path: str, version: Optional[Tuple[int, int]]) -> List[Asset]:
        text = util.read_text(path)
        loc = logical(ctx, path)
        a = self._asset(ctx, AssetKind.VPN_CONFIG, f"OpenVPN config {os.path.basename(path)}", loc, path, vpn="openvpn")
        if text is None:
            a.errors.append(f"cannot read {path}")
            return [a]
        d, inline = parse_openvpn(text)
        is_server = "server" in d or "tls-server" in d or ("mode" in d and d["mode"][0][:1] == ["server"])
        is_client = "client" in d or "tls-client" in d or "remote" in d
        role = "server" if is_server else ("client" if is_client else "unknown")
        a.attributes["role"] = role
        if "remote" in d:
            a.attributes["remotes"] = [" ".join(x[:2]) for x in d["remote"]][:10]
        ciphers: List[CryptoUse] = []
        have_cipher = False
        for args in d.get("cipher", []):
            if args:
                have_cipher = True
                ciphers.append(openvpn_cipher(args[0], "cipher"))
        for key in ("data-ciphers", "ncp-ciphers"):
            for args in d.get(key, []):
                if args:
                    have_cipher = True
                    for c in args[0].split(":"):
                        if c:
                            ciphers.append(openvpn_cipher(c, key))
        for args in d.get("data-ciphers-fallback", []):
            if args:
                have_cipher = True
                ciphers.append(openvpn_cipher(args[0], "data-ciphers-fallback"))
        if not have_cipher and version is not None and version < (2, 5):
            u = CryptoUse(Primitive.CIPHER, "blowfish", key_bits=128, mode="cbc", raw="BF-CBC", context="cipher",
                          extra={"source": "default", "openvpn_version": "%d.%d" % version})
            ciphers.append(u)
        elif not have_cipher and version is None:
            a.attributes["default_cipher"] = "unknown (OpenVPN version not detected; BF-CBC before 2.5)"
        _add_unique(a, ciphers)
        for args in d.get("auth", []):
            if not args:
                continue
            v = args[0]
            if v.lower() == "none":
                if not ciphers or not all(_is_aead(c) for c in ciphers):
                    a.add(CryptoUse(Primitive.MAC, "null", raw="auth none", context="auth"))
                continue
            a.add(CryptoUse(Primitive.MAC, "hmac", hash_algorithm=names.hash_name(v), raw=v, context="auth"))
        for key in ("tls-cipher", "tls-ciphersuites"):
            for args in d.get(key, []):
                for tok in (args[0].split(":") if args else []):
                    t = tok.strip()
                    if not t or t[0] in "!-+@" or t.upper() in _TLS_ALIASES or not re.fullmatch(r"[A-Za-z0-9_-]+", t):
                        continue
                    if "-" not in t and "_" not in t:
                        continue
                    if t.upper().startswith("TLS-"):
                        t = t.replace("-", "_")
                    a.add(names.tls_cipher_suite(t, negotiated=False))
                if args:
                    a.attributes[key.replace("-", "_")] = args[0]
        for args in d.get("tls-version-min", []):
            if args:
                u = names.tls_protocol("TLSv" + args[0], negotiated=None)
                u.context = "openvpn-min-protocol"
                a.add(u)
        for args in d.get("tls-version-max", []):
            if args:
                a.attributes["tls_version_max"] = args[0]
        # DH parameters
        dh_bytes: Optional[bytes] = None
        if "dh" in inline:
            dh_bytes = inline["dh"].encode()
        elif d.get("dh") and d["dh"][0]:
            if d["dh"][0][0].lower() == "none":
                a.attributes["dh"] = "none (ECDH)"
            else:
                p = d["dh"][0][0]
                cand = ctx.path(p) if os.path.isabs(p) else os.path.join(os.path.dirname(path), p)
                dh_bytes = util.read_bytes(cand)
                if dh_bytes is None:
                    a.errors.append(f"dh parameter file {p} not readable")
        if dh_bytes:
            for info in x509.parse_key_data(dh_bytes):
                if info.public_key and info.public_key.algorithm == "dh":
                    a.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=info.public_key.key_bits, raw="dh parameters",
                                    context="openvpn-dh"))
                    a.attributes["dh_bits"] = info.public_key.key_bits
        for args in d.get("ecdh-curve", []):
            if args:
                c, bits = _OVPN_CURVES.get(args[0].lower(), (args[0].lower(), None))
                a.add(CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=bits, curve=c, raw=args[0], context="openvpn-ecdh"))
        a.attributes["tls_auth"] = "tls-auth" in d or "tls-auth" in inline
        a.attributes["tls_crypt"] = any(k in d or k in inline for k in ("tls-crypt", "tls-crypt-v2"))
        if "key-direction" in d and d["key-direction"][0]:
            a.attributes["key_direction"] = d["key-direction"][0][0]
        comp = [k for k in ("comp-lzo", "compress") if k in d]
        if comp:
            a.attributes["compression"] = comp
            a.attributes["compression_note"] = "compression enables VORACLE-style compression-oracle attacks; prefer none"
        for k in ("ns-cert-type", "remote-cert-tls", "proto", "port", "verify-x509-name"):
            if k in d and d[k]:
                a.attributes[k.replace("-", "_")] = " ".join(d[k][0])
        out = [a]
        for block, anchor in (("ca", True), ("cert", False), ("extra-certs", False)):
            if block not in inline:
                continue
            for cert in x509.load_certificates(inline[block].encode()):
                out.append(self._cert_asset(ctx, cert, f"{loc}#<{block}>", os.path.basename(path), anchor, path))
        return out

    def _cert_asset(self, ctx: ScanContext, cert, location: str, fname: str, anchor: bool, path: str) -> Asset:
        is_anchor = anchor and (cert.is_ca or cert.self_signed)
        kind = AssetKind.CA_CERTIFICATE if is_anchor else AssetKind.CERTIFICATE
        a = Asset(kind, f"{fname} inline cert {cert.subject}", location, self.name, ctx.hostname)
        a.attributes.update(cert.summary())
        a.attributes["serial_bits"] = cert.serial.bit_length()
        a.attributes["trust_anchor"] = bool(is_anchor)
        a.attributes.update(file_attrs(path))
        pk = cert.public_key
        a.add(CryptoUse(Primitive.PUBLIC_KEY, pk.algorithm, key_bits=pk.key_bits, curve=pk.curve, context="public-key",
                        extra={"rsa_exponent": pk.rsa_exponent} if pk.rsa_exponent else {}))
        a.add(CryptoUse(Primitive.SIGNATURE, cert.signature_algorithm, hash_algorithm=cert.signature_hash,
                        context="certificate-signature"))
        return a

    # -- WireGuard ----------------------------------------------------------------

    def _wireguard(self, ctx: ScanContext) -> List[Asset]:
        out = []
        for path in ctx_glob(ctx, "/etc/wireguard/*.conf"):
            if not os.path.isfile(path):
                continue
            iface = os.path.basename(path)[:-5]
            a = self._asset(ctx, AssetKind.VPN_CONFIG, f"WireGuard {iface}", logical(ctx, path), path, vpn="wireguard", interface=iface)
            text = util.read_text(path)
            if text is None:
                a.errors.append(f"cannot read {path} (it holds the private key; run as root)")
                out.append(a)
                continue
            peers: List[bool] = []
            section = ""
            private = False
            for line in text.splitlines():
                s = line.split("#", 1)[0].strip()
                if not s:
                    continue
                if s.startswith("["):
                    section = s.strip("[] ").lower()
                    if section == "peer":
                        peers.append(False)
                    continue
                if "=" not in s:
                    continue
                k, v = (x.strip() for x in s.split("=", 1))
                k = k.lower()
                if section == "interface":
                    if k == "privatekey":
                        private = True
                    elif k == "listenport":
                        a.attributes["listen_port"] = v
                elif section == "peer" and k == "presharedkey" and v:
                    peers[-1] = True
            psk_any = any(peers)
            a.attributes.update(peer_count=len(peers), preshared_key_present=psk_any, preshared_key_per_peer=peers,
                                private_key_in_file=private)
            a.add(CryptoUse(Primitive.KEY_EXCHANGE, "ecdh", key_bits=256, curve="curve25519", raw="Noise_IK_25519",
                            context="wireguard", extra={"preshared_key_present": psk_any,
                                                        "note": "a PresharedKey adds a symmetric layer (PQ-hybrid-ish); it is not a KEM"}))
            a.add(CryptoUse(Primitive.CIPHER, "chacha20-poly1305", key_bits=256, mode="aead", raw="ChaCha20Poly1305", context="wireguard"))
            a.add(CryptoUse(Primitive.HASH, "blake2s", raw="BLAKE2s", context="wireguard"))
            out.append(a)
        return out

    # -- PPTP / L2TP -----------------------------------------------------------------

    def _pptp(self, ctx: ScanContext) -> List[Asset]:
        found = [p for p in ("/etc/pptpd.conf", "/etc/ppp/options.pptpd") if os.path.isfile(ctx.path(p))]
        if not found:
            return []
        a = self._asset(ctx, AssetKind.VPN_CONFIG, "PPTP server", found[0], ctx.path(found[0]), vpn="pptp", files=found)
        a.add(CryptoUse(Primitive.PROTOCOL, "pptp", raw=found[0], context="pptp"))
        opt = util.read_text(ctx.path("/etc/ppp/options.pptpd"))
        if opt:
            keep = ("require-mppe", "require-mppe-128", "require-mppe-40", "refuse-pap", "refuse-chap", "refuse-mschap",
                    "require-mschap-v2", "nomppe", "nomppe-40", "nomppe-128", "mppe-stateful")
            toks = {l.split("#")[0].strip().split()[0] for l in opt.splitlines() if l.split("#")[0].strip()}
            a.attributes["ppp_options"] = sorted(t for t in toks if t in keep)
        return [a]

    def _l2tp(self, ctx: ScanContext) -> List[Asset]:
        conf = None
        for p in ("/etc/xl2tpd/xl2tpd.conf", "/etc/l2tp/l2tp.conf"):
            if os.path.isfile(ctx.path(p)):
                conf = p
                break
        if conf is None:
            return []
        psk = self._psk_conns
        for p in ("/etc/ipsec.secrets", "/etc/strongswan/ipsec.secrets"):
            t = util.read_text(ctx.path(p)) if os.path.isfile(ctx.path(p)) else None
            if t and re.search(r"\bPSK\b", t):
                psk = True
        a = self._asset(ctx, AssetKind.VPN_CONFIG, "L2TP/IPsec (xl2tpd)", conf, ctx.path(conf), vpn="l2tp", ipsec_psk_detected=psk)
        if psk:
            a.add(CryptoUse(Primitive.PROTOCOL, "l2tp-ipsec-psk", raw="xl2tpd with IPsec PSK", context="l2tp"))
        return [a]
