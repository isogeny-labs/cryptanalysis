"""Network-device configuration collector (offline configs + light management probes).

Inputs
------
* ``ctx.netdev_configs``: saved configuration files or directories (one level of
  sub-directories is followed; files over 8 MB and binary files are skipped).
* files in ``ctx.extra_paths`` (and one level below a directory there) whose
  content auto-detects as a device configuration.

Paths are used verbatim (they are files on the scanning host, e.g. a RANCID or
Oxidized checkout); a relative path that does not exist is retried under
``ctx.root``.

Platforms are detected from content (`detect_platform`): Cisco IOS / IOS-XE,
NX-OS, IOS-XR, ASA, Junos (brace and ``set`` formats), Arista EOS, HP/Aruba
ProCurve, FortiOS, PAN-OS (``set`` format), MikroTik RouterOS exports, Huawei
VRP and F5 ``bigip.conf``.  Each file becomes one NETWORK_DEVICE asset
(attributes platform, os_version, hostname, config_file) whose
uses come from the platform parsers in ``_netdev_cli`` / ``_netdev_tree``.  A
file whose platform is not recognised is scanned with a keyword heuristic
(`generic_heuristic`); those uses carry ``extra["heuristic"] = True``.

Secret hygiene: password, community and key *values* are never stored; only
their storage type (``type7``, ``md5crypt``), the presence of a community and
algorithm names.  The SNMP probe below never records the community it tried.

Active probes (only when ``ctx.active_probes``) for targets whose service is
``netdev`` or ``snmp``, or ``auto`` with port 23, 80 or 161:

* TCP 23: a telnet server is recognised by IAC (0xff) option negotiation
  -> PROTOCOL ``telnet`` negotiated=True.
* TCP 80: ``GET /`` -> PROTOCOL ``http-mgmt`` negotiated=True when an HTTP status
  line comes back (status line and Server header recorded, 2 KB read at most).
* UDP 161, only with ``ctx.snmp_probe`` (explicit operator consent): one SNMPv1
  and one SNMPv2c GET of sysDescr per community in
  ``ctx.opt("snmp_communities", ["public"])`` -> PROTOCOL ``snmpv1`` /
  ``snmpv2c`` negotiated=True plus attribute ``sysDescr`` (200 chars), and one
  SNMPv3 engine discovery -> attributes ``snmpv3`` / ``engine_id_present``.

SSH and TLS handshakes with devices are done by the ``ssh_remote`` and
``tls_remote`` collectors; this collector does not duplicate them.
"""

from __future__ import annotations

import os
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Iterable, List, Optional, Tuple

from .. import snmp
from ..ciphers import protocol_use
from ..confparse import brace_paths, junos_paths, parse_forti, parse_indent_tree
from ..model import Asset, AssetKind, CryptoUse, Primitive
from ..util import read_bytes
from . import register
from ._netdev_cli import run_asa, run_eos, run_huawei, run_ios, run_iosxr, run_nxos, run_procurve
from ._netdev_common import Dev, enc_use, ike_group_use
from ._netdev_tree import parse_routeros, run_f5, run_forti, run_junos, run_mikrotik, run_panos
from .base import Collector, ScanContext, Target

MAX_BYTES = 8 * 1024 * 1024

PLATFORM_LABELS = {
    "ios": "Cisco IOS", "iosxe": "Cisco IOS-XE", "nxos": "Cisco NX-OS", "iosxr": "Cisco IOS-XR", "asa": "Cisco ASA",
    "junos": "Juniper Junos", "eos": "Arista EOS", "procurve": "HP/Aruba ProCurve", "fortios": "FortiOS",
    "panos": "PAN-OS", "mikrotik": "MikroTik RouterOS", "huawei": "Huawei VRP", "f5": "F5 BIG-IP", "generic": "unknown",
}

_SKIP_EXTS = {".pem", ".crt", ".cer", ".der", ".key", ".p12", ".pfx", ".jks", ".gz", ".xz", ".bz2", ".zip", ".tar",
              ".png", ".jpg", ".gif", ".pdf", ".bin", ".img", ".pyc", ".so", ".exe"}


# ---------------------------------------------------------------------------
# platform detection
# ---------------------------------------------------------------------------

def _has(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.M) is not None


def detect_platform(text: str) -> str:
    """Platform key (see PLATFORM_LABELS) for a configuration text; "generic" when unknown."""
    head = text[:200000]
    if _has(head, r"^#TMSH-VERSION") or (_has(head, r"^(ltm|sys|net|auth|gtm|apm) \S.*\{\s*$") and _has(head, r"^(ltm (virtual|profile|pool)|sys (global-settings|sshd|httpd|snmp))\b")):
        return "f5"
    if _has(head, r"^#config-version=F") or (_has(head, r"^config (system|firewall|vpn) \S") and _has(head, r"^\s*(edit|next|end)\b")):
        return "fortios"
    if _has(head, r"^# (by|software id = ).*RouterOS|^# \S+ by RouterOS") or len(re.findall(r"^/(ip|interface|system|snmp|routing|user|tool|ipv6|queue)\b", head, re.M)) >= 2:
        return "mikrotik"
    if _has(head, r"^set (deviceconfig|mgt-config|network (ike|interface|virtual-router)|shared|vsys|rulebase)\b"):
        return "panos"
    if _has(head, r"^set (system|security|interfaces|snmp|protocols|routing-options|policy-options|version)\b"):
        return "junos"
    if _has(head, r"^\s*system \{\s*$") or (_has(head, r"^## Last (commit|changed)") and "{" in head) or \
            (_has(head, r"^\s*version \d+\.\d+[^;\n]*;\s*$") and _has(head, r"^\s*\S+ \{\s*$")):
        return "junos"
    if _has(head, r"^(ASA|PIX|FWSM) Version \d") or _has(head, r"^: Saved\b") and _has(head, r"^(ASA|PIX) Version"):
        return "asa"
    if _has(head, r"IOS[ -]XR") or _has(head, r"^!! IOS XR"):
        return "iosxr"
    if _has(head, r"^\s*(sysname|snmp-agent|user-interface (vty|con|maint))\b") or _has(head, r"^!Software Version V\d+R\d+"):
        return "huawei"
    if _has(head, r"^;\s*\S+ Configuration Editor") or _has(head, r'^\s*name "DEFAULT_VLAN"') or _has(head, r"^password (manager|operator)\b") \
            or (_has(head, r'^hostname "') and _has(head, r"^(no )?telnet-server\b|^ip ssh filetransfer|^web-management\b")):
        return "procurve"
    if _has(head, r"EOS-\d+\.\d+") or _has(head, r"^! device: .*\(.*(DCS|CCS|vEOS|cEOS)") or \
            _has(head, r"^management (api http-commands|ssh|security|telnet)\s*$"):
        return "eos"
    if _has(head, r"^!Command: show running-config") or _has(head, r"^boot nxos ") or _has(head, r"^version \d+\.\d+\(\d+\)[A-Z]?\d*\s*$") and _has(head, r"^feature \S+"):
        return "nxos"
    if _has(head, r"^feature (ssh|telnet|nxapi|interface-vlan|lacp|vpc|bgp|ospf)\s*$"):
        return "nxos"
    if _has(head, r"^version \d+\.\d+") and _has(head, r"^(hostname|line (vty|con)|interface |ip |service |crypto |snmp-server )"):
        return "iosxe" if _has(head, r"^version (1[6-9]|[2-9]\d)\.") or "IOS-XE" in head or "IOS XE" in head else "ios"
    if _has(head, r"^(Building configuration|Current configuration : \d+)") and _has(head, r"^(hostname|line vty|interface )"):
        return "ios"
    if _has(head, r"^line vty \d") and _has(head, r"^(hostname|interface )\S*"):
        return "ios"
    return "generic"


def _vt(*parts: Optional[str]) -> Optional[Tuple[int, ...]]:
    try:
        return tuple(int(p) for p in parts if p is not None)
    except ValueError:
        return None


def detect_version(platform: str, text: str) -> Tuple[Optional[str], Optional[Tuple[int, ...]]]:
    """(display version, comparable tuple) for a platform's configuration text."""
    pats = {
        "ios": r"^version (\d+)\.(\d+)", "iosxe": r"(?:^version |IOS[- ]XE Software, Version )(\d+)\.(\d+)",
        "nxos": r"^version (\d+)\.(\d+)\((\d+)\)", "asa": r"^(?:ASA|PIX) Version (\d+)\.(\d+)\((\d+)\)",
        "iosxr": r"IOS XR (?:Configuration )?(\d+)\.(\d+)\.(\d+)", "eos": r"EOS-(\d+)\.(\d+)\.(\d+)",
        "junos": r"^\s*(?:set )?version \"?(\d+)\.(\d+)", "fortios": r"^#config-version=\S*?-(\d+)\.(\d+)\.(\d+)-",
        "mikrotik": r"RouterOS (\d+)\.(\d+)(?:\.(\d+))?", "f5": r"^#TMSH-VERSION:\s*(\d+)\.(\d+)\.(\d+)",
        "procurve": r"^;\s*\S+ Configuration Editor; Created on release #?\S*?(\d+)\.(\d+)\.(\d+)",
        "panos": r"^set deviceconfig system .*sw-version (\d+)\.(\d+)\.(\d+)",
    }
    pat = pats.get(platform)
    if pat:
        m = re.search(pat, text, re.M)
        if m:
            groups = [g for g in m.groups() if g is not None]
            eol = text.find("\n", m.start())
            line = text[m.start():eol if eol >= 0 else len(text)]
            raw = re.search(r"\d+\.\d+[^\s;\"]*", line[m.start(1) - m.start():]) if platform != "fortios" else None
            return (raw.group(0).rstrip("-") if raw else ".".join(groups)), _vt(*groups)
    if platform == "huawei":
        m = re.search(r"Version (V\d+R\d+\S*)", text)
        if m:
            return m.group(1), None
    return None, None


def detect_hostname(platform: str, text: str) -> Optional[str]:
    pats = {
        "huawei": r"^\s*sysname (\S+)", "fortios": r"^\s*set hostname \"?([^\"\s]+)",
        "panos": r"^set deviceconfig system hostname \"?([^\"\s]+)", "mikrotik": r"^/system identity\s+set name=\"?([^\"\s]+)",
        "f5": r"^\s*hostname ([^\s;]+)", "junos": r"^\s*(?:set system )?host-name \"?([^\"\s;]+)",
    }
    m = re.search(pats.get(platform, r"^\s*(?:hostname|switchname) \"?([^\"\s]+)"), text, re.M)
    if not m and platform == "mikrotik":
        m = re.search(r"^/system identity\s*\n\s*set name=\"?([^\"\s]+)", text, re.M)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# generic heuristic
# ---------------------------------------------------------------------------

_DISABLE = re.compile(r"^\s*(no|undo|delete|unset)\b|\b(disable|disabled|deny|off|false|shutdown)\b", re.I)
_GEN_RULES: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"\bssh\b.*\b(?:protocol\s+|version\s+)1\b(?![.\d])|\bssh(?:-?v|\s+version\s*)1\b(?![.\d])", re.I), "proto", "ssh1"),
    (re.compile(r"\btelnet\b", re.I), "proto", "telnet"),
    (re.compile(r"\bsnmp\S*\b.*\b(?:v1|version\s+1)\b", re.I), "proto", "snmpv1"),
    (re.compile(r"\bv2c\b|\bsnmp\S*\b.*\bcommunity\b|\bcommunity\b.*\bsnmp", re.I), "proto", "snmpv2c"),
    (re.compile(r"\b(?:hmac-)?md5\b", re.I), "hash", "md5"),
    (re.compile(r"\b(?:3des|des3|triple-?des|des-ede3?)(?:-cbc)?\b", re.I), "enc", "3des"),
    (re.compile(r"(?<![\w-])des(?:-cbc|56)?(?![\w-])", re.I), "enc", "des"),
    (re.compile(r"\b(?:rc4|arcfour)\w*\b", re.I), "enc", "rc4"),
    (re.compile(r"\b(?:dh-?)?group-?(?:1|2)\b(?!\d)|\bmodp(?:768|1024)\b", re.I), "group", ""),
    (re.compile(r"\bsslv?2\b", re.I), "tls", "SSLv2"),
    (re.compile(r"\bsslv?3\b", re.I), "tls", "SSLv3"),
    (re.compile(r"\btlsv?1(?:[._]0)?\b(?![._]\d)", re.I), "tls", "TLSv1"),
    (re.compile(r"\btlsv?1[._]1\b", re.I), "tls", "TLSv1.1"),
]


def generic_heuristic(dev: Dev, text: str) -> int:
    """Keyword scan for an unrecognised platform; returns the number of uses added."""
    before = len(dev.asset.uses)
    for no, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(("!", "#", ";", "//")) or _DISABLE.search(s):
            continue
        # only the matched keyword goes into `raw`, never the rest of the line (it may hold a secret)
        for rx, kind, alg in _GEN_RULES:
            m = rx.search(s)
            if not m:
                continue
            raw = f"line {no}: {m.group(0).lower()}"
            ex = {"heuristic": True, "line": no}
            if kind == "proto":
                dev.add(CryptoUse(Primitive.PROTOCOL, alg, raw=raw, context="heuristic", negotiated=None, extra=ex))
            elif kind == "hash":
                dev.add(CryptoUse(Primitive.HASH, alg, raw=raw, context="heuristic", negotiated=None, extra=ex))
            elif kind == "enc":
                dev.add(enc_use(alg, raw, "heuristic", **ex))
            elif kind == "group":
                tok = m.group(0).lower()
                dev.add(ike_group_use(tok if tok.startswith("modp") else "group" + tok[-1], raw, "heuristic", **ex))
            elif kind == "tls":
                u = protocol_use(alg, **ex)
                u.raw, u.context = raw, "heuristic"
                dev.add(u)
    return len(dev.asset.uses) - before


# ---------------------------------------------------------------------------
# file discovery
# ---------------------------------------------------------------------------

def _is_text(data: bytes) -> bool:
    return b"\x00" not in data[:8192]


def _expand(paths: Iterable[str], ctx: ScanContext) -> List[str]:
    """Files named directly plus regular files directly inside named directories (and one level below)."""
    out: List[str] = []
    for p in paths:
        if not p:
            continue
        if not os.path.exists(p) and not os.path.isabs(p) and os.path.exists(ctx.path(p)):
            p = ctx.path(p)
        if os.path.isfile(p):
            out.append(p)
        elif os.path.isdir(p):
            try:
                entries = sorted(os.listdir(p))
            except OSError as e:
                ctx.warn(f"netdev: cannot list {p}: {e}")
                continue
            for e in entries:
                if e.startswith("."):
                    continue
                full = os.path.join(p, e)
                if os.path.isfile(full):
                    out.append(full)
                elif os.path.isdir(full) and not os.path.islink(full):
                    try:
                        out.extend(os.path.join(full, f) for f in sorted(os.listdir(full))
                                   if not f.startswith(".") and os.path.isfile(os.path.join(full, f)))
                    except OSError:
                        continue
        else:
            ctx.warn(f"netdev: config path not found: {p}")
    seen = set()
    uniq = []
    for f in out:
        r = os.path.realpath(f)
        if r not in seen:
            seen.add(r)
            uniq.append(f)
    return uniq[:max(ctx.max_files, 0)]


def _read_config(path: str) -> Optional[str]:
    if os.path.splitext(path)[1].lower() in _SKIP_EXTS:
        return None
    try:
        if os.path.getsize(path) > MAX_BYTES:
            return None
    except OSError:
        return None
    data = read_bytes(path, MAX_BYTES)
    if data is None or not _is_text(data):
        return None
    return data.decode("utf-8", "replace")


# ---------------------------------------------------------------------------
# parsing one file
# ---------------------------------------------------------------------------

def parse_config(text: str, path: str, ctx: ScanContext, platform: Optional[str] = None) -> Asset:
    """Build the NETWORK_DEVICE asset for one configuration text."""
    plat = platform or detect_platform(text)
    disp_ver, ver = detect_version(plat, text)
    hostname = detect_hostname(plat, text)
    stem = os.path.splitext(os.path.basename(path))[0]
    host = hostname or stem
    # the OS version is stored as "os_version": policy.rule_certificate reads attributes["version"] of *every*
    # asset as an X.509 version integer (int("12.4") would raise, "2" would raise CERT-V1)
    attrs: Dict[str, object] = {"platform": plat, "platform_label": PLATFORM_LABELS.get(plat, plat), "os_version": disp_ver,
                                "hostname": hostname, "config_file": path}
    asset = Asset(AssetKind.NETWORK_DEVICE, f"{PLATFORM_LABELS.get(plat, plat)} {host}", path, "netdev", host=host,
                  attributes=attrs)
    dev = Dev(asset, plat, ver)
    try:
        if plat in ("ios", "iosxe"):
            run_ios(dev, parse_indent_tree(text), text)
        elif plat == "nxos":
            run_nxos(dev, parse_indent_tree(text), text)
        elif plat == "iosxr":
            run_iosxr(dev, parse_indent_tree(text), text)
        elif plat == "asa":
            run_asa(dev, parse_indent_tree(text), text)
        elif plat == "eos":
            run_eos(dev, parse_indent_tree(text), text)
        elif plat == "procurve":
            run_procurve(dev, parse_indent_tree(text), text)
        elif plat == "huawei":
            run_huawei(dev, parse_indent_tree(text), text)
        elif plat == "junos":
            run_junos(dev, junos_paths(text))
        elif plat == "fortios":
            run_forti(dev, parse_forti(text))
        elif plat == "panos":
            run_panos(dev, junos_paths(text))
        elif plat == "mikrotik":
            run_mikrotik(dev, text)
        elif plat == "f5":
            run_f5(dev, brace_paths(text, newline_terminates=True))
        else:
            attrs["heuristic"] = True
            generic_heuristic(dev, text)
    except Exception as e:          # a parser bug on one file must not lose the others
        asset.errors.append(f"{plat} parser failed: {type(e).__name__}: {e}")
        ctx.log.debug("netdev parser failure on %s", path, exc_info=True)
    if not asset.uses and plat != "generic":
        attrs["no_crypto_settings_found"] = True
    return asset


def looks_like_device_config(text: str) -> bool:
    return detect_platform(text) != "generic"


# ---------------------------------------------------------------------------
# active probes
# ---------------------------------------------------------------------------

def _probe_targets(ctx: ScanContext) -> List[Target]:
    out = []
    for t in ctx.targets:
        svc = (t.service or "auto").lower()
        if svc in ("netdev", "snmp") or (svc == "auto" and t.port in (23, 80, 161)):
            out.append(t)
    return out


def probe_telnet(host: str, port: int, timeout: float) -> Optional[bool]:
    """True when the port speaks telnet (IAC negotiation), False when open without IAC, None when closed."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            try:
                data = s.recv(512)
            except (socket.timeout, TimeoutError):
                data = b""
            return b"\xff" in data
    except OSError:
        return None


def probe_http(host: str, port: int, timeout: float) -> Optional[Dict[str, str]]:
    """Status line and Server header of `GET /`, or None when nothing HTTP answers."""
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(f"GET / HTTP/1.0\r\nHost: {host}\r\nUser-Agent: cryptoscan\r\nConnection: close\r\n\r\n".encode("ascii", "replace"))
            buf = b""
            while len(buf) < 2048 and b"\r\n\r\n" not in buf:
                try:
                    chunk = s.recv(2048 - len(buf))
                except (socket.timeout, TimeoutError):
                    break
                if not chunk:
                    break
                buf += chunk
    except OSError:
        return None
    text = buf[:2048].decode("latin-1", "replace")
    lines = text.split("\r\n") if "\r\n" in text else text.split("\n")
    if not lines or not lines[0].startswith("HTTP/"):
        return None
    out = {"status": lines[0][:120]}
    for ln in lines[1:]:
        if ln.lower().startswith("server:"):
            out["server"] = ln.split(":", 1)[1].strip()[:120]
    return out


def _udp_exchange(host: str, port: int, payload: bytes, timeout: float) -> Optional[bytes]:
    try:
        infos = socket.getaddrinfo(host, port, type=socket.SOCK_DGRAM)
    except OSError:
        return None
    for family, stype, proto, _, addr in infos[:2]:
        try:
            with socket.socket(family, stype, proto) as s:
                s.settimeout(timeout)
                s.sendto(payload, addr)
                data, _ = s.recvfrom(65535)
                return data
        except OSError:
            continue
    return None


def probe_snmp(host: str, port: int, communities: List[str], timeout: float = 2.0) -> Dict[str, object]:
    """SNMP sysDescr GETs (v1, v2c per community) and one v3 discovery.  The result never names a community."""
    res: Dict[str, object] = {"versions": [], "sysDescr": None, "snmpv3": False, "engine_id_present": False}
    for version, label in ((snmp.VERSION_V1, "snmpv1"), (snmp.VERSION_V2C, "snmpv2c")):
        for i, comm in enumerate(communities):
            rid = snmp.new_request_id()
            data = _udp_exchange(host, port, snmp.build_get_request(version, comm, request_id=rid), timeout)
            if not data:
                continue
            try:
                msg = snmp.parse_message(data)
            except snmp.SnmpError:
                continue
            if msg.version == version and msg.pdu_type == snmp.PDU_RESPONSE and msg.request_id == rid:
                if label not in res["versions"]:
                    res["versions"].append(label)
                    res.setdefault("community_index", {})[label] = i + 1
                descr = msg.value_text(snmp.SYS_DESCR)
                if descr and not res["sysDescr"]:
                    res["sysDescr"] = descr[:200]
                break
    data = _udp_exchange(host, port, snmp.build_v3_discovery(), timeout)
    if data:
        try:
            msg = snmp.parse_message(data)
            if msg.version == snmp.VERSION_V3:
                res["snmpv3"] = True
                res["engine_id_present"] = bool(msg.engine_id)
        except snmp.SnmpError:
            pass
    return res


def probe_target(t: Target, ctx: ScanContext) -> Optional[Asset]:
    svc = (t.service or "auto").lower()
    timeout = min(ctx.timeout, 5.0)
    attrs: Dict[str, object] = {"platform": "probe", "target": str(t)}
    a = Asset(AssetKind.NETWORK_DEVICE, f"device {t.label or t.host} (management probes)", f"{t.host}", "netdev",
              host=t.host, attributes=attrs)
    tried = []
    tcp_all = svc == "netdev" or t.port is None
    if tcp_all or t.port == 23:
        port = 23 if tcp_all else t.port
        tried.append(f"tcp/{port}")
        r = probe_telnet(t.host, port, timeout)
        attrs["telnet_port_open"] = r is not None
        if r:
            a.add(CryptoUse(Primitive.PROTOCOL, "telnet", raw=f"telnet IAC negotiation on {t.host}:{port}", context="management",
                            negotiated=True, extra={"port": port, "probe": True}))
    if tcp_all or t.port == 80:
        port = 80 if tcp_all else t.port
        tried.append(f"tcp/{port}")
        r = probe_http(t.host, port, timeout)
        if r:
            attrs["http_status"] = r.get("status")
            if r.get("server"):
                attrs["http_server"] = r["server"]
            a.add(CryptoUse(Primitive.PROTOCOL, "http-mgmt", raw=f"HTTP on {t.host}:{port}", context="management",
                            negotiated=True, extra={"port": port, "probe": True}))
    if ctx.snmp_probe and (svc in ("netdev", "snmp") or t.port == 161):
        port = t.port if (t.port and svc == "snmp") or t.port == 161 else 161
        tried.append(f"udp/{port}")
        comms = ctx.opt("snmp_communities", ["public"]) or ["public"]
        if isinstance(comms, str):
            comms = [c for c in comms.split(",") if c]
        r = probe_snmp(t.host, port, list(comms), timeout=2.0)
        for label in r["versions"]:
            a.add(CryptoUse(Primitive.PROTOCOL, label, raw=f"{label} GET sysDescr answered on {t.host}:{port}",
                            context="snmp-probe", negotiated=True,
                            extra={"port": port, "probe": True, "community": "accepted",
                                   "community_index": r.get("community_index", {}).get(label)}))
        if r["sysDescr"]:
            attrs["sysDescr"] = r["sysDescr"]
        attrs["snmpv3"] = r["snmpv3"]
        attrs["engine_id_present"] = r["engine_id_present"]
    attrs["probes"] = tried
    return a if a.uses or tried else None


# ---------------------------------------------------------------------------
# collector
# ---------------------------------------------------------------------------

@register
class NetdevCollector(Collector):
    name = "netdev"
    description = ("Network-device configurations (Cisco IOS/NX-OS/XR/ASA, Junos, Arista, ProCurve, FortiOS, PAN-OS, "
                   "MikroTik, Huawei, F5): SSH/TLS/SNMP/IKE/IPsec settings, password storage types, plus "
                   "telnet/HTTP/SNMP management probes")
    needs_network = False

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        if ctx.netdev_configs or ctx.extra_paths:
            return True, ""
        if ctx.active_probes and _probe_targets(ctx):
            return True, ""
        return False, "no device configs (--netdev-config) or netdev/snmp targets"

    def collect(self, ctx: ScanContext) -> List[Asset]:
        assets: List[Asset] = []
        files = _expand(ctx.netdev_configs, ctx)
        explicit = {os.path.realpath(f) for f in files}
        for f in files:
            text = _read_config(f)
            if text is None:
                ctx.log.debug("netdev: skipping unreadable/binary/large file %s", f)
                continue
            assets.append(parse_config(text, f, ctx))
        for f in _expand(ctx.extra_paths, ctx) if ctx.extra_paths else []:
            if os.path.realpath(f) in explicit:
                continue
            text = _read_config(f)
            if text is None:
                continue
            plat = detect_platform(text)
            if plat != "generic":
                assets.append(parse_config(text, f, ctx, plat))
        if ctx.active_probes:
            targets = _probe_targets(ctx)
            if targets:
                workers = max(1, int(ctx.opt("workers", 16) or 16))
                with ThreadPoolExecutor(max_workers=min(workers, len(targets))) as pool:
                    for res in pool.map(lambda t: self._safe_probe(t, ctx), targets):
                        if res is not None:
                            assets.append(res)
        return assets

    @staticmethod
    def _safe_probe(t: Target, ctx: ScanContext) -> Optional[Asset]:
        try:
            return probe_target(t, ctx)
        except Exception as e:      # never let one target kill the pool
            ctx.warn(f"netdev probe {t}: {type(e).__name__}: {e}")
            return None


__all__ = ["NetdevCollector", "detect_platform", "detect_version", "detect_hostname", "parse_config", "generic_heuristic",
           "looks_like_device_config", "probe_snmp", "probe_telnet", "probe_http", "parse_routeros"]
