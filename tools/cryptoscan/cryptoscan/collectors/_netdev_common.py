"""Shared helpers for the netdev platform parsers (not a collector).

`Dev` wraps the Asset being built and removes duplicate uses; the `*_use`
functions normalise the algorithm spellings of IKE/IPsec/SNMP/SSH configuration
(Cisco, Junos, FortiOS, Huawei, MikroTik, PAN-OS) into CryptoUses.  Nothing
here ever sees or stores a password, community string or key value: callers
pass only *types* and algorithm names.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from .. import names
from ..model import Asset, CryptoUse, Primitive

# ---------------------------------------------------------------------------
# asset wrapper
# ---------------------------------------------------------------------------


class Dev:
    """Builder around one NETWORK_DEVICE asset: dedupes uses, offers short constructors."""

    def __init__(self, asset: Asset, platform: str, version: Optional[Tuple[int, ...]] = None):
        self.asset = asset
        self.platform = platform
        self.version = version
        self._seen: set = set()

    def add(self, use: Optional[CryptoUse]) -> Optional[CryptoUse]:
        if use is None:
            return None
        key = (use.primitive, use.algorithm, use.key_bits, use.curve, use.hash_algorithm, use.mode, use.raw, use.context)
        if key in self._seen:
            return None
        self._seen.add(key)
        self.asset.add(use)
        return use

    def proto(self, algorithm: str, raw: str, context: str = "management", **extra) -> None:
        self.add(CryptoUse(Primitive.PROTOCOL, algorithm, raw=raw, context=context, negotiated=None, extra=extra))

    def cfg(self, knob: str, raw: str, context: Optional[str] = None, **extra) -> None:
        self.add(CryptoUse(Primitive.CONFIG, knob, raw=raw, context=context, negotiated=None, extra=extra))

    def hash(self, algorithm: str, raw: str, context: str, **extra) -> None:
        self.add(CryptoUse(Primitive.HASH, names.hash_name(algorithm), raw=raw, context=context, negotiated=None, extra=extra))

    def mac_hmac(self, hash_alg: str, raw: str, context: str, **extra) -> None:
        self.add(CryptoUse(Primitive.MAC, "hmac", hash_algorithm=names.hash_name(hash_alg), raw=raw, context=context,
                           negotiated=None, extra=extra))

    def pubkey(self, algorithm: str, bits: int, raw: str, context: str = "hostkey-material", curve: Optional[str] = None, **extra) -> None:
        self.add(CryptoUse(Primitive.PUBLIC_KEY, algorithm, key_bits=bits, curve=curve, raw=raw, context=context,
                           negotiated=None, extra=extra))

    def password(self, kind: str, context: str, **extra) -> None:
        """CONFIG password-hash: `kind` is only the storage type ("type7", "md5crypt", ...)."""
        self.cfg("password-hash", kind, context, **extra)

    def err(self, msg: str) -> None:
        self.asset.errors.append(msg)

    @property
    def attrs(self) -> Dict:
        return self.asset.attributes


def with_src(extra: Optional[Dict], source: Optional[str]) -> Dict:
    d = dict(extra or {})
    if source:
        d["source"] = source
    return d


# ---------------------------------------------------------------------------
# SSH names
# ---------------------------------------------------------------------------

_HOSTKEY_ALIASES = {
    "rsa": "ssh-rsa", "ssh-rsa": "ssh-rsa", "dsa": "ssh-dss", "dss": "ssh-dss", "ssh-dss": "ssh-dss",
    "ecdsa-nistp256": "ecdsa-sha2-nistp256", "ecdsa-nistp384": "ecdsa-sha2-nistp384", "ecdsa-nistp521": "ecdsa-sha2-nistp521",
    "ecc": "ecdsa-sha2-nistp256", "ecdsa": "ecdsa-sha2-nistp256", "ed25519": "ssh-ed25519",
    "rsa-sha2-256": "rsa-sha2-256", "rsa-sha2-512": "rsa-sha2-512",
}


def norm_kex(tok: str) -> str:
    t = tok.strip().lower().replace("_", "-")
    if t.startswith("dh-group"):
        t = "diffie-hellman-" + t[3:]
    return t


def norm_cipher(tok: str) -> str:
    t = tok.strip().lower().replace("_", "-")
    if t in ("aes128-gcm", "aes256-gcm"):
        t += "@openssh.com"
    return t


def norm_mac(tok: str) -> str:
    t = tok.strip().lower().replace("_", "-")
    if not t.startswith(("hmac-", "umac", "aead")) and t != "none":
        t = "hmac-" + t
    return t


def norm_hostkey(tok: str) -> str:
    t = tok.strip().lower().replace("_", "-")
    return _HOSTKEY_ALIASES.get(t, t)


def add_ssh_algos(dev: Dev, kind: str, tokens: List[str], **extra) -> None:
    """Record SSH algorithm names (kex | cipher | mac | hostkey | pubkey) as uses."""
    fn = {"kex": (names.ssh_kex, norm_kex), "cipher": (names.ssh_cipher, norm_cipher), "mac": (names.ssh_mac, norm_mac),
          "hostkey": (names.ssh_hostkey, norm_hostkey), "pubkey": (names.ssh_sig_algorithm, norm_hostkey)}[kind]
    for tok in tokens:
        if not tok or tok.startswith(("no-", "!", "-")) or tok.lower() in ("none-given",):
            continue
        name = fn[1](tok)
        if kind == "mac" and name.endswith("-96") and name.startswith("hmac-sha2"):
            u = CryptoUse(Primitive.MAC, "hmac", hash_algorithm=names.hash_name("sha2-" + name.split("-")[2]),
                          key_bits=96, raw=name, context="mac", negotiated=None, extra={"truncated": True})
            dev.add(_extra(u, extra))
            continue
        u = fn[0](name, negotiated=None)
        dev.add(_extra(u, extra))


def _extra(u: CryptoUse, extra: Dict) -> CryptoUse:
    if extra:
        u.extra.update(extra)
    return u


# ---------------------------------------------------------------------------
# IKE / IPsec primitives
# ---------------------------------------------------------------------------

_DH_GROUPS: Dict[int, Tuple[str, int, Optional[str]]] = {
    1: ("dh", 768, None), 2: ("dh", 1024, None), 5: ("dh", 1536, None), 14: ("dh", 2048, None), 15: ("dh", 3072, None),
    16: ("dh", 4096, None), 17: ("dh", 6144, None), 18: ("dh", 8192, None),
    19: ("ecdh", 256, "p-256"), 20: ("ecdh", 384, "p-384"), 21: ("ecdh", 521, "p-521"),
    22: ("dh", 1024, None), 23: ("dh", 2048, None), 24: ("dh", 2048, None),
    25: ("ecdh", 192, "p-192"), 26: ("ecdh", 224, "p-224"),
    27: ("ecdh", 224, "brainpoolp224r1"), 28: ("ecdh", 256, "brainpoolp256r1"), 29: ("ecdh", 384, "brainpoolp384r1"),
    30: ("ecdh", 512, "brainpoolp512r1"), 31: ("ecdh", 256, "curve25519"), 32: ("ecdh", 448, "curve448"),
}
_SUBGROUP = {22: 160, 23: 224, 24: 256}


def ike_group_use(token: str, raw: str, context: str, **extra) -> Optional[CryptoUse]:
    """KEY_EXCHANGE use for an IKE/IPsec DH group spelled group14, 14, modp1024, ecp256, curve25519."""
    t = token.strip().lower()
    m = re.fullmatch(r"(?:dh-?)?group-?(\d+)|(\d+)", t)
    spec: Optional[Tuple[str, int, Optional[str]]] = None
    n = None
    if m:
        n = int(m.group(1) or m.group(2))
        spec = _DH_GROUPS.get(n)
    else:
        m = re.fullmatch(r"modp-?(\d+)(?:-\d+)?", t)
        if m:
            spec = ("dh", int(m.group(1)), None)
        else:
            m = re.fullmatch(r"ecp-?(\d+)", t)
            if m:
                b = int(m.group(1))
                spec = ("ecdh", b, f"p-{b}")
            elif t in ("curve25519", "x25519"):
                spec = ("ecdh", 256, "curve25519")
            elif t in ("curve448", "x448"):
                spec = ("ecdh", 448, "curve448")
    if spec is None:
        return None
    alg, bits, curve = spec
    ex = dict(extra)
    if n in _SUBGROUP:
        ex["subgroup_bits"] = _SUBGROUP[n]
    return CryptoUse(Primitive.KEY_EXCHANGE, alg, key_bits=bits, curve=curve, raw=raw, context=context, negotiated=None, extra=ex)


def enc_use(token: str, raw: str, context: str, **extra) -> CryptoUse:
    """CIPHER use for IKE/IPsec/SNMP encryption tokens: des, 3des, aes-cbc-256, aes-gcm-128, esp-aes, null ..."""
    t = token.strip().lower().replace("_", "-")
    t = re.sub(r"^(esp|ah)-", "", t).replace("-ede", "")

    def cu(**kw) -> CryptoUse:
        return CryptoUse(Primitive.CIPHER, raw=raw, context=context, negotiated=None, extra=dict(extra), **kw)

    if t in ("null", "none", "enull") or t.startswith("null"):
        return cu(algorithm="null", key_bits=0)
    if t in ("des", "des-cbc", "des56", "56-bit-des", "des-56"):
        return cu(algorithm="des", key_bits=56, mode="cbc")
    if t in ("3des", "3des-cbc", "triple-des", "des3", "3des-168", "3des-cbc-168") or t.startswith("3des"):
        return cu(algorithm="3des", key_bits=168, mode="cbc")
    if t.startswith("aes") or t.startswith(("gcm", "gmac")):
        bits = 128
        m = re.search(r"(128|192|256)", t)
        if m:
            bits = int(m.group(1))
        mode = "gcm" if ("gcm" in t or "gmac" in t) else "ctr" if "ctr" in t else "ccm" if "ccm" in t else "cbc"
        return cu(algorithm="aes", key_bits=bits, mode=mode)
    if "chacha" in t:
        return cu(algorithm="chacha20-poly1305", key_bits=256, mode="aead")
    m = re.match(r"(camellia|blowfish|cast5|cast128|cast|twofish|serpent|seed|idea|aria|rc4|rc2)-?(\d+)?", t)
    if m:
        alg = {"cast128": "cast5", "cast": "cast5"}.get(m.group(1), m.group(1))
        return cu(algorithm=alg, key_bits=int(m.group(2)) if m.group(2) else None,
                  mode="cbc" if "cbc" in t else None)
    return cu(algorithm=t)


def hmac_hash_from_transform(token: str) -> Optional[str]:
    """esp-md5-hmac -> md5, esp-sha-hmac -> sha1, ah-sha256-hmac -> sha256; None when not an HMAC token."""
    m = re.fullmatch(r"(?:esp|ah)-(md5|sha|sha1|sha256|sha384|sha512)-hmac", token.strip().lower())
    return names.hash_name(m.group(1)) if m else None


def add_enc(dev: Dev, token: str, raw: str, context: str, **extra) -> None:
    dev.add(enc_use(token, raw, context, **extra))


def add_group(dev: Dev, token: str, raw: str, context: str, **extra) -> bool:
    u = ike_group_use(token, raw, context, **extra)
    dev.add(u)
    return u is not None


# ---------------------------------------------------------------------------
# SNMP
# ---------------------------------------------------------------------------

def norm_snmp_priv(tokens: List[str]) -> str:
    """Privacy protocol from the tokens after `priv`: des, des56, 3des, aes128, aes192, aes256."""
    if not tokens:
        return "des"
    t = tokens[0].lower().replace("_", "-")
    if t in ("des", "des56", "des-56", "3des", "3des-ede"):
        return {"des-56": "des56", "3des-ede": "3des"}.get(t, t)
    m = re.fullmatch(r"aes-?(128|192|256)?", t)
    if m:
        bits = m.group(1)
        if not bits and len(tokens) > 1 and tokens[1] in ("128", "192", "256"):
            bits = tokens[1]
        return "aes" + (bits or "128")
    return t


def snmp_user_findings(dev: Dev, user: str, auth: Optional[str], priv: Optional[str], context: str, source: Optional[str] = None) -> None:
    """Record SNMPv3 user security: no auth / no priv as PROTOCOL, algorithms as CONFIG (never the keys)."""
    ex = with_src({"user": user}, source)
    if not auth or auth.lower() in ("none", "noauth"):
        dev.proto("snmpv3-noauth", f"snmpv3 user {user} without authentication", context, **ex)
        return
    dev.cfg("snmp-auth-proto", auth.lower(), context, **ex)
    if not priv or priv.lower() in ("none", "nopriv"):
        dev.proto("snmpv3-noprivacy", f"snmpv3 user {user} without privacy", context, **ex)
    else:
        dev.cfg("snmp-priv-proto", priv.lower(), context, **ex)
