"""System policy collector, offline against a fixture root."""

import os
import tempfile
import shutil
import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.system_policy import (SystemPolicyCollector, classify_shadow_hash, java_missing_disabled,
                                                 parse_luks_dump, parse_openssl_ciphers, parse_pam_unix)
from cryptoscan.policy import evaluate

ROOT = os.path.join(os.path.dirname(__file__), "fixtures", "policy", "root")


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


class SystemPolicyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = SystemPolicyCollector().collect(ScanContext(root=ROOT, hostname="h"))

    def by(self, prefix):
        return [a for a in self.assets if a.name.startswith(prefix)]

    def test_crypto_policy_legacy(self):
        a = self.by("crypto-policies")[0]
        self.assertEqual([u.raw for u in a.uses], ["LEGACY"])          # identical state/current collapsed
        self.assertIn("CFG-CRYPTO-POLICY-LEGACY", ids([a]))

    def test_openssl_seclevel_and_min_protocol(self):
        a = self.by("openssl.cnf")[0]
        self.assertEqual(a.location, "/etc/ssl/openssl.cnf")
        r = ids([a])
        self.assertIn("CFG-OPENSSL-SECLEVEL", r)
        self.assertIn("PROTO-TLS10", r)                                  # MinProtocol = TLSv1
        self.assertTrue(a.attributes["legacy_provider_configured"])
        self.assertEqual(a.attributes["options"], ["UnsafeLegacyRenegotiation"])

    def test_java_disabled_algorithms(self):
        bad = [a for a in self.assets if "jdk-17)" in a.name][0]
        good = [a for a in self.assets if "jdk-17-good" in a.name][0]
        missing = [u.raw for u in bad.uses if u.algorithm == "java-disabled-algorithms-missing"][0]
        self.assertEqual(missing, "TLSv1, TLSv1.1, DH keySize < 1024, 3DES_EDE_CBC")
        self.assertIn("CFG-JAVA-DISABLED-ALGS", ids([bad]))
        self.assertEqual(good.uses, [])                                   # stricter DH size is fine
        self.assertEqual(bad.attributes["keystore_type"], "pkcs12")
        self.assertEqual(bad.attributes["crypto_policy"], "unlimited")
        self.assertIn("RSA keySize < 1024", bad.attributes["certpath_disabled"])   # continuation joined

    def test_password_hashes(self):
        a = self.by("login.defs")[0]
        self.assertIn("CFG-PASSWORD-HASH", ids([a]))
        pam = self.by("PAM")[0]
        self.assertTrue(pam.attributes["nullok"])
        self.assertEqual([u.raw for u in pam.uses], ["md5crypt"])
        sh = self.by("/etc/shadow")[0]
        self.assertEqual(sh.attributes["hash_histogram"],
                         {"descrypt": 1, "empty": 1, "locked": 1, "md5crypt": 1, "sha512crypt": 1, "yescrypt": 1})
        self.assertIn("CFG-PASSWORD-HASH", ids([sh]))
        blob = repr([vars(u) for u in sh.uses]) + repr(sh.attributes)
        for secret in ("saltsalt", "abJnggxhB", "oldguy", "XXXXXXXX"):
            self.assertNotIn(secret, blob)

    def test_gnutls_legacy_back_end(self):
        a = self.by("GnuTLS")[0]
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "PROTO-TLS11", "CIPHER-3DES"} <= r)

    def test_not_applicable_on_empty_root(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(SystemPolicyCollector().collect(ScanContext(root=d, hostname="h")), [])


class HelpersTest(unittest.TestCase):
    def test_java_missing_all_when_absent(self):
        self.assertEqual(len(java_missing_disabled(None)), 11)
        self.assertEqual(java_missing_disabled("SSLv3,TLSv1,TLSv1.1,RC4,DES,MD5withRSA,DH keySize<1024,EC keySize < 224,3DES_EDE_CBC,anon,NULL"), [])

    def test_openssl_ciphers(self):
        txt = ("TLS_AES_256_GCM_SHA384         TLSv1.3 Kx=any      Au=any   Enc=AESGCM(256) Mac=AEAD\n"
               "ECDHE-RSA-AES128-SHA           TLSv1   Kx=ECDH     Au=RSA   Enc=AES(128)    Mac=SHA1\n"
               "DES-CBC3-SHA                   SSLv3   Kx=RSA      Au=RSA   Enc=3DES(168)   Mac=SHA1\n")
        s = parse_openssl_ciphers(txt)
        self.assertEqual(s, [("TLS_AES_256_GCM_SHA384", "tls1.3"), ("ECDHE-RSA-AES128-SHA", "tls1"), ("DES-CBC3-SHA", "sslv3")])

    def test_cipher_list_asset_rules(self):
        from cryptoscan import names
        from cryptoscan.model import Asset, AssetKind
        a = Asset(AssetKind.SYSTEM_POLICY, "ciphers", "x", "system_policy")
        for n, p in parse_openssl_ciphers("DES-CBC3-SHA SSLv3 Kx=RSA Au=RSA Enc=3DES(168) Mac=SHA1\n"):
            a.add(names.tls_cipher_suite(n, protocol=p, negotiated=False))
        self.assertIn("CIPHER-3DES", ids([a]))

    def test_shadow_classifier(self):
        self.assertEqual([classify_shadow_hash(x) for x in ("", "*", "!!", "$6$a$b", "!$1$a$b", "abJnggxhB/yWI", "$y$j9T$a$b", "$2b$12$x")],
                         ["empty", "locked", "locked", "sha512crypt", "md5crypt", "descrypt", "yescrypt", "bcrypt"])

    def test_pam_unix(self):
        r = parse_pam_unix("# c\npassword required pam_unix.so sha512 shadow nullok\nauth required pam_unix.so md5\n")
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["algo"], "sha512")

    def test_luks_luks2_and_luks1(self):
        l2 = ("LUKS header information\nVersion:       \t2\nData segments:\n  0: crypt\n\tcipher: aes-xts-plain64\n"
              "Keyslots:\n  0: luks2\n\tKey:        512 bits\n\tPriority:   normal\n\tCipher:     aes-xts-plain64\n"
              "\tCipher key: 512 bits\n\tPBKDF:      argon2id\nDigests:\n  0: pbkdf2\n\tHash:       sha256\n")
        i = parse_luks_dump(l2)
        self.assertEqual((i["version"], i["cipher"], i["key_bits"], i["pbkdf"], i["hash"]), (2, "aes-xts-plain64", 512, "argon2id", "sha256"))
        l1 = "LUKS header information for /dev/x\nVersion:       \t1\nCipher name:    \taes\nCipher mode:    \tcbc-essiv:sha256\nHash spec:      \tsha1\nMK bits:        \t256\n"
        i = parse_luks_dump(l1)
        self.assertEqual((i["version"], i["cipher"], i["hash"], i["key_bits"]), (1, "aes-cbc-essiv:sha256", "sha1", 256))


if __name__ == "__main__":
    unittest.main()
