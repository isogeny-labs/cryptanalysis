"""Normalisation of algorithm names from different ecosystems into CryptoUse.

Every collector funnels raw names through here so that the policy engine only
ever sees canonical fields (algorithm, key_bits, curve, hash_algorithm, mode).
"""

from __future__ import annotations

import re
from typing import Optional

from .model import CryptoUse, Primitive

# ---------------------------------------------------------------------------
# SSH (RFC 4253, 4344, 4345, 5656, 6668, 8268, 8308, 8332, 8709, OpenSSH ext.)
# ---------------------------------------------------------------------------

_SSH_KEX = {
    "diffie-hellman-group1-sha1": dict(algorithm="dh", key_bits=1024, hash_algorithm="sha1"),
    "diffie-hellman-group14-sha1": dict(algorithm="dh", key_bits=2048, hash_algorithm="sha1"),
    "diffie-hellman-group14-sha256": dict(algorithm="dh", key_bits=2048, hash_algorithm="sha256"),
    "diffie-hellman-group15-sha512": dict(algorithm="dh", key_bits=3072, hash_algorithm="sha512"),
    "diffie-hellman-group16-sha512": dict(algorithm="dh", key_bits=4096, hash_algorithm="sha512"),
    "diffie-hellman-group17-sha512": dict(algorithm="dh", key_bits=6144, hash_algorithm="sha512"),
    "diffie-hellman-group18-sha512": dict(algorithm="dh", key_bits=8192, hash_algorithm="sha512"),
    "diffie-hellman-group-exchange-sha1": dict(algorithm="dh-gex", key_bits=None, hash_algorithm="sha1"),
    "diffie-hellman-group-exchange-sha256": dict(algorithm="dh-gex", key_bits=None, hash_algorithm="sha256"),
    "ecdh-sha2-nistp256": dict(algorithm="ecdh", key_bits=256, curve="p-256", hash_algorithm="sha256"),
    "ecdh-sha2-nistp384": dict(algorithm="ecdh", key_bits=384, curve="p-384", hash_algorithm="sha384"),
    "ecdh-sha2-nistp521": dict(algorithm="ecdh", key_bits=521, curve="p-521", hash_algorithm="sha512"),
    "curve25519-sha256": dict(algorithm="ecdh", key_bits=256, curve="curve25519", hash_algorithm="sha256"),
    "curve25519-sha256@libssh.org": dict(algorithm="ecdh", key_bits=256, curve="curve25519", hash_algorithm="sha256"),
    "curve448-sha512": dict(algorithm="ecdh", key_bits=448, curve="curve448", hash_algorithm="sha512"),
    "sntrup761x25519-sha512": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", hash_algorithm="sha512", extra={"kem": "sntrup761"}),
    "sntrup761x25519-sha512@openssh.com": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", hash_algorithm="sha512", extra={"kem": "sntrup761"}),
    "sntrup4591761x25519-sha512@tinyssh.org": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", hash_algorithm="sha512", extra={"kem": "sntrup4591761"}),
    "mlkem768x25519-sha256": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", hash_algorithm="sha256", extra={"kem": "ml-kem-768"}),
    "mlkem768nistp256-sha256": dict(algorithm="hybrid-pq", key_bits=256, curve="p-256", hash_algorithm="sha256", extra={"kem": "ml-kem-768"}),
    "mlkem1024nistp384-sha384": dict(algorithm="hybrid-pq", key_bits=384, curve="p-384", hash_algorithm="sha384", extra={"kem": "ml-kem-1024"}),
    "rsa1024-sha1": dict(algorithm="rsa-kex", key_bits=1024, hash_algorithm="sha1"),
    "rsa2048-sha256": dict(algorithm="rsa-kex", key_bits=2048, hash_algorithm="sha256"),
    "ext-info-c": dict(algorithm="ext-info", extra={"marker": True}),
    "ext-info-s": dict(algorithm="ext-info", extra={"marker": True}),
    "kex-strict-c-v00@openssh.com": dict(algorithm="kex-strict", extra={"marker": True}),
    "kex-strict-s-v00@openssh.com": dict(algorithm="kex-strict", extra={"marker": True}),
}

_SSH_HOSTKEY = {
    "ssh-rsa": dict(algorithm="rsa", hash_algorithm="sha1"),
    "rsa-sha2-256": dict(algorithm="rsa", hash_algorithm="sha256"),
    "rsa-sha2-512": dict(algorithm="rsa", hash_algorithm="sha512"),
    "ssh-dss": dict(algorithm="dsa", key_bits=1024, hash_algorithm="sha1"),
    "ecdsa-sha2-nistp256": dict(algorithm="ecdsa", key_bits=256, curve="p-256", hash_algorithm="sha256"),
    "ecdsa-sha2-nistp384": dict(algorithm="ecdsa", key_bits=384, curve="p-384", hash_algorithm="sha384"),
    "ecdsa-sha2-nistp521": dict(algorithm="ecdsa", key_bits=521, curve="p-521", hash_algorithm="sha512"),
    "ssh-ed25519": dict(algorithm="ed25519", key_bits=256, curve="curve25519"),
    "ssh-ed448": dict(algorithm="ed448", key_bits=448, curve="curve448"),
    "sk-ssh-ed25519@openssh.com": dict(algorithm="ed25519", key_bits=256, curve="curve25519", extra={"security_key": True}),
    "sk-ecdsa-sha2-nistp256@openssh.com": dict(algorithm="ecdsa", key_bits=256, curve="p-256", hash_algorithm="sha256", extra={"security_key": True}),
    "ssh-rsa1": dict(algorithm="rsa", hash_algorithm="md5", extra={"protocol": "1"}),
    "x509v3-ssh-rsa": dict(algorithm="rsa", hash_algorithm="sha1"),
    "x509v3-rsa2048-sha256": dict(algorithm="rsa", key_bits=2048, hash_algorithm="sha256"),
    "x509v3-ssh-dss": dict(algorithm="dsa", hash_algorithm="sha1"),
    "x509v3-ecdsa-sha2-nistp256": dict(algorithm="ecdsa", key_bits=256, curve="p-256", hash_algorithm="sha256"),
    "x509v3-ecdsa-sha2-nistp384": dict(algorithm="ecdsa", key_bits=384, curve="p-384", hash_algorithm="sha384"),
    "x509v3-ecdsa-sha2-nistp521": dict(algorithm="ecdsa", key_bits=521, curve="p-521", hash_algorithm="sha512"),
}

_SSH_CIPHER = {
    "none": dict(algorithm="null"),
    "3des-cbc": dict(algorithm="3des", key_bits=168, mode="cbc"),
    "blowfish-cbc": dict(algorithm="blowfish", key_bits=128, mode="cbc"),
    "twofish-cbc": dict(algorithm="twofish", key_bits=256, mode="cbc"),
    "twofish128-cbc": dict(algorithm="twofish", key_bits=128, mode="cbc"),
    "twofish192-cbc": dict(algorithm="twofish", key_bits=192, mode="cbc"),
    "twofish256-cbc": dict(algorithm="twofish", key_bits=256, mode="cbc"),
    "serpent128-cbc": dict(algorithm="serpent", key_bits=128, mode="cbc"),
    "serpent192-cbc": dict(algorithm="serpent", key_bits=192, mode="cbc"),
    "serpent256-cbc": dict(algorithm="serpent", key_bits=256, mode="cbc"),
    "arcfour": dict(algorithm="rc4", key_bits=128),
    "arcfour128": dict(algorithm="rc4", key_bits=128),
    "arcfour256": dict(algorithm="rc4", key_bits=256),
    "idea-cbc": dict(algorithm="idea", key_bits=128, mode="cbc"),
    "cast128-cbc": dict(algorithm="cast5", key_bits=128, mode="cbc"),
    "des-cbc": dict(algorithm="des", key_bits=56, mode="cbc"),
    "des-cbc@ssh.com": dict(algorithm="des", key_bits=56, mode="cbc"),
    "rijndael-cbc@lysator.liu.se": dict(algorithm="aes", key_bits=256, mode="cbc"),
    "aes128-cbc": dict(algorithm="aes", key_bits=128, mode="cbc"),
    "aes192-cbc": dict(algorithm="aes", key_bits=192, mode="cbc"),
    "aes256-cbc": dict(algorithm="aes", key_bits=256, mode="cbc"),
    "aes128-ctr": dict(algorithm="aes", key_bits=128, mode="ctr"),
    "aes192-ctr": dict(algorithm="aes", key_bits=192, mode="ctr"),
    "aes256-ctr": dict(algorithm="aes", key_bits=256, mode="ctr"),
    "aes128-gcm@openssh.com": dict(algorithm="aes", key_bits=128, mode="gcm"),
    "aes256-gcm@openssh.com": dict(algorithm="aes", key_bits=256, mode="gcm"),
    "AEAD_AES_128_GCM": dict(algorithm="aes", key_bits=128, mode="gcm"),
    "AEAD_AES_256_GCM": dict(algorithm="aes", key_bits=256, mode="gcm"),
    "chacha20-poly1305@openssh.com": dict(algorithm="chacha20-poly1305", key_bits=256, mode="aead"),
    "chacha20-poly1305": dict(algorithm="chacha20-poly1305", key_bits=256, mode="aead"),
}

_SSH_MAC = {
    "none": dict(algorithm="null"),
    "hmac-md5": dict(algorithm="hmac", hash_algorithm="md5", key_bits=128),
    "hmac-md5-96": dict(algorithm="hmac", hash_algorithm="md5", key_bits=96, extra={"truncated": True}),
    "hmac-sha1": dict(algorithm="hmac", hash_algorithm="sha1", key_bits=160),
    "hmac-sha1-96": dict(algorithm="hmac", hash_algorithm="sha1", key_bits=96, extra={"truncated": True}),
    "hmac-sha2-256": dict(algorithm="hmac", hash_algorithm="sha256", key_bits=256),
    "hmac-sha2-512": dict(algorithm="hmac", hash_algorithm="sha512", key_bits=512),
    "hmac-ripemd160": dict(algorithm="hmac", hash_algorithm="ripemd160", key_bits=160),
    "hmac-ripemd160@openssh.com": dict(algorithm="hmac", hash_algorithm="ripemd160", key_bits=160),
    "umac-64@openssh.com": dict(algorithm="umac", key_bits=64),
    "umac-128@openssh.com": dict(algorithm="umac", key_bits=128),
    "hmac-md5-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="md5", key_bits=128, mode="etm"),
    "hmac-md5-96-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="md5", key_bits=96, mode="etm", extra={"truncated": True}),
    "hmac-sha1-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="sha1", key_bits=160, mode="etm"),
    "hmac-sha1-96-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="sha1", key_bits=96, mode="etm", extra={"truncated": True}),
    "hmac-sha2-256-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="sha256", key_bits=256, mode="etm"),
    "hmac-sha2-512-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="sha512", key_bits=512, mode="etm"),
    "hmac-ripemd160-etm@openssh.com": dict(algorithm="hmac", hash_algorithm="ripemd160", key_bits=160, mode="etm"),
    "umac-64-etm@openssh.com": dict(algorithm="umac", key_bits=64, mode="etm"),
    "umac-128-etm@openssh.com": dict(algorithm="umac", key_bits=128, mode="etm"),
    "AEAD_AES_128_GCM": dict(algorithm="aead", key_bits=128),
    "AEAD_AES_256_GCM": dict(algorithm="aead", key_bits=256),
}


def _mk(primitive: Primitive, raw: str, spec: dict, context: str, **kw) -> CryptoUse:
    spec = dict(spec)
    extra = dict(spec.pop("extra", {}))
    extra.update(kw.pop("extra", {}))
    return CryptoUse(primitive=primitive, raw=raw, context=context, extra=extra, **spec, **kw)


def ssh_kex(name: str, **kw) -> CryptoUse:
    spec = _SSH_KEX.get(name)
    if spec is None:
        if name.startswith("gss-"):
            # gss-group14-sha256-<base64 oid>, gss-gex-sha1-..., gss-curve25519-sha256-...
            m = re.match(r"gss-(group1|group14|group16|group18|gex|nistp256|nistp384|nistp521|curve25519)-(sha1|sha256|sha512)-", name)
            if m:
                g, h = m.groups()
                base = {"group1": "diffie-hellman-group1-", "group14": "diffie-hellman-group14-",
                        "group16": "diffie-hellman-group16-", "group18": "diffie-hellman-group18-",
                        "gex": "diffie-hellman-group-exchange-", "nistp256": "ecdh-sha2-nistp256",
                        "nistp384": "ecdh-sha2-nistp384", "nistp521": "ecdh-sha2-nistp521",
                        "curve25519": "curve25519-sha256"}[g]
                key = base + h if base.endswith("-") else base
                spec = dict(_SSH_KEX.get(key, {"algorithm": "unknown"}))
                spec.setdefault("extra", {})["gssapi"] = True
        if spec is None:
            spec = dict(algorithm="unknown")
    return _mk(Primitive.KEY_EXCHANGE, name, spec, "kex", **kw)


def ssh_hostkey(name: str, **kw) -> CryptoUse:
    base = name.replace("-cert-v01@openssh.com", "")
    spec = dict(_SSH_HOSTKEY.get(base, dict(algorithm="unknown")))
    if base != name:
        spec.setdefault("extra", {})["certificate"] = True
    return _mk(Primitive.SIGNATURE, name, spec, "hostkey", **kw)


def ssh_cipher(name: str, **kw) -> CryptoUse:
    return _mk(Primitive.CIPHER, name, _SSH_CIPHER.get(name, dict(algorithm="unknown")), "cipher", **kw)


def ssh_mac(name: str, **kw) -> CryptoUse:
    return _mk(Primitive.MAC, name, _SSH_MAC.get(name, dict(algorithm="unknown")), "mac", **kw)


def ssh_sig_algorithm(name: str, context: str = "pubkey-auth", **kw) -> CryptoUse:
    """PubkeyAcceptedAlgorithms / CASignatureAlgorithms / HostbasedAcceptedAlgorithms."""
    u = ssh_hostkey(name, **kw)
    u.context = context
    return u


# ---------------------------------------------------------------------------
# TLS cipher suites (IANA names, and OpenSSL names mapped onto them)
# ---------------------------------------------------------------------------

_TLS_CIPHERS = {
    "NULL": dict(algorithm="null", key_bits=0),
    "RC4_40": dict(algorithm="rc4", key_bits=40), "RC4_128": dict(algorithm="rc4", key_bits=128),
    "RC2_CBC_40": dict(algorithm="rc2", key_bits=40, mode="cbc"),
    "DES40_CBC": dict(algorithm="des", key_bits=40, mode="cbc"),
    "DES_CBC": dict(algorithm="des", key_bits=56, mode="cbc"),
    "3DES_EDE_CBC": dict(algorithm="3des", key_bits=168, mode="cbc"),
    "IDEA_CBC": dict(algorithm="idea", key_bits=128, mode="cbc"),
    "SEED_CBC": dict(algorithm="seed", key_bits=128, mode="cbc"),
    "AES_128_CBC": dict(algorithm="aes", key_bits=128, mode="cbc"),
    "AES_256_CBC": dict(algorithm="aes", key_bits=256, mode="cbc"),
    "AES_128_GCM": dict(algorithm="aes", key_bits=128, mode="gcm"),
    "AES_256_GCM": dict(algorithm="aes", key_bits=256, mode="gcm"),
    "AES_128_CCM": dict(algorithm="aes", key_bits=128, mode="ccm"),
    "AES_256_CCM": dict(algorithm="aes", key_bits=256, mode="ccm"),
    "AES_128_CCM_8": dict(algorithm="aes", key_bits=128, mode="ccm-8"),
    "AES_256_CCM_8": dict(algorithm="aes", key_bits=256, mode="ccm-8"),
    "CAMELLIA_128_CBC": dict(algorithm="camellia", key_bits=128, mode="cbc"),
    "CAMELLIA_256_CBC": dict(algorithm="camellia", key_bits=256, mode="cbc"),
    "CAMELLIA_128_GCM": dict(algorithm="camellia", key_bits=128, mode="gcm"),
    "CAMELLIA_256_GCM": dict(algorithm="camellia", key_bits=256, mode="gcm"),
    "ARIA_128_GCM": dict(algorithm="aria", key_bits=128, mode="gcm"),
    "ARIA_256_GCM": dict(algorithm="aria", key_bits=256, mode="gcm"),
    "ARIA_128_CBC": dict(algorithm="aria", key_bits=128, mode="cbc"),
    "ARIA_256_CBC": dict(algorithm="aria", key_bits=256, mode="cbc"),
    "CHACHA20_POLY1305": dict(algorithm="chacha20-poly1305", key_bits=256, mode="aead"),
    "GOSTR341112_256_WITH_KUZNYECHIK_CTR_OMAC": dict(algorithm="kuznyechik", key_bits=256, mode="ctr-omac"),
    "GOSTR341112_256_WITH_MAGMA_CTR_OMAC": dict(algorithm="magma", key_bits=256, mode="ctr-omac"),
    "SM4_GCM": dict(algorithm="sm4", key_bits=128, mode="gcm"),
    "SM4_CCM": dict(algorithm="sm4", key_bits=128, mode="ccm"),
}

_TLS_KX = {
    "RSA": dict(algorithm="rsa-kex"),                  # static RSA key transport, no PFS
    "DH_anon": dict(algorithm="dh-anon"), "ECDH_anon": dict(algorithm="ecdh-anon"),
    "DHE_RSA": dict(algorithm="dhe"), "DHE_DSS": dict(algorithm="dhe"), "DHE_PSK": dict(algorithm="dhe"),
    "DH_RSA": dict(algorithm="dh-static"), "DH_DSS": dict(algorithm="dh-static"),
    "ECDHE_RSA": dict(algorithm="ecdhe"), "ECDHE_ECDSA": dict(algorithm="ecdhe"), "ECDHE_PSK": dict(algorithm="ecdhe"),
    "ECDH_RSA": dict(algorithm="ecdh-static"), "ECDH_ECDSA": dict(algorithm="ecdh-static"),
    "PSK": dict(algorithm="psk"), "RSA_PSK": dict(algorithm="rsa-kex"),
    "SRP_SHA": dict(algorithm="srp"), "SRP_SHA_RSA": dict(algorithm="srp"), "SRP_SHA_DSS": dict(algorithm="srp"),
    "KRB5": dict(algorithm="krb5"), "KRB5_EXPORT": dict(algorithm="krb5"),
    "ECCPWD": dict(algorithm="eccpwd"), "GOSTR341112_256": dict(algorithm="gost-vko"),
}

_TLS_AUTH = {
    "RSA": "rsa", "DSS": "dsa", "ECDSA": "ecdsa", "anon": "none", "PSK": "psk", "KRB5": "krb5",
}

_OPENSSL_TO_IANA = {
    # the most common OpenSSL spellings; anything else is parsed heuristically
    "AES128-SHA": "TLS_RSA_WITH_AES_128_CBC_SHA", "AES256-SHA": "TLS_RSA_WITH_AES_256_CBC_SHA",
    "AES128-SHA256": "TLS_RSA_WITH_AES_128_CBC_SHA256", "AES256-SHA256": "TLS_RSA_WITH_AES_256_CBC_SHA256",
    "AES128-GCM-SHA256": "TLS_RSA_WITH_AES_128_GCM_SHA256", "AES256-GCM-SHA384": "TLS_RSA_WITH_AES_256_GCM_SHA384",
    "DES-CBC3-SHA": "TLS_RSA_WITH_3DES_EDE_CBC_SHA", "RC4-SHA": "TLS_RSA_WITH_RC4_128_SHA", "RC4-MD5": "TLS_RSA_WITH_RC4_128_MD5",
    "DES-CBC-SHA": "TLS_RSA_WITH_DES_CBC_SHA", "NULL-SHA": "TLS_RSA_WITH_NULL_SHA", "NULL-MD5": "TLS_RSA_WITH_NULL_MD5",
    "EXP-RC4-MD5": "TLS_RSA_EXPORT_WITH_RC4_40_MD5", "EXP-DES-CBC-SHA": "TLS_RSA_EXPORT_WITH_DES40_CBC_SHA",
    "ECDHE-RSA-AES128-GCM-SHA256": "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    "ECDHE-RSA-AES256-GCM-SHA384": "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "ECDHE-ECDSA-AES128-GCM-SHA256": "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
    "ECDHE-ECDSA-AES256-GCM-SHA384": "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
    "ECDHE-RSA-CHACHA20-POLY1305": "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
    "ECDHE-ECDSA-CHACHA20-POLY1305": "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
    "ECDHE-RSA-AES128-SHA": "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA", "ECDHE-RSA-AES256-SHA": "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA",
    "ECDHE-RSA-AES128-SHA256": "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256", "ECDHE-RSA-AES256-SHA384": "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
    "ECDHE-ECDSA-AES128-SHA": "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA", "ECDHE-ECDSA-AES256-SHA": "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA",
    "ECDHE-RSA-DES-CBC3-SHA": "TLS_ECDHE_RSA_WITH_3DES_EDE_CBC_SHA", "ECDHE-RSA-RC4-SHA": "TLS_ECDHE_RSA_WITH_RC4_128_SHA",
    "DHE-RSA-AES128-GCM-SHA256": "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256", "DHE-RSA-AES256-GCM-SHA384": "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
    "DHE-RSA-AES128-SHA": "TLS_DHE_RSA_WITH_AES_128_CBC_SHA", "DHE-RSA-AES256-SHA": "TLS_DHE_RSA_WITH_AES_256_CBC_SHA",
    "DHE-RSA-AES128-SHA256": "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256", "DHE-RSA-AES256-SHA256": "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256",
    "DHE-RSA-CHACHA20-POLY1305": "TLS_DHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
    "DHE-DSS-AES128-SHA": "TLS_DHE_DSS_WITH_AES_128_CBC_SHA", "EDH-RSA-DES-CBC3-SHA": "TLS_DHE_RSA_WITH_3DES_EDE_CBC_SHA",
    "ADH-AES128-SHA": "TLS_DH_anon_WITH_AES_128_CBC_SHA", "AECDH-AES128-SHA": "TLS_ECDH_anon_WITH_AES_128_CBC_SHA",
    "TLS_AES_128_GCM_SHA256": "TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384": "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256": "TLS_CHACHA20_POLY1305_SHA256", "TLS_AES_128_CCM_SHA256": "TLS_AES_128_CCM_SHA256",
    "TLS_AES_128_CCM_8_SHA256": "TLS_AES_128_CCM_8_SHA256",
    "PSK-AES128-CBC-SHA": "TLS_PSK_WITH_AES_128_CBC_SHA", "CAMELLIA128-SHA": "TLS_RSA_WITH_CAMELLIA_128_CBC_SHA",
    "SEED-SHA": "TLS_RSA_WITH_SEED_CBC_SHA", "IDEA-CBC-SHA": "TLS_RSA_WITH_IDEA_CBC_SHA",
}

_TLS13 = {"TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256",
          "TLS_AES_128_CCM_SHA256", "TLS_AES_128_CCM_8_SHA256", "TLS_SM4_GCM_SM3", "TLS_SM4_CCM_SM3"}


def tls_cipher_suite(name: str, protocol: Optional[str] = None, **kw) -> CryptoUse:
    """Normalise a TLS cipher suite (IANA or OpenSSL name) into one CryptoUse.

    The returned use is primitive CIPHER with extra = {kx, auth, prf, export,
    pfs, aead}; the policy engine looks at those fields.
    """
    raw = name
    iana = _OPENSSL_TO_IANA.get(name, name)
    if not iana.startswith(("TLS_", "SSL_")) and "-" in iana:
        iana = _openssl_heuristic(iana)
    extra = {"kx": None, "auth": None, "prf": None, "export": False, "pfs": None, "aead": False, "iana": iana}
    spec = dict(algorithm="unknown")
    hash_alg = None
    body = re.sub(r"^(TLS|SSL)_", "", iana)
    if iana in _TLS13 or (body.startswith(("AES_", "CHACHA20_", "SM4_")) and "_WITH_" not in body):
        # TLS 1.3 suites: ephemeral (EC)DHE or PQ hybrid negotiated separately
        extra.update(kx="tls13-ephemeral", auth="certificate", pfs=True, aead=True)
        m = re.match(r"(.+)_(SHA256|SHA384|SM3)$", body)
        if m:
            spec = dict(_TLS_CIPHERS.get(m.group(1), spec))
            hash_alg = m.group(2).lower()
    elif "_WITH_" in body:
        kx_part, rest = body.split("_WITH_", 1)
        export = "_EXPORT" in kx_part
        kx_part = kx_part.replace("_EXPORT1024", "").replace("_EXPORT", "")
        kxspec = _TLS_KX.get(kx_part, dict(algorithm="unknown"))
        auth = None
        for suffix, a in _TLS_AUTH.items():
            if kx_part.endswith("_" + suffix) or kx_part == suffix:
                auth = a
        if kx_part in ("DH_anon", "ECDH_anon"):
            auth = "none"
        m = re.match(r"(.+)_(MD5|SHA|SHA256|SHA384|SHA512|NULL)$", rest)
        cipher_part, mac = (m.group(1), m.group(2)) if m else (rest, None)
        spec = dict(_TLS_CIPHERS.get(cipher_part, dict(algorithm=cipher_part.lower())))
        hash_alg = {"SHA": "sha1", "MD5": "md5", "SHA256": "sha256", "SHA384": "sha384", "SHA512": "sha512", "NULL": None}.get(mac or "", None)
        extra.update(kx=kxspec["algorithm"], auth=auth, export=export,
                     pfs=kxspec["algorithm"] in ("dhe", "ecdhe"),
                     aead=spec.get("mode") in ("gcm", "ccm", "ccm-8", "aead", "ctr-omac"))
        if export:
            spec["key_bits"] = min(spec.get("key_bits") or 40, 56)
    if protocol:
        extra["protocol"] = protocol
    extra.update(kw.pop("extra", {}))
    return CryptoUse(primitive=Primitive.CIPHER, raw=raw, context="tls-cipher-suite",
                     hash_algorithm=hash_alg, extra=extra, **spec, **kw)


def _openssl_heuristic(name: str) -> str:
    """Best-effort OpenSSL -> IANA conversion for suites not in the table."""
    n = name
    kx = "RSA"
    for prefix, k in (("ECDHE-ECDSA-", "ECDHE_ECDSA"), ("ECDHE-RSA-", "ECDHE_RSA"), ("ECDHE-PSK-", "ECDHE_PSK"),
                      ("DHE-RSA-", "DHE_RSA"), ("DHE-DSS-", "DHE_DSS"), ("DHE-PSK-", "DHE_PSK"), ("EDH-RSA-", "DHE_RSA"),
                      ("ECDH-ECDSA-", "ECDH_ECDSA"), ("ECDH-RSA-", "ECDH_RSA"), ("ADH-", "DH_anon"), ("AECDH-", "ECDH_anon"),
                      ("RSA-PSK-", "RSA_PSK"), ("PSK-", "PSK"), ("SRP-RSA-", "SRP_SHA_RSA"), ("SRP-", "SRP_SHA")):
        if n.startswith(prefix):
            kx, n = k, n[len(prefix):]
            break
    export = n.startswith("EXP-")
    n = n[4:] if export else n
    m = re.match(r"(.+?)-(SHA384|SHA256|SHA|MD5)$", n)
    cipher, mac = (m.group(1), m.group(2)) if m else (n, "SHA")
    cipher_map = {"AES128-GCM": "AES_128_GCM", "AES256-GCM": "AES_256_GCM", "AES128": "AES_128_CBC", "AES256": "AES_256_CBC",
                  "DES-CBC3": "3DES_EDE_CBC", "DES-CBC": "DES_CBC", "RC4": "RC4_128", "RC2-CBC": "RC2_CBC_40",
                  "CHACHA20-POLY1305": "CHACHA20_POLY1305", "CAMELLIA128": "CAMELLIA_128_CBC", "CAMELLIA256": "CAMELLIA_256_CBC",
                  "SEED": "SEED_CBC", "IDEA-CBC": "IDEA_CBC", "NULL": "NULL", "AES128-CCM": "AES_128_CCM", "AES256-CCM": "AES_256_CCM",
                  "AES128-CCM8": "AES_128_CCM_8", "AES256-CCM8": "AES_256_CCM_8", "ARIA128-GCM": "ARIA_128_GCM", "ARIA256-GCM": "ARIA_256_GCM"}
    c = cipher_map.get(cipher, cipher.replace("-", "_"))
    if export and c == "RC4_128":
        c = "RC4_40"
    if export and c == "DES_CBC":
        c = "DES40_CBC"
    return f"TLS_{kx}{'_EXPORT' if export else ''}_WITH_{c}_{mac}"


_TLS_GROUPS = {
    "x25519": dict(algorithm="ecdh", key_bits=256, curve="curve25519"),
    "x448": dict(algorithm="ecdh", key_bits=448, curve="curve448"),
    "secp256r1": dict(algorithm="ecdh", key_bits=256, curve="p-256"), "prime256v1": dict(algorithm="ecdh", key_bits=256, curve="p-256"),
    "p-256": dict(algorithm="ecdh", key_bits=256, curve="p-256"),
    "secp384r1": dict(algorithm="ecdh", key_bits=384, curve="p-384"), "p-384": dict(algorithm="ecdh", key_bits=384, curve="p-384"),
    "secp521r1": dict(algorithm="ecdh", key_bits=521, curve="p-521"), "p-521": dict(algorithm="ecdh", key_bits=521, curve="p-521"),
    "secp224r1": dict(algorithm="ecdh", key_bits=224, curve="p-224"), "secp192r1": dict(algorithm="ecdh", key_bits=192, curve="p-192"),
    "secp160r1": dict(algorithm="ecdh", key_bits=160, curve="secp160r1"), "sect163k1": dict(algorithm="ecdh", key_bits=163, curve="sect163k1"),
    "brainpoolp256r1": dict(algorithm="ecdh", key_bits=256, curve="brainpoolp256r1"), "brainpoolp384r1": dict(algorithm="ecdh", key_bits=384, curve="brainpoolp384r1"),
    "brainpoolp512r1": dict(algorithm="ecdh", key_bits=512, curve="brainpoolp512r1"),
    "brainpoolp256r1tls13": dict(algorithm="ecdh", key_bits=256, curve="brainpoolp256r1"),
    "ffdhe2048": dict(algorithm="dh", key_bits=2048), "ffdhe3072": dict(algorithm="dh", key_bits=3072),
    "ffdhe4096": dict(algorithm="dh", key_bits=4096), "ffdhe6144": dict(algorithm="dh", key_bits=6144), "ffdhe8192": dict(algorithm="dh", key_bits=8192),
    "x25519mlkem768": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", extra={"kem": "ml-kem-768"}),
    "x25519_mlkem768": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", extra={"kem": "ml-kem-768"}),
    "secp256r1mlkem768": dict(algorithm="hybrid-pq", key_bits=256, curve="p-256", extra={"kem": "ml-kem-768"}),
    "secp384r1mlkem1024": dict(algorithm="hybrid-pq", key_bits=384, curve="p-384", extra={"kem": "ml-kem-1024"}),
    "x25519kyber768draft00": dict(algorithm="hybrid-pq", key_bits=256, curve="curve25519", extra={"kem": "kyber768-draft"}),
    "mlkem512": dict(algorithm="ml-kem", key_bits=512), "mlkem768": dict(algorithm="ml-kem", key_bits=768), "mlkem1024": dict(algorithm="ml-kem", key_bits=1024),
}


def tls_group(name: str, **kw) -> CryptoUse:
    spec = _TLS_GROUPS.get(name.lower(), dict(algorithm="unknown"))
    return _mk(Primitive.KEY_EXCHANGE, name, spec, "tls-group", **kw)


def tls_protocol(name: str, **kw) -> CryptoUse:
    canon = {"SSLV2": "sslv2", "SSLV3": "sslv3", "TLSV1": "tls1.0", "TLSV1.0": "tls1.0", "TLSV1_0": "tls1.0", "TLS1.0": "tls1.0", "TLS1": "tls1.0",
             "TLSV1.1": "tls1.1", "TLSV1_1": "tls1.1", "TLS1.1": "tls1.1", "TLSV1.2": "tls1.2", "TLSV1_2": "tls1.2", "TLS1.2": "tls1.2",
             "TLSV1.3": "tls1.3", "TLSV1_3": "tls1.3", "TLS1.3": "tls1.3", "DTLSV1.0": "dtls1.0", "DTLSV1.2": "dtls1.2", "DTLS1.0": "dtls1.0", "DTLS1.2": "dtls1.2"}
    canon.update({"DTLSV1": "dtls1.0", "DTLS1": "dtls1.0", "DTLSV1_0": "dtls1.0", "DTLSV1_2": "dtls1.2", "TLSV1.0": "tls1.0", "SSL2": "sslv2", "SSL3": "sslv3", "SSLV2.0": "sslv2", "SSLV3.0": "sslv3"})
    key = name.upper().replace(" ", "")
    context = kw.pop("context", "tls-protocol")
    return CryptoUse(primitive=Primitive.PROTOCOL, algorithm=canon.get(key, name.lower()), raw=name, context=context, **kw)


_TLS_SIGALGS = {
    "rsa_pkcs1_sha1": ("rsa", "sha1"), "ecdsa_sha1": ("ecdsa", "sha1"), "dsa_sha1": ("dsa", "sha1"),
    "rsa_pkcs1_md5": ("rsa", "md5"), "rsa_pkcs1_sha256": ("rsa", "sha256"), "rsa_pkcs1_sha384": ("rsa", "sha384"), "rsa_pkcs1_sha512": ("rsa", "sha512"),
    "ecdsa_secp256r1_sha256": ("ecdsa", "sha256"), "ecdsa_secp384r1_sha384": ("ecdsa", "sha384"), "ecdsa_secp521r1_sha512": ("ecdsa", "sha512"),
    "rsa_pss_rsae_sha256": ("rsa-pss", "sha256"), "rsa_pss_rsae_sha384": ("rsa-pss", "sha384"), "rsa_pss_rsae_sha512": ("rsa-pss", "sha512"),
    "rsa_pss_pss_sha256": ("rsa-pss", "sha256"), "rsa_pss_pss_sha384": ("rsa-pss", "sha384"), "rsa_pss_pss_sha512": ("rsa-pss", "sha512"),
    "ed25519": ("ed25519", None), "ed448": ("ed448", None), "dsa_sha256": ("dsa", "sha256"),
    "mldsa44": ("ml-dsa-44", None), "mldsa65": ("ml-dsa-65", None), "mldsa87": ("ml-dsa-87", None),
}


def tls_sigalg(name: str, **kw) -> CryptoUse:
    alg, h = _TLS_SIGALGS.get(name.lower(), (name.lower(), None))
    return CryptoUse(primitive=Primitive.SIGNATURE, algorithm=alg, hash_algorithm=h, raw=name, context="tls-sigalg", **kw)


# ---------------------------------------------------------------------------
# Kerberos encryption types (RFC 3961, 3962, 4757, 6649, 8009, 8429)
# ---------------------------------------------------------------------------

_KRB_ENCTYPES = {
    1: ("des-cbc-crc", "des", 56, "crc32"), 2: ("des-cbc-md4", "des", 56, "md4"), 3: ("des-cbc-md5", "des", 56, "md5"),
    5: ("des3-cbc-md5", "3des", 168, "md5"), 7: ("des3-cbc-sha1", "3des", 168, "sha1"), 16: ("des3-cbc-sha1", "3des", 168, "sha1"),
    4: ("des-cbc-raw", "des", 56, None), 6: ("des3-cbc-raw", "3des", 168, None), 8: ("des-hmac-sha1", "des", 56, "sha1"),
    9: ("dsaWithSHA1-CmsOID", "dsa", None, "sha1"), 10: ("md5WithRSAEncryption-CmsOID", "rsa", None, "md5"),
    11: ("sha1WithRSAEncryption-CmsOID", "rsa", None, "sha1"), 12: ("rc2CBC-EnvOID", "rc2", None, None),
    13: ("rsaEncryption-EnvOID", "rsa", None, None), 14: ("rsaES-OAEP-ENV-OID", "rsa", None, None), 15: ("des-ede3-cbc-Env-OID", "3des", 168, None),
    17: ("aes128-cts-hmac-sha1-96", "aes", 128, "sha1"), 18: ("aes256-cts-hmac-sha1-96", "aes", 256, "sha1"),
    19: ("aes128-cts-hmac-sha256-128", "aes", 128, "sha256"), 20: ("aes256-cts-hmac-sha384-192", "aes", 256, "sha384"),
    23: ("rc4-hmac", "rc4", 128, "md5"), 24: ("rc4-hmac-exp", "rc4", 40, "md5"), -128: ("rc4-hmac-old", "rc4", 128, "md5"),
    -133: ("rc4-hmac-old-exp", "rc4", 40, "md5"), -135: ("rc4-hmac-old", "rc4", 128, "md5"),
    25: ("camellia128-cts-cmac", "camellia", 128, "cmac"), 26: ("camellia256-cts-cmac", "camellia", 256, "cmac"),
    65: ("subkey-keymaterial", "unknown", None, None),
}
_KRB_ALIASES = {
    "des": "des-cbc-crc", "des3": "des3-cbc-sha1", "des3-hmac-sha1": "des3-cbc-sha1", "des3-cbc-sha1-kd": "des3-cbc-sha1",
    "arcfour-hmac": "rc4-hmac", "arcfour-hmac-md5": "rc4-hmac", "rc4-hmac-md5": "rc4-hmac", "arcfour-hmac-exp": "rc4-hmac-exp",
    "arcfour-hmac-md5-exp": "rc4-hmac-exp", "aes128-cts": "aes128-cts-hmac-sha1-96", "aes256-cts": "aes256-cts-hmac-sha1-96",
    "aes128-sha1": "aes128-cts-hmac-sha1-96", "aes256-sha1": "aes256-cts-hmac-sha1-96", "aes128-sha2": "aes128-cts-hmac-sha256-128",
    "aes256-sha2": "aes256-cts-hmac-sha384-192", "aes": "aes-family", "aes128": "aes128-cts-hmac-sha1-96", "aes256": "aes256-cts-hmac-sha1-96",
    "rc4": "rc4-hmac", "camellia": "camellia-family", "camellia128-cts": "camellia128-cts-cmac", "camellia256-cts": "camellia256-cts-cmac",
    "des-cbc-crc": "des-cbc-crc", "des-cbc-md5": "des-cbc-md5", "des-cbc-md4": "des-cbc-md4", "des-cbc-raw": "des-cbc-raw", "des-hmac-sha1": "des-hmac-sha1",
    # Windows msDS-SupportedEncryptionTypes / AD names
    "des_cbc_crc": "des-cbc-crc", "des_cbc_md5": "des-cbc-md5", "rc4_hmac_md5": "rc4-hmac", "aes128_cts_hmac_sha1_96": "aes128-cts-hmac-sha1-96",
    "aes256_cts_hmac_sha1_96": "aes256-cts-hmac-sha1-96", "aes256_cts_hmac_sha1_96_sk": "aes256-cts-hmac-sha1-96",
}
_KRB_BY_NAME = {v[0]: (k,) + v[1:] for k, v in _KRB_ENCTYPES.items() if v[0] not in ("des3-cbc-sha1",) or k == 16}
_KRB_BY_NAME["des3-cbc-sha1"] = (16, "3des", 168, "sha1")


def krb_enctype(name_or_id, **kw) -> CryptoUse:
    """Normalise a Kerberos enctype given by name (krb5.conf / klist) or number (keytab)."""
    raw = str(name_or_id)
    context = kw.pop("context", "enctype")
    extra_in = kw.pop("extra", {})
    if isinstance(name_or_id, int) or re.fullmatch(r"-?\d+", raw):
        etype = int(name_or_id)
        name, alg, bits, h = _KRB_ENCTYPES.get(etype, (f"etype-{etype}", "unknown", None, None))
        return CryptoUse(primitive=Primitive.ENCTYPE, algorithm=alg, key_bits=bits, hash_algorithm=h, raw=raw,
                         context=context, extra={**extra_in, "enctype": name, "etype_id": etype}, **kw)
    n = raw.strip().lower()
    neg = n.startswith(("-", "!"))
    n = n.lstrip("-!+")
    canon = _KRB_ALIASES.get(n, n)
    if canon == "aes-family":
        return CryptoUse(primitive=Primitive.ENCTYPE, algorithm="aes", key_bits=256, hash_algorithm="sha1", raw=raw, context=context,
                         extra={**extra_in, "enctype": "aes", "family": True, "negated": neg}, **kw)
    if canon == "camellia-family":
        return CryptoUse(primitive=Primitive.ENCTYPE, algorithm="camellia", key_bits=256, hash_algorithm="cmac", raw=raw, context=context,
                         extra={**extra_in, "enctype": "camellia", "family": True, "negated": neg}, **kw)
    if canon in _KRB_BY_NAME:
        etype, alg, bits, h = _KRB_BY_NAME[canon]
        return CryptoUse(primitive=Primitive.ENCTYPE, algorithm=alg, key_bits=bits, hash_algorithm=h, raw=raw, context=context,
                         extra={**extra_in, "enctype": canon, "etype_id": etype, "negated": neg}, **kw)
    if n == "default":
        return CryptoUse(primitive=Primitive.ENCTYPE, algorithm="default", raw=raw, context=context, extra={**extra_in, "enctype": "default", "negated": neg}, **kw)
    return CryptoUse(primitive=Primitive.ENCTYPE, algorithm="unknown", raw=raw, context=context, extra={**extra_in, "enctype": n, "negated": neg}, **kw)


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def hash_name(name: str) -> str:
    n = name.lower().replace("_", "-").replace(" ", "")
    return {"sha-1": "sha1", "sha": "sha1", "sha-256": "sha256", "sha-384": "sha384", "sha-512": "sha512",
            "sha-224": "sha224", "sha2-256": "sha256", "sha2-384": "sha384", "sha2-512": "sha512",
            "sha2": "sha256", "md-5": "md5", "ripemd-160": "ripemd160", "sha3": "sha3-256"}.get(n, n)


def security_strength(use: CryptoUse) -> Optional[int]:
    """Approximate classical security strength in bits (NIST SP 800-57 Part 1 Table 2)."""
    alg = use.algorithm
    bits = use.key_bits
    if alg in ("rsa", "rsa-pss", "rsa-kex", "dsa", "dh", "dhe", "dh-gex", "dh-static"):
        if not bits:
            return None
        if bits < 1024:
            return 56 if bits >= 512 else 40
        if bits < 2048:
            return 80
        if bits < 3072:
            return 112
        if bits < 7680:
            return 128
        if bits < 15360:
            return 192
        return 256
    if alg in ("ec", "ecdsa", "ecdh", "ecdhe", "ecdh-static", "ed25519", "ed448", "x25519", "x448", "ecdsa-sk", "ed25519-sk", "hybrid-pq"):
        if not bits:
            return None
        if bits >= 512:
            return 256
        if bits >= 384:
            return 192
        if bits >= 256:
            return 128
        if bits >= 224:
            return 112
        if bits >= 192:
            return 96   # NIST: 80 for P-192 (n ~ 2^192 -> 96 generic, but legacy tables say 80)
        return bits // 2
    if alg in ("aes", "camellia", "aria", "chacha20-poly1305", "serpent", "twofish", "sm4", "kuznyechik"):
        return bits
    if alg == "3des":
        return 112 if (bits or 168) >= 168 else 80
    if alg in ("des", "des40"):
        return 56 if (bits or 56) >= 56 else 40
    if alg in ("rc4", "rc2", "blowfish", "idea", "cast5", "seed"):
        return min(bits or 64, 64)      # 64-bit blocks or broken
    if alg == "null":
        return 0
    if alg in ("ml-kem", "ml-dsa-44", "ml-dsa-65", "ml-dsa-87") or alg.startswith(("ml-dsa", "slh-dsa", "ml-kem")):
        return 128
    h = {"md2": 0, "md4": 0, "md5": 0, "sha1": 63, "sha224": 112, "sha256": 128, "sha384": 192, "sha512": 256, "ripemd160": 80}
    if alg == "hmac" and use.hash_algorithm:
        if use.hash_algorithm in ("md5", "md2", "md4"):
            return 0
        return min(use.key_bits or 256, {"sha1": 128, "ripemd160": 128}.get(use.hash_algorithm, 256))
    if use.primitive == Primitive.HASH:
        return h.get(alg)
    return None
