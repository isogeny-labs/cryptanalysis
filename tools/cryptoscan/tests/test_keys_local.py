import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.keys_local import KeysLocalCollector, ec_spki, rsa_spki
from cryptoscan.model import AssetKind, Primitive, Severity
from cryptoscan.policy import evaluate

try:
    from fixtures_util import cert_path, key_path, make_root, put, read, rmtree
except ImportError:                     # pragma: no cover
    from .fixtures_util import cert_path, key_path, make_root, put, read, rmtree


class KeysLocalTests(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.addCleanup(rmtree, self.root)
        d = "/etc/ssl/private/"
        put(self.root, d + "open.pem", read(key_path("rsa2048_plain.pem")), mode=0o644)
        put(self.root, d + "closed.pem", read(key_path("rsa2048_plain.pem")), mode=0o600)
        put(self.root, d + "legacy.pem", read(key_path("rsa_legacy_enc.pem")), mode=0o600)
        put(self.root, d + "pbes2.pem", read(key_path("pkcs8_pbes2_enc.pem")), mode=0o600)
        put(self.root, d + "rsa1024.pem", read(key_path("rsa1024_plain.pem")), mode=0o600)
        put(self.root, d + "dh.pem", read(key_path("dhparam1024.pem")), mode=0o644)
        put(self.root, d + "ec.pem", read(key_path("ecparams.pem")), mode=0o644)
        put(self.root, "/etc/nginx/server.key", read(cert_path("server.key")), mode=0o600)
        put(self.root, "/etc/nginx/server.pem", read(cert_path("server_sha256.pem")))
        put(self.root, "/root/work/user.pem", read(key_path("rsa2048_plain.pem")), mode=0o600)
        put(self.root, "/root/.ssh/id_rsa", read(key_path("rsa2048_plain.pem")), mode=0o600)       # ssh_local's job
        put(self.root, "/root/.ssh/other.pem", read(key_path("rsa2048_plain.pem")), mode=0o600)
        put(self.root, "/etc/ssh/ssh_host_rsa_key", read(key_path("rsa2048_plain.pem")), mode=0o600)
        self.ctx = ScanContext(root=self.root, hostname="h")
        self.assets = KeysLocalCollector().collect(self.ctx)
        self.findings = evaluate(self.assets, "nist")

    def asset(self, suffix):
        m = [a for a in self.assets if a.location.endswith(suffix)]
        self.assertEqual(len(m), 1, suffix)
        return m[0]

    def rules(self, suffix):
        a = self.asset(suffix)
        return {f.rule_id for f in self.findings if f.asset_id == a.asset_id}

    def test_permissions(self):
        self.assertEqual(self.asset("/open.pem").attributes["mode"], 0o644)
        self.assertIn("KEY-PERMS", self.rules("/open.pem"))
        self.assertNotIn("KEY-PERMS", self.rules("/closed.pem"))
        f = [f for f in self.findings if f.rule_id == "KEY-PERMS"][0]
        self.assertEqual(f.severity, Severity.HIGH)

    def test_legacy_pem_encryption(self):
        a = self.asset("/legacy.pem")
        self.assertTrue(a.attributes["encrypted"])
        self.assertEqual(a.attributes["fmt"], "pkcs1")
        self.assertIn("des-ede3-cbc", a.attributes["encryption_note"])
        self.assertIn("KEY-LEGACY-PEM-ENC", self.rules("/legacy.pem"))
        self.assertEqual(a.uses, [])                       # public part is not recoverable without the passphrase

    def test_pkcs8_pbes2_is_modern(self):
        a = self.asset("/pbes2.pem")
        self.assertTrue(a.attributes["encrypted"])
        self.assertEqual(a.attributes["fmt"], "pkcs8-encrypted")
        self.assertIn("PBES2", a.attributes["encryption_note"])
        r = self.rules("/pbes2.pem")
        self.assertFalse(r & {"KEY-LEGACY-PEM-ENC", "KEY-WEAK-PBE", "KEY-UNENCRYPTED"})

    def test_public_key_use_and_rsa_rules(self):
        a = self.asset("/rsa1024.pem")
        self.assertEqual(a.kind, AssetKind.PRIVATE_KEY)
        u = a.uses[0]
        self.assertEqual((u.primitive, u.algorithm, u.key_bits, u.context), (Primitive.PUBLIC_KEY, "rsa", 1024, "public-key"))
        self.assertIn("PK-RSA-LT-2048", self.rules("/rsa1024.pem"))

    def test_service_key_flag_and_unencrypted_info(self):
        self.assertTrue(self.asset("/closed.pem").attributes["service_key"])
        self.assertNotIn("KEY-UNENCRYPTED", self.rules("/closed.pem"))
        user = self.asset("/work/user.pem")
        self.assertFalse(user.attributes["service_key"])
        self.assertIn("KEY-UNENCRYPTED", self.rules("/work/user.pem"))
        sev = [f.severity for f in self.findings if f.asset_id == user.asset_id and f.rule_id == "KEY-UNENCRYPTED"]
        self.assertEqual(sev, [Severity.INFO])

    def test_parameter_files(self):
        dh = self.asset("/dh.pem")
        self.assertEqual(dh.uses[0].primitive, Primitive.KEY_EXCHANGE)
        self.assertEqual((dh.uses[0].algorithm, dh.uses[0].key_bits, dh.uses[0].context), ("dh", 1024, "dhparam"))
        self.assertIn("PK-DH-LT-2048", self.rules("/dh.pem"))
        ec = self.asset("/ec.pem")
        self.assertEqual(ec.uses[0].curve, "p-256")

    def test_ssh_files_left_to_ssh_local(self):
        locs = {a.location for a in self.assets}
        self.assertNotIn("/root/.ssh/id_rsa", locs)
        self.assertNotIn("/etc/ssh/ssh_host_rsa_key", locs)
        self.assertIn("/root/.ssh/other.pem", locs)

    def test_pairs_key_with_certificate(self):
        k = self.asset("/etc/nginx/server.key")
        self.assertEqual(k.attributes["paired_certificate"], "/etc/nginx/server.pem")
        self.assertIsNone(self.asset("/closed.pem").attributes.get("paired_certificate"))

    def test_spki_encoder_matches_openssl_parser(self):
        from cryptoscan import asn1, x509
        cert = x509.load_certificates(read(cert_path("server_sha256.pem")))[0]
        node = asn1.decode(cert.der)
        spki = node.children[0].children[6 if node.children[0].children[0].tag_class == 2 else 5]
        n_e = asn1.decode(spki.children[1].as_bitstring()[1])
        n, e = n_e.children[0].as_int(), n_e.children[1].as_int()
        self.assertEqual(rsa_spki(n, e), spki.raw)
        pc = x509.load_certificates(read(cert_path("p256_leaf.pem")))[0]
        pnode = asn1.decode(pc.der).children[0]
        pspki = pnode.children[6 if pnode.children[0].tag_class == 2 else 5]
        point = pspki.children[1].as_bitstring()[1]
        self.assertEqual(ec_spki(pc.public_key.curve_oid, point), pspki.raw)

    def test_empty_root(self):
        empty = make_root()
        self.addCleanup(rmtree, empty)
        self.assertEqual(KeysLocalCollector().collect(ScanContext(root=empty)), [])


if __name__ == "__main__":
    unittest.main()
