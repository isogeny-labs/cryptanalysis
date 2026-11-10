"""Kerberos collector: krb5.conf, KDC config, keytabs, ticket caches, Samba, AD exports.

Sources (all read-only; key material is never read into reports):

* ``/etc/krb5.conf`` (+ ``include`` / ``includedir``, ``/etc/krb5.conf.d/*`` and
  ``$KRB5_CONFIG`` when scanning the live root) -> one KERBEROS_CONFIG asset per
  file.  Enctype lists, ``allow_weak_crypto`` and PKINIT anchors are recorded;
  when no list is configured the library defaults for the detected MIT krb5
  version are recorded with ``extra["source"] == "default"``.
* KDC configs (``kdc.conf``): ``supported_enctypes`` / ``master_key_type``
  (role="kdc").
* Keytabs (``/etc/krb5.keytab``, ``$KRB5_KTNAME``, kadm5 keytabs,
  ``/etc/security/keytabs/*``, ``/etc/*.keytab``, ``~/*.keytab`` and
  ``--extra-path`` files ending ``.keytab``) -> KERBEROS_KEYTAB asset per file,
  one ENCTYPE use per distinct (principal, enctype).  Only the key *length* is
  parsed, never the key bytes.
* Credential caches via ``klist -e`` (live root only) -> KERBEROS_TICKET assets
  with session-key and ticket enctypes.  Only principal names and enctypes are
  kept.
* ``/etc/samba/smb.conf`` (role="samba"): ``kerberos encryption types``, SMB1
  minimum protocol, NTLMv1/LM switches.
* Offline Active Directory export (``ctx.options["ad_enctype_export"]``): a CSV
  or JSON file with ``samAccountName`` and ``msDS-SupportedEncryptionTypes``.
  Create it on a domain controller / admin workstation with::

      Get-ADObject -LDAPFilter "(|(objectClass=user)(objectClass=computer))" `
        -Properties sAMAccountName,msDS-SupportedEncryptionTypes |
        Select-Object sAMAccountName,@{n='msDS-SupportedEncryptionTypes';
          e={$_.'msDS-SupportedEncryptionTypes'}} |
        Export-Csv ad_enctypes.csv -NoTypeInformation

  The bitmask is decoded as 0x1 DES_CBC_CRC, 0x2 DES_CBC_MD5, 0x4 RC4_HMAC,
  0x8 AES128, 0x10 AES256, 0x20 AES256 session keys.  A value of 0 or a missing
  attribute means "domain default", which older domain controllers treat as RC4
  (recorded as an assumed RC4 use).
"""

from __future__ import annotations

import csv
import glob
import io
import json
import os
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

from . import register
from ._confparse import (blocks, ctx_glob, file_attrs, first, is_root_host, logical, parse_braces, real,
                         strip_quotes, values)
from .base import Collector, ScanContext
from .. import keytab, names, util
from ..model import Asset, AssetKind, CryptoUse, Primitive

ENCTYPE_SETTINGS = ("default_tgs_enctypes", "default_tkt_enctypes", "permitted_enctypes")

DEFAULTS_MIT_118 = ["aes256-cts-hmac-sha1-96", "aes128-cts-hmac-sha1-96", "aes256-cts-hmac-sha384-192",
                    "aes128-cts-hmac-sha256-128", "des3-cbc-sha1", "arcfour-hmac-md5",
                    "camellia256-cts-cmac", "camellia128-cts-cmac"]
DEFAULTS_MIT_121 = [e for e in DEFAULTS_MIT_118 if e not in ("des3-cbc-sha1", "arcfour-hmac-md5")]

_SMB1 = {"smb1", "nt1", "nt lm 0.12", "lanman1", "lanman2", "core", "coreplus"}

AD_BITS = ((0x1, 1, "DES_CBC_CRC"), (0x2, 3, "DES_CBC_MD5"), (0x4, 23, "RC4_HMAC"),
           (0x8, 17, "AES128_CTS_HMAC_SHA1_96"), (0x10, 18, "AES256_CTS_HMAC_SHA1_96"))


# ---------------------------------------------------------------------------
# Pure helpers (unit-tested)
# ---------------------------------------------------------------------------

def enctype_uses(value: str, context: str, **extra) -> List[CryptoUse]:
    """Turn 'aes256-cts -des3 arcfour-hmac' into ENCTYPE uses (negations flagged)."""
    out: List[CryptoUse] = []
    for tok in re.split(r"[\s,]+", value.strip()):
        if not tok:
            continue
        u = names.krb_enctype(tok)
        u.context = context
        u.extra.update(extra)
        out.append(u)
    return out


def parse_klist(text: str) -> List[Dict[str, object]]:
    """Parse `klist -e` output into caches: {cache, principal, tickets:[{service,skey,tkt}]}."""
    caches: List[Dict[str, object]] = []
    cur: Optional[Dict[str, object]] = None
    service: Optional[str] = None
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        low = s.lower()
        if low.startswith(("ticket cache:", "credentials cache:")):
            cur = {"cache": s.split(":", 1)[1].strip(), "principal": None, "tickets": []}
            caches.append(cur)
            service = None
            continue
        if cur is None:
            cur = {"cache": "default", "principal": None, "tickets": []}
            caches.append(cur)
        if low.startswith(("default principal:", "principal:")):
            cur["principal"] = s.split(":", 1)[1].strip()
            continue
        m = re.search(r"Etype \(skey, tkt\):\s*([^,]+?)\s*,\s*(\S+)", s)
        if m:
            def clean(x: str) -> str:
                return re.sub(r"^DEPRECATED:", "", x.strip())
            cur["tickets"].append({"service": service, "skey": clean(m.group(1)), "tkt": clean(m.group(2))})
            service = None
            continue
        m = re.match(r"Etype:\s*(\S+)", s)           # Heimdal: single etype line
        if m:
            e = re.sub(r"^DEPRECATED:", "", m.group(1)).rstrip(",")
            cur["tickets"].append({"service": service, "skey": e, "tkt": e})
            service = None
            continue
        if not line[0].isspace() and "valid starting" not in low and "issued" not in low and len(s.split()) >= 3:
            service = s.split()[-1]
    return caches


def decode_ad_enctypes(value: Optional[int]) -> Tuple[List[Tuple[int, str]], bool, int]:
    """Decode msDS-SupportedEncryptionTypes -> ([(etype_id, label)], defaulted, other_flags)."""
    v = value or 0
    if v & 0x3F == 0:
        return [(23, "RC4_HMAC (domain default)")], True, v & ~0x3F
    out = [(eid, label) for bit, eid, label in AD_BITS if v & bit]
    if v & 0x20:
        out.append((18, "AES256_CTS_HMAC_SHA1_96_SK"))
    return out, False, v & ~0x3F


def _parse_int(s: object) -> Optional[int]:
    if s is None:
        return None
    if isinstance(s, int):
        return s
    t = str(s).strip()
    if not t:
        return None
    try:
        return int(t, 16) if t.lower().startswith("0x") else int(t)
    except ValueError:
        return None


def read_ad_export(path: str) -> Tuple[List[Tuple[str, Optional[int], str]], List[str]]:
    """Read the CSV/JSON export -> ([(account, value|None, raw_value_text)], errors)."""
    raw = util.read_bytes(path)
    if raw is None:
        return [], [f"cannot read AD export {path}"]
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16", "replace")
    else:
        text = raw.decode("utf-8-sig", "replace")
    rows: List[Dict[str, object]] = []
    errors: List[str] = []
    stripped = text.lstrip()
    if stripped[:1] in "[{":
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                for key in ("accounts", "value", "objects", "items"):
                    if isinstance(data.get(key), list):
                        data = data[key]
                        break
                else:
                    data = [data]
            rows = [d for d in data if isinstance(d, dict)]
        except ValueError as e:
            errors.append(f"AD export is not valid JSON: {e}")
    else:
        lines = [l for l in text.splitlines() if not l.startswith("#TYPE")]
        rows = list(csv.DictReader(io.StringIO("\n".join(lines))))

    def pick(row: Dict[str, object], *cands: str):
        low = {str(k).lower().replace("-", "").replace("_", ""): v for k, v in row.items()}
        for c in cands:
            if c in low:
                return low[c]
        return None

    out: List[Tuple[str, Optional[int], str]] = []
    for row in rows:
        acct = pick(row, "samaccountname", "name", "account", "user")
        val = pick(row, "msdssupportedencryptiontypes", "supportedencryptiontypes", "enctypes")
        if acct is None:
            continue
        out.append((str(acct), _parse_int(val), "" if val is None else str(val)))
    return out, errors


# ---------------------------------------------------------------------------
# Collector
# ---------------------------------------------------------------------------

@register
class KerberosCollector(Collector):
    name = "kerberos"
    description = "Kerberos: krb5.conf, kdc.conf, keytabs, ticket caches, Samba, offline AD export"

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        assets: List[Asset] = []
        for step in (self._krb5_conf, self._kdc_conf, self._keytabs, self._ccaches, self._samba, self._ad_export):
            try:
                assets.extend(step(ctx))
            except Exception as e:            # one failing source must not hide the others
                ctx.warn(f"kerberos: {step.__name__} failed: {type(e).__name__}: {e}")
        return assets

    # -- krb5.conf ----------------------------------------------------------

    def _krb5_version(self, ctx: ScanContext) -> Tuple[Optional[Tuple[int, int]], str]:
        """(version, flavour) of the installed Kerberos; live root only."""
        forced = ctx.opt("krb5_version")
        if forced:
            m = re.search(r"(\d+)\.(\d+)", str(forced))
            if m:
                return (int(m.group(1)), int(m.group(2))), "mit"
        if not is_root_host(ctx):
            return None, "unknown"
        for argv in (["krb5-config", "--version"], ["klist", "-V"]):
            r = util.run_cmd(argv, timeout=ctx.cmd_timeout)
            text = (r.stdout + r.stderr)
            if not text.strip():
                continue
            if "heimdal" in text.lower():
                return None, "heimdal"
            m = re.search(r"(\d+)\.(\d+)", text)
            if m:
                return (int(m.group(1)), int(m.group(2))), "mit"
        return None, "unknown"

    def _krb5_files(self, ctx: ScanContext) -> List[str]:
        out: List[str] = []
        if is_root_host(ctx):
            env = os.environ.get("KRB5_CONFIG")
            if env:
                out.extend(p for p in env.split(":") if p)
        for p in ("/etc/krb5.conf", "/usr/local/etc/krb5.conf", "/etc/krb5/krb5.conf"):
            out.append(ctx.path(p))
        out.extend(f for f in ctx_glob(ctx, "/etc/krb5.conf.d/*") if os.path.isfile(f))
        return out

    def _krb5_conf(self, ctx: ScanContext) -> List[Asset]:
        assets: List[Asset] = []
        seen: Set[str] = set()
        queue: List[Tuple[str, int, Optional[str]]] = [(p, 0, None) for p in self._krb5_files(ctx)]
        any_list = False
        main_asset: Optional[Asset] = None
        while queue:
            path, depth, parent = queue.pop(0)
            rp = real(path)
            if rp in seen or not os.path.isfile(path):
                continue
            seen.add(rp)
            text = util.read_text(path)
            a = Asset(AssetKind.KERBEROS_CONFIG, f"krb5 config {logical(ctx, path)}", logical(ctx, path),
                      self.name, ctx.hostname, attributes={"role": "client", **file_attrs(path)})
            if parent:
                a.attributes["included_from"] = parent
            if text is None:
                a.errors.append(f"cannot read {path}")
                assets.append(a)
                continue
            tree, includes = parse_braces(text, bracket_sections=True, comment_chars="#;")
            any_list |= self._apply_krb5(a, tree)
            if includes:
                a.attributes["includes"] = [f"{d} {p}" for d, p in includes]
            for d, p in includes:
                if depth >= 5:
                    break
                target = ctx.path(p)
                if d == "include":
                    queue.append((target, depth + 1, logical(ctx, path)))
                elif d == "includedir" and os.path.isdir(target):
                    for fn in sorted(os.listdir(target)):
                        if re.fullmatch(r"[A-Za-z0-9_-]+|.*\.conf", fn):
                            queue.append((os.path.join(target, fn), depth + 1, logical(ctx, path)))
            assets.append(a)
            if main_asset is None:
                main_asset = a
        if assets and not any_list:
            self._add_defaults(ctx, assets[0])
        return assets

    def _apply_krb5(self, a: Asset, tree) -> bool:
        """Record crypto settings of one parsed krb5.conf; True if an enctype list was seen."""
        saw_list = False
        for _, ld in blocks(tree, "libdefaults"):
            for setting in ENCTYPE_SETTINGS:
                for v in values(ld, setting):
                    saw_list = True
                    for u in enctype_uses(v, setting):
                        a.add(u)
            for v in values(ld, "allow_weak_crypto"):
                a.add(CryptoUse(Primitive.CONFIG, "krb-allow-weak-crypto", raw=v, context="libdefaults"))
            for knob, enc in (("allow_rc4", "rc4-hmac"), ("allow_des3", "des3-cbc-sha1")):
                for v in values(ld, knob):
                    a.attributes[knob] = v
                    if v.lower() in ("true", "yes", "on", "1"):
                        u = names.krb_enctype(enc)
                        u.context = knob
                        u.extra["source"] = knob
                        a.add(u)
            for k in ("default_realm", "dns_lookup_kdc", "dns_lookup_realm", "ticket_lifetime", "renew_lifetime",
                      "forwardable", "rdns", "udp_preference_limit"):
                v = first(ld, k)
                if v is not None:
                    a.attributes.setdefault("libdefaults", {})[k] = v
            anchors = values(ld, "pkinit_anchors")
            if anchors:
                a.attributes.setdefault("pkinit_anchors", []).extend(anchors)
        realms = []
        for _, rb in blocks(tree, "realms"):
            for realm, body in blocks(rb):
                realms.append(realm)
                anchors = values(body, "pkinit_anchors")
                if anchors:
                    a.attributes.setdefault("pkinit_anchors", []).extend(f"{realm}: {x}" for x in anchors)
        if realms:
            a.attributes["realms"] = realms
        if blocks(tree, "capaths"):
            a.attributes["capaths"] = True
        return saw_list

    def _add_defaults(self, ctx: ScanContext, asset: Asset) -> None:
        ver, flavour = self._krb5_version(ctx)
        if flavour == "heimdal":
            asset.attributes["library_defaults"] = "heimdal (not inventoried)"
            return
        if ver is None:
            asset.attributes["library_defaults"] = "unknown (krb5 version not detected)"
            return
        lst = DEFAULTS_MIT_121 if ver >= (1, 21) else DEFAULTS_MIT_118
        asset.attributes["krb5_version"] = "%d.%d" % ver
        asset.attributes["library_defaults"] = "MIT krb5 %d.%d" % ver
        for e in lst:
            u = names.krb_enctype(e)
            u.context = "default_enctypes"
            u.extra["source"] = "default"
            asset.add(u)

    # -- KDC ----------------------------------------------------------------

    def _kdc_conf(self, ctx: ScanContext) -> List[Asset]:
        files: List[str] = []
        for p in ("/var/kerberos/krb5kdc/kdc.conf", "/etc/krb5kdc/kdc.conf", "/etc/heimdal-kdc/kdc.conf",
                  "/usr/local/var/krb5kdc/kdc.conf"):
            files.append(ctx.path(p))
        d = ctx.path("/var/lib/heimdal-kdc")
        if os.path.isdir(d):
            files.extend(sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".conf")))
        out: List[Asset] = []
        seen: Set[str] = set()
        for path in files:
            rp = real(path)
            if rp in seen or not os.path.isfile(path):
                continue
            seen.add(rp)
            a = Asset(AssetKind.KERBEROS_CONFIG, f"KDC config {logical(ctx, path)}", logical(ctx, path), self.name,
                      ctx.hostname, attributes={"role": "kdc", **file_attrs(path)})
            text = util.read_text(path)
            if text is None:
                a.errors.append(f"cannot read {path}")
                out.append(a)
                continue
            tree, _ = parse_braces(text, bracket_sections=True)
            self._apply_krb5(a, tree)            # Heimdal kdc.conf may carry [libdefaults] too
            realms, flags, mkt = [], {}, {}
            for _, rb in blocks(tree, "realms"):
                for realm, body in blocks(rb):
                    realms.append(realm)
                    for v in values(body, "supported_enctypes"):
                        for tok in v.split():
                            u = names.krb_enctype(tok.split(":")[0])
                            u.context = "supported_enctypes"
                            u.extra["realm"] = realm
                            a.add(u)
                    for v in values(body, "master_key_type"):
                        u = names.krb_enctype(v.strip())
                        u.context = "master_key_type"
                        u.extra["realm"] = realm
                        a.add(u)
                        mkt[realm] = v
                    f = first(body, "default_principal_flags")
                    if f is not None:
                        flags[realm] = f
            if realms:
                a.attributes["realms"] = realms
            if flags:
                a.attributes["default_principal_flags"] = flags
            if mkt:
                a.attributes["master_key_type"] = mkt
            out.append(a)
        return out

    # -- keytabs ------------------------------------------------------------

    def _keytab_paths(self, ctx: ScanContext) -> List[str]:
        cand: List[str] = []
        for p in ("/etc/krb5.keytab", "/var/kerberos/krb5kdc/kadm5.keytab", "/etc/krb5kdc/kadm5.keytab"):
            cand.append(ctx.path(p))
        if is_root_host(ctx):
            env = os.environ.get("KRB5_KTNAME", "")
            for part in env.split(","):
                part = part.strip()
                if part.startswith(("FILE:", "WRFILE:")):
                    part = part.split(":", 1)[1]
                elif ":" in part and not part.startswith("/"):
                    continue
                if part.startswith("/"):
                    cand.append(part)
        cand.extend(ctx_glob(ctx, "/etc/security/keytabs/*"))
        cand.extend(ctx_glob(ctx, "/etc/*.keytab"))
        if is_root_host(ctx):
            homes = util.home_dirs()
            for h in homes:
                cand.extend(sorted(glob.glob(os.path.join(h, "*.keytab"))))
        else:
            cand.extend(ctx_glob(ctx, "/home/*/*.keytab"))
            cand.extend(ctx_glob(ctx, "/root/*.keytab"))
        for ep in ctx.extra_paths:
            if os.path.isdir(ep):
                cand.extend(f for f in util.walk_files([ep], max_files=ctx.max_files) if f.endswith(".keytab"))
            elif ep.endswith(".keytab"):
                cand.append(ep)
        out, seen = [], set()
        for p in cand:
            rp = real(p)
            if rp not in seen and os.path.isfile(p):
                seen.add(rp)
                out.append(p)
        return out

    def _keytabs(self, ctx: ScanContext) -> List[Asset]:
        out: List[Asset] = []
        for path in self._keytab_paths(ctx):
            a = Asset(AssetKind.KERBEROS_KEYTAB, f"keytab {logical(ctx, path)}", logical(ctx, path), self.name,
                      ctx.hostname, attributes=file_attrs(path))
            data = util.read_bytes(path)
            if data is None:
                a.errors.append(f"cannot read keytab {path} (permission denied or too large)")
                out.append(a)
                continue
            try:
                res = keytab.parse_keytab_ex(data)
            except keytab.KeytabError as e:
                a.errors.append(f"not a keytab: {e}")
                out.append(a)
                continue
            entries = res.entries
            a.attributes["format_version"] = "0x%04x" % res.version
            a.attributes["entry_count"] = len(entries)
            principals = sorted({e.principal for e in entries})
            a.attributes["principals"] = principals[:50]
            if len(principals) > 50:
                a.attributes["principals_truncated"] = len(principals)
            a.attributes["kvnos"] = sorted({e.kvno for e in entries})
            if res.deleted_slots:
                a.attributes["deleted_slots"] = res.deleted_slots
            if res.truncated:
                a.errors.append("keytab is truncated or has trailing garbage; partial results")
            best: Dict[Tuple[str, int], Tuple[int, set]] = {}
            for e in entries:
                kv, kvs = best.get((e.principal, e.enctype), (-1, set()))
                kvs.add(e.kvno)
                best[(e.principal, e.enctype)] = (max(kv, e.kvno), kvs)
            for (princ, etype), (kv, kvs) in sorted(best.items()):
                u = names.krb_enctype(etype)
                u.context = "keytab-key"
                u.extra.update(principal=princ, kvno=kv)
                a.add(u)
            out.append(a)
        return out

    # -- credential caches --------------------------------------------------

    def _ccaches(self, ctx: ScanContext) -> List[Asset]:
        if not is_root_host(ctx) or util.which("klist") is None:
            return []
        r = util.run_cmd(["klist", "-e"], timeout=ctx.cmd_timeout)
        if not r.ok or not r.stdout.strip():
            return []
        out: List[Asset] = []
        for c in parse_klist(r.stdout):
            tickets = c["tickets"]
            if not tickets:
                continue
            cache = str(c["cache"])
            a = Asset(AssetKind.KERBEROS_TICKET, f"credential cache {cache}", cache, self.name, ctx.hostname,
                      attributes={"principal": c["principal"], "ticket_count": len(tickets),
                                  "services": sorted({str(t["service"]) for t in tickets if t["service"]})[:20]})
            seen: Set[Tuple[str, str]] = set()
            for t in tickets:
                for ctxname, key in (("ticket-session-key", "skey"), ("ticket-encryption", "tkt")):
                    if (ctxname, t[key]) in seen:
                        continue
                    seen.add((ctxname, t[key]))
                    u = names.krb_enctype(t[key])
                    u.context = ctxname
                    if t["service"]:
                        u.extra["service"] = t["service"]
                    a.add(u)
            out.append(a)
        return out

    # -- Samba ----------------------------------------------------------------

    def _samba(self, ctx: ScanContext) -> List[Asset]:
        path = ctx.path("/etc/samba/smb.conf")
        if not os.path.isfile(path):
            return []
        a = Asset(AssetKind.KERBEROS_CONFIG, f"Samba config {logical(ctx, path)}", logical(ctx, path), self.name,
                  ctx.hostname, attributes={"role": "samba", **file_attrs(path)})
        text = util.read_text(path)
        if text is None:
            a.errors.append(f"cannot read {path}")
            return [a]
        glob_opts: Dict[str, str] = {}
        section = ""
        buf = ""
        for line in text.splitlines():
            s = line.strip()
            if buf:
                s, buf = buf + s, ""
            if s.endswith("\\"):
                buf = s[:-1] + " "
                continue
            if not s or s[0] in "#;":
                continue
            if s.startswith("["):
                section = s.strip("[] ").lower()
                continue
            if section == "global" and "=" in s:
                k, v = s.split("=", 1)
                glob_opts[re.sub(r"[\s_]+", " ", k.strip().lower())] = v.strip()
        yes = lambda v: v.strip().lower() in ("yes", "true", "1", "on")  # noqa: E731
        ket = glob_opts.get("kerberos encryption types")
        if ket:
            kv = ket.strip().lower()
            a.attributes["kerberos_encryption_types"] = kv
            toks = {"legacy": ["rc4-hmac"], "all": ["rc4-hmac", "aes256-cts-hmac-sha1-96", "aes128-cts-hmac-sha1-96"],
                    "strong": ["aes256-cts-hmac-sha1-96", "aes128-cts-hmac-sha1-96"]}.get(kv, [])
            for t in toks:
                u = names.krb_enctype(t)
                u.context = "kerberos encryption types"
                a.add(u)
        for key in ("client min protocol", "server min protocol", "min protocol"):
            v = glob_opts.get(key)
            if v is None:
                continue
            a.attributes[key.replace(" ", "_")] = v
            if v.strip().lower() in _SMB1:
                a.add(CryptoUse(Primitive.PROTOCOL, "smbv1", raw=f"{key} = {v}", context="samba-config"))
        ntlm = glob_opts.get("ntlm auth")
        if ntlm is not None:
            a.attributes["ntlm_auth"] = ntlm
            if ntlm.strip().lower() in ("yes", "true", "1", "on", "ntlmv1-permitted"):
                a.add(CryptoUse(Primitive.PROTOCOL, "ntlmv1", raw=f"ntlm auth = {ntlm}", context="samba-config"))
        for key in ("lanman auth", "client lanman auth"):
            v = glob_opts.get(key)
            if v is not None:
                a.attributes[key.replace(" ", "_")] = v
                if yes(v):
                    a.add(CryptoUse(Primitive.PROTOCOL, "ntlmv1", raw=f"{key} = {v}", context="samba-config"))
        v = glob_opts.get("client ntlmv2 auth")
        if v is not None:
            a.attributes["client_ntlmv2_auth"] = v
            if v.strip().lower() in ("no", "false", "0", "off"):
                a.add(CryptoUse(Primitive.PROTOCOL, "ntlmv1", raw=f"client ntlmv2 auth = {v}", context="samba-config"))
        for key in ("client use spnego", "smb encrypt", "server smb encrypt", "client smb encrypt",
                    "server signing", "client signing", "security", "encrypt passwords"):
            if key in glob_opts:
                a.attributes[key.replace(" ", "_")] = glob_opts[key]
        return [a]

    # -- offline AD export ----------------------------------------------------

    def _ad_export(self, ctx: ScanContext) -> List[Asset]:
        path = ctx.opt("ad_enctype_export")
        if not path:
            return []
        path = str(path)
        rows, errors = read_ad_export(path)
        out: List[Asset] = []
        if errors or not rows:
            a = Asset(AssetKind.KERBEROS_CONFIG, f"AD enctype export {path}", path, self.name, ctx.hostname,
                      attributes={"role": "ad-export"})
            a.errors.extend(errors or [f"no accounts found in {path}"])
            return [a]
        for acct, val, rawtext in rows[:100000]:
            a = Asset(AssetKind.KERBEROS_CONFIG, f"AD account {acct}", path, self.name, ctx.hostname,
                      attributes={"role": "ad-account", "account": acct, "supported_enc_types": val,
                                  "supported_enc_types_raw": rawtext})
            if val is None and rawtext.strip():
                a.errors.append(f"unparseable msDS-SupportedEncryptionTypes {rawtext!r} for {acct}")
            ets, defaulted, other = decode_ad_enctypes(val)
            if defaulted:
                a.attributes["default_applied"] = True
            if other:
                a.attributes["other_flags"] = hex(other)
            for eid, label in ets:
                u = names.krb_enctype(eid)
                u.context = "msDS-SupportedEncryptionTypes"
                u.raw = label
                u.extra["account"] = acct
                if defaulted:
                    u.extra.update(source="default", assumed=True)
                a.add(u)
            out.append(a)
        return out
