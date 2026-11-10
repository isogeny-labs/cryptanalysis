"""Active TLS probing of remote endpoints (handshake only, no application data).

For every target the collector

* negotiates each protocol version (TLS 1.0-1.3) with the stdlib ``ssl`` module
  and records the versions the server accepts (never "disabled" ones);
* enumerates the cipher suites the *local* OpenSSL knows for TLS <= 1.2 and
  records those the server accepts (iterative elimination: offer the remaining
  suites, record the one the server picks, remove it, repeat; this needs about
  ``accepted + 1`` handshakes instead of one per suite, and is bounded by
  ``tls_max_handshakes``);
* uses ``openssl s_client`` (when installed) for what Python cannot select:
  key-exchange groups (X25519MLKEM768, X25519, secp256r1, ffdhe2048), the TLS 1.2
  ephemeral DH/ECDH parameters (Logjam detection), the TLS 1.3 suites one by one,
  SSLv3, OCSP stapling and session tickets;
* captures the certificate chain and emits CERTIFICATE assets plus one
  TLS_ENDPOINT asset carrying the protocol / suite / group uses.

STARTTLS is implemented for smtp, imap, pop3, ftp, ldap, postgres, xmpp and rdp
(X.224); mysql is recorded as "not implemented".  The collector never sends
credentials and closes every connection right after the handshake.
"""

from __future__ import annotations

import re
import socket
import ssl
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Tuple

from .. import names, x509
from ..model import Asset, AssetKind, CryptoUse, Primitive
from ..util import run_cmd, which
from . import register
from ._certassets import cert_attributes, cert_label, cert_uses, hostname_matches
from .base import Collector, ScanContext, Target

SERVICES = ("tls", "https", "smtp", "smtps", "imap", "imaps", "pop3", "pop3s", "ldap", "ldaps",
            "ftp", "ftps", "postgres", "mysql", "xmpp", "rdp", "auto")

# service -> (default port, starttls protocol or None for implicit TLS)
SERVICE_DEFAULTS: Dict[str, Tuple[int, Optional[str]]] = {
    "tls": (443, None), "https": (443, None), "smtp": (25, "smtp"), "smtps": (465, None),
    "imap": (143, "imap"), "imaps": (993, None), "pop3": (110, "pop3"), "pop3s": (995, None),
    "ldap": (389, "ldap"), "ldaps": (636, None), "ftp": (21, "ftp"), "ftps": (990, None),
    "postgres": (5432, "postgres"), "mysql": (3306, "mysql"), "xmpp": (5222, "xmpp"), "rdp": (3389, "rdp"),
}
# well-known ports for "auto"
STARTTLS_PORTS = {25: "smtp", 587: "smtp", 143: "imap", 110: "pop3", 21: "ftp", 389: "ldap",
                  5432: "postgres", 5222: "xmpp", 3306: "mysql", 3389: "rdp"}
DIRECT_TLS_PORTS = {443, 465, 993, 995, 636, 990, 989, 8443, 8883, 853, 9443, 5061, 6697, 5671, 2376, 6443, 10250, 8444}

LOCAL_CIPHER_STRING = "ALL:COMPLEMENTOFALL:@SECLEVEL=0"
VERSIONS = [("tls1.0", "TLSv1"), ("tls1.1", "TLSv1_1"), ("tls1.2", "TLSv1_2"), ("tls1.3", "TLSv1_3")]
TLS13_SUITES = ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256", "TLS_AES_128_GCM_SHA256",
                "TLS_AES_128_CCM_SHA256", "TLS_AES_128_CCM_8_SHA256"]
GROUP_PROBES = ["X25519MLKEM768", "X25519", "secp256r1", "secp384r1", "ffdhe2048"]


def resolve_mode(t: Target) -> Tuple[int, Optional[str]]:
    """(port, starttls protocol or None) for a target."""
    svc = (t.service or "auto").lower()
    if svc == "auto":
        if not t.port:
            return 443, None
        return t.port, STARTTLS_PORTS.get(t.port)
    default_port, starttls = SERVICE_DEFAULTS.get(svc, (443, None))
    port = t.port or default_port
    if starttls and t.port and t.port in DIRECT_TLS_PORTS and svc != "rdp":
        starttls = None                      # e.g. smtp on 465 is implicit TLS
    return port, starttls


# ---------------------------------------------------------------------------
# STARTTLS dialogues (plain socket, then the caller wraps with ssl)
# ---------------------------------------------------------------------------

class StarttlsError(Exception):
    pass


def _readline(sock: socket.socket, limit: int = 4096) -> bytes:
    buf = b""
    while not buf.endswith(b"\n") and len(buf) < limit:
        c = sock.recv(1)
        if not c:
            break
        buf += c
    return buf


def _read_smtp_reply(sock: socket.socket) -> Tuple[int, List[str]]:
    lines: List[str] = []
    code = 0
    for _ in range(100):
        line = _readline(sock).decode("latin-1").rstrip("\r\n")
        if not line:
            break
        lines.append(line)
        try:
            code = int(line[:3])
        except ValueError:
            break
        if line[3:4] != "-":
            break
    return code, lines


LDAP_STARTTLS_REQUEST = bytes.fromhex("301d02010177188016312e332e362e312e342e312e313436362e3230303337")


def ldap_starttls_result(resp: bytes) -> Optional[int]:
    """Parse an LDAP ExtendedResponse and return its resultCode (None if malformed)."""
    from .. import asn1
    try:
        msg, _ = asn1.decode_prefix(resp)
        op = msg.children[1]
        if op.tag_class != 1 or op.tag != 24:      # [APPLICATION 24] ExtendedResponse
            return None
        return int.from_bytes(op.children[0].value, "big")      # ENUMERATED resultCode
    except Exception:
        return None


def do_starttls(sock: socket.socket, proto: str, host: str) -> None:
    """Run the plaintext part of STARTTLS; raises StarttlsError when the server refuses."""
    if proto == "smtp":
        code, _ = _read_smtp_reply(sock)
        if code != 220:
            raise StarttlsError(f"smtp banner {code}")
        sock.sendall(b"EHLO cryptoscan.invalid\r\n")
        code, lines = _read_smtp_reply(sock)
        if code != 250 or not any("STARTTLS" in l.upper() for l in lines):
            raise StarttlsError("smtp server does not offer STARTTLS")
        sock.sendall(b"STARTTLS\r\n")
        code, _ = _read_smtp_reply(sock)
        if code != 220:
            raise StarttlsError(f"smtp STARTTLS refused ({code})")
    elif proto == "imap":
        _readline(sock)
        sock.sendall(b". STARTTLS\r\n")
        for _ in range(20):
            line = _readline(sock)
            if line.startswith(b". "):
                if not line.startswith(b". OK"):
                    raise StarttlsError("imap STARTTLS refused")
                return
            if not line:
                break
        raise StarttlsError("imap: no STARTTLS reply")
    elif proto == "pop3":
        _readline(sock)
        sock.sendall(b"STLS\r\n")
        if not _readline(sock).startswith(b"+OK"):
            raise StarttlsError("pop3 STLS refused")
    elif proto == "ftp":
        code, _ = _read_smtp_reply(sock)
        if code != 220:
            raise StarttlsError(f"ftp banner {code}")
        sock.sendall(b"AUTH TLS\r\n")
        code, _ = _read_smtp_reply(sock)
        if code != 234:
            raise StarttlsError(f"ftp AUTH TLS refused ({code})")
    elif proto == "ldap":
        sock.sendall(LDAP_STARTTLS_REQUEST)
        resp = sock.recv(4096)
        rc = ldap_starttls_result(resp)
        if rc != 0:
            raise StarttlsError(f"ldap StartTLS result code {rc}")
    elif proto == "postgres":
        sock.sendall(bytes.fromhex("00000008") + bytes.fromhex("04d2162f"))
        if sock.recv(1) != b"S":
            raise StarttlsError("postgres server refused SSLRequest")
    elif proto == "xmpp":
        sock.sendall(("<stream:stream xmlns='jabber:client' xmlns:stream='http://etherx.jabber.org/streams' "
                      f"to='{host}' version='1.0'>").encode())
        data = b""
        deadline = time.time() + 5
        while b"starttls" not in data.lower() and b"</stream:features>" not in data and time.time() < deadline:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        if b"starttls" not in data.lower():
            raise StarttlsError("xmpp server does not offer starttls")
        sock.sendall(b"<starttls xmlns='urn:ietf:params:xml:ns:xmpp-tls'/>")
        data = sock.recv(4096)
        if b"<proceed" not in data:
            raise StarttlsError("xmpp starttls refused")
    elif proto == "rdp":
        # X.224 Connection Request with RDP_NEG_REQ(requestedProtocols = TLS | CredSSP)
        sock.sendall(bytes([3, 0, 0, 0x13, 0x0E, 0xE0, 0, 0, 0, 0, 0, 1, 0, 8, 0, 3, 0, 0, 0]))
        resp = sock.recv(64)
        if len(resp) < 19 or resp[11] != 0x02 or resp[15] & 0x03 == 0:
            raise StarttlsError("rdp server did not select TLS/CredSSP")
    elif proto == "mysql":
        raise StarttlsError("mysql STARTTLS not implemented")
    else:
        raise StarttlsError(f"unknown STARTTLS protocol {proto}")


# ---------------------------------------------------------------------------
# One handshake
# ---------------------------------------------------------------------------

def _is_ip(host: str) -> bool:
    try:
        import ipaddress
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def make_context(version: Optional[str] = None, ciphers: Optional[str] = LOCAL_CIPHER_STRING,
                 alpn: Optional[List[str]] = None) -> ssl.SSLContext:
    """Client context that accepts anything: we measure the server, we do not trust it."""
    # This context deliberately allows TLS 1.0/1.1 and disables verification: it is a
    # probe that asks a server which legacy versions it still accepts; no data is sent over it.
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # codeql[py/insecure-protocol] lgtm[py/insecure-protocol]
    c.check_hostname = False  # codeql[py/insecure-default-protocol]
    c.verify_mode = ssl.CERT_NONE
    if ciphers:
        try:
            c.set_ciphers(ciphers)
        except ssl.SSLError:
            try:
                c.set_ciphers("ALL:COMPLEMENTOFALL")
            except ssl.SSLError:
                pass
    if version:
        with warnings.catch_warnings():             # TLSv1 / TLSv1_1 members are deprecated, still needed here
            warnings.simplefilter("ignore", DeprecationWarning)
            v = getattr(ssl.TLSVersion, version)
            c.minimum_version = v
            c.maximum_version = v
    else:
        try:
            c.minimum_version = ssl.TLSVersion.MINIMUM_SUPPORTED
        except (ValueError, ssl.SSLError):
            pass
    if alpn:
        try:
            c.set_alpn_protocols(alpn)
        except (NotImplementedError, ssl.SSLError):
            pass
    try:
        c.options &= ~getattr(ssl, "OP_NO_COMPRESSION", 0)    # let the server show whether it compresses
    except Exception:
        pass
    return c


def handshake(host: str, port: int, starttls: Optional[str], tctx: ssl.SSLContext, timeout: float,
              deadline: Optional[float] = None) -> ssl.SSLSocket:
    """Connect (+ STARTTLS) and complete the TLS handshake; caller closes the socket."""
    if deadline is not None:
        timeout = max(0.5, min(timeout, deadline - time.time()))
    raw = socket.create_connection((host, port), timeout=timeout)
    try:
        raw.settimeout(timeout)
        if starttls:
            do_starttls(raw, starttls, host)
        return tctx.wrap_socket(raw, server_hostname=None if _is_ip(host) else host)  # codeql[py/insecure-protocol] lgtm[py/insecure-protocol]
    except BaseException:
        raw.close()
        raise


def _chain_der(sock: ssl.SSLSocket) -> List[bytes]:
    out: List[bytes] = []
    fn = getattr(sock, "get_unverified_chain", None)
    if fn is not None:
        try:
            for item in fn() or []:
                if isinstance(item, (bytes, bytearray)):
                    out.append(bytes(item))
                elif hasattr(item, "public_bytes"):
                    out.append(item.public_bytes(ssl.ENCODING_DER) if hasattr(ssl, "ENCODING_DER") else item.public_bytes())
        except Exception:
            out = []
    if not out:
        try:
            leaf = sock.getpeercert(binary_form=True)
            if leaf:
                out = [leaf]
        except Exception:
            pass
    return out


# ---------------------------------------------------------------------------
# openssl s_client helpers
# ---------------------------------------------------------------------------

_STARTTLS_OPENSSL = {"smtp": "smtp", "imap": "imap", "pop3": "pop3", "ftp": "ftp", "ldap": "ldap",
                     "postgres": "postgres", "xmpp": "xmpp", "mysql": "mysql"}


def s_client(host: str, port: int, starttls: Optional[str], extra: List[str], timeout: float) -> Optional[str]:
    """Run openssl s_client with empty stdin; combined stdout+stderr text, or None when unavailable."""
    if which("openssl") is None or starttls == "rdp":
        return None
    argv = ["openssl", "s_client", "-connect", f"[{host}]:{port}" if ":" in host else f"{host}:{port}"]
    if not _is_ip(host):
        argv += ["-servername", host]
    if starttls in _STARTTLS_OPENSSL:
        argv += ["-starttls", _STARTTLS_OPENSSL[starttls]]
    argv += extra
    r = run_cmd(argv, timeout=timeout + 5, input_text="")
    if r.error:
        return None
    return (r.stdout or "") + "\n" + (r.stderr or "")


_RE_TEMP_ECDH = re.compile(r"Server Temp Key:\s*(?:ECDH|EC),\s*([^,\n]+),\s*(\d+)\s*bits", re.I)
_RE_TEMP_X = re.compile(r"Server Temp Key:\s*(X25519|X448),\s*(\d+)\s*bits", re.I)
_RE_TEMP_DH = re.compile(r"Server Temp Key:\s*DH,\s*(\d+)\s*bits", re.I)
_RE_NEG_GROUP = re.compile(r"Negotiated TLS1\.3 group:\s*(\S+)", re.I)
_RE_DIGEST = re.compile(r"Peer signing digest:\s*(\S+)", re.I)
_RE_SIGTYPE = re.compile(r"Peer signature type:\s*(\S+)", re.I)
_RE_PROTO = re.compile(r"^\s*Protocol\s*:\s*(\S+)", re.M)
_RE_CIPHER = re.compile(r"(?:^\s*Cipher\s*:\s*|Cipher is\s+)(\S+)", re.M)


def s_client_ok(text: Optional[str]) -> bool:
    if not text:
        return False
    m = _RE_CIPHER.search(text)
    return bool(m) and m.group(1).strip(",") not in ("0000", "(NONE)")


def group_use_from(text: str, tls13: bool) -> Optional[CryptoUse]:
    """Extract the negotiated (EC)DH group from s_client output as a CryptoUse."""
    m = _RE_NEG_GROUP.search(text)
    if m:
        return names.tls_group(m.group(1), negotiated=True)
    m = _RE_TEMP_X.search(text)
    if m:
        return names.tls_group(m.group(1), negotiated=True)
    m = _RE_TEMP_ECDH.search(text)
    if m:
        return names.tls_group(m.group(1).strip(), negotiated=True)
    m = _RE_TEMP_DH.search(text)
    if m:
        bits = int(m.group(1))
        if tls13:
            u = names.tls_group(f"ffdhe{bits}", negotiated=True)
            if u.algorithm != "unknown":
                return u
        return CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=bits, raw=f"DH {bits} bits",
                         context="tls-group", negotiated=True)
    return None


# ---------------------------------------------------------------------------
# Per-target probe
# ---------------------------------------------------------------------------

class _Budget:
    """Thread-safe handshake counter."""

    def __init__(self, n: int) -> None:
        self.left = n
        self.lock = threading.Lock()
        self.exhausted = False

    def take(self) -> bool:
        with self.lock:
            if self.left <= 0:
                self.exhausted = True
                return False
            self.left -= 1
            return True


def _local_suites() -> List[dict]:
    c = make_context("TLSv1_2")
    try:
        return [s for s in c.get_ciphers() if s.get("protocol") != "TLSv1.3"]
    except Exception:
        return []


def _enumerate_suites(host: str, port: int, starttls: Optional[str], version: str, label: str,
                      suites: List[dict], budget: _Budget, timeout: float, deadline: float) -> List[str]:
    """Iterative elimination: returns accepted suite names (OpenSSL spelling) for one protocol."""
    candidates = [s["name"] for s in suites
                  if not (version in ("TLSv1", "TLSv1_1") and s.get("protocol") == "TLSv1.2")]
    accepted: List[str] = []
    while candidates and time.time() < deadline and budget.take():
        c = make_context(version, ":".join(candidates) + ":@SECLEVEL=0")
        try:
            s = handshake(host, port, starttls, c, timeout, deadline)
        except (OSError, ssl.SSLError, StarttlsError, ValueError):
            break
        try:
            ci = s.cipher()
        finally:
            _close(s)
        if not ci or ci[0] not in candidates:
            break
        accepted.append(ci[0])
        candidates.remove(ci[0])
    return accepted


def _close(s) -> None:
    try:
        s.close()
    except Exception:
        pass


def _chain_assets(ctx: ScanContext, target: Target, port: int, ders: List[bytes], loc: str,
                  trust_subjects: Dict[str, List[Optional[str]]]) -> Tuple[List[Asset], Dict[str, object]]:
    assets: List[Asset] = []
    info: Dict[str, object] = {}
    certs: List[x509.Certificate] = []
    for d in ders:
        try:
            certs.append(x509.parse_certificate(d))
        except Exception as e:
            info.setdefault("chain_parse_errors", []).append(str(e))
    info["chain_length"] = len(certs)
    for i, cert in enumerate(certs):
        role = "leaf" if i == 0 else ("root" if cert.self_signed else "intermediate")
        attrs = cert_attributes(cert)
        attrs["chain_position"] = i
        attrs["trust_anchor"] = False
        if i == 0:
            attrs["hostname_match"] = hostname_matches(cert, target.host)
        a = Asset(AssetKind.CERTIFICATE, f"{cert_label(cert)} ({role})", loc, "tls_remote", host=target.host,
                  uses=cert_uses(cert), attributes=attrs)
        assets.append(a)
    if certs:
        last = certs[-1]
        if not last.self_signed:
            known = trust_subjects.get(last.issuer)
            in_store = bool(known) and (last.authority_key_id is None or last.authority_key_id in known or None in known)
            if not in_store:
                info["chain_incomplete"] = True
                assets[-1].attributes["chain_incomplete"] = True
    return assets, info


def _load_trust(ctx: ScanContext) -> Dict[str, List[Optional[str]]]:
    """subject DN -> [SKI, ...] from the local CA bundle (best effort)."""
    out: Dict[str, List[Optional[str]]] = {}
    from ..util import read_bytes
    for p in ("/etc/ssl/certs/ca-certificates.crt", "/etc/pki/tls/certs/ca-bundle.crt", "/etc/ssl/cert.pem"):
        data = read_bytes(ctx.path(p), 16 * 1024 * 1024)
        if not data:
            continue
        for c in x509.load_certificates(data):
            out.setdefault(c.subject, []).append(c.subject_key_id)
        break
    return out


def probe_target(ctx: ScanContext, target: Target, trust: Dict[str, List[Optional[str]]]) -> List[Asset]:
    """Probe one endpoint; never raises."""
    port, starttls = resolve_mode(target)
    host = target.host
    loc = f"{host}:{port}"
    timeout = float(ctx.timeout)
    deadline = time.time() + float(ctx.opt("tls_target_deadline", 90))
    ep = Asset(AssetKind.TLS_ENDPOINT, f"TLS {loc}" + (f" ({starttls} STARTTLS)" if starttls else ""), loc,
               "tls_remote", host=host)
    ep.attributes.update({"port": port, "service": target.service or "auto", "starttls": starttls,
                          "sni": None if _is_ip(host) else host})
    assets: List[Asset] = [ep]
    budget = _Budget(int(ctx.opt("tls_max_handshakes", 120)))
    have_openssl = which("openssl") is not None

    # -- protocol versions ------------------------------------------------
    working: List[str] = []
    ders: List[bytes] = []
    first_sock_info: Dict[str, object] = {}
    probe_notes: List[str] = []
    refused = False
    for canon, ver in VERSIONS:
        if time.time() > deadline:
            ep.errors.append("per-target deadline reached during protocol probing")
            break
        try:
            c = make_context(ver, alpn=["h2", "http/1.1"])
        except (ValueError, ssl.SSLError) as e:
            probe_notes.append(f"{canon}: local OpenSSL cannot probe ({e})")
            continue
        try:
            s = handshake(host, port, starttls, c, timeout, deadline)
        except ConnectionRefusedError:
            refused = True
            ep.errors.append(f"connection refused: {loc}")
            break
        except (socket.timeout, TimeoutError):
            ep.errors.append(f"timeout connecting to {loc}")
            break
        except StarttlsError as e:
            ep.errors.append(f"STARTTLS: {e}")
            ep.attributes["starttls_error"] = str(e)
            break
        except (OSError, ssl.SSLError, ValueError):
            continue
        try:
            ep.add(names.tls_protocol(canon, negotiated=True))
            working.append(canon)
            if canon == "tls1.3":
                ep.attributes["tls1.3"] = True
            if not ders:
                ders = _chain_der(s)
            if not first_sock_info:
                first_sock_info = {"alpn": s.selected_alpn_protocol(), "compression": s.compression(),
                                   "server_name": host if not _is_ip(host) else None}
            ci = s.cipher()
            if canon == "tls1.3" and ci:
                ep.add(names.tls_cipher_suite(ci[0], protocol="tls1.3", negotiated=True))
        finally:
            _close(s)
    ep.attributes["tls1.3"] = "tls1.3" in working
    ep.attributes["protocols"] = working
    if probe_notes:
        ep.attributes["probe_notes"] = probe_notes
    if refused or not working:
        if not ep.errors:
            ep.errors.append(f"no TLS protocol version negotiated with {loc}")
        return assets
    ep.attributes.update(first_sock_info)
    ep.attributes["alpn"] = first_sock_info.get("alpn")
    ep.attributes["compression"] = first_sock_info.get("compression")

    # -- cipher suites (TLS <= 1.2), one worker per protocol -----------------
    suites = _local_suites()
    legacy = [v for v in working if v != "tls1.3"]
    verkey = {c: v for c, v in VERSIONS}
    seen: set = set()
    if suites and legacy:
        with ThreadPoolExecutor(max_workers=min(4, len(legacy))) as pool:
            futs = {p: pool.submit(_enumerate_suites, host, port, starttls, verkey[p], p, suites, budget, timeout, deadline)
                    for p in legacy}
            for p in legacy:
                try:
                    names_ok = futs[p].result()
                except Exception as e:
                    ep.errors.append(f"cipher enumeration {p}: {e}")
                    continue
                for n in names_ok:
                    ep.add(names.tls_cipher_suite(n, protocol=p, negotiated=True))
                    seen.add((p, n))
        if budget.exhausted:
            ep.attributes["cipher_enum_truncated"] = True
    elif legacy:
        ep.attributes["cipher_enum"] = "local OpenSSL lists no suites"
    ep.attributes["accepted_suites"] = sorted({n for _, n in seen})

    # -- openssl-driven probes ---------------------------------------------
    if not have_openssl:
        ep.attributes["group_probe"] = "openssl unavailable"
        ep.attributes["sslv3_probe"] = "unsupported"
    elif starttls == "rdp":
        ep.attributes["group_probe"] = "openssl s_client cannot do RDP"
        ep.attributes["sslv3_probe"] = "unsupported"
    else:
        _openssl_probes(ep, host, port, starttls, working, timeout, deadline)

    # -- OCSP / ticket from the default handshake (also fills chain fallback) ---
    main = s_client(host, port, starttls, ["-status", "-showcerts"], timeout) if have_openssl and starttls != "rdp" else None
    if main:
        m = re.search(r"OCSP Response Status:\s*(\w+)", main)
        ep.attributes["ocsp_stapling"] = bool(m and m.group(1).lower() == "successful")
        ep.attributes["session_ticket"] = ("session ticket lifetime hint" in main.lower()
                                           or "new session ticket" in main.lower())
        if not ders:
            ders = [x.der for x in x509.load_certificates(main.encode("latin-1", "replace"))]
        sig = _sig_uses(main)
        for u in sig:
            ep.add(u)
    elif have_openssl:
        ep.attributes["ocsp_stapling"] = None

    # -- certificate chain ---------------------------------------------------
    cert_assets, info = _chain_assets(ctx, target, port, ders, loc, trust)
    ep.attributes.update(info)
    if cert_assets:
        ep.attributes["hostname_match"] = cert_assets[0].attributes.get("hostname_match")
        leaf = cert_assets[0]
        ep.attributes["leaf_sha256"] = leaf.attributes.get("sha256")
    assets.extend(cert_assets)
    return assets


def _sig_uses(text: str) -> List[CryptoUse]:
    out: List[CryptoUse] = []
    dm = _RE_DIGEST.search(text)
    sm = _RE_SIGTYPE.search(text)
    if sm or dm:
        typ = (sm.group(1) if sm else "").lower()
        dig = (dm.group(1) if dm else "").lower()
        if typ.startswith("rsa-pss"):
            raw = f"rsa_pss_rsae_{dig}"
        elif typ == "rsa":
            raw = f"rsa_pkcs1_{dig}"
        elif typ in ("ecdsa", "ec"):
            raw = {"sha256": "ecdsa_secp256r1_sha256", "sha384": "ecdsa_secp384r1_sha384",
                   "sha512": "ecdsa_secp521r1_sha512", "sha1": "ecdsa_sha1"}.get(dig, f"ecdsa_{dig}")
        elif typ in ("ed25519", "ed448"):
            raw = typ
        else:
            raw = f"{typ}_{dig}".strip("_")
        u = names.tls_sigalg(raw, negotiated=True)
        if u.algorithm == raw and dig:     # unknown spelling: still keep the digest for the policy
            u.hash_algorithm = names.hash_name(dig)
        out.append(u)
    return out


def _openssl_probes(ep: Asset, host: str, port: int, starttls: Optional[str], working: List[str],
                    timeout: float, deadline: float) -> None:
    """Groups, TLS 1.3 suites, TLS 1.2 ephemeral DH parameters and SSLv3 via openssl s_client."""
    # SSLv3 / SSLv2
    if starttls is None:
        r = s_client(host, port, starttls, ["-ssl3"], timeout)
        if r is None:
            ep.attributes["sslv3_probe"] = "unsupported"
        elif s_client_ok(r) and "SSLv3" in r:
            ep.add(names.tls_protocol("sslv3", negotiated=True))
            ep.attributes["sslv3_probe"] = "accepted"
        elif "unknown option" in r.lower() or "ssl3" in r.lower() and "unsupported" in r.lower():
            ep.attributes["sslv3_probe"] = "unsupported"
        else:
            ep.attributes["sslv3_probe"] = "rejected" if "alert" in r.lower() or "wrong version" in r.lower() else "unsupported"
    else:
        ep.attributes["sslv3_probe"] = "unsupported"
    groups_seen: set = set()

    def add_group(u: Optional[CryptoUse]) -> None:
        if u is None:
            return
        key = (u.algorithm, u.raw, u.key_bits)
        if key in groups_seen:
            return
        groups_seen.add(key)
        ep.add(u)

    if "tls1.3" in working:
        for g in GROUP_PROBES:
            if time.time() > deadline:
                break
            t = s_client(host, port, starttls, ["-tls1_3", "-groups", g], timeout)
            if s_client_ok(t) and "TLSv1.3" in (t or ""):
                add_group(group_use_from(t, True))
        for suite in TLS13_SUITES:
            if time.time() > deadline:
                break
            t = s_client(host, port, starttls, ["-tls1_3", "-ciphersuites", suite], timeout)
            if s_client_ok(t):
                m = _RE_CIPHER.search(t)
                if m and m.group(1).startswith("TLS_") and not any(
                        u.raw == m.group(1) and u.extra.get("protocol") == "tls1.3" for u in ep.uses):
                    ep.add(names.tls_cipher_suite(m.group(1), protocol="tls1.3", negotiated=True))
    if "tls1.2" in working:
        for cs in ("kDHE", "kECDHE"):
            if time.time() > deadline:
                break
            t = s_client(host, port, starttls, ["-tls1_2", "-cipher", f"{cs}:@SECLEVEL=0"], timeout)
            if s_client_ok(t):
                add_group(group_use_from(t, False))
    ep.attributes.setdefault("group_probe", "openssl s_client")


@register
class TlsRemoteCollector(Collector):
    name = "tls_remote"
    description = "Handshake-only TLS probing: protocols, cipher suites, groups, certificate chain, STARTTLS"
    needs_network = True

    def applicable(self, ctx: ScanContext) -> Tuple[bool, str]:
        ok, why = super().applicable(ctx)
        if not ok:
            return ok, why
        if not any((t.service or "auto").lower() in SERVICES for t in ctx.targets):
            return False, "no TLS-capable targets"
        return True, ""

    def collect(self, ctx: ScanContext) -> List[Asset]:
        targets = [t for t in ctx.targets if (t.service or "auto").lower() in SERVICES]
        trust = _load_trust(ctx)
        workers = max(1, int(ctx.opt("workers", 16)))

        def run(t: Target) -> List[Asset]:
            try:
                return probe_target(ctx, t, trust)
            except Exception as e:     # a probe bug must not lose the other targets
                a = Asset(AssetKind.TLS_ENDPOINT, f"TLS {t}", str(t), "tls_remote", host=t.host)
                a.errors.append(f"probe failed: {type(e).__name__}: {e}")
                return [a]

        out: List[Asset] = []
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for res in pool.map(run, targets):
                out.extend(res)
        return out
