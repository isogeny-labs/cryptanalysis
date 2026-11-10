"""Tests for the dependency-free core: DER, X.509, key files, name normalisation, policy."""

import datetime as dt
import glob
import os
import unittest

from cryptoscan import asn1, names, policy, x509
from cryptoscan.model import Asset, AssetKind, CryptoUse, Primitive, ScanMeta, ScanResult, Severity

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "core")
NOW = dt.datetime(2026, 11, 10, tzinfo=dt.timezone.utc)


def _read(name):
    with open(os.path.join(FIX, name), "rb") as fh:
        return fh.read()


class DERTests(unittest.TestCase):
    def test_oid_decode(self):
        self.assertEqual(asn1.decode_oid(bytes([0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0B])), "1.2.840.113549.1.1.11")
        self.assertEqual(asn1.decode_oid(bytes([0x55, 0x1D, 0x13])), "2.5.29.19")

    def test_rejects_indefinite_and_trailing(self):
        with self.assertRaises(asn1.DERError):
            asn1.decode(b"\x30\x80\x00\x00")
        with self.assertRaises(asn1.DERError):
            asn1.decode(b"\x02\x01\x05\x00")
        node, rest = asn1.decode_prefix(b"\x02\x01\x05\x00")
        self.assertEqual(node.as_int(), 5)
        self.assertEqual(rest, b"\x00")

    def test_times(self):
        n = asn1.Node(0, False, asn1.UTCTIME, 2, b"490101000000Z", b"")
        self.assertEqual(n.as_time().year, 2049)
        n = asn1.Node(0, False, asn1.UTCTIME, 2, b"500101000000Z", b"")
        self.assertEqual(n.as_time().year, 1950)
        n = asn1.Node(0, False, asn1.GENERALIZEDTIME, 2, b"20991231235959Z", b"")
        self.assertEqual(n.as_time().year, 2099)


class X509Tests(unittest.TestCase):
    def test_rsa1024_root(self):
        c = x509.load_certificates(_read("rsa1024-root.pem"))[0]
        self.assertEqual(c.public_key.algorithm, "rsa")
        self.assertEqual(c.public_key.key_bits, 1024)
        self.assertEqual(c.public_key.rsa_exponent, 65537)
        self.assertTrue(c.is_ca)
        self.assertTrue(c.self_signed)
        self.assertEqual(c.signature_algorithm, "rsa")
        self.assertEqual(c.signature_hash, "sha256")
        self.assertIn("CN=weak-root", c.subject)
        self.assertEqual(c.version, 3)
        self.assertTrue(c.extensions.get("basicConstraints"))

    def test_sha1_leaf_pem_and_der(self):
        for name in ("rsa2048-sha1.pem", "rsa2048-sha1.der"):
            c = x509.load_certificates(_read(name))[0]
            self.assertEqual((c.signature_algorithm, c.signature_hash), ("rsa", "sha1"))
            self.assertEqual(c.public_key.key_bits, 2048)
            self.assertIn("DNS:sha1.example.test", c.sans)
            self.assertIn("IP:10.0.0.1", c.sans)
            self.assertIn("serverAuth", c.ext_key_usage)
            self.assertFalse(c.is_ca)
            self.assertEqual(c.validity_days(), 365)

    def test_ec_ed25519_pss(self):
        p256 = x509.load_certificates(_read("p256.pem"))[0]
        self.assertEqual((p256.public_key.algorithm, p256.public_key.curve, p256.public_key.key_bits), ("ec", "p-256", 256))
        self.assertEqual((p256.signature_algorithm, p256.signature_hash), ("ecdsa", "sha256"))
        p384 = x509.load_certificates(_read("p384-root.pem"))[0]
        self.assertEqual((p384.public_key.curve, p384.signature_hash), ("p-384", "sha384"))
        ed = x509.load_certificates(_read("ed25519-root.pem"))[0]
        self.assertEqual((ed.public_key.algorithm, ed.signature_algorithm, ed.signature_hash), ("ed25519", "ed25519", None))
        pss = x509.load_certificates(_read("rsa-pss.pem"))[0]
        self.assertEqual((pss.signature_algorithm, pss.signature_hash), ("rsa-pss", "sha256"))

    def test_bundles(self):
        pem = x509.load_certificates(_read("bundle.pem"))
        p7 = x509.load_certificates(_read("bundle.p7b"))
        self.assertEqual(len(pem), 3)
        self.assertEqual({c.fingerprint_sha256 for c in pem}, {c.fingerprint_sha256 for c in p7})

    def test_system_store_parses(self):
        files = glob.glob("/etc/ssl/certs/*.pem")[:50]
        if not files:
            self.skipTest("no system trust store")
        n = 0
        for fn in files:
            with open(fn, "rb") as fh:
                for c in x509.load_certificates(fh.read()):
                    n += 1
                    self.assertIn(c.public_key.algorithm, ("rsa", "ec", "ed25519", "ed448", "dsa"))
                    self.assertTrue(c.public_key.key_bits)
        self.assertGreater(n, 0)

    def test_garbage(self):
        self.assertEqual(x509.load_certificates(b"not a cert"), [])
        self.assertEqual(x509.load_certificates(b"-----BEGIN CERTIFICATE-----\nAAAA\n-----END CERTIFICATE-----\n"), [])


class KeyFileTests(unittest.TestCase):
    def test_private_keys(self):
        k = x509.parse_key_data(_read("rsa1024.key"))[0]
        self.assertEqual((k.kind, k.public_key.algorithm, k.public_key.key_bits), ("private", "rsa", 1024))
        k = x509.parse_key_data(_read("p256.key"))[0]
        self.assertEqual((k.kind, k.fmt, k.public_key.curve), ("private", "sec1", "p-256"))
        k = x509.parse_key_data(_read("ed25519.key"))[0]
        self.assertEqual((k.fmt, k.public_key.algorithm), ("pkcs8", "ed25519"))
        k = x509.parse_key_data(_read("rsa2048.pub"))[0]
        self.assertEqual((k.kind, k.public_key.key_bits), ("public", 2048))

    def test_encrypted_keys(self):
        k = x509.parse_key_data(_read("rsa2048-pkcs8-enc.key"))[0]
        self.assertEqual(k.kind, "encrypted-private")
        self.assertIn("prf=hmac-sha256", k.note)
        self.assertIn("aes-256-cbc", k.note)
        k = x509.parse_key_data(_read("rsa2048-legacy-enc.key"))[0]
        self.assertEqual((k.kind, k.fmt, k.encrypted), ("encrypted-private", "pkcs1", True))
        p = os.path.join(FIX, "rsa2048-pkcs8-pbes1.key")
        if os.path.getsize(p):
            k = x509.parse_key_data(_read("rsa2048-pkcs8-pbes1.key"))[0]
            self.assertIn("PBES1", k.note)

    def test_dhparam(self):
        k = x509.parse_key_data(_read("dh1024.pem"))[0]
        self.assertEqual((k.kind, k.public_key.algorithm, k.public_key.key_bits), ("parameters", "dh", 1024))


class NamesTests(unittest.TestCase):
    def test_tls_suites(self):
        u = names.tls_cipher_suite("TLS_RSA_WITH_RC4_128_MD5")
        self.assertEqual((u.algorithm, u.key_bits, u.hash_algorithm, u.extra["kx"], u.extra["pfs"]), ("rc4", 128, "md5", "rsa-kex", False))
        u = names.tls_cipher_suite("ECDHE-ECDSA-AES256-GCM-SHA384")
        self.assertEqual((u.algorithm, u.key_bits, u.mode, u.extra["kx"], u.extra["auth"], u.extra["aead"]), ("aes", 256, "gcm", "ecdhe", "ecdsa", True))
        u = names.tls_cipher_suite("EXP-DES-CBC-SHA")
        self.assertTrue(u.extra["export"])
        u = names.tls_cipher_suite("TLS_AES_128_GCM_SHA256")
        self.assertEqual(u.extra["kx"], "tls13-ephemeral")
        u = names.tls_cipher_suite("ADH-AES256-SHA")
        self.assertEqual(u.extra["auth"], "none")

    def test_ssh(self):
        self.assertEqual(names.ssh_kex("diffie-hellman-group1-sha1").key_bits, 1024)
        self.assertEqual(names.ssh_kex("mlkem768x25519-sha256").algorithm, "hybrid-pq")
        self.assertTrue(names.ssh_kex("gss-gex-sha1-toWM5Slw5Ew8Mqkay+al2g==").extra["gssapi"])
        self.assertEqual(names.ssh_hostkey("ssh-rsa-cert-v01@openssh.com").extra["certificate"], True)
        self.assertEqual(names.ssh_mac("hmac-sha1-96-etm@openssh.com").mode, "etm")

    def test_krb(self):
        self.assertEqual(names.krb_enctype(23).extra["enctype"], "rc4-hmac")
        self.assertEqual(names.krb_enctype("arcfour-hmac-md5").extra["etype_id"], 23)
        self.assertTrue(names.krb_enctype("-des3").extra["negated"])
        self.assertEqual(names.krb_enctype("aes256-sha2").extra["enctype"], "aes256-cts-hmac-sha384-192")

    def test_strength(self):
        self.assertEqual(names.security_strength(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=2048)), 112)
        self.assertEqual(names.security_strength(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=3072)), 128)
        self.assertEqual(names.security_strength(CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=384)), 192)
        self.assertEqual(names.security_strength(CryptoUse(Primitive.CIPHER, "3des", key_bits=168)), 112)
        self.assertEqual(names.security_strength(CryptoUse(Primitive.CIPHER, "rc4", key_bits=128)), 64)


def _cert_asset(name, kind=AssetKind.CERTIFICATE, anchor=False):
    c = x509.load_certificates(_read(name))[0]
    # A synthetic location: the real fixture path contains "/tests/", which the policy treats as test material.
    a = Asset(kind, c.subject, "/etc/ssl/certs/" + name, "test", attributes=dict(c.summary()))
    a.attributes["trust_anchor"] = anchor
    a.add(CryptoUse(Primitive.PUBLIC_KEY, c.public_key.algorithm, key_bits=c.public_key.key_bits, curve=c.public_key.curve, context="public-key"))
    a.add(CryptoUse(Primitive.SIGNATURE, c.signature_algorithm, hash_algorithm=c.signature_hash, context="certificate-signature"))
    return a


def _ids(assets, profile="nist", now=NOW):
    return {f.rule_id: f for f in policy.evaluate(assets, profile, now=now)}


class PolicyTests(unittest.TestCase):
    def test_rsa1024_root_is_high_even_as_anchor(self):
        ids = _ids([_cert_asset("rsa1024-root.pem", AssetKind.CA_CERTIFICATE, anchor=True)])
        self.assertIn("PK-RSA-LT-2048", ids)
        self.assertEqual(ids["PK-RSA-LT-2048"].severity, Severity.HIGH)
        self.assertTrue(ids["PK-RSA-LT-2048"].quantum_vulnerable)

    def test_sha1_leaf_high_but_anchor_info(self):
        leaf = _ids([_cert_asset("rsa2048-sha1.pem")])
        self.assertEqual(leaf["SIG-HASH-SHA1"].severity, Severity.HIGH)
        anchor = _cert_asset("rsa2048-sha1.pem", AssetKind.CA_CERTIFICATE, anchor=True)
        ids = _ids([anchor])
        self.assertNotIn("SIG-HASH-SHA1", ids)
        self.assertEqual(ids["SIG-ANCHOR-WEAK-HASH"].severity, Severity.INFO)

    def test_expiry_and_sunset(self):
        a = _cert_asset("p256.pem")
        ids = _ids([a])
        self.assertIn("CERT-EXPIRING", ids)              # 30-day cert generated at fixture time
        self.assertNotIn("CERT-EXPIRED", ids)
        later = _ids([a], now=NOW + dt.timedelta(days=400))
        self.assertIn("CERT-EXPIRED", later)
        rsa = _ids([_cert_asset("rsa2048-sha1.pem")])
        self.assertIn("PK-RSA-2048-SUNSET", rsa)
        self.assertEqual(rsa["PK-RSA-2048-SUNSET"].deprecation_year, 2030)
        self.assertEqual(rsa["PQC-TRANSITION"].severity, Severity.LOW)

    def test_profiles_differ(self):
        a = _cert_asset("p256.pem")
        self.assertNotIn("PK-EC-NOT-IN-PROFILE", _ids([a], "nist"))
        self.assertIn("PK-EC-NOT-IN-PROFILE", _ids([a], "cnsa2"))
        r = _cert_asset("rsa2048-sha1.pem")
        self.assertIn("PK-RSA-BELOW-PROFILE", _ids([r], "bsi"))
        self.assertIn("PK-RSA-BELOW-PROFILE", _ids([r], "cnsa2"))
        self.assertNotIn("PK-RSA-BELOW-PROFILE", _ids([r], "nist"))
        leg = _ids([r], "legacy")
        self.assertNotIn("PQC-TRANSITION", leg)
        self.assertNotIn("PK-RSA-2048-SUNSET", leg)
        self.assertIn("SIG-HASH-SHA1", leg)

    def test_ssh_server_rules_and_dedup(self):
        a = Asset(AssetKind.SSH_SERVER, "sshd", "/etc/ssh/sshd_config", "test")
        for k in ("diffie-hellman-group1-sha1", "curve25519-sha256"):
            a.add(names.ssh_kex(k))
        for k in ("ssh-rsa", "ssh-dss", "rsa-sha2-512"):
            a.add(names.ssh_hostkey(k))
        a.add(names.ssh_cipher("3des-cbc"))
        a.add(names.ssh_mac("hmac-md5"))
        a.add(names.ssh_cipher("chacha20-poly1305@openssh.com"))
        ids = _ids([a])
        for rid in ("PK-DH-LT-2048", "KX-SHA1", "SSH-RSA-SHA1", "SIG-DSA", "CIPHER-3DES", "MAC-MD5", "SSH-TERRAPIN"):
            self.assertIn(rid, ids, rid)
        self.assertNotIn("PK-DSA", ids)            # ssh-dss is reported once, as SIG-DSA
        self.assertNotIn("SIG-HASH-SHA1", ids)
        a.attributes["kex_strict"] = True
        self.assertNotIn("SSH-TERRAPIN", _ids([a]))
        # determinism
        f1 = [f.finding_id for f in policy.evaluate([a], "nist", now=NOW)]
        f2 = [f.finding_id for f in policy.evaluate([a], "nist", now=NOW)]
        self.assertEqual(f1, f2)

    def test_roundtrip_json(self):
        a = _cert_asset("rsa2048-sha1.pem")
        res = ScanResult(meta=ScanMeta(profile="nist"), assets=[a], findings=policy.evaluate([a], "nist", now=NOW))
        import json
        back = ScanResult.from_dict(json.loads(res.to_json()))
        self.assertEqual(back.to_json(), res.to_json())
        self.assertEqual(back.findings[0].severity, res.findings[0].severity)


if __name__ == "__main__":
    unittest.main()


class PolicyRefinementTests(unittest.TestCase):
    def test_self_signed_ca_anywhere_is_anchor(self):
        a = _cert_asset("rsa2048-sha1.pem")
        a.attributes.update({"is_ca": True, "self_signed": True})
        ids = _ids([a])
        self.assertNotIn("SIG-HASH-SHA1", ids)
        self.assertIn("SIG-ANCHOR-WEAK-HASH", ids)

    def test_test_material_capped(self):
        a = Asset(AssetKind.PRIVATE_KEY, "k", "/opt/sdk/third_party/requests/tests/certs/server.key", "t",
                  attributes={"mode": 0o644, "encrypted": False})
        a.add(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=1024, context="public-key"))
        ids = _ids([a])
        self.assertEqual(ids["KEY-PERMS"].severity, Severity.LOW)
        self.assertIn("test-data", ids["KEY-PERMS"].tags)
        self.assertEqual(ids["PK-RSA-LT-2048"].severity, Severity.LOW)
        b = Asset(AssetKind.PRIVATE_KEY, "k", "/etc/ssl/private/server.key", "t", attributes={"mode": 0o644, "encrypted": False})
        b.add(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=1024, context="public-key"))
        self.assertEqual(_ids([b])["KEY-PERMS"].severity, Severity.HIGH)
        self.assertFalse(policy.is_test_material("/etc/ssl/private/latest/server.key"))


class NonCertificateVersionAttributeTests(unittest.TestCase):
    def test_ssh_server_version_string_does_not_break_certificate_rules(self):
        a = Asset(AssetKind.SSH_SERVER, "sshd", "/etc/ssh/sshd_config", "t", attributes={"version": "OpenSSH_10.2p1"})
        a.add(names.ssh_kex("curve25519-sha256"))
        ids = _ids([a])
        self.assertNotIn("CERT-V1", ids)
        c = Asset(AssetKind.CERTIFICATE, "c", "/etc/ssl/certs/c.pem", "t", attributes={"version": "1", "serial_bits": "12"})
        ids = _ids([c])
        self.assertIn("CERT-V1", ids)
        self.assertIn("CERT-SHORT-SERIAL", ids)
        c2 = Asset(AssetKind.CERTIFICATE, "c", "/etc/ssl/certs/c2.pem", "t", attributes={"version": "garbage"})
        self.assertNotIn("CERT-V1", _ids([c2]))
