"""Regenerate the SSH fixtures under tests/fixtures/ssh (run once; output is committed).

The keys are SYNTHETIC: well-formed OpenSSH public blobs / openssh-key-v1 files
with random (deterministically seeded) numbers of the stated size.  They are not
usable keys, which is all the parser tests need, and it avoids requiring
ssh-keygen (modern builds refuse RSA-1024).  Usage: python3 gen_fixtures.py
"""
import base64
import os
import random
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
rng = random.Random(20261110)


def s(b: bytes) -> bytes:
    return struct.pack(">I", len(b)) + b


def mpint(n: int) -> bytes:
    b = n.to_bytes((n.bit_length() + 8) // 8, "big")
    return s(b)


def rnd_int(bits: int) -> int:
    return rng.getrandbits(bits) | (1 << (bits - 1)) | 1


def rsa_blob(bits: int) -> bytes:
    return s(b"ssh-rsa") + mpint(65537) + mpint(rnd_int(bits))


def dss_blob() -> bytes:
    return s(b"ssh-dss") + mpint(rnd_int(1024)) + mpint(rnd_int(160)) + mpint(rnd_int(1023)) + mpint(rnd_int(1022))


def ecdsa_blob(curve: str = "nistp256", size: int = 32) -> bytes:
    pt = b"\x04" + bytes(rng.getrandbits(8) for _ in range(2 * size))
    return s(b"ecdsa-sha2-" + curve.encode()) + s(curve.encode()) + s(pt)


def ed25519_blob() -> bytes:
    return s(b"ssh-ed25519") + s(bytes(rng.getrandbits(8) for _ in range(32)))


def ktype(blob: bytes) -> str:
    n = struct.unpack(">I", blob[:4])[0]
    return blob[4:4 + n].decode()


def pub_line(blob: bytes, comment: str = "") -> str:
    return f"{ktype(blob)} {base64.b64encode(blob).decode()} {comment}".rstrip() + "\n"


def priv_file(blob: bytes, encrypted: bool = False) -> bytes:
    cipher, kdf = (b"aes256-ctr", b"bcrypt") if encrypted else (b"none", b"none")
    kdfopts = s(bytes(rng.getrandbits(8) for _ in range(16))) + struct.pack(">I", 16) if encrypted else b""
    body = b"openssh-key-v1\x00" + s(cipher) + s(kdf) + s(kdfopts) + struct.pack(">I", 1) + s(blob)
    body += s(bytes(rng.getrandbits(8) for _ in range(96)))
    b64 = base64.b64encode(body).decode()
    lines = [b64[i:i + 70] for i in range(0, len(b64), 70)]
    return ("-----BEGIN OPENSSH PRIVATE KEY-----\n" + "\n".join(lines) + "\n-----END OPENSSH PRIVATE KEY-----\n").encode()


def w(rel: str, data, mode: int = 0o644) -> None:
    p = os.path.join(HERE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data if isinstance(data, bytes) else data.encode())
    os.chmod(p, mode)


def main() -> None:
    e = "etc/ssh/"
    for name, blob, enc in (("rsa", rsa_blob(1024), False), ("ed25519", ed25519_blob(), False), ("dsa", dss_blob(), False)):
        w(f"{e}ssh_host_{name}_key", priv_file(blob, enc), 0o644)       # world-readable on purpose
        w(f"{e}ssh_host_{name}_key.pub", pub_line(blob, "root@fixture"))
    ecd = ecdsa_blob()
    w(f"{e}ssh_host_ecdsa_key", priv_file(ecd), 0o600)
    w(f"{e}ssh_host_ecdsa_key.pub", pub_line(ecd, "root@fixture"))
    w(f"{e}ssh_known_hosts", "# system known hosts\nfixture.example.org,10.0.0.5 " + pub_line(rsa_blob(2048)))
    w(f"{e}moduli", "# Time Type Tests Tries Size Generator Modulus\n"
      "20230101000000 2 6 100 1023 2 C0FFEE\n"      # 1024-bit group: weak
      "20230101000000 2 6 100 1535 2 C0FFEE\n"      # 1536-bit: weak
      "20230101000000 2 6 100 2047 2 C0FFEE\n"      # 2048-bit: fine
      "20230101000000 2 6 100 3071 2 C0FFEE\n")
    w(f"{e}sshd_config", """# fixture sshd_config
Include /etc/ssh/sshd_config.d/*.conf
Port 22
Protocol 2,1
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_dsa_key
KexAlgorithms +diffie-hellman-group14-sha1
Ciphers ^aes128-cbc
MACs ^hmac-sha1
HostKeyAlgorithms ssh-rsa,rsa-sha2-512,ssh-ed25519
PubkeyAcceptedAlgorithms -*-cert-v01@openssh.com
FingerprintHash md5
RequiredRSASize 1024

Match User backup
    Ciphers +3des-cbc
    PubkeyAcceptedAlgorithms +ssh-rsa
Match all
""")
    w(f"{e}sshd_config.d/10-local.conf", "CASignatureAlgorithms ssh-ed25519,ssh-rsa\nMACs hmac-md5,hmac-sha2-256\n")
    w(f"{e}ssh_config", """# fixture ssh_config
Host legacy
    KexAlgorithms diffie-hellman-group1-sha1
    Ciphers 3des-cbc
Host *
    FingerprintHash sha256
""")
    w(f"{e}ssh_config.d/20-extra.conf", "Host *\n    MACs hmac-sha2-512-etm@openssh.com\n")
    h = "home/alice/.ssh/"
    rsa3072 = rsa_blob(3072)
    w(f"{h}id_rsa", priv_file(rsa3072, True), 0o600)
    w(f"{h}id_rsa.pub", pub_line(rsa3072, "alice@fixture"))
    ed = ed25519_blob()
    w(f"{h}id_ed25519", priv_file(ed), 0o640)                         # group-readable + unencrypted
    w(f"{h}id_ed25519.pub", pub_line(ed, "alice@fixture"))
    ec = ecdsa_blob()
    w(f"{h}id_ecdsa.pub", pub_line(ec, "alice@laptop"))              # public only
    w(f"{h}authorized_keys",
      "# keys\n" + pub_line(rsa_blob(1024), "old@box")
      + 'command="/bin/true",no-pty ' + pub_line(ed, "restricted")
      + pub_line(dss_blob(), "ancient")
      + "this line is not a key\n")
    w(f"{h}known_hosts",
      "github.example.com " + pub_line(rsa_blob(3072))
      + "|1|c2FsdHNhbHRzYWx0c2FsdA==|aGFzaGhhc2hoYXNoaGFzaGhhc2g= " + pub_line(ecdsa_blob("nistp384", 48))
      + "@cert-authority *.corp.example " + pub_line(ed))
    # dropbear: wire-format key files
    w("etc/dropbear/dropbear_rsa_host_key", rsa_blob(2048) + mpint(rnd_int(2048)), 0o600)
    w("etc/dropbear/dropbear_ed25519_host_key", s(b"ssh-ed25519") + s(b"\x01" * 32), 0o600)


if __name__ == "__main__":
    main()
