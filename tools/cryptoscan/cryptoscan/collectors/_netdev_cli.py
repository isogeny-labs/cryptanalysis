"""Indentation-style CLI platforms for the netdev collector (not a collector itself).

Cisco IOS / IOS-XE / NX-OS / IOS-XR / ASA, Arista EOS, HP/Aruba ProCurve and
Huawei VRP.  Every function receives the parsed indentation tree and a `Dev`
builder and records CryptoUses.  Password, community and key *values* are
never copied: only their storage type or the algorithm names.

Vendor default algorithm lists (`_IOS_*`) are approximations of the lists in
the release notes of the respective train; they are recorded with
extra["source"] = "default" (version known) or "default-unknown-version".
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

from .. import names
from ..ciphers import cipher_string_uses, normalize_proto, proto_range, protocol_use
from ..confparse import INode, tokenize
from ..model import CryptoUse, Primitive
from ._netdev_common import (
    Dev,
    add_enc,
    add_group,
    add_ssh_algos,
    hmac_hash_from_transform,
    norm_snmp_priv,
    snmp_user_findings,
    with_src,
)


def _walk(tree: List[INode]) -> Iterable[INode]:
    for n in tree:
        yield from n.walk()


def _tk(n: INode) -> List[str]:
    return n.text.split()


# ---------------------------------------------------------------------------
# generic pieces shared by the Cisco family and Arista
# ---------------------------------------------------------------------------

_PW_TYPES = {"0", "4", "5", "6", "7", "8", "9", "10"}


def _pw_kind(toks: List[str]) -> Optional[str]:
    """Storage type from the tokens following `password`/`secret`: type7, type5, type0 ..."""
    i = 0
    if toks and toks[0] == "level" and len(toks) >= 3:
        i = 2
    if i >= len(toks):
        return None
    if toks[i] in _PW_TYPES and len(toks) > i + 1:
        return "type" + toks[i]
    return "type0"


def _pw_cisco(dev: Dev, tree: List[INode], plat: str) -> None:
    for n in tree:
        t, tk = n.text, _tk(n)
        if t == "service password-encryption":
            dev.attrs["password_encryption"] = True
        elif re.match(r"^enable (password|secret)\b", t) and len(tk) > 2:
            if plat == "asa" and tk[-1] in ("encrypted", "pbkdf2", "nt-encrypted"):
                dev.password({"encrypted": "md5crypt", "pbkdf2": "pbkdf2", "nt-encrypted": "ntlm"}[tk[-1]], "enable")
                continue
            kind = _pw_kind(tk[2:])
            if kind:
                dev.password(kind, "enable " + tk[1])
        elif tk[0] == "username" and len(tk) > 3:
            idx = next((i for i, x in enumerate(tk) if x in ("password", "secret")), None)
            if idx is None:
                continue
            ctx = f"username {tk[1]}"
            rest = tk[idx + 1:]
            if plat == "asa" and rest and rest[-1] in ("encrypted", "pbkdf2", "nt-encrypted"):
                dev.password({"encrypted": "md5crypt", "pbkdf2": "pbkdf2", "nt-encrypted": "ntlm"}[rest[-1]], ctx)
                continue
            kind = _pw_kind(rest)
            if kind and plat in ("nxos", "eos") and kind in ("type5",) and len(rest) > 1:
                v = rest[1]
                kind = "md5crypt" if v.startswith("$1$") else "type5-sha-crypt" if v.startswith(("$5$", "$6$")) else kind
            if kind:
                dev.password(kind, ctx)
        elif tk[0] == "line" and n.children:
            for c in n.children:
                ct = _tk(c)
                if ct[0] == "password" and len(ct) > 1:
                    k = _pw_kind(ct[1:])
                    if k:
                        dev.password(k, n.text)
        elif tk[0] in ("tacacs-server", "radius-server") and "key" in tk:
            i = tk.index("key")
            k = _pw_kind(tk[i + 1:])
            if k:
                dev.password(k, f"{tk[0]} key")
        elif t.startswith(("tacacs server", "tacacs-server host", "radius server")) and n.children:
            for c in n.children:
                m = re.match(r"^key (?:(\d+) )?\S+", c.text)
                if m:
                    dev.password("type" + (m.group(1) or "0"), f"{tk[0]} key")
        elif re.match(r"^crypto isakmp key\b", t) and len(tk) > 3:
            dev.password("type" + tk[3] if tk[3] in ("0", "6") and len(tk) > 4 else "type0", "isakmp-key")
        elif t.startswith("crypto keyring"):
            for c in n.children:
                m = re.match(r"^pre-shared-key .*?\bkey (?:(\d+) )?\S+", c.text)
                if m:
                    dev.password("type" + (m.group(1) or "0"), "isakmp-key")
    for n in _walk(tree):
        m = re.match(r"^key-string (?:(\d+) )?\S+", n.text)
        if m:
            dev.password("type" + (m.group(1) or "0"), "key-chain")
        m = re.match(r"^cryptographic-algorithm (md5|hmac-sha-1|hmac-sha-256|hmac-sha-384|hmac-sha-512|sha-1)\b", n.text)
        if m and m.group(1) == "md5":
            dev.hash("md5", "key chain cryptographic-algorithm md5", "routing-auth")


def _snmp_cli(dev: Dev, tree: List[INode], plat: str) -> None:
    n_comm = 0
    for n in _walk(tree):
        t, tk = n.text, _tk(n)
        if tk[0] == "no":
            continue
        if t.startswith("snmp-server community ") and len(tk) >= 3:
            n_comm += 1
            rest = [x.lower() for x in tk[3:]]
            access = "ro" if "ro" in rest else "rw" if "rw" in rest else "unspecified"
            acl = any(x not in ("ro", "rw", "view", "use-ipv4acl", "use-ipv6acl") for x in rest[:]) and access != "unspecified"
            group = None
            if "group" in rest and rest.index("group") + 1 < len(rest):
                group = rest[rest.index("group") + 1]
            dev.proto("snmpv2c", f"snmp-server community #{n_comm} ({access})", "snmp-community",
                      community="present", access=access, acl=bool(acl or "use-ipv4acl" in rest), **({"group": group} if group else {}))
        elif t.startswith("snmp-server group ") and len(tk) >= 5:
            ver = tk[3].lower()
            if ver == "v1":
                dev.proto("snmpv1", f"snmp-server group {tk[2]} v1", "snmp-group")
            elif ver == "v2c":
                dev.proto("snmpv2c", f"snmp-server group {tk[2]} v2c", "snmp-group")
            elif ver == "v3":
                lvl = tk[4].lower() if len(tk) > 4 else ""
                if lvl == "noauth":
                    dev.proto("snmpv3-noauth", f"snmp-server group {tk[2]} v3 noauth", "snmp-group")
                elif lvl == "auth":
                    dev.proto("snmpv3-noprivacy", f"snmp-server group {tk[2]} v3 auth", "snmp-group")
        elif t.startswith("snmp-server user ") and len(tk) >= 4:
            user = tk[2]
            rest = tk[4:] if len(tk) > 4 and tk[4].lower() != "v3" else tk[5:]
            low = [r.lower() for r in rest]
            auth = priv = None
            src = None
            if "auth" in low and low.index("auth") + 1 < len(low):
                auth = low[low.index("auth") + 1]
            if "priv" in low:
                i = low.index("priv")
                after = low[i + 1:]
                if plat == "nxos" and after and not re.fullmatch(r"(des|3des|aes(-?\d+)?)", after[0]):
                    priv, src = "des", "default"
                else:
                    priv = norm_snmp_priv(after)
            snmp_user_findings(dev, user, auth, priv, f"snmp-user {user}", src)
        elif t.startswith("snmp-server host ") and len(tk) >= 3:
            host = tk[3] if plat == "asa" and len(tk) > 3 else tk[2]
            m = re.search(r"\bversion\s+(1|2c|3)\b", t)
            if m:
                if m.group(1) == "1":
                    dev.proto("snmpv1", f"snmp-server host {host} version 1", "snmp-host", community="present")
                elif m.group(1) == "2c":
                    dev.proto("snmpv2c", f"snmp-server host {host} version 2c", "snmp-host", community="present")
            elif plat in ("ios", "iosxe", "iosxr") and not re.search(r"\b(auth|priv|noauth)\b", t) and len(tk) > 3:
                dev.proto("snmpv1", f"snmp-server host {host} (default version 1)", "snmp-host", community="present", source="default")


def _ntp(dev: Dev, tree: List[INode]) -> None:
    for n in tree:
        m = re.match(r"^ntp authentication-key (\d+) (\S+)", n.text)
        if m:
            algo = m.group(2).lower()
            if algo in ("md5", "sha1", "sha-1"):
                dev.hash(algo, f"ntp authentication-key {m.group(1)} {algo}", "ntp-auth")
        m = re.match(r"^ntp-service authentication-keyid (\d+) authentication-mode (\S+)", n.text)
        if m and m.group(2).lower() in ("md5", "sha1"):
            dev.hash(m.group(2), f"ntp-service authentication-keyid {m.group(1)} {m.group(2).lower()}", "ntp-auth")


# ---------------------------------------------------------------------------
# IKE / IPsec (IOS-style syntax, also ASA and Huawei children)
# ---------------------------------------------------------------------------

def _ikev1_policy(dev: Dev, node: INode, num: str, plat: str) -> Dict:
    """Record one IKEv1 policy; absent encryption/hash/group lines are the platform defaults (DES, SHA-1, group 1)."""
    enc = hsh = grp = auth = None
    for c in node.children:
        t = _tk(c)
        if t[0] in ("encryption", "encr") and len(t) > 1:
            enc = t[1] if not (t[1] == "aes" and len(t) > 2 and t[2].isdigit()) else f"aes-{t[2]}"
        elif t[0] == "hash" and len(t) > 1:
            hsh = t[1]
        elif t[0] == "group" and len(t) > 1:
            grp = t[1]
        elif t[0] in ("authentication", "auth") and len(t) > 1:
            auth = t[1]
    ctx = f"isakmp-policy {num}"
    ex = {"policy": num, "authentication": auth or "rsa-sig"}
    defaults = {"enc": enc is None, "hash": hsh is None, "group": grp is None} if plat in ("ios", "iosxe", "asa") else {}
    if defaults.get("enc"):
        enc = "des"
    if defaults.get("hash"):
        hsh = "sha"
    if defaults.get("group"):
        grp = "1"
    if enc:
        add_enc(dev, enc, f"encryption {enc}", ctx, **with_src(ex, "default" if defaults.get("enc") else None))
    if hsh:
        dev.hash(hsh, f"hash {hsh}", ctx, **with_src(ex, "default" if defaults.get("hash") else None))
    if grp:
        add_group(dev, grp, f"group {grp}", ctx, **with_src(ex, "default" if defaults.get("group") else None))
    return {"policy": num, "auth": auth}


def _ike_cisco(dev: Dev, tree: List[INode], plat: str) -> None:
    policies: List[Dict] = []
    psk = False
    aggressive_disabled = False
    aggressive_peer = False
    for n in tree:
        t = n.text
        m = re.match(r"^(?:crypto )?(?:isakmp|ikev1) policy (\d+)$", t)
        if m:
            policies.append(_ikev1_policy(dev, n, m.group(1), plat))
            continue
        if t == "crypto isakmp aggressive-mode disable" or t == "crypto ikev1 am-disable":
            aggressive_disabled = True
        if t.startswith("crypto isakmp peer"):
            if any("aggressive" in c.text for c in n.children) or "aggressive" in t:
                aggressive_peer = True
        if t.startswith("crypto isakmp key") or t.startswith("crypto keyring") or "ikev1 pre-shared-key" in t:
            psk = True
        if t.startswith("tunnel-group") or t.startswith("crypto isakmp profile"):
            for c in n.walk():
                if "pre-shared-key" in c.text:
                    psk = True
        # ikev2 (no protocol finding)
        m = re.match(r"^crypto ikev2 (?:proposal|policy) (\S+)$", t)
        if m:
            _ikev2_block(dev, n, m.group(1))
        m = re.match(r"^crypto ipsec (?:ikev1 )?transform-set (\S+) (.+)$", t)
        if m:
            _transform_set(dev, m.group(1), m.group(2).split())
        m = re.match(r"^crypto ipsec ikev2 ipsec-proposal (\S+)$", t)
        if m:
            _asa_ipsec_proposal(dev, n, m.group(1))
    for n in _walk(tree):
        m = re.match(r"^(?:crypto map \S+ \d+ )?set pfs(?: (group\d+))?$", n.text)
        if m:
            g = m.group(1) or "group1"
            add_group(dev, g, f"set pfs {g}", "pfs", **({"source": "default"} if not m.group(1) else {}))
    if policies:
        pol_ids = [p["policy"] for p in policies]
        dev.proto("ikev1", "isakmp policy (IKEv1)", "ike", policies=pol_ids)
        if aggressive_peer:
            dev.proto("ikev1-aggressive", "crypto isakmp peer aggressive-mode", "ike", source="configured")
        elif not aggressive_disabled and (psk or any((p["auth"] or "") == "pre-share" for p in policies)):
            dev.proto("ikev1-aggressive", "aggressive mode not disabled (pre-shared keys in use)", "ike", source="default")


def _transform_set(dev: Dev, name: str, toks: List[str]) -> None:
    ctx = f"transform-set {name}"
    i = 0
    while i < len(toks):
        low = toks[i].lower()
        h = hmac_hash_from_transform(low)
        nxt = toks[i + 1] if i + 1 < len(toks) else ""
        if h:
            dev.mac_hmac(h, low, ctx, transform_set=name)
        elif low.startswith("esp-"):
            if low in ("esp-aes", "esp-gcm", "esp-gmac") and nxt in ("128", "192", "256"):
                add_enc(dev, f"{low}-{nxt}", f"{low} {nxt}", ctx, transform_set=name)
                i += 1
            elif low != "esp-seal":
                add_enc(dev, low, low, ctx, transform_set=name)
        i += 1


def _ikev2_block(dev: Dev, node: INode, name: str) -> None:
    ctx = f"ikev2-proposal {name}"
    for c in node.children:
        t = _tk(c)
        if not t:
            continue
        if t[0] == "encryption":
            for e in t[1:]:
                add_enc(dev, e, f"encryption {e}", ctx, proposal=name)
        elif t[0] == "integrity":
            for h in t[1:]:
                if h.lower() == "null":
                    continue
                dev.mac_hmac(h, f"integrity {h}", ctx, proposal=name)
        elif t[0] == "group":
            for g in t[1:]:
                add_group(dev, g, f"group {g}", ctx, proposal=name)


def _asa_ipsec_proposal(dev: Dev, node: INode, name: str) -> None:
    ctx = f"ipsec-proposal {name}"
    for c in node.children:
        t = _tk(c)
        if len(t) >= 4 and t[0] == "protocol":
            if t[2] == "encryption":
                for e in t[3:]:
                    add_enc(dev, e, f"encryption {e}", ctx, proposal=name)
            elif t[2] == "integrity":
                for h in t[3:]:
                    if h.lower() != "null":
                        dev.mac_hmac(h, f"integrity {h}", ctx, proposal=name)


# ---------------------------------------------------------------------------
# Cisco IOS / IOS-XE
# ---------------------------------------------------------------------------

_IOS_NEW = {   # IOS-XE 16.x+ (approximate vendor defaults)
    "kex": ["ecdh-sha2-nistp256", "ecdh-sha2-nistp384", "ecdh-sha2-nistp521", "diffie-hellman-group-exchange-sha1", "diffie-hellman-group14-sha1"],
    "cipher": ["aes128-ctr", "aes192-ctr", "aes256-ctr", "aes128-cbc", "3des-cbc", "aes192-cbc", "aes256-cbc"],
    "mac": ["hmac-sha2-256", "hmac-sha2-512", "hmac-sha1", "hmac-sha1-96"],
    "hostkey": ["ssh-rsa"],
}
_IOS_MID = {   # IOS 15.5+ (algorithm knobs exist, group-exchange default)
    "kex": ["diffie-hellman-group-exchange-sha1", "diffie-hellman-group14-sha1"],
    "cipher": ["aes128-ctr", "aes192-ctr", "aes256-ctr", "aes128-cbc", "3des-cbc", "aes192-cbc", "aes256-cbc"],
    "mac": ["hmac-sha1", "hmac-sha1-96"],
    "hostkey": ["ssh-rsa"],
}
_IOS_OLD = {   # IOS before 15.5: fixed group1 key exchange, CBC ciphers
    "kex": ["diffie-hellman-group1-sha1"],
    "cipher": ["aes128-cbc", "aes192-cbc", "aes256-cbc", "3des-cbc"],
    "mac": ["hmac-sha1", "hmac-sha1-96"],
}
_IOS_UNKNOWN = {"kex": ["diffie-hellman-group1-sha1"], "cipher": ["3des-cbc"], "mac": ["hmac-sha1-96"]}


def _ssh_defaults(ver: Optional[Tuple[int, ...]]) -> Tuple[Dict[str, List[str]], str]:
    if ver is None:
        return _IOS_UNKNOWN, "default-unknown-version"
    if ver >= (16,):
        return _IOS_NEW, "default"
    if ver >= (15, 5):
        return _IOS_MID, "default"
    return _IOS_OLD, "default"


def _rsa_material(dev: Dev, text: str, tree: List[INode]) -> None:
    for n in _walk(tree):
        m = re.match(r"^crypto key generate rsa\b.*?\bmodulus (\d+)", n.text)
        if m:
            dev.pubkey("rsa", int(m.group(1)), f"crypto key generate rsa modulus {m.group(1)}")
        m = re.match(r"^crypto key generate ec\b.*?\bkeysize (256|384|521)", n.text)
        if m:
            dev.pubkey("ec", int(m.group(1)), f"crypto key generate ec keysize {m.group(1)}", curve=f"p-{m.group(1)}")
        m = re.match(r"^ip ssh rsa keypair-name (\S+)", n.text)
        if m:
            dev.attrs["ssh_keypair"] = m.group(1)
    for m in re.finditer(r"Modulus Size\s*:\s*(\d+)\s*bits?", text):
        dev.pubkey("rsa", int(m.group(1)), f"Modulus Size : {m.group(1)} bits")
    for m in re.finditer(r"(?im)^\s*Key Data:?\s*$", text):
        dev.attrs["key_data_present"] = True


def _ssh_ios(dev: Dev, tree: List[INode], text: str) -> None:
    ver = dev.version
    algos: Dict[str, List[str]] = {}
    ssh_version = None
    enabled = False
    for n in tree:
        t = n.text
        m = re.match(r"^ip ssh version (\d)", t)
        if m:
            ssh_version = int(m.group(1))
            enabled = True
        m = re.match(r"^ip ssh (server|client) algorithm (kex|encryption|mac|hostkey|publickey) (.+)$", t)
        if m:
            side, kind, rest = m.groups()
            kind = {"encryption": "cipher", "publickey": "hostkey"}.get(kind, kind)
            algos.setdefault(kind, []).extend(rest.split())
            add_ssh_algos(dev, kind, rest.split(), direction=side)
            enabled = True
        m = re.match(r"^ip ssh dh min size (\d+)", t)
        if m:
            dev.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=int(m.group(1)), raw=f"ip ssh dh min size {m.group(1)}",
                              context="kex", negotiated=None, extra={"directive": "ip ssh dh min size"}))
        if t.startswith("ip ssh ") or t.startswith(("crypto key generate rsa", "crypto key generate ec")):
            enabled = True
        if t.startswith("line vty"):
            for c in n.children:
                if c.text.startswith("transport input") and set(_tk(c)[2:]) & {"ssh", "all"}:
                    enabled = True
    _rsa_material(dev, text, tree)
    dev.attrs["ssh_enabled"] = enabled
    if ssh_version == 1:
        dev.proto("ssh1", "ip ssh version 1", "ssh")
    elif ssh_version is None and enabled and (ver is None or ver < (17,)):
        dev.proto("ssh1.99", "ip ssh version not set (SSH 1.99 compatibility)", "ssh", source="default")
    dev.attrs["ssh_version"] = ssh_version
    if enabled:
        defaults, src = _ssh_defaults(ver)
        for kind in ("kex", "cipher", "mac", "hostkey"):
            if kind not in algos and kind in defaults:
                add_ssh_algos(dev, kind, defaults[kind], source=src, direction="server")


_TLS_CISCO = {   # `ip http secure-ciphersuite` tokens -> (kx, cipher, mac)
    "3des-ede-cbc-sha": ("RSA", "3DES_EDE_CBC", "SHA"), "rc4-128-sha": ("RSA", "RC4_128", "SHA"), "rc4-128-md5": ("RSA", "RC4_128", "MD5"),
    "des-cbc-sha": ("RSA", "DES_CBC", "SHA"), "aes-128-cbc-sha": ("RSA", "AES_128_CBC", "SHA"), "aes-256-cbc-sha": ("RSA", "AES_256_CBC", "SHA"),
    "dhe-aes-128-cbc-sha": ("DHE_RSA", "AES_128_CBC", "SHA"), "dhe-aes-256-cbc-sha": ("DHE_RSA", "AES_256_CBC", "SHA"),
    "null-sha": ("RSA", "NULL", "SHA"), "null-md5": ("RSA", "NULL", "MD5"),
}


def _cisco_suite(tok: str) -> CryptoUse:
    low = tok.lower()
    spec = _TLS_CISCO.get(low)
    if spec is None:
        m = re.match(r"^(ecdhe-rsa|ecdhe-ecdsa|dhe-rsa|dhe)-(.+?)-(sha384|sha256|sha2|sha|md5)$", low)
        if m:
            kx = {"ecdhe-rsa": "ECDHE_RSA", "ecdhe-ecdsa": "ECDHE_ECDSA", "dhe-rsa": "DHE_RSA", "dhe": "DHE_RSA"}[m.group(1)]
            body, mac = m.group(2), {"SHA2": "SHA256"}.get(m.group(3).upper(), m.group(3).upper())
            mm = re.fullmatch(r"aes-(gcm|cbc)-(128|256)|aes-(128|256)-(gcm|cbc)|aes-(gcm|cbc)", body)
            if mm:
                mode = (mm.group(1) or mm.group(4) or mm.group(5)).upper()
                bits = mm.group(2) or mm.group(3) or ("256" if mac == "SHA384" else "128")
                c = f"AES_{bits}_{mode}"
            else:
                c = body.upper().replace("-", "_")
            spec = (kx, c, mac)
    if spec is None:
        return names.tls_cipher_suite(tok.upper().replace("-", "_"), negotiated=None)
    iana = f"TLS_{spec[0]}_WITH_{spec[1]}_{spec[2]}"
    u = names.tls_cipher_suite(iana, negotiated=None)
    u.raw = tok
    return u


def _mgmt_ios(dev: Dev, tree: List[INode], plat: str) -> None:
    texts = {n.text for n in tree}
    if "ip http server" in texts:
        dev.proto("http-mgmt", "ip http server", "management")
    if "ip http secure-server" in texts:
        dev.attrs["https_mgmt"] = True
    for n in tree:
        t, tk = n.text, _tk(n)
        if t.startswith("ip http tls-version"):
            for v in tk[3:]:
                p = normalize_proto(v)
                if p:
                    u = protocol_use(p, directive="ip http tls-version")
                    u.context = "ip http tls-version"
                    dev.add(u)
        elif t.startswith("ip http secure-ciphersuite"):
            for c in tk[3:]:
                u = _cisco_suite(c)
                u.extra["directive"] = "ip http secure-ciphersuite"
                dev.add(u)
        elif t.startswith("tftp-server "):
            dev.proto("tftp", "tftp-server", "management")
        elif t == "ftp-server enable" or t.startswith("ip ftp-server"):
            dev.proto("ftp", "ftp-server", "management")
        elif tk[0] == "line" and len(tk) > 1 and tk[1] == "vty":
            _vty(dev, n, plat)


def _vty(dev: Dev, n: INode, plat: str) -> None:
    transport = None
    for c in n.children:
        t = _tk(c)
        if t[:2] == ["transport", "input"]:
            transport = set(x.lower() for x in t[2:]) or {"none"}
    if transport is None:
        if plat in ("ios", "iosxe"):
            dev.proto("telnet", f"{n.text}: no transport input (default all)", "management", source="default")
        return
    if transport & {"telnet", "all"}:
        dev.proto("telnet", f"{n.text}: transport input {' '.join(sorted(transport))}", "management")


def run_ios(dev: Dev, tree: List[INode], text: str) -> None:
    _ssh_ios(dev, tree, text)
    _mgmt_ios(dev, tree, dev.platform)
    _snmp_cli(dev, tree, dev.platform)
    _pw_cisco(dev, tree, dev.platform)
    _ike_cisco(dev, tree, dev.platform)
    _ntp(dev, tree)


# ---------------------------------------------------------------------------
# NX-OS
# ---------------------------------------------------------------------------

def run_nxos(dev: Dev, tree: List[INode], text: str) -> None:
    texts = [n.text for n in tree]
    if "feature telnet" in texts:
        dev.proto("telnet", "feature telnet", "management")
    if "no feature ssh" in texts:
        dev.attrs["ssh_enabled"] = False
    elif "feature ssh" in texts:
        dev.attrs["ssh_enabled"] = True
    for n in tree:
        t = n.text
        m = re.match(r"^ssh key (rsa|dsa|ecdsa)(?: (\d+))?", t)
        if m:
            alg, bits = m.group(1), m.group(2)
            if bits:
                if alg == "ecdsa":
                    dev.pubkey("ec", int(bits), f"ssh key ecdsa {bits}", curve=f"p-{bits}")
                else:
                    dev.pubkey(alg, int(bits), f"ssh key {alg} {bits}")
        if t.startswith("ssh cipher-mode weak"):
            for c in ("3des-cbc", "aes128-cbc", "aes192-cbc", "aes256-cbc"):
                add_ssh_algos(dev, "cipher", [c], source="cipher-mode-weak", direction="server")
        if t == "feature tftp-server":
            dev.proto("tftp", "feature tftp-server", "management")
        if t == "feature ftp-server":
            dev.proto("ftp", "feature ftp-server", "management")
        if re.match(r"^nxapi http port \d+", t):
            dev.proto("http-mgmt", "nxapi http", "management")
    _snmp_cli(dev, tree, "nxos")
    _pw_cisco(dev, tree, "nxos")
    _ike_cisco(dev, tree, "nxos")
    _ntp(dev, tree)


# ---------------------------------------------------------------------------
# IOS-XR
# ---------------------------------------------------------------------------

def run_iosxr(dev: Dev, tree: List[INode], text: str) -> None:
    for n in tree:
        t = n.text
        if t == "ssh server v2":
            dev.attrs["ssh_version"] = 2
        elif t == "ssh server v1":
            dev.proto("ssh1", "ssh server v1", "ssh")
        m = re.match(r"^ssh server algorithms (cipher|key-exchange|mac|host-key) (.+)$", t)
        if m:
            kind = {"cipher": "cipher", "key-exchange": "kex", "mac": "mac", "host-key": "hostkey"}[m.group(1)]
            add_ssh_algos(dev, kind, m.group(2).split(), direction="server")
        if re.match(r"^telnet (vrf \S+ )?ipv[46] server\b", t):
            dev.proto("telnet", "telnet ipv4 server", "management")
        if t == "ftp server" or t.startswith("ftp server"):
            dev.proto("ftp", "ftp server", "management")
    _snmp_cli(dev, tree, "iosxr")
    _pw_cisco(dev, tree, "iosxr")
    _ntp(dev, tree)


# ---------------------------------------------------------------------------
# Cisco ASA
# ---------------------------------------------------------------------------

_ASA_SSL_LEVELS = {
    "all": ["RC4-SHA", "DES-CBC3-SHA", "DES-CBC-SHA", "AES128-SHA", "AES256-SHA"],
    "low": ["RC4-SHA", "DES-CBC3-SHA", "AES128-SHA", "AES256-SHA"],
    "medium": ["DES-CBC3-SHA", "AES128-SHA", "AES256-SHA"],
    "fips": ["DES-CBC3-SHA", "AES128-SHA", "AES256-SHA"],
    "high": ["AES256-SHA", "AES128-SHA"],
}
_ASA_ENC = {"rc4-sha1": "RC4-SHA", "rc4-md5": "RC4-MD5", "3des-sha1": "DES-CBC3-SHA", "des-sha1": "DES-CBC-SHA",
            "aes128-sha1": "AES128-SHA", "aes256-sha1": "AES256-SHA", "dhe-aes128-sha1": "DHE-RSA-AES128-SHA",
            "dhe-aes256-sha1": "DHE-RSA-AES256-SHA", "null-sha1": "NULL-SHA"}
_ASA_SSH_ENC = {"low": ["3des-cbc", "aes128-cbc", "aes192-cbc", "aes256-cbc"], "medium": ["aes128-cbc", "aes192-cbc", "aes256-cbc"],
                "fips": ["aes128-cbc", "aes256-cbc"], "high": ["aes256-cbc"]}
_ASA_SSH_INT = {"low": ["hmac-sha1", "hmac-sha2-256"], "medium": ["hmac-sha1", "hmac-sha2-256"], "fips": ["hmac-sha1", "hmac-sha2-256"],
                "high": ["hmac-sha2-256"]}


def _asa_versions(dev: Dev, args: List[str], direction: str) -> None:
    ctx = f"ssl-{direction}-version"
    for a in args:
        low = a.lower()
        if low.startswith("dtls"):
            for p in (["DTLSv1.0", "DTLSv1.2"] if low in ("dtlsv1", "dtlsv1.0") else ["DTLSv1.2"]):
                u = names.tls_protocol(p, negotiated=None, extra={"directive": ctx, "min": a})
                u.context = ctx
                dev.add(u)
            continue
        if low in ("any", "sslv3"):
            protos = ["SSLv3", "TLSv1", "TLSv1.1", "TLSv1.2"]
        elif low.endswith("-only"):
            p = normalize_proto(low[:-5])
            protos = [p] if p else []
        else:
            p = normalize_proto(low)
            protos = proto_range(p, "TLSv1.2" if p != "TLSv1.3" else "TLSv1.3") if p else []
        for p in protos:
            u = protocol_use(p, directive=ctx, min=a)
            u.context = ctx
            dev.add(u)


def run_asa(dev: Dev, tree: List[INode], text: str) -> None:
    ver = dev.version
    ssh_version = None
    ssh_access = False
    has_kex = False
    for n in tree:
        t, tk = n.text, _tk(n)
        if re.match(r"^ssl (server|client)-version\b", t):
            _asa_versions(dev, tk[2:], tk[1])
        elif t.startswith("ssl cipher "):
            _asa_cipher(dev, t)
        elif t.startswith("ssl encryption "):
            for tok in tk[2:]:
                if tok.lower() in _ASA_ENC:
                    u = names.tls_cipher_suite(_ASA_ENC[tok.lower()], negotiated=None, extra={"directive": "ssl encryption"})
                    dev.add(u)
        elif t.startswith("ssl dh-group "):
            g = tk[2]
            add_group(dev, g, f"ssl dh-group {g}", "ssl-dh-group", directive="ssl dh-group")
        elif t.startswith("ssl ecdh-group "):
            g = tk[2]
            add_group(dev, g, f"ssl ecdh-group {g}", "ssl-ecdh-group", directive="ssl ecdh-group")
        elif re.match(r"^ssh version \d", t):
            ssh_version = int(tk[2])
            if ssh_version == 1:
                dev.proto("ssh1", "ssh version 1", "ssh")
        elif t.startswith("ssh cipher encryption "):
            _asa_ssh_list(dev, tk[3:], "cipher", _ASA_SSH_ENC)
        elif t.startswith("ssh cipher integrity "):
            _asa_ssh_list(dev, tk[3:], "mac", _ASA_SSH_INT)
        elif t.startswith("ssh key-exchange group "):
            has_kex = True
            add_ssh_algos(dev, "kex", tk[3:], direction="server")
        elif t.startswith("ssh key-exchange hostkey"):
            add_ssh_algos(dev, "hostkey", tk[3:], direction="server")
        elif re.match(r"^ssh \d+\.\d+\.\d+\.\d+ ", t) or re.match(r"^ssh (::|[0-9a-f:]+/\d+) ", t):
            ssh_access = True
        elif re.match(r"^telnet \d+\.\d+\.\d+\.\d+ ", t) or re.match(r"^telnet (::|[0-9a-f:]+/\d+) ", t):
            dev.proto("telnet", "telnet <acl> (ASA telnet access)", "management")
        elif t.startswith("crypto ca trustpoint"):
            for c in n.children:
                if c.text.startswith(("keypair ", "rsakeypair ")):
                    dev.attrs.setdefault("trustpoint_keypairs", []).append(_tk(c)[1])
        elif t == "webvpn":
            dev.attrs["webvpn"] = True
    if ssh_access:
        if ssh_version is None:
            dev.proto("ssh1.99", "ssh version not set (v1 and v2 accepted)", "ssh", source="default")
        if not has_kex:
            if ver is not None and ver >= (9, 12):
                add_ssh_algos(dev, "kex", ["dh-group14-sha256"], source="default", direction="server")
            else:
                add_ssh_algos(dev, "kex", ["dh-group1-sha1"], source="default" if ver else "default-unknown-version", direction="server")
    _rsa_material(dev, text, tree)
    _ike_cisco(dev, tree, "asa")
    _snmp_cli(dev, tree, "asa")
    _pw_cisco(dev, tree, "asa")
    _ntp(dev, tree)


def _asa_ssh_list(dev: Dev, args: List[str], kind: str, levels: Dict[str, List[str]]) -> None:
    if not args:
        return
    if args[0] == "custom":
        toks = [x for x in re.split(r"[:,\s]+", " ".join(args[1:]).strip("\"'")) if x]
    else:
        toks = levels.get(args[0].lower(), [])
    add_ssh_algos(dev, kind, toks, direction="server")


def _asa_cipher(dev: Dev, line: str) -> None:
    tk = tokenize(line)            # ssl cipher <proto> (all|low|medium|fips|high|custom "spec")
    if len(tk) < 4:
        return
    proto, level = tk[2], tk[3].lower()
    if level == "custom" and len(tk) > 4:
        info = cipher_string_uses(tk[4], negotiated=None, extra={"directive": f"ssl cipher {proto}"})
        for u in info.uses:
            dev.add(u)
        if info.flags:
            dev.attrs.setdefault("cipher_string_flags", sorted(info.flags))
    else:
        for name in _ASA_SSL_LEVELS.get(level, []):
            dev.add(names.tls_cipher_suite(name, negotiated=None, extra={"directive": f"ssl cipher {proto} {level}", "heuristic": True}))


# ---------------------------------------------------------------------------
# Arista EOS
# ---------------------------------------------------------------------------

def run_eos(dev: Dev, tree: List[INode], text: str) -> None:
    for n in tree:
        t = n.text
        if t == "management ssh":
            for c in n.children:
                ct = _tk(c)
                if ct[0] == "cipher":
                    add_ssh_algos(dev, "cipher", ct[1:], direction="server")
                elif ct[0] == "mac":
                    add_ssh_algos(dev, "mac", ct[1:], direction="server")
                elif ct[0] == "key-exchange":
                    add_ssh_algos(dev, "kex", ct[1:], direction="server")
                elif ct[0] == "hostkey" and len(ct) > 2 and ct[1] == "server":
                    add_ssh_algos(dev, "hostkey", ct[2:], direction="server")
        elif t == "management telnet":
            if not any(c.text == "shutdown" for c in n.children):
                dev.proto("telnet", "management telnet", "management")
        elif t == "management api http-commands":
            texts = [c.text for c in n.children]
            if "protocol http" in texts and "shutdown" not in texts:
                dev.proto("http-mgmt", "management api http-commands: protocol http", "management")
        elif t == "management security":
            for c in n.walk():
                if c.text.startswith("ssl profile "):
                    _eos_profile(dev, c)
    _snmp_cli(dev, tree, "eos")
    _pw_cisco(dev, tree, "eos")
    _ntp(dev, tree)


def _eos_profile(dev: Dev, node: INode) -> None:
    name = _tk(node)[2] if len(_tk(node)) > 2 else "?"
    for c in node.children:
        ct = _tk(c)
        if ct[:2] == ["tls", "versions"]:
            for v in ct[2:]:
                p = normalize_proto("TLSv" + v)
                if p:
                    u = protocol_use(p, profile=name)
                    u.context = f"ssl-profile {name}"
                    dev.add(u)
        elif ct[0] == "cipher-list":
            info = cipher_string_uses(" ".join(ct[1:]), negotiated=None, extra={"profile": name})
            for u in info.uses:
                dev.add(u)


# ---------------------------------------------------------------------------
# HP / Aruba ProCurve
# ---------------------------------------------------------------------------

def run_procurve(dev: Dev, tree: List[INode], text: str) -> None:
    texts = [n.text for n in tree]
    if "telnet-server" in texts:
        dev.proto("telnet", "telnet-server", "management")
    elif "no telnet-server" not in texts:
        dev.proto("telnet", "telnet-server not disabled (default enabled)", "management", source="default")
    n_comm = 0
    for n in tree:
        t, tk = n.text, tokenize(n.text)
        if t.startswith("ip ssh cipher ") or t.startswith("ip ssh mac "):
            add_ssh_algos(dev, "cipher" if "cipher" in tk[2] else "mac", tk[3:], direction="server")
        elif re.match(r"^ip ssh version", t):
            v = tk[3] if len(tk) > 3 else ""
            if v == "1":
                dev.proto("ssh1", "ip ssh version 1", "ssh")
            elif v in ("1-or-2", "1or2"):
                dev.proto("ssh1.99", "ip ssh version 1-or-2", "ssh")
        elif t == "web-management plaintext" or t.startswith("web-management plaintext"):
            dev.proto("http-mgmt", "web-management plaintext", "management")
        elif t.startswith("snmp-server community "):
            n_comm += 1
            low = [x.lower() for x in tk[3:]]
            access = "manager" if "manager" in low else "operator" if "operator" in low else "unspecified"
            dev.proto("snmpv2c", f"snmp-server community #{n_comm} ({access})", "snmp-community", community="present", access=access)
        elif t.startswith("snmpv3 user "):
            low = [x.lower() for x in tk]
            user = tk[2]
            auth = low[low.index("auth") + 1] if "auth" in low and low.index("auth") + 1 < len(low) else None
            priv = norm_snmp_priv(low[low.index("priv") + 1:]) if "priv" in low else None
            snmp_user_findings(dev, user, auth, priv, f"snmp-user {user}")
        elif t.startswith("tls application "):
            m = re.search(r"lowest-version (tls\d(?:\.\d)?)", t, re.I)
            if m:
                p = normalize_proto(m.group(1).replace("tls", "TLSv"))
                for q in proto_range(p, "TLSv1.2") if p else []:
                    u = protocol_use(q, directive="tls application lowest-version")
                    u.context = "tls-application"
                    dev.add(u)
        elif re.match(r"^crypto key generate (ssh|cert) rsa bits (\d+)", t):
            m = re.match(r"^crypto key generate (ssh|cert) rsa bits (\d+)", t)
            dev.pubkey("rsa", int(m.group(2)), f"crypto key generate {m.group(1)} rsa bits {m.group(2)}")
        elif t.startswith("password "):
            m = re.match(r"^password (manager|operator)(?: user-name \S+)?(?: (sha1|plaintext))?", t)
            if m and m.group(2) == "sha1":
                dev.password("sha1crypt", f"password {m.group(1)}")
            elif m and m.group(2) == "plaintext":
                dev.password("type0", f"password {m.group(1)}")


# ---------------------------------------------------------------------------
# Huawei VRP
# ---------------------------------------------------------------------------

def run_huawei(dev: Dev, tree: List[INode], text: str) -> None:
    users: Dict[str, Dict[str, Optional[str]]] = {}
    n_comm = 0
    for n in _walk(tree):
        t, tk = n.text, _tk(n)
        m = re.match(r"^ssh (server|client) (cipher|hmac|key-exchange|publickey|hostkey) (.+)$", t)
        if m:
            side, what, rest = m.groups()
            kind = {"cipher": "cipher", "hmac": "mac", "key-exchange": "kex", "publickey": "pubkey", "hostkey": "hostkey"}[what]
            add_ssh_algos(dev, kind, rest.split(), direction=side)
        elif re.match(r"^ssh server compatible[-_]ssh1x enable", t):
            dev.proto("ssh1.99", "ssh server compatible-ssh1x enable", "ssh")
        elif t == "telnet server enable":
            dev.proto("telnet", "telnet server enable", "management")
        elif t == "ftp server enable" or t.startswith("ftp server enable"):
            dev.proto("ftp", "ftp server enable", "management")
        elif t == "http server enable":
            dev.proto("http-mgmt", "http server enable", "management")
        elif t.startswith("user-interface vty"):
            for c in n.children:
                ct = _tk(c)
                if ct[:2] == ["protocol", "inbound"] and set(x.lower() for x in ct[2:]) & {"telnet", "all"}:
                    dev.proto("telnet", f"{t}: protocol inbound {' '.join(ct[2:])}", "management")
                if ct[:3] == ["set", "authentication", "password"] and len(ct) > 3:
                    kind = {"simple": "type0", "cipher": "huawei-cipher", "irreversible-cipher": "huawei-irreversible"}.get(ct[3])
                    if kind:
                        dev.password(kind, t)
        elif t.startswith("snmp-agent sys-info version"):
            vs = [x.lower() for x in tk[3:]]
            if "all" in vs:
                vs = ["v1", "v2c", "v3"]
            if "v1" in vs:
                dev.proto("snmpv1", "snmp-agent sys-info version v1", "snmp-version")
            if "v2c" in vs:
                dev.proto("snmpv2c", "snmp-agent sys-info version v2c", "snmp-version")
        elif t.startswith("snmp-agent community "):
            n_comm += 1
            access = tk[2] if len(tk) > 2 else "unspecified"
            dev.proto("snmpv2c", f"snmp-agent community #{n_comm} ({access})", "snmp-community", community="present", access=access)
        elif t.startswith("snmp-agent usm-user v3 ") and len(tk) >= 4:
            u = users.setdefault(tk[3], {"auth": None, "priv": None})
            low = [x.lower() for x in tk]
            if "authentication-mode" in low and low.index("authentication-mode") + 1 < len(low):
                u["auth"] = low[low.index("authentication-mode") + 1]
            if "privacy-mode" in low and low.index("privacy-mode") + 1 < len(low):
                u["priv"] = norm_snmp_priv([low[low.index("privacy-mode") + 1]])
        elif re.match(r"^local-user \S+ password (simple|cipher|irreversible-cipher)\b", t):
            kind = {"simple": "type0", "cipher": "huawei-cipher", "irreversible-cipher": "huawei-irreversible"}[tk[3]]
            dev.password(kind, f"local-user {tk[1]}")
        elif re.match(r"^ike proposal \d+$", t):
            _huawei_ike(dev, n, tk[2], v1=True)
        elif re.match(r"^ikev2 proposal \S+$", t):
            _huawei_ike(dev, n, tk[2], v1=False)
        elif re.match(r"^ipsec proposal \S+$", t):
            ctx = f"ipsec-proposal {tk[2]}"
            for c in n.children:
                ct = _tk(c)
                if len(ct) >= 3 and ct[0] in ("esp", "ah") and ct[1] == "encryption-algorithm":
                    add_enc(dev, ct[2], f"{ct[0]} encryption-algorithm {ct[2]}", ctx, proposal=tk[2])
                elif len(ct) >= 3 and ct[0] in ("esp", "ah") and ct[1] == "authentication-algorithm":
                    dev.mac_hmac(ct[2], f"{ct[0]} authentication-algorithm {ct[2]}", ctx, proposal=tk[2])
        elif re.match(r"^pfs dh-group\d+", t):
            add_group(dev, tk[1], f"pfs {tk[1]}", "pfs")
    for name, u in users.items():
        snmp_user_findings(dev, name, u["auth"], u["priv"], f"snmp-user {name}")
    _ntp(dev, tree)


def _huawei_ike(dev: Dev, node: INode, num: str, v1: bool) -> None:
    ctx = f"{'ike' if v1 else 'ikev2'}-proposal {num}"
    for c in node.children:
        ct = _tk(c)
        if not ct:
            continue
        if ct[0] == "encryption-algorithm" and len(ct) > 1:
            add_enc(dev, ct[1], f"encryption-algorithm {ct[1]}", ctx, proposal=num)
        elif ct[0] in ("authentication-algorithm", "integrity-algorithm") and len(ct) > 1:
            for h in ct[1:]:
                dev.hash(h.replace("hmac-", ""), f"{ct[0]} {h}", ctx, proposal=num)
        elif ct[0] == "dh" and len(ct) > 1:
            add_group(dev, ct[1], f"dh {ct[1]}", ctx, proposal=num)
    if v1:
        dev.proto("ikev1", "ike proposal (IKEv1)", "ike", proposals=[num])
