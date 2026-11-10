"""Tree/keyword-structured platforms for the netdev collector (not a collector itself).

Junos (curly-brace and `set` formats), FortiOS, PAN-OS, MikroTik RouterOS and
F5 BIG-IP.  Junos/PAN-OS/F5 arrive as token paths (`confparse`), FortiOS as
config/edit sections, MikroTik as parsed `/section verb key=value` statements.
Password, community and key values are never copied: only storage types and
algorithm names.
"""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional, Tuple

from .. import names
from ..ciphers import PROTO_ORDER, cipher_string_uses, normalize_proto, proto_range, protocol_use, resolve_protocol_expr
from ..confparse import FSection, Path, has_path, paths_under, tokenize
from ._netdev_common import Dev, add_enc, add_group, add_ssh_algos, snmp_user_findings


def _group_by_name(paths: List[Path], prefix: Path) -> Dict[str, List[Path]]:
    out: Dict[str, List[Path]] = {}
    for tail in paths_under(paths, prefix):
        if len(tail) > 1:
            out.setdefault(tail[0], []).append(tail[1:])
        else:
            out.setdefault(tail[0], [])
    return out


def _clean(vals: Iterable[str]) -> List[str]:
    return [v for v in vals if v not in ("[", "]")]


def _proto_uses(dev: Dev, protos: Iterable[str], context: str, **extra) -> None:
    for p in protos:
        u = protocol_use(p, **extra)
        u.context = context
        dev.add(u)


_HMAC_JUNOS = re.compile(r"hmac-(md5|sha1|sha-?256|sha-?384|sha-?512)")


# ---------------------------------------------------------------------------
# Junos
# ---------------------------------------------------------------------------

def _junos_pw(val: str) -> str:
    if val.startswith("$1$"):
        return "junos-1"
    if val.startswith("$9$"):
        return "junos-9"
    if val.startswith("$5$"):
        return "sha256crypt"
    if val.startswith("$6$"):
        return "sha512crypt"
    if val.startswith("$2"):
        return "bcrypt"
    return "junos-other"


def run_junos(dev: Dev, P: List[Path]) -> None:
    if has_path(P, ("system", "services", "telnet")):
        dev.proto("telnet", "system services telnet", "management")
    if has_path(P, ("system", "services", "ftp")):
        dev.proto("ftp", "system services ftp", "management")
    if has_path(P, ("system", "services", "web-management", "http")):
        dev.proto("http-mgmt", "system services web-management http", "management")
    if has_path(P, ("system", "services", "xnm-clear-text")):
        dev.proto("http-mgmt", "system services xnm-clear-text", "management")
    for tail in paths_under(P, ("system", "services", "ssh")):
        key, vals = tail[0], _clean(tail[1:])
        if key == "protocol-version" and any(v.lower() == "v1" for v in vals):
            dev.proto("ssh1", "system services ssh protocol-version v1", "ssh")
        elif key == "ciphers":
            add_ssh_algos(dev, "cipher", vals, direction="server")
        elif key == "macs":
            add_ssh_algos(dev, "mac", vals, direction="server")
        elif key == "key-exchange":
            add_ssh_algos(dev, "kex", vals, direction="server")
        elif key == "hostkey-algorithm":
            add_ssh_algos(dev, "hostkey", vals, direction="server")
    # SNMP
    for i, (name, tails) in enumerate(_group_by_name(P, ("snmp", "community")).items(), 1):
        flat = [x for t in tails for x in t]
        access = "rw" if "read-write" in flat else "ro"
        acl = any(t and t[0] in ("clients", "client-list-name") for t in tails)
        dev.proto("snmpv2c", f"snmp community #{i} ({access})", "snmp-community", community="present", access=access, acl=acl)
    for p in P:
        if p[:5] == ("snmp", "v3", "vacm", "security-to-group", "security-model") and len(p) > 5:
            if p[5] in ("v1", "v2c"):
                dev.proto("snmpv1" if p[5] == "v1" else "snmpv2c", f"snmp vacm security-model {p[5]}", "snmp-vacm")
    for user, tails in _group_by_name(P, ("snmp", "v3", "usm", "local-engine", "user")).items():
        keys = {t[0] for t in tails if t}
        auth = next((a for k, a in (("authentication-md5", "md5"), ("authentication-sha", "sha"), ("authentication-sha1", "sha"),
                                    ("authentication-sha256", "sha-256"), ("authentication-sha384", "sha-384"),
                                    ("authentication-sha512", "sha-512")) if k in keys), None)
        priv = next((a for k, a in (("privacy-des", "des"), ("privacy-3des", "3des"), ("privacy-aes128", "aes128"),
                                    ("privacy-aes192", "aes192"), ("privacy-aes256", "aes256")) if k in keys), None)
        snmp_user_findings(dev, user, auth, priv, f"snmp-user {user}")
    # IKE / IPsec
    for name, tails in _group_by_name(P, ("security", "ike", "proposal")).items():
        ctx = f"ike-proposal {name}"
        for t in tails:
            k, v = t[0], (t[1] if len(t) > 1 else None)
            if v is None:
                continue
            if k == "authentication-algorithm":
                dev.hash(v.replace("hmac-", ""), f"authentication-algorithm {v}", ctx, proposal=name)
            elif k == "dh-group":
                add_group(dev, v, f"dh-group {v}", ctx, proposal=name)
            elif k == "encryption-algorithm":
                add_enc(dev, v, f"encryption-algorithm {v}", ctx, proposal=name)
    gws = _group_by_name(P, ("security", "ike", "gateway"))
    v1_gws = [g for g, tails in gws.items()
              if next((t[1] for t in tails if t[0] == "version" and len(t) > 1), "v1-only") != "v2-only"]
    aggressive = any(len(t) > 1 and t[0] == "mode" and t[1] == "aggressive"
                     for tails in _group_by_name(P, ("security", "ike", "policy")).values() for t in tails)
    if v1_gws:
        dev.proto("ikev1", "security ike gateway (IKEv1)", "ike", gateways=v1_gws)
        if aggressive:
            dev.proto("ikev1-aggressive", "security ike policy mode aggressive", "ike")
    for name, tails in _group_by_name(P, ("security", "ipsec", "proposal")).items():
        ctx = f"ipsec-proposal {name}"
        for t in tails:
            k, v = t[0], (t[1] if len(t) > 1 else None)
            if v is None:
                continue
            if k == "encryption-algorithm":
                add_enc(dev, v, f"encryption-algorithm {v}", ctx, proposal=name)
            elif k == "authentication-algorithm":
                m = _HMAC_JUNOS.match(v)
                if m:
                    dev.mac_hmac(m.group(1).replace("-", ""), f"authentication-algorithm {v}", ctx, proposal=name)
    for name, tails in _group_by_name(P, ("security", "ipsec", "policy")).items():
        for t in tails:
            if t[:2] == ("perfect-forward-secrecy", "keys") and len(t) > 2:
                add_group(dev, t[2], f"perfect-forward-secrecy keys {t[2]}", "pfs", policy=name)
    # secrets
    for p in P:
        if p[:3] == ("system", "login", "user") and len(p) >= 7 and p[4] == "authentication" and p[5] == "encrypted-password":
            dev.password(_junos_pw(p[6]), f"user {p[3]}")
        elif p[:3] == ("system", "root-authentication", "encrypted-password") and len(p) > 3:
            dev.password(_junos_pw(p[3]), "root-authentication")
        elif p[:3] == ("system", "ntp", "authentication-key") and len(p) >= 6 and p[4] == "type" and p[5].lower() == "md5":
            dev.hash("md5", f"ntp authentication-key {p[3]} md5", "ntp-auth")


# ---------------------------------------------------------------------------
# FortiOS
# ---------------------------------------------------------------------------

def _forti_proposal(dev: Dev, tok: str, ctx: str, phase2: bool, **extra) -> None:
    enc, _, h = tok.partition("-")
    add_enc(dev, enc, f"proposal {tok}", ctx, **extra)
    h = re.sub(r"^prf", "", h.split("-")[0]) if h else ""
    if h and h != "null":
        if phase2:
            dev.mac_hmac(h, f"proposal {tok}", ctx, **extra)
        else:
            dev.hash(h, f"proposal {tok}", ctx, **extra)


def run_forti(dev: Dev, secs: List[FSection]) -> None:
    def by(cfg: str) -> List[FSection]:
        return [s for s in secs if s.config == cfg]

    for g in by("system global"):
        if g.edit is not None:
            continue
        if g.first("admin-ssh-v1") == "enable":
            dev.proto("ssh1", "admin-ssh-v1 enable", "ssh")
        if g.first("admin-telnet") == "enable":
            dev.proto("telnet", "admin-telnet enable", "management")
        sc = g.first("strong-crypto")
        if sc:
            dev.attrs["strong_crypto"] = sc == "enable"
        if sc == "disable":
            _proto_uses(dev, ["TLSv1", "TLSv1.1"], "strong-crypto-disabled", source="strong-crypto-disabled")
            for n in ("DES-CBC3-SHA", "RC4-SHA"):
                dev.add(names.tls_cipher_suite(n, negotiated=None, extra={"source": "strong-crypto-disabled", "heuristic": True}))
        if g.get("admin-https-ssl-versions"):
            _proto_uses(dev, [p for p in (normalize_proto(v) for v in g.get("admin-https-ssl-versions")) if p],
                        "admin-https-ssl-versions", directive="admin-https-ssl-versions")
        mv = g.first("ssl-min-proto-version")
        if mv:
            p = normalize_proto(mv)
            if p:
                _proto_uses(dev, proto_range(p, "TLSv1.2" if p != "TLSv1.3" else "TLSv1.3"), "ssl-min-proto-version",
                            directive="ssl-min-proto-version", min=mv)
        for key, kind in (("ssh-kex-algo", "kex"), ("ssh-enc-algo", "cipher"), ("ssh-mac-algo", "mac"), ("ssh-hsk-algo", "hostkey")):
            if g.get(key):
                add_ssh_algos(dev, kind, [v.split("@")[0] if kind == "kex" and v.startswith("curve25519") else v for v in g.get(key)],
                              direction="server")
    for s in by("system interface"):
        for a in s.get("allowaccess") or []:
            if a == "telnet":
                dev.proto("telnet", f"interface {s.edit} allowaccess telnet", "management")
            elif a == "http":
                dev.proto("http-mgmt", f"interface {s.edit} allowaccess http", "management")
    for i, s in enumerate((x for x in by("system snmp community") if x.edit is not None), 1):
        if s.first("status", "enable") == "disable":
            continue
        v1 = s.first("query-v1-status", "enable") == "enable" or s.first("trap-v1-status", "enable") == "enable"
        v2 = s.first("query-v2c-status", "enable") == "enable" or s.first("trap-v2c-status", "enable") == "enable"
        if v1:
            dev.proto("snmpv1", f"snmp community #{i} v1", "snmp-community", community="present")
        if v2:
            dev.proto("snmpv2c", f"snmp community #{i} v2c", "snmp-community", community="present")
    for s in by("system snmp user"):
        if s.edit is None:
            continue
        lvl = s.first("security-level", "no-auth-no-priv")
        user = s.edit
        if lvl == "no-auth-no-priv":
            snmp_user_findings(dev, user, None, None, f"snmp-user {user}", None if s.first("security-level") else "default")
        else:
            auth = s.first("auth-proto", "sha1")
            priv = None
            if lvl == "auth-priv":
                pv = s.first("priv-proto", "aes")
                priv = {"aes": "aes128", "aes256": "aes256", "aes256cisco": "aes256", "des": "des"}.get(pv, pv)
            snmp_user_findings(dev, user, auth, priv, f"snmp-user {user}")
    for s in by("vpn ipsec phase1-interface") + by("vpn ipsec phase1"):
        if s.edit is None:
            continue
        name, ctx = s.edit, f"phase1 {s.edit}"
        ver = s.first("ike-version", "1")
        if ver == "1":
            dev.proto("ikev1", f"phase1 {name} ike-version 1", "ike", **({} if s.first("ike-version") else {"source": "default"}))
            if s.first("mode") == "aggressive":
                dev.proto("ikev1-aggressive", f"phase1 {name} mode aggressive", "ike")
        for tok in s.get("proposal") or []:
            _forti_proposal(dev, tok, ctx, False, phase1=name)
        for g in s.get("dhgrp") or []:
            add_group(dev, g, f"dhgrp {g}", ctx, phase1=name)
    for s in by("vpn ipsec phase2-interface") + by("vpn ipsec phase2"):
        if s.edit is None:
            continue
        name, ctx = s.edit, f"phase2 {s.edit}"
        for tok in s.get("proposal") or []:
            _forti_proposal(dev, tok, ctx, True, phase2=name)
        if s.first("pfs", "enable") != "disable":
            for g in s.get("dhgrp") or []:
                add_group(dev, g, f"dhgrp {g}", f"pfs {name}", phase2=name)
    for s in by("vpn ssl settings"):
        mv = s.first("ssl-min-proto-ver") or s.first("ssl-min-proto-version")
        if mv:
            p = normalize_proto(mv)
            if p:
                _proto_uses(dev, proto_range(p, "TLSv1.2" if p != "TLSv1.3" else "TLSv1.3"), "ssl-vpn-min-proto",
                            directive="ssl-min-proto-ver", min=mv)
        for key, proto in (("tlsv1-0", "TLSv1"), ("tlsv1-1", "TLSv1.1"), ("sslv3", "SSLv3")):
            if s.first(key) == "enable":
                _proto_uses(dev, [proto], "ssl-vpn-protocol", directive=key)
        alg = s.first("algorithm")
        if alg in ("low", "medium"):
            for n in (["RC4-SHA", "DES-CBC3-SHA"] if alg == "low" else ["RC4-SHA"]):
                dev.add(names.tls_cipher_suite(n, negotiated=None, extra={"source": f"ssl-vpn-algorithm-{alg}", "heuristic": True}))
    for s in by("system admin"):
        pw = s.get("password")
        if s.edit is not None and pw and len(pw) >= 2 and pw[0] == "ENC":
            kind = {"AK1": "sha1crypt", "SH2": "fortios-sh2", "PBK": "pbkdf2"}.get(pw[1][:3])
            if kind:
                dev.password(kind, f"admin {s.edit}")


# ---------------------------------------------------------------------------
# PAN-OS
# ---------------------------------------------------------------------------

_KV_KEYS = {"hash", "dh-group", "encryption", "authentication", "lifetime", "esp", "ah"}


def _kv(tail: Tuple[str, ...]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    key: Optional[str] = None
    for t in tail:
        if t in ("[", "]"):
            continue
        if t in _KV_KEYS:
            if t not in ("esp", "ah"):
                key = t
                out.setdefault(key, [])
        elif key:
            out[key].append(t)
    return out


def _panos_pw(val: str) -> Optional[str]:
    if val.startswith("$1$"):
        return "md5crypt"
    if val.startswith(("$5$", "$6$")):
        return "sha-crypt"
    return None


def run_panos(dev: Dev, P: List[Path]) -> None:
    base = ("deviceconfig", "system", "ssh")
    for kind, key in (("cipher", "ciphers"), ("mac", "mac"), ("kex", "kex")):
        for tail in paths_under(P, base + (key,)):
            add_ssh_algos(dev, kind, _clean(tail[1:]), direction="server")
    for tail in paths_under(P, base + ("default-hostkey",)):
        toks = _clean(tail)
        if "key-type" in toks:
            rest = toks[toks.index("key-type") + 1:]
            if len(rest) >= 2 and rest[1].isdigit():
                if rest[0].upper() == "RSA":
                    dev.pubkey("rsa", int(rest[1]), f"default-hostkey RSA {rest[1]}")
                elif rest[0].upper() == "ECDSA":
                    dev.pubkey("ec", int(rest[1]), f"default-hostkey ECDSA {rest[1]}", curve=f"p-{rest[1]}")
    for name, tails in _group_by_name(P, ("shared", "ssl-tls-service-profile")).items():
        ps = {}
        for t in tails:
            if t[:1] == ("protocol-settings",) and len(t) >= 3:
                ps.setdefault(t[1], t[2])
        lo = normalize_proto(ps.get("min-version", "")) if "min-version" in ps else None
        hi = None if ps.get("max-version") in (None, "max") else normalize_proto(ps["max-version"])
        if lo or hi:
            _proto_uses(dev, proto_range(lo or "TLSv1", hi or "TLSv1.3"), f"ssl-tls-service-profile {name}", profile=name)
        for key, suite in (("enc-algo-3des", "DES-CBC3-SHA"), ("enc-algo-rc4", "RC4-SHA")):
            if ps.get(key) == "yes":
                dev.add(names.tls_cipher_suite(suite, negotiated=None, extra={"profile": name, "directive": key}))
    ike = ("network", "ike", "crypto-profiles")
    for name, tails in _group_by_name(P, ike + ("ike-crypto-profiles",)).items():
        kv = _kv(tuple(x for t in tails for x in t))
        ctx = f"ike-crypto-profile {name}"
        for h in kv.get("hash", []):
            dev.hash(h, f"hash {h}", ctx, profile=name)
        for g in kv.get("dh-group", []):
            add_group(dev, g, f"dh-group {g}", ctx, profile=name)
        for e in kv.get("encryption", []):
            add_enc(dev, e, f"encryption {e}", ctx, profile=name)
    for name, tails in _group_by_name(P, ike + ("ipsec-crypto-profiles",)).items():
        kv = _kv(tuple(x for t in tails for x in t))
        ctx = f"ipsec-crypto-profile {name}"
        for e in kv.get("encryption", []):
            add_enc(dev, e, f"encryption {e}", ctx, profile=name)
        for a in kv.get("authentication", []):
            if a != "none":
                dev.mac_hmac(a, f"authentication {a}", ctx, profile=name)
        for g in kv.get("dh-group", []):
            add_group(dev, g, f"dh-group {g}", "pfs", profile=name)
    v1 = []
    aggressive = False
    for gw, tails in _group_by_name(P, ("network", "ike", "gateway")).items():
        flat = [x for t in tails for x in t]
        ver = None
        if "version" in flat:
            ver = flat[flat.index("version") + 1] if flat.index("version") + 1 < len(flat) else None
        if ver == "ikev1" or (ver is None and "ikev1" in flat):
            v1.append(gw)
        if "aggressive" in flat:
            aggressive = True
            if gw not in v1:
                v1.append(gw)
    if v1:
        dev.proto("ikev1", "network ike gateway (IKEv1)", "ike", gateways=v1)
        if aggressive:
            dev.proto("ikev1-aggressive", "network ike gateway exchange-mode aggressive", "ike")
    for p in P:
        if p[:5] == ("deviceconfig", "system", "snmp-setting", "access-setting", "version") and len(p) > 5 and p[5] == "v2c":
            dev.proto("snmpv2c", "snmp-setting access-setting version v2c", "snmp-community", community="present")
        if p[:4] == ("deviceconfig", "system", "service", "disable-telnet") and len(p) > 4 and p[4] == "no":
            dev.proto("telnet", "deviceconfig system service disable-telnet no", "management")
        if p[:4] == ("deviceconfig", "system", "service", "disable-http") and len(p) > 4 and p[4] == "no":
            dev.proto("http-mgmt", "deviceconfig system service disable-http no", "management")
        if p[:2] == ("mgt-config", "users") and len(p) >= 5 and p[3] == "phash":
            k = _panos_pw(p[4])
            if k:
                dev.password(k, f"admin {p[2]}")


# ---------------------------------------------------------------------------
# MikroTik RouterOS
# ---------------------------------------------------------------------------

Stmt = Tuple[str, str, List[str], Dict[str, str]]


def parse_routeros(text: str) -> List[Stmt]:
    """RouterOS export -> [(section, verb, positional args, key=value dict)]."""
    joined: List[str] = []
    buf = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.endswith("\\"):
            buf += line[:-1].strip() + " "
            continue
        joined.append(buf + line.strip())
        buf = ""
    if buf:
        joined.append(buf)
    out: List[Stmt] = []
    section = ""
    for line in joined:
        if not line or line.startswith("#"):
            continue
        if line.startswith("/"):
            toks = tokenize(line)
            sec_toks = []
            i = 0
            while i < len(toks) and (toks[i].startswith("/") or (i > 0 and sec_toks and toks[i] not in ("set", "add", "remove", "enable", "disable", "print", "export") and "=" not in toks[i] and not toks[i].startswith("["))):
                sec_toks.append(toks[i].lstrip("/") if i == 0 else toks[i])
                i += 1
            section = "/" + " ".join(sec_toks)
            line = " ".join(f'"{t}"' if " " in t else t for t in toks[i:])
            if not line:
                continue
        toks = tokenize(line)
        if not toks:
            continue
        verb = toks[0]
        pos = [t for t in toks[1:] if "=" not in t and t not in ("[", "]", "find")]
        kv = {t.split("=", 1)[0]: t.split("=", 1)[1] for t in toks[1:] if "=" in t and not t.startswith("[")}
        out.append((section, verb, pos, kv))
    return out


def _csv(v: Optional[str]) -> List[str]:
    return [x for x in (v or "").split(",") if x]


def run_mikrotik(dev: Dev, text: str) -> None:
    stmts = parse_routeros(text)
    sections = {s for s, _, _, _ in stmts}
    # ssh
    strong = None
    for sec, verb, pos, kv in stmts:
        if sec == "/ip ssh" and "strong-crypto" in kv:
            strong = kv["strong-crypto"]
    services: Dict[str, bool] = {}
    for sec, verb, pos, kv in stmts:
        if sec == "/ip service":
            name = pos[0] if pos else None
            if name and verb == "set" and "disabled" in kv:
                services[name] = kv["disabled"] == "yes"
            elif name and verb == "disable":
                services[name] = True
            elif name and verb == "enable":
                services[name] = False
    have_service = "/ip service" in sections
    if strong == "no" or (strong is None and have_service and not services.get("ssh", False)):
        src = "strong-crypto-no" if strong == "no" else "default"
        add_ssh_algos(dev, "kex", ["diffie-hellman-group1-sha1"], source=src, direction="server")
        add_ssh_algos(dev, "cipher", ["3des-cbc"], source=src, direction="server")
        add_ssh_algos(dev, "mac", ["hmac-sha1"], source=src, direction="server")
    if have_service or services:
        for svc, alg in (("telnet", "telnet"), ("ftp", "ftp"), ("www", "http-mgmt")):
            if not services.get(svc, False):
                dev.proto(alg, f"/ip service {svc} enabled", "management", **({} if svc in services else {"source": "default"}))
    # snmp
    snmp_on = any(sec == "/snmp" and verb == "set" and kv.get("enabled") == "yes" for sec, verb, _, kv in stmts)
    n = 0
    if snmp_on:
        for sec, verb, pos, kv in stmts:
            if sec == "/snmp community" and verb in ("add", "set"):
                sec_level = kv.get("security", "none")
                if sec_level in ("authorized", "private"):
                    auth = kv.get("authentication-protocol", "MD5").lower()
                    priv = kv.get("encryption-protocol", "DES").lower() if sec_level == "private" else None
                    name = kv.get("name", "user")
                    snmp_user_findings(dev, name, auth, priv, f"snmp-user {name}")
                else:
                    n += 1
                    access = "rw" if kv.get("write-access") == "yes" else "ro"
                    dev.proto("snmpv2c", f"snmp community #{n} ({access})", "snmp-community", community="present", access=access)
    # ipsec
    for sec, verb, pos, kv in stmts:
        if verb not in ("add", "set"):
            continue
        name = kv.get("name") or "default"
        if sec == "/ip ipsec proposal":
            ctx = f"ipsec-proposal {name}"
            for e in _csv(kv.get("enc-algorithms")):
                add_enc(dev, e, f"enc-algorithms {e}", ctx, proposal=name)
            for a in _csv(kv.get("auth-algorithms")):
                if a != "null":
                    dev.mac_hmac(a, f"auth-algorithms {a}", ctx, proposal=name)
            pg = kv.get("pfs-group")
            if pg and pg != "none":
                add_group(dev, pg, f"pfs-group {pg}", "pfs", proposal=name)
        elif sec == "/ip ipsec profile":
            ctx = f"ipsec-profile {name}"
            for e in _csv(kv.get("enc-algorithm")):
                add_enc(dev, e, f"enc-algorithm {e}", ctx, profile=name)
            if kv.get("hash-algorithm"):
                dev.hash(kv["hash-algorithm"], f"hash-algorithm {kv['hash-algorithm']}", ctx, profile=name)
            for g in _csv(kv.get("dh-group")):
                add_group(dev, g, f"dh-group {g}", ctx, profile=name)
        elif sec == "/ip ipsec peer" and kv.get("exchange-mode"):
            mode = kv["exchange-mode"]
            if mode in ("main", "base", "main-l2tp", "aggressive"):
                dev.proto("ikev1", f"ipsec peer exchange-mode {mode}", "ike")
            if mode == "aggressive":
                dev.proto("ikev1-aggressive", "ipsec peer exchange-mode aggressive", "ike")


# ---------------------------------------------------------------------------
# F5 BIG-IP
# ---------------------------------------------------------------------------

_F5_OPTION_PROTO = {"no-sslv3": "SSLv3", "no-tlsv1": "TLSv1", "no-tlsv1.1": "TLSv1.1", "no-tlsv1.2": "TLSv1.2", "no-tlsv1.3": "TLSv1.3"}


def run_f5(dev: Dev, P: List[Path]) -> None:
    for kind in ("client-ssl", "server-ssl"):
        for name, tails in _group_by_name(P, ("ltm", "profile", kind)).items():
            ctx = f"{kind} {name}"
            opts: Optional[List[str]] = None
            for t in tails:
                k = t[0]
                if k == "ciphers" and len(t) > 1:
                    info = cipher_string_uses(t[1], negotiated=None, extra={"profile": name, "profile_type": kind})
                    for u in info.uses:
                        dev.add(u)
                    if info.flags:
                        dev.attrs.setdefault("cipher_string_flags", {})[ctx] = sorted(info.flags)
                    dev.attrs.setdefault("cipher_strings", {})[ctx] = t[1]
                elif k in ("options", "tm-options"):
                    opts = (opts or []) + _clean(t[1:])
            if opts is not None:
                disabled = {_F5_OPTION_PROTO[o] for o in opts if o in _F5_OPTION_PROTO}
                _proto_uses(dev, [p for p in PROTO_ORDER[1:] if p not in disabled], ctx, profile=name, profile_type=kind)
    for tail in paths_under(P, ("sys", "sshd", "include")):
        for line in "\n".join(tail).replace("\\n", "\n").splitlines():
            parts = line.split(None, 1)
            if len(parts) < 2:
                continue
            key, val = parts[0].lower(), re.split(r"[,\s]+", parts[1].strip())
            if key == "ciphers":
                add_ssh_algos(dev, "cipher", val, direction="server")
            elif key == "macs":
                add_ssh_algos(dev, "mac", val, direction="server")
            elif key == "kexalgorithms":
                add_ssh_algos(dev, "kex", val, direction="server")
            elif key == "hostkeyalgorithms":
                add_ssh_algos(dev, "hostkey", val, direction="server")
            elif key == "protocol" and "1" in val:
                dev.proto("ssh1", "sys sshd include Protocol 1", "ssh")
    for tail in paths_under(P, ("sys", "httpd", "ssl-protocol")):
        _proto_uses(dev, resolve_protocol_expr(" ".join(tail)), "sys httpd ssl-protocol", directive="sys httpd ssl-protocol")
    for tail in paths_under(P, ("sys", "httpd", "ssl-ciphersuite")):
        for u in cipher_string_uses(" ".join(tail), negotiated=None, extra={"directive": "sys httpd ssl-ciphersuite"}).uses:
            dev.add(u)
    if has_path(P, ("sys", "snmp", "communities")):
        dev.proto("snmpv2c", "sys snmp communities", "snmp-community", community="present")
    for user, tails in _group_by_name(P, ("sys", "snmp", "users")).items():
        flat = [x for t in tails for x in t]
        auth = flat[flat.index("auth-protocol") + 1] if "auth-protocol" in flat and flat.index("auth-protocol") + 1 < len(flat) else None
        priv = flat[flat.index("privacy-protocol") + 1] if "privacy-protocol" in flat and flat.index("privacy-protocol") + 1 < len(flat) else None
        snmp_user_findings(dev, user, auth, priv, f"snmp-user {user}")
