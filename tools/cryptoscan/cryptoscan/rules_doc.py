"""Enumerate the rule ids the policy engine can emit, by exercising it with synthetic inputs.

The rules live in policy.py as code; this module keeps the documentation honest by
deriving the list from the engine itself (the `rules` subcommand and README table).
"""

from __future__ import annotations

import datetime as _dt
from typing import Dict, List

from . import names
from .model import Asset, AssetKind, CryptoUse, Primitive
from .policy import PROFILES, evaluate


def _synthetic_assets() -> List[Asset]:
    a = Asset(AssetKind.SSH_SERVER, "sshd", "/etc/ssh/sshd_config", "doc")
    for k in ["diffie-hellman-group1-sha1", "diffie-hellman-group14-sha1", "diffie-hellman-group14-sha256", "ecdh-sha2-nistp256",
              "curve25519-sha256", "sntrup761x25519-sha512@openssh.com", "rsa1024-sha1", "x25519kyber768draft00"]:
        a.add(names.ssh_kex(k))
    for k in ["ssh-rsa", "ssh-dss", "rsa-sha2-512", "ssh-ed25519", "ecdsa-sha2-nistp256", "ssh-rsa1"]:
        a.add(names.ssh_hostkey(k))
    for k in ["3des-cbc", "aes128-cbc", "arcfour", "blowfish-cbc", "des-cbc", "none", "aes256-gcm@openssh.com", "chacha20-poly1305@openssh.com"]:
        a.add(names.ssh_cipher(k))
    for k in ["hmac-md5", "hmac-sha1-96", "hmac-sha1", "umac-64@openssh.com", "hmac-ripemd160", "hmac-sha2-256-etm@openssh.com", "none"]:
        a.add(names.ssh_mac(k))
    a.add(CryptoUse(Primitive.CONFIG, "ssh-protocol", raw="2,1"))
    a.add(CryptoUse(Primitive.CONFIG, "ssh-fingerprint-hash", raw="md5"))
    a.add(CryptoUse(Primitive.CONFIG, "weak-moduli", raw="12"))
    a.add(CryptoUse(Primitive.CONFIG, "ssh-version", raw="OpenSSH_7.2p2"))
    t = Asset(AssetKind.TLS_ENDPOINT, "https", "example:443", "doc")
    for s in ["TLS_RSA_WITH_RC4_128_MD5", "TLS_RSA_EXPORT_WITH_DES40_CBC_SHA", "TLS_RSA_WITH_3DES_EDE_CBC_SHA", "TLS_RSA_WITH_AES_128_CBC_SHA",
              "TLS_DH_anon_WITH_AES_128_CBC_SHA", "TLS_ECDH_RSA_WITH_AES_128_GCM_SHA256", "TLS_DHE_DSS_WITH_AES_128_CBC_SHA",
              "TLS_RSA_WITH_NULL_SHA", "TLS_RSA_WITH_IDEA_CBC_SHA", "TLS_ECDHE_RSA_WITH_AES_128_CCM_8", "TLS_AES_128_GCM_SHA256"]:
        t.add(names.tls_cipher_suite(s))
    for pr in ["sslv2", "sslv3", "tls1.0", "tls1.1", "tls1.2"]:
        t.add(names.tls_protocol(pr))
    for g in ["ffdhe2048", "secp224r1", "sect163k1", "brainpoolP256r1", "x25519", "X25519MLKEM768"]:
        t.add(names.tls_group(g))
    t.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=1024, context="tls-group", raw="DH 1024"))
    t.add(CryptoUse(Primitive.KEY_EXCHANGE, "dh", key_bits=512, context="tls-group", raw="DH 512"))
    t.add(names.tls_sigalg("rsa_pkcs1_sha1"))
    t.add(names.tls_sigalg("rsa_pkcs1_md5"))
    t.add(CryptoUse(Primitive.CONFIG, "dh-param-missing", raw="no dhparam"))
    t.add(CryptoUse(Primitive.CONFIG, "openssl-version", raw="OpenSSL 1.0.2k"))
    t.add(CryptoUse(Primitive.CONFIG, "openssl-seclevel", raw="1"))
    c = Asset(AssetKind.CERTIFICATE, "cert", "/etc/ssl/x.pem", "doc",
              attributes={"not_before": "2015-01-01T00:00:00+00:00", "not_after": "2016-01-01T00:00:00+00:00", "version": 1,
                          "ext_key_usage": ["serverAuth"], "serial_bits": 20, "self_signed": True})
    c.add(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=512, context="public-key"))
    c.add(CryptoUse(Primitive.SIGNATURE, "rsa", hash_algorithm="md5", context="certificate-signature"))
    c2 = Asset(AssetKind.CERTIFICATE, "cert2", "/etc/ssl/y.pem", "doc",
               attributes={"not_before": "2020-01-01T00:00:00+00:00", "not_after": "2099-01-01T00:00:00+00:00", "ext_key_usage": ["serverAuth"]})
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=256, curve="explicit", context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=1024, context="public-key", extra={"rsa_exponent": 3}))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=160, curve="secp160r1", context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=256, curve="secp256k1", context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=224, curve="p-224", context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "ed25519", key_bits=256, curve="curve25519", context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "dsa", key_bits=2048, context="public-key"))
    c2.add(CryptoUse(Primitive.PUBLIC_KEY, "gost-r34.10-2001", context="public-key"))
    c2.add(CryptoUse(Primitive.SIGNATURE, "rsa", hash_algorithm="sha1", context="certificate-signature"))
    c2.add(CryptoUse(Primitive.SIGNATURE, "rsa", hash_algorithm="sha224", context="certificate-signature"))
    ca = Asset(AssetKind.CA_CERTIFICATE, "root", "/etc/ssl/certs/root.pem", "doc",
               attributes={"trust_anchor": True, "self_signed": True, "not_after": "2010-01-01T00:00:00+00:00"})
    ca.add(CryptoUse(Primitive.SIGNATURE, "rsa", hash_algorithm="sha1", context="certificate-signature"))
    ca.add(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=2048, context="public-key"))
    k = Asset(AssetKind.SSH_USER_KEY, "id_rsa", "/home/u/.ssh/id_rsa", "doc", attributes={"mode": 0o644, "encrypted": False, "fmt": "pkcs1"})
    k2 = Asset(AssetKind.PRIVATE_KEY, "k.pem", "/etc/x/k.pem", "doc", attributes={"mode": 0o600, "encrypted": True, "fmt": "pkcs1", "encryption_note": "PBES1 pbeWithMD5AndDES-CBC"})
    k3 = Asset(AssetKind.PRIVATE_KEY, "k3.pem", "/etc/x/k3.pem", "doc", attributes={"mode": 0o600, "encrypted": True, "fmt": "pkcs8-encrypted", "encryption_note": "PBES2 pbkdf2 iterations=2048 prf=hmac-sha1 cipher=aes-256-cbc"})
    k4 = Asset(AssetKind.PRIVATE_KEY, "k4.pem", "/opt/x/k4.pem", "doc", attributes={"mode": 0o600, "encrypted": False, "fmt": "pkcs8"})
    kr = Asset(AssetKind.KERBEROS_CONFIG, "krb5.conf", "/etc/krb5.conf", "doc")
    for e in ["des-cbc-crc", "rc4-hmac", "rc4-hmac-exp", "des3-cbc-sha1", "aes128-cts-hmac-sha1-96", "aes256-cts-hmac-sha384-192", 99]:
        kr.add(names.krb_enctype(e))
    kr.add(CryptoUse(Primitive.CONFIG, "krb-allow-weak-crypto", raw="true"))
    nd = Asset(AssetKind.NETWORK_DEVICE, "sw1", "sw1.cfg", "doc")
    for pr in ["ssh1.99", "snmpv1", "snmpv2c", "snmpv3-noauth", "snmpv3-noprivacy", "telnet", "http-mgmt", "ftp", "tftp", "ikev1", "ikev1-aggressive",
               "pptp", "l2tp-ipsec-psk", "ntlmv1", "ntlmv2", "wep", "wpa-tkip", "smbv1", "ldap-cleartext", "rdp-no-nla", "dtls1.0"]:
        nd.add(CryptoUse(Primitive.PROTOCOL, pr, raw=pr))
    for knob, val in [("snmp-auth-proto", "md5"), ("snmp-priv-proto", "des"), ("snmp-priv-proto", "3des"), ("password-hash", "type7"), ("password-hash", "type5"),
                      ("crypto-policy", "LEGACY"), ("crypto-policy", "DEFAULT:SHA1"), ("java-disabled-algorithms-missing", "TLSv1")]:
        nd.add(CryptoUse(Primitive.CONFIG, knob, raw=val, context=knob))
    nd.add(CryptoUse(Primitive.HASH, "md5", context="ntp-auth"))
    nd.add(CryptoUse(Primitive.HASH, "sha1", context="signature"))
    nd.add(CryptoUse(Primitive.HASH, "sha224", context="x"))
    return [a, t, c, c2, ca, k, k2, k3, k4, kr, nd]


def list_rules() -> List[Dict[str, str]]:
    rows: Dict[str, Dict[str, str]] = {}
    now = _dt.datetime(2026, 1, 1, tzinfo=_dt.timezone.utc)
    for prof in PROFILES:
        for f in evaluate(_synthetic_assets(), prof, now=now):
            r = rows.setdefault(f.rule_id, {"rule_id": f.rule_id, "title": f.title, "max_severity": f.severity.label, "profiles": set()})
            r["profiles"].add(prof)
            if f.severity.label != r["max_severity"] and f.severity > _sev(r["max_severity"]):
                r["max_severity"] = f.severity.label
    out = []
    for r in sorted(rows.values(), key=lambda r: r["rule_id"]):
        r["profiles"] = ",".join(sorted(r["profiles"]))
        out.append(r)
    return out


def _sev(label: str):
    from .model import Severity
    return Severity[label.upper()]
