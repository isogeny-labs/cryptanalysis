"""Pure-stdlib SSH transport probe (RFC 4253 sections 4 and 7.1).

The probe is passive: it reads the server identification string, sends its own
identification string and one KEXINIT, reads the server's KEXINIT and closes
the socket.  No key exchange is completed, nothing is authenticated and no
credentials are sent.  The server's KEXINIT lists everything it supports, which
is what an algorithm inventory needs.

Public API: `probe(host, port, timeout)` -> `SSHProbe`, `parse_banner`,
`build_kexinit`, `parse_packet`, `parse_kexinit`, and
`fetch_host_keys(host, port, ctx)` (optional `ssh-keyscan`, also passive).
"""

from __future__ import annotations

import os
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from . import sshkeys, util
from .x509 import PublicKeyInfo

CLIENT_BANNER = "SSH-2.0-cryptoscan_0.1"
MSG_DISCONNECT, MSG_IGNORE, MSG_DEBUG, MSG_KEXINIT = 1, 2, 4, 20
MAX_PACKET = 35000          # RFC 4253 section 6.1 minimum every implementation must accept
MAX_BANNER_BYTES = 64 * 1024

OFFER_KEX = [
    "curve25519-sha256", "curve25519-sha256@libssh.org", "ecdh-sha2-nistp256", "ecdh-sha2-nistp384",
    "ecdh-sha2-nistp521", "diffie-hellman-group-exchange-sha256", "diffie-hellman-group16-sha512",
    "diffie-hellman-group18-sha512", "diffie-hellman-group14-sha256", "diffie-hellman-group14-sha1",
    "diffie-hellman-group-exchange-sha1", "diffie-hellman-group1-sha1", "ext-info-c",
    "kex-strict-c-v00@openssh.com",
]
OFFER_HOSTKEY = [
    "ssh-ed25519", "ecdsa-sha2-nistp256", "ecdsa-sha2-nistp384", "ecdsa-sha2-nistp521",
    "rsa-sha2-512", "rsa-sha2-256", "ssh-rsa", "ssh-dss",
]
OFFER_CIPHERS = [
    "chacha20-poly1305@openssh.com", "aes128-ctr", "aes192-ctr", "aes256-ctr", "aes128-gcm@openssh.com",
    "aes256-gcm@openssh.com", "aes128-cbc", "aes192-cbc", "aes256-cbc", "3des-cbc", "blowfish-cbc",
    "cast128-cbc", "arcfour", "arcfour128", "arcfour256",
]
OFFER_MACS = [
    "hmac-sha2-256-etm@openssh.com", "hmac-sha2-512-etm@openssh.com", "hmac-sha1-etm@openssh.com",
    "umac-128-etm@openssh.com", "hmac-sha2-256", "hmac-sha2-512", "hmac-sha1", "umac-64@openssh.com",
    "umac-128@openssh.com", "hmac-md5", "hmac-md5-96", "hmac-sha1-96",
]
OFFER_COMPRESSION = ["none", "zlib@openssh.com", "zlib"]

KEX_STRICT_MARKER = "kex-strict-s-v00@openssh.com"
EXT_INFO_MARKER = "ext-info-s"


class SSHProbeError(Exception):
    """Raised internally; `probe()` converts it into SSHProbe.error."""


@dataclass
class SSHProbe:
    host: str = ""
    port: int = 22
    ok: bool = False
    error: Optional[str] = None
    banner: str = ""                      # "SSH-2.0-OpenSSH_9.6p1 Ubuntu-3"
    protocol_version: str = ""            # "2.0", "1.99", "1.5"
    software: str = ""                    # "OpenSSH_9.6p1"
    banner_comment: str = ""
    pre_banner: List[str] = field(default_factory=list)
    kex: List[str] = field(default_factory=list)
    hostkey: List[str] = field(default_factory=list)
    ciphers_c2s: List[str] = field(default_factory=list)
    ciphers_s2c: List[str] = field(default_factory=list)
    macs_c2s: List[str] = field(default_factory=list)
    macs_s2c: List[str] = field(default_factory=list)
    compression_c2s: List[str] = field(default_factory=list)
    compression_s2c: List[str] = field(default_factory=list)
    languages_c2s: List[str] = field(default_factory=list)
    languages_s2c: List[str] = field(default_factory=list)
    first_kex_follows: bool = False
    kex_strict: bool = False
    ext_info: bool = False

    @property
    def ciphers(self) -> List[str]:
        return _union(self.ciphers_c2s, self.ciphers_s2c)

    @property
    def macs(self) -> List[str]:
        return _union(self.macs_c2s, self.macs_s2c)

    @property
    def compression(self) -> List[str]:
        return _union(self.compression_c2s, self.compression_s2c)

    @property
    def languages(self) -> List[str]:
        return _union(self.languages_c2s, self.languages_s2c)


def _union(a: List[str], b: List[str]) -> List[str]:
    out = list(a)
    out.extend(x for x in b if x not in out)
    return out


# ---------------------------------------------------------------------------
# pure parsing / building helpers (unit-testable without a socket)
# ---------------------------------------------------------------------------

def parse_banner(line: str) -> Tuple[str, str, str]:
    """Split "SSH-protoversion-softwareversion SP comments" -> (proto, software, comment).

    Raises ValueError when `line` is not an SSH identification string.
    """
    line = line.strip("\r\n")
    if not line.startswith("SSH-"):
        raise ValueError("not an SSH identification string")
    body = line[4:]
    proto, sep, rest = body.partition("-")
    if not sep or not proto:
        raise ValueError("malformed SSH identification string")
    software, _, comment = rest.partition(" ")
    return proto, software, comment


def _namelist(names: List[str]) -> bytes:
    raw = ",".join(names).encode("ascii")
    return struct.pack(">I", len(raw)) + raw


def build_kexinit(cookie: Optional[bytes] = None) -> bytes:
    """Return the KEXINIT *payload* (message byte 20 onwards)."""
    cookie = cookie if cookie is not None else os.urandom(16)
    if len(cookie) != 16:
        raise ValueError("cookie must be 16 bytes")
    p = bytes([MSG_KEXINIT]) + cookie
    for names in (OFFER_KEX, OFFER_HOSTKEY, OFFER_CIPHERS, OFFER_CIPHERS, OFFER_MACS, OFFER_MACS,
                  OFFER_COMPRESSION, OFFER_COMPRESSION, [], []):
        p += _namelist(names)
    return p + b"\x00" + struct.pack(">I", 0)


def build_packet(payload: bytes, padding: Optional[bytes] = None) -> bytes:
    """Wrap a payload in the unencrypted binary packet format (RFC 4253 section 6)."""
    pad = 8 - ((5 + len(payload)) % 8)
    if pad < 4:
        pad += 8
    padding = padding if padding is not None else os.urandom(pad)
    pad = len(padding)
    return struct.pack(">IB", 1 + len(payload) + pad, pad) + payload + padding


def parse_packet(buf: bytes) -> Optional[Tuple[bytes, int]]:
    """Return (payload, bytes_consumed) for the first packet in `buf`, None if incomplete.

    Raises SSHProbeError for an implausible length (not SSH, or encrypted already).
    """
    if len(buf) < 5:
        return None
    length, pad = struct.unpack(">IB", buf[:5])
    if length < 2 or length > MAX_PACKET or pad + 1 > length:
        raise SSHProbeError(f"implausible SSH packet length {length}")
    if len(buf) < 4 + length:
        return None
    payload = buf[5:4 + length - pad]
    return payload, 4 + length


def parse_kexinit(payload: bytes) -> dict:
    """Parse a KEXINIT payload into a dict of the ten name-lists plus flags."""
    if not payload or payload[0] != MSG_KEXINIT:
        raise SSHProbeError("not a KEXINIT message")
    if len(payload) < 17:
        raise SSHProbeError("truncated KEXINIT")
    off = 17
    keys = ("kex", "hostkey", "ciphers_c2s", "ciphers_s2c", "macs_c2s", "macs_s2c",
            "compression_c2s", "compression_s2c", "languages_c2s", "languages_s2c")
    out: dict = {"cookie": payload[1:17]}
    for k in keys:
        if off + 4 > len(payload):
            raise SSHProbeError("truncated KEXINIT name-list")
        (n,) = struct.unpack(">I", payload[off:off + 4])
        off += 4
        if off + n > len(payload):
            raise SSHProbeError("truncated KEXINIT name-list")
        text = payload[off:off + n].decode("ascii", "replace")
        out[k] = [x for x in text.split(",") if x]
        off += n
    out["first_kex_follows"] = bool(payload[off]) if off < len(payload) else False
    return out


# ---------------------------------------------------------------------------
# network probe
# ---------------------------------------------------------------------------

class _Reader:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buf = b""

    def fill(self) -> bool:
        data = self.sock.recv(4096)
        if not data:
            return False
        self.buf += data
        return True

    def line(self) -> Optional[str]:
        """Next text line (without terminator), or None on EOF."""
        while True:
            i = self.buf.find(b"\n")
            if i >= 0:
                raw, self.buf = self.buf[:i], self.buf[i + 1:]
                return raw.rstrip(b"\r").decode("utf-8", "replace")
            if len(self.buf) > 4096:
                raise SSHProbeError("not an SSH service (overlong line before identification string)")
            if not self.fill():
                return None


def probe(host: str, port: int = 22, timeout: float = 8.0) -> SSHProbe:
    """Handshake-only probe of an SSH server.  Never raises; see `SSHProbe.error`."""
    r = SSHProbe(host=host, port=port)
    h = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    sock: Optional[socket.socket] = None
    try:
        sock = socket.create_connection((h, port), timeout=timeout)
        _probe_on(sock, r, timeout)
    except SSHProbeError as e:
        r.error = str(e)
    except socket.timeout:
        r.error = f"timed out after {timeout}s"
    except ConnectionRefusedError:
        r.error = "connection refused"
    except (OSError, UnicodeError) as e:
        r.error = f"{type(e).__name__}: {e}"
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass
    return r


def _probe_on(sock: socket.socket, r: SSHProbe, timeout: float) -> None:
    """Drive the exchange on a connected socket (separate so tests can reuse it)."""
    reader = _Reader(sock)
    deadline = time.monotonic() + max(timeout, 1.0) * 2
    sent_banner = False
    # Phase 1: wait briefly for the server banner; some servers wait for ours first.
    sock.settimeout(min(1.5, timeout))
    total = 0
    while True:
        try:
            line = reader.line()
        except socket.timeout:
            if sent_banner:
                raise
            sock.sendall((CLIENT_BANNER + "\r\n").encode())
            sent_banner = True
            sock.settimeout(timeout)
            continue
        if line is None:
            raise SSHProbeError("connection closed before an SSH identification string (not an SSH service?)")
        total += len(line) + 1
        if line.startswith("SSH-"):
            try:
                r.protocol_version, r.software, r.banner_comment = parse_banner(line)
            except ValueError as e:
                raise SSHProbeError(str(e))
            r.banner = line
            break
        r.pre_banner.append(line[:255])
        if total > MAX_BANNER_BYTES or len(r.pre_banner) > 200:
            raise SSHProbeError("not an SSH service (no identification string)")
        if time.monotonic() > deadline:
            raise SSHProbeError("timed out waiting for identification string")
    sock.settimeout(timeout)
    if not sent_banner:
        sock.sendall((CLIENT_BANNER + "\r\n").encode())
    if r.protocol_version.startswith("1.") and r.protocol_version != "1.99":
        r.ok = True               # SSHv1-only server: no binary-packet KEXINIT to read
        return
    sock.sendall(build_packet(build_kexinit()))
    # Phase 2: read packets until the server KEXINIT.
    for _ in range(8):
        while True:
            got = parse_packet(reader.buf)
            if got is not None:
                break
            if time.monotonic() > deadline:
                raise SSHProbeError("timed out waiting for KEXINIT")
            if not reader.fill():
                raise SSHProbeError("connection closed before KEXINIT")
        payload, used = got
        reader.buf = reader.buf[used:]
        if not payload:
            continue
        if payload[0] == MSG_KEXINIT:
            k = parse_kexinit(payload)
            for name in ("kex", "hostkey", "ciphers_c2s", "ciphers_s2c", "macs_c2s", "macs_s2c",
                         "compression_c2s", "compression_s2c", "languages_c2s", "languages_s2c"):
                setattr(r, name, k[name])
            r.first_kex_follows = k["first_kex_follows"]
            r.kex_strict = KEX_STRICT_MARKER in r.kex
            r.ext_info = EXT_INFO_MARKER in r.kex
            r.ok = True
            return
        if payload[0] == MSG_DISCONNECT:
            reason = ""
            if len(payload) >= 9:
                (n,) = struct.unpack(">I", payload[5:9])
                reason = payload[9:9 + min(n, 200)].decode("utf-8", "replace")
            raise SSHProbeError(f"server disconnected before KEXINIT: {reason}".rstrip(": "))
        if payload[0] in (MSG_IGNORE, MSG_DEBUG):
            continue
        raise SSHProbeError(f"unexpected SSH message type {payload[0]} before KEXINIT")
    raise SSHProbeError("no KEXINIT received")


# ---------------------------------------------------------------------------
# ssh-keyscan (optional, passive)
# ---------------------------------------------------------------------------

@dataclass
class ScannedKey:
    key_type: str
    info: PublicKeyInfo
    line: str


def fetch_host_keys(host: str, port: int, ctx) -> List[ScannedKey]:
    """Run `ssh-keyscan` (when installed) and parse the public host keys it prints.

    ssh-keyscan only performs the key exchange far enough to receive the host
    key; it never authenticates.  Returns [] when the binary is absent.
    """
    exe = util.which("ssh-keyscan")
    if exe is None:
        return []
    h = host[1:-1] if host.startswith("[") and host.endswith("]") else host
    timeout = max(1, int(getattr(ctx, "timeout", 8.0)))
    res = util.run_cmd([exe, "-T", str(timeout), "-t", "rsa,dsa,ecdsa,ed25519", "-p", str(port), h],
                       timeout=float(getattr(ctx, "cmd_timeout", 20.0)) + timeout)
    out: List[ScannedKey] = []
    seen = set()
    for line in res.stdout.splitlines():
        if line.startswith("#"):
            continue
        parsed = sshkeys.parse_public_line(line)
        if parsed is None:
            continue
        ktype, info, _comment = parsed
        key = (ktype, info.key_bits, info.curve)
        if key in seen:
            continue
        seen.add(key)
        out.append(ScannedKey(ktype, info, line.strip()))
    return out
