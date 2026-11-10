"""Local SSH inventory: sshd / ssh configuration, host keys, moduli, user keys.

* `sshd -T` is preferred for the effective server configuration (only when
  scanning the live root); otherwise sshd_config is parsed, including `Include`
  globs and `Match` blocks.  Directives outside Match are global; Match-scoped
  directives are recorded with `extra["match"]`.
* OpenSSH list syntax (`+`, `-`, `^`, wildcards) is expanded against embedded
  OpenSSH 9.x default lists; `extra["relative_to_defaults"]` is then True.
  Absent directives record the defaults with `negotiated=None` and
  `extra["source"]="default"`.
* Host keys, certificates, Dropbear keys, /etc/ssh/moduli, user keys
  (~/.ssh/*), authorized_keys and known_hosts files are parsed for key type and
  size; private keys are inspected for mode, owner and encryption only (their
  secret material is never extracted).

Options: `home_dirs` (list of home directories to use instead of util.home_dirs()).
"""

from __future__ import annotations

import base64
import fnmatch
import glob
import hashlib
import os
import re
from typing import Dict, List, Optional, Tuple

from .. import names, sshkeys, util, x509
from ..model import Asset, AssetKind, CryptoUse, Primitive
from . import register
from .base import Collector, ScanContext

# ---------------------------------------------------------------------------
# OpenSSH 9.x default algorithm lists (9.6 era; client and server agree)
# ---------------------------------------------------------------------------

_HK_CERTS = ("ssh-ed25519-cert-v01@openssh.com,ecdsa-sha2-nistp256-cert-v01@openssh.com,"
             "ecdsa-sha2-nistp384-cert-v01@openssh.com,ecdsa-sha2-nistp521-cert-v01@openssh.com,"
             "sk-ssh-ed25519-cert-v01@openssh.com,sk-ecdsa-sha2-nistp256-cert-v01@openssh.com,"
             "rsa-sha2-512-cert-v01@openssh.com,rsa-sha2-256-cert-v01@openssh.com")
_HK_PLAIN = ("ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,"
             "sk-ssh-ed25519@openssh.com,sk-ecdsa-sha2-nistp256@openssh.com,rsa-sha2-512,rsa-sha2-256")
_DEFAULTS_COMMON = {
    "kexalgorithms": ("sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,"
                      "ecdh-sha2-nistp256,ecdh-sha2-nistp384,ecdh-sha2-nistp521,"
                      "diffie-hellman-group-exchange-sha256,diffie-hellman-group16-sha512,"
                      "diffie-hellman-group18-sha512,diffie-hellman-group14-sha256"),
    "ciphers": ("chacha20-poly1305@openssh.com,aes128-ctr,aes192-ctr,aes256-ctr,"
                "aes128-gcm@openssh.com,aes256-gcm@openssh.com"),
    "macs": ("umac-64-etm@openssh.com,umac-128-etm@openssh.com,hmac-sha2-256-etm@openssh.com,"
             "hmac-sha2-512-etm@openssh.com,hmac-sha1-etm@openssh.com,umac-64@openssh.com,"
             "umac-128@openssh.com,hmac-sha2-256,hmac-sha2-512,hmac-sha1"),
    "hostkeyalgorithms": _HK_CERTS + "," + _HK_PLAIN,
    "pubkeyacceptedalgorithms": _HK_CERTS + "," + _HK_PLAIN,
    "hostbasedacceptedalgorithms": _HK_CERTS + "," + _HK_PLAIN,
    "casignaturealgorithms": ("ssh-ed25519,ecdsa-sha2-nistp256,ecdsa-sha2-nistp384,ecdsa-sha2-nistp521,"
                              "sk-ssh-ed25519@openssh.com,sk-ecdsa-sha2-nistp256@openssh.com,rsa-sha2-512,rsa-sha2-256"),
    "gssapikexalgorithms": ("gss-group14-sha256-,gss-group16-sha512-,gss-nistp256-sha256-,"
                            "gss-curve25519-sha256-"),
}
SERVER_DEFAULTS: Dict[str, str] = dict(_DEFAULTS_COMMON)
CLIENT_DEFAULTS: Dict[str, str] = dict(_DEFAULTS_COMMON)
# Defaults recorded when the directive is absent (the rest only when configured).
SERVER_DEFAULT_RECORDED = ("kexalgorithms", "hostkeyalgorithms", "ciphers", "macs",
                           "pubkeyacceptedalgorithms", "casignaturealgorithms")
CLIENT_DEFAULT_RECORDED = ("kexalgorithms", "hostkeyalgorithms", "ciphers", "macs", "pubkeyacceptedalgorithms")

_ALIASES = {"pubkeyacceptedkeytypes": "pubkeyacceptedalgorithms",
            "hostbasedacceptedkeytypes": "hostbasedacceptedalgorithms"}
_LIST_DIRECTIVES = ("kexalgorithms", "hostkeyalgorithms", "ciphers", "macs", "pubkeyacceptedalgorithms",
                    "casignaturealgorithms", "hostbasedacceptedalgorithms", "gssapikexalgorithms")
_SERVER_SCALARS = ("protocol", "fingerprinthash", "requiredrsasize")
_CLIENT_SCALARS = ("protocol", "fingerprinthash", "requiredrsasize")
_DISPLAY = {"kexalgorithms": "KexAlgorithms", "hostkeyalgorithms": "HostKeyAlgorithms", "ciphers": "Ciphers",
            "macs": "MACs", "pubkeyacceptedalgorithms": "PubkeyAcceptedAlgorithms",
            "casignaturealgorithms": "CASignatureAlgorithms", "hostbasedacceptedalgorithms": "HostbasedAcceptedAlgorithms",
            "gssapikexalgorithms": "GSSAPIKexAlgorithms"}
_DEFAULT_HOSTKEYS = ("rsa", "ecdsa", "ed25519", "dsa")
_SSH_DIR = "/etc/ssh"

_VERSION_RE = re.compile(r"OpenSSH_(\d+)\.(\d+)(\S*)")


def expand_list(value: str, default: List[str]) -> Tuple[List[str], bool]:
    """Apply OpenSSH list syntax (`+`, `-`, `^`, wildcards) to `default`.

    Returns (names, relative_to_defaults).
    """
    value = value.strip()
    items = [x.strip() for x in value.lstrip("+-^").split(",") if x.strip()]
    if not value or value[0] not in "+-^":
        return [x.strip() for x in value.split(",") if x.strip()], False
    cur = list(default)
    if value[0] == "+":
        cur += [x for x in items if x not in cur]
    elif value[0] == "^":
        cur = items + [x for x in cur if x not in items]
    else:
        cur = [x for x in cur if not any(fnmatch.fnmatchcase(x, p) for p in items)]
    return cur, True


def _split_kv(line: str) -> Optional[Tuple[str, str]]:
    m = re.match(r"^(\S+?)(?:\s*=\s*|\s+)(.*)$", line.strip())
    if not m:
        return None
    val = m.group(2).strip()
    if len(val) >= 2 and val[0] == val[-1] == '"':
        val = val[1:-1]
    return m.group(1).lower(), val


def _parse_config_file(ctx: ScanContext, path: str, client: bool, records: List[dict],
                       seen: set, cond: Optional[str] = None, depth: int = 0,
                       block: Optional[str] = None) -> None:
    """Parse one sshd_config / ssh_config file (recursing into Include)."""
    real = os.path.realpath(path)
    if real in seen or depth > 8:
        return
    seen.add(real)
    text = util.read_text(path)
    if text is None:
        return
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        kv = _split_kv(s)
        if kv is None:
            continue
        kw, val = kv
        kw = _ALIASES.get(kw, kw)
        if kw == "include":
            for pat in val.split():
                full = ctx.path(pat) if os.path.isabs(pat) else os.path.join(ctx.path(_SSH_DIR), pat)
                for f in sorted(glob.glob(full)):
                    _parse_config_file(ctx, f, client, records, seen, cond, depth + 1, block)
            continue
        if kw == "match":
            cond = "all" if val.strip().lower() == "all" else val
            if client:
                block, cond = f"match {val}", None
                cond = f"match {val}"
            continue
        if client and kw == "host":
            block = val
            cond = None if val.strip() == "*" else f"host {val}"
            continue
        records.append({"kw": kw, "val": val, "cond": cond, "block": block if client else None,
                        "file": path, "line": n, "source": "config"})


def _parse_sshd_T(text: str) -> List[dict]:
    out = []
    for line in text.splitlines():
        kv = _split_kv(line)
        if kv is None:
            continue
        kw, val = kv
        out.append({"kw": _ALIASES.get(kw, kw), "val": val, "cond": None, "block": None,
                    "file": "sshd -T", "line": 0, "source": "sshd -T"})
    return out


def _maker(directive: str):
    if directive in ("kexalgorithms", "gssapikexalgorithms"):
        return lambda n, **kw: names.ssh_kex(n, **kw)
    if directive == "hostkeyalgorithms":
        return lambda n, **kw: names.ssh_hostkey(n, **kw)
    if directive == "ciphers":
        return lambda n, **kw: names.ssh_cipher(n, **kw)
    if directive == "macs":
        return lambda n, **kw: names.ssh_mac(n, **kw)
    ctxname = {"pubkeyacceptedalgorithms": "pubkey-auth", "casignaturealgorithms": "ca-signature",
               "hostbasedacceptedalgorithms": "hostbased-auth"}[directive]
    return lambda n, **kw: names.ssh_sig_algorithm(n, ctxname, **kw)


def _emit_directives(asset: Asset, records: List[dict], defaults: Dict[str, str],
                     default_recorded: Tuple[str, ...], scalars: Tuple[str, ...], client: bool) -> None:
    default_list = {k: [x for x in v.split(",") if x] for k, v in defaults.items()}
    for kw in _LIST_DIRECTIVES:
        recs = [r for r in records if r["kw"] == kw]
        seen_conds = set()
        got_global = False
        for r in recs:
            key = (r["cond"], r["block"])
            if key in seen_conds:
                continue                     # sshd/ssh: the first value of a directive wins
            seen_conds.add(key)
            got_global = got_global or r["cond"] is None
            lst, rel = expand_list(r["val"], default_list.get(kw, []))
            mk = _maker(kw)
            for nme in lst:
                extra = {"directive": _DISPLAY[kw], "source": r["source"], "config_file": r["file"], "line": r["line"]}
                if rel:
                    extra["relative_to_defaults"] = True
                if r["cond"] is not None:
                    extra["host_block" if client else "match"] = r["cond"]
                elif r["block"]:
                    extra["host_block"] = r["block"]
                asset.add(mk(nme, negotiated=False, extra=extra))
        if not got_global and kw in default_recorded:
            mk = _maker(kw)
            for nme in default_list[kw]:
                asset.add(mk(nme, negotiated=None, extra={"directive": _DISPLAY[kw], "source": "default",
                                                          "openssh_defaults": "9.x"}))
    cfg_names = {"protocol": "ssh-protocol", "fingerprinthash": "ssh-fingerprint-hash",
                 "requiredrsasize": "ssh-required-rsa-size"}
    for kw in scalars:
        seen_conds = set()
        for r in (x for x in records if x["kw"] == kw):
            key = (r["cond"], r["block"])
            if key in seen_conds:
                continue
            seen_conds.add(key)
            extra = {"directive": {"protocol": "Protocol", "fingerprinthash": "FingerprintHash",
                                   "requiredrsasize": "RequiredRSASize"}[kw], "source": r["source"],
                     "config_file": r["file"], "line": r["line"]}
            if r["cond"] is not None:
                extra["host_block" if client else "match"] = r["cond"]
            elif r["block"]:
                extra["host_block"] = r["block"]
            asset.add(CryptoUse(Primitive.CONFIG, cfg_names[kw], raw=r["val"], context=cfg_names[kw],
                                negotiated=False, extra=extra))


# ---------------------------------------------------------------------------
# key helpers
# ---------------------------------------------------------------------------

_KEYLINE_RE = re.compile(r"(?:^|\s)((?:ssh-|ecdsa-sha2-|sk-|rsa-sha2-|x509v3-)[\w@.\-]*)\s+([A-Za-z0-9+/=]{16,})")


def _alg(info: x509.PublicKeyInfo) -> str:
    return "ecdsa" if info.algorithm == "ec" else info.algorithm


def _key_use(info: x509.PublicKeyInfo, context: str, raw: Optional[str] = None, extra: Optional[dict] = None) -> CryptoUse:
    ex = dict(extra or {})
    if info.rsa_exponent:
        ex["rsa_exponent"] = info.rsa_exponent
    return CryptoUse(Primitive.PUBLIC_KEY, _alg(info), key_bits=info.key_bits, curve=info.curve,
                     raw=raw, context=context, extra=ex)


def _fingerprint(line: str) -> Optional[str]:
    m = _KEYLINE_RE.search(line)
    if not m:
        return None
    try:
        blob = base64.b64decode(m.group(2))
    except ValueError:
        return None
    return "SHA256:" + base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip("=")


def _first_pub(path: str) -> Optional[Tuple[str, x509.PublicKeyInfo, str, str]]:
    """(key_type, info, comment, line) of the first key in a .pub file."""
    text = util.read_text(path, 256 * 1024)
    if text is None:
        return None
    for line in text.splitlines():
        p = sshkeys.parse_public_line(line)
        if p:
            return p[0], p[1], p[2], line
    return None


def _inspect_private(path: str, asset: Asset) -> Optional[x509.PublicKeyInfo]:
    """Fill mode/owner/encrypted/fmt on `asset` from a private key file; return its public info."""
    asset.attributes["mode"] = util.file_mode(path)
    asset.attributes["owner"] = util.file_owner(path)
    data = util.read_bytes(path)
    if data is None:
        asset.errors.append(f"cannot read private key {path} (permission denied, too large or not a regular file)")
        return None
    infos = x509.parse_key_data(data)
    infos = [i for i in infos if i.kind in ("private", "encrypted-private")] or infos
    if not infos:
        if b"PRIVATE KEY" in data[:200]:
            asset.errors.append(f"unrecognised private key format in {path}")
        else:
            asset.errors.append(f"no key material recognised in {path}")
        return None
    k = infos[0]
    asset.attributes.update(encrypted=bool(k.encrypted), fmt=k.fmt)
    if k.note:
        asset.attributes["encryption_note"] = k.note
    return k.public_key


def _key_asset(ctx: ScanContext, kind: AssetKind, label: str, priv: Optional[str], pub: Optional[str],
               context: str, extra_attrs: Optional[dict] = None) -> Optional[Asset]:
    """One asset for a key pair (private file, .pub file, or both)."""
    loc = priv or pub
    if loc is None:
        return None
    asset = Asset(kind, f"{label} {loc}", loc, "ssh_local", host=ctx.hostname)
    asset.attributes.update(extra_attrs or {})
    info: Optional[x509.PublicKeyInfo] = None
    keytype = None
    comment = ""
    if priv:
        info = _inspect_private(priv, asset)
    if pub:
        asset.attributes["pub_path"] = pub
        asset.attributes["pub_mode"] = util.file_mode(pub)
        fp = _first_pub(pub)
        if fp:
            keytype, pinfo, comment, line = fp
            if info is None:
                info = pinfo
            asset.attributes["fingerprint_sha256"] = _fingerprint(line)
            if "-cert-v01@openssh.com" in keytype:
                asset.attributes["certificate"] = True
        elif not priv:
            asset.errors.append(f"no parsable public key in {pub}")
    if info is None:
        if not asset.errors:
            asset.errors.append(f"no parsable key in {loc}")
    else:
        asset.add(_key_use(info, context, raw=keytype, extra={"comment": comment} if comment else None))
    return asset


def _cert_ca_type(path: str, cmd_timeout: float) -> Optional[str]:
    """CA key type of an OpenSSH certificate via `ssh-keygen -L` (optional)."""
    exe = util.which("ssh-keygen")
    if not exe:
        return None
    res = util.run_cmd([exe, "-L", "-f", path], timeout=cmd_timeout)
    m = re.search(r"Signing CA:\s+(\S+)", res.stdout)
    return m.group(1) if m else None


def _classify(name: str) -> Optional[str]:
    if name in ("authorized_keys", "authorized_keys2"):
        return "authorized"
    if name in ("known_hosts", "known_hosts2", "ssh_known_hosts", "ssh_known_hosts2"):
        return "known_hosts"
    return None


def _multi_key_asset(ctx: ScanContext, path: str, how: str, extra_attrs: Optional[dict] = None) -> Optional[Asset]:
    kind = AssetKind.SSH_AUTHORIZED_KEY if how == "authorized" else AssetKind.SSH_KNOWN_HOST
    label = "authorized_keys" if how == "authorized" else "known_hosts"
    text = util.read_text(path)
    asset = Asset(kind, f"{label} {path}", path, "ssh_local", host=ctx.hostname)
    asset.attributes.update(extra_attrs or {})
    asset.attributes["file_mode"] = util.file_mode(path)
    asset.attributes["owner"] = util.file_owner(path)
    if text is None:
        asset.errors.append(f"cannot read {path}")
        return asset
    nkeys = 0
    for n, line in enumerate(text.splitlines()[:100000], 1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        p = sshkeys.parse_public_line(s)
        if p is None:
            asset.errors.append(f"{path}:{n}: unparsable key line")
            continue
        ktype, info, comment = p
        m = _KEYLINE_RE.search(s)
        prefix = s[:m.start(1)].strip() if m else ""
        extra: dict = {"line": n, "comment": comment, "key_type": ktype}
        if how == "authorized":
            if prefix:
                extra["options"] = prefix
                if "cert-authority" in prefix:
                    extra["cert_authority"] = True
        else:
            toks = prefix.split()
            if toks and toks[0].startswith("@"):
                extra["marker"] = toks[0]
                toks = toks[1:]
            host = toks[0] if toks else ""
            extra["hostname"] = host[:40] + ("..." if len(host) > 40 else "")
            extra["hashed"] = host.startswith("|1|")
        fp = _fingerprint(s)
        if fp:
            extra["fingerprint_sha256"] = fp
        asset.add(_key_use(info, "public-key", raw=ktype, extra=extra))
        nkeys += 1
    asset.attributes["keys"] = nkeys
    return asset if (nkeys or asset.errors) else None


def _files_to_assets(ctx: ScanContext, files: List[str], seen: set, extra_attrs: Optional[dict] = None) -> List[Asset]:
    """Classify the files of one directory into key assets."""
    out: List[Asset] = []
    byname = {os.path.basename(f): f for f in files}
    privs = set()
    for nme in byname:
        if _classify(nme) or nme.endswith(".pub"):
            continue
        if nme.startswith("id_") or (nme + ".pub") in byname:
            privs.add(nme)
    for nme in sorted(byname):
        f = byname[nme]
        real = os.path.realpath(f)
        how = _classify(nme)
        if how:
            if real in seen:
                continue
            seen.add(real)
            a = _multi_key_asset(ctx, f, how, extra_attrs)
            if a:
                out.append(a)
        elif nme in privs:
            if real in seen:
                continue
            seen.add(real)
            pub = byname.get(nme + ".pub")
            if pub:
                seen.add(os.path.realpath(pub))
            a = _key_asset(ctx, AssetKind.SSH_USER_KEY, "ssh user key", f, pub, "public-key", extra_attrs)
            if a:
                out.append(a)
        elif nme.endswith(".pub") and nme[:-4] not in privs:
            if real in seen:
                continue
            seen.add(real)
            a = _key_asset(ctx, AssetKind.SSH_USER_KEY, "ssh public key", None, f, "public-key", extra_attrs)
            if a:
                if a.attributes.get("certificate"):
                    ca = _cert_ca_type(f, ctx.cmd_timeout)
                    if ca:
                        a.attributes["ca_key_type"] = ca
                out.append(a)
    return out


def _version_of(banner: Optional[str]) -> Optional[Tuple[int, int]]:
    m = _VERSION_RE.search(banner or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def _find_exe(name: str, extra: Tuple[str, ...] = ()) -> Optional[str]:
    exe = util.which(name)
    if exe:
        return exe
    for p in extra:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p
    return None


@register
class SSHLocalCollector(Collector):
    name = "ssh_local"
    description = "Local OpenSSH/Dropbear: sshd and ssh configuration, host keys, moduli, user and authorized keys, known_hosts"

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        return True, ""

    # -- helpers -----------------------------------------------------------
    def _version(self, ctx: ScanContext, exe: Optional[str], flag: str) -> Optional[str]:
        if ctx.root not in ("", "/") or not exe:
            return None
        res = util.run_cmd([exe, flag], timeout=ctx.cmd_timeout)
        m = re.search(r"OpenSSH_[\w.]+", res.stderr + "\n" + res.stdout)
        return m.group(0) if m else None

    def _homes(self, ctx: ScanContext) -> List[str]:
        opt = ctx.opt("home_dirs")
        if opt is not None:
            return [str(h) for h in opt]
        if ctx.root in ("", "/"):
            return util.home_dirs()
        homes = sorted(glob.glob(ctx.path("/home/*"))) + [ctx.path("/root")]
        return [h for h in homes if os.path.isdir(h)]

    # -- main --------------------------------------------------------------
    def collect(self, ctx: ScanContext) -> List[Asset]:
        assets: List[Asset] = []
        seen: set = set()
        self._server(ctx, assets, seen)
        self._client(ctx, assets)
        self._dropbear(ctx, assets, seen)
        self._user_keys(ctx, assets, seen)
        return assets

    def _server(self, ctx: ScanContext, assets: List[Asset], seen: set):
        cfg = ctx.path(_SSH_DIR, "sshd_config")
        sshd = _find_exe("sshd", ("/usr/sbin/sshd", "/usr/local/sbin/sshd"))
        records: List[dict] = []
        cfg_exists = os.path.isfile(cfg)
        _parse_config_file(ctx, cfg, False, records, set())
        source = "files"
        if ctx.root in ("", "/") and sshd:
            res = util.run_cmd([sshd, "-T", "-f", cfg], timeout=ctx.cmd_timeout)
            if res.ok and res.stdout.strip():
                effective = _parse_sshd_T(res.stdout)
                records = effective + [r for r in records if r["cond"] is not None]
                source = "sshd -T"
        moduli_weak, moduli_file = self._moduli(ctx)
        ssh_dir = ctx.path(_SSH_DIR)
        if not (cfg_exists or source == "sshd -T" or moduli_weak or os.path.isdir(ssh_dir) and glob.glob(os.path.join(ssh_dir, "ssh_host_*"))):
            return None
        asset = Asset(AssetKind.SSH_SERVER, f"sshd on {ctx.hostname}", cfg, self.name, host=ctx.hostname)
        asset.attributes["config_source"] = source
        if not cfg_exists:
            asset.attributes["config_present"] = False
        banner = self._version(ctx, sshd, "-V")
        self._version_attrs(asset, banner)
        _emit_directives(asset, records, SERVER_DEFAULTS, SERVER_DEFAULT_RECORDED, _SERVER_SCALARS, False)
        if moduli_weak:
            asset.add(CryptoUse(Primitive.CONFIG, "weak-moduli", raw=str(moduli_weak), context="weak-moduli",
                                negotiated=False, extra={"file": moduli_file, "threshold_bits": 2048}))
        assets.append(asset)
        # host keys
        hostkeys = []
        for r in records:
            if r["kw"] == "hostkey" and r["cond"] is None and r["val"] not in hostkeys:
                hostkeys.append(r["val"])
        explicit = bool(hostkeys)
        if not hostkeys:
            hostkeys = [f"{_SSH_DIR}/ssh_host_{t}_key" for t in _DEFAULT_HOSTKEYS]
        for hk in hostkeys:
            priv = ctx.path(hk)
            pub = priv + ".pub"
            has_priv, has_pub = os.path.exists(priv), os.path.isfile(pub)
            if not (has_priv or has_pub):
                if explicit:
                    asset.errors.append(f"HostKey {hk} not found")
                continue
            seen.add(os.path.realpath(priv))
            a = _key_asset(ctx, AssetKind.SSH_HOST_KEY, "ssh host key", priv if has_priv else None,
                           pub if has_pub else None, "hostkey-material", {"software": "openssh"})
            if a:
                assets.append(a)
            cert = priv + "-cert.pub"
            if os.path.isfile(cert):
                seen.add(os.path.realpath(cert))
        for cert in sorted(glob.glob(os.path.join(ssh_dir, "ssh_host_*_key-cert.pub"))):
            a = _key_asset(ctx, AssetKind.SSH_HOST_KEY, "ssh host certificate", None, cert, "hostkey-material",
                           {"software": "openssh", "certificate": True})
            if a:
                a.attributes["certificate"] = True
                ca = _cert_ca_type(cert, ctx.cmd_timeout)
                if ca:
                    a.attributes["ca_key_type"] = ca
                for u in a.uses:
                    u.extra["certificate"] = True
                assets.append(a)
        # system-wide known_hosts
        files = [p for p in (os.path.join(ssh_dir, n) for n in ("ssh_known_hosts", "ssh_known_hosts2")) if os.path.isfile(p)]
        if files:
            assets.extend(_files_to_assets(ctx, files, seen))
        return asset

    def _version_attrs(self, asset: Asset, banner: Optional[str]) -> None:
        if not banner:
            return
        asset.attributes["version"] = banner
        asset.add(CryptoUse(Primitive.CONFIG, "ssh-version", raw=banner, context="ssh-version", negotiated=True))
        v = _version_of(banner)
        if v and v >= (9, 6):
            asset.attributes["kex_strict"] = True

    def _moduli(self, ctx: ScanContext) -> Tuple[int, Optional[str]]:
        path = ctx.path(_SSH_DIR, "moduli")
        text = util.read_text(path)
        if text is None:
            return 0, None
        weak = 0
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            f = line.split()
            if len(f) >= 7:
                try:
                    if int(f[4]) + 1 < 2048:
                        weak += 1
                except ValueError:
                    continue
        return weak, path

    def _client(self, ctx: ScanContext, assets: List[Asset]) -> None:
        cfg = ctx.path(_SSH_DIR, "ssh_config")
        cdir = ctx.path(_SSH_DIR, "ssh_config.d")
        d_files = sorted(glob.glob(os.path.join(cdir, "*.conf")))
        if not os.path.isfile(cfg) and not d_files:
            return
        records: List[dict] = []
        seen: set = set()
        _parse_config_file(ctx, cfg, True, records, seen)
        for f in d_files:
            _parse_config_file(ctx, f, True, records, seen)
        asset = Asset(AssetKind.SSH_CLIENT, f"ssh client on {ctx.hostname}", cfg, self.name, host=ctx.hostname)
        asset.attributes["config_source"] = "files"
        self._version_attrs(asset, self._version(ctx, _find_exe("ssh"), "-V"))
        _emit_directives(asset, records, CLIENT_DEFAULTS, CLIENT_DEFAULT_RECORDED, _CLIENT_SCALARS, True)
        assets.append(asset)

    def _dropbear(self, ctx: ScanContext, assets: List[Asset], seen: set) -> None:
        d = ctx.path("/etc/dropbear")
        if not os.path.isdir(d):
            return
        types = {"rsa": "rsa", "dss": "dsa", "ecdsa": "ecdsa", "ed25519": "ed25519"}
        for t, alg in types.items():
            p = os.path.join(d, f"dropbear_{t}_host_key")
            if not os.path.exists(p):
                continue
            a = Asset(AssetKind.SSH_HOST_KEY, f"dropbear host key {p}", p, self.name, host=ctx.hostname)
            a.attributes.update(software="dropbear", key_type=alg)
            info = _inspect_private(p, a)
            if info is None:
                data = util.read_bytes(p)
                if data:
                    try:       # dropbear stores SSH wire-format blobs (type, then key parts)
                        info = sshkeys.parse_public_blob(data)
                        a.errors = [e for e in a.errors if not e.startswith("no key material")]
                        a.attributes["fmt"] = "dropbear"
                    except (sshkeys.SSHBlobError, ValueError, IndexError):
                        info = None
            if info is not None:
                a.add(_key_use(info, "hostkey-material", extra={"software": "dropbear"}))
            else:
                a.errors.append(f"could not parse dropbear key type {alg}; recorded by file name only")
            assets.append(a)

    def _user_keys(self, ctx: ScanContext, assets: List[Asset], seen: set) -> None:
        budget = ctx.max_files
        for home in self._homes(ctx):
            sd = os.path.join(home, ".ssh")
            if not os.path.isdir(sd):
                continue
            try:
                names_ = sorted(os.listdir(sd))[:budget]
            except OSError as e:
                ctx.warn(f"cannot list {sd}: {e}")
                continue
            files = [os.path.join(sd, n) for n in names_ if os.path.isfile(os.path.join(sd, n))]
            assets.extend(_files_to_assets(ctx, files, seen, {"home": home}))
        for p in ctx.extra_paths:
            if os.path.isfile(p):
                assets.extend(_files_to_assets(ctx, [p], seen))
            elif os.path.isdir(p):
                groups: Dict[str, List[str]] = {}
                for f in util.walk_files([p], ctx.max_files, max_depth=4):
                    groups.setdefault(os.path.dirname(f), []).append(f)
                for _d, fs in sorted(groups.items()):
                    assets.extend(_files_to_assets(ctx, fs, seen))
