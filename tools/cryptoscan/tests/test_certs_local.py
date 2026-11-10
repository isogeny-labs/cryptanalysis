import datetime as dt
import os
import unittest

from cryptoscan import jks, x509
from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.certs_local import CertsLocalCollector, parse_nss_list, trust_store_summary
from cryptoscan.model import AssetKind, Primitive, Severity
from cryptoscan.policy import evaluate

try:                                    # `unittest discover -s tests` vs `unittest tests.test_x`
    import jks_builder
    from fixtures_util import cert_path, make_root, pem_to_der, put, read, rmtree
except ImportError:                     # pragma: no cover
    from . import jks_builder
    from .fixtures_util import cert_path, make_root, pem_to_der, put, read, rmtree

FUTURE = dt.datetime(2200, 1, 1, tzinfo=dt.timezone.utc)


def _certs(*names):
    return [x509.load_certificates(read(cert_path(n)))[0] for n in names]


class CertsLocalTests(unittest.TestCase):
    def setUp(self):
        self.root = make_root()
        self.addCleanup(rmtree, self.root)
        weak = read(cert_path("ca1024_sha1_root.pem"))
        p256 = read(cert_path("p256_leaf.pem"))
        # system bundle (Debian layout) and an enterprise root added locally
        put(self.root, "/etc/ssl/certs/ca-certificates.crt", weak + p256)
        put(self.root, "/usr/local/share/ca-certificates/corp-root.crt", weak)
        # service certificates
        put(self.root, "/etc/nginx/ssl/leaf.pem", read(cert_path("rsa2048_sha1_leaf.pem")) + weak, mode=0o640)
        put(self.root, "/etc/nginx/ssl/server.pem", read(cert_path("server_sha256.pem")))
        put(self.root, "/etc/nginx/ssl/ed.crt", read(cert_path("ed25519_cert.pem")))
        put(self.root, "/etc/nginx/ssl/short.pem", read(cert_path("short_lived_1day.pem")))
        put(self.root, "/etc/nginx/ssl/legacy.p12", read(cert_path("legacy_3des_sha1mac.p12")), mode=0o600)
        put(self.root, "/etc/nginx/ssl/rc2.p12", read(cert_path("legacy_rc2_40.p12")), mode=0o600)
        put(self.root, "/etc/nginx/ssl/modern.p12", read(cert_path("modern_aes_sha256.p12")), mode=0o600)
        # JDK cacerts (JKS) and an application keystore with a private-key entry
        weak_der = pem_to_der(weak)
        leaf_der = pem_to_der(read(cert_path("rsa2048_sha1_leaf.pem")))
        put(self.root, "/usr/lib/jvm/java-17/lib/security/cacerts",
            jks_builder.build([("trusted", "weakroot", weak_der), ("trusted", "p256", pem_to_der(p256))]))
        put(self.root, "/opt/app/keystore.jks",
            jks_builder.build([("key", "server", [leaf_der, weak_der])], version=1))
        self.ctx = ScanContext(root=self.root, hostname="testhost")
        self.assets = CertsLocalCollector().collect(self.ctx)
        self.findings = evaluate(self.assets, "nist", now=FUTURE)
        self.ids = {f.rule_id for f in self.findings}

    def by_name(self, needle, kind=None):
        return [a for a in self.assets if needle in a.name and (kind is None or a.kind == kind)]

    def test_trust_store_summary_attributes(self):
        stores = [a for a in self.assets if a.kind == AssetKind.TRUST_STORE and a.location.endswith("ca-certificates.crt")]
        self.assertEqual(len(stores), 1)
        at = stores[0].attributes
        self.assertEqual(at["count"], 2)
        self.assertEqual(at["rsa1024"], 1)
        self.assertEqual(at["sha1_roots"], 1)
        self.assertEqual(at["by_key_algorithm"].get("rsa-1024"), 1)
        self.assertIn("rsa-1024", at["weakest_key"])

    def test_dedup_and_locally_added(self):
        roots = self.by_name("Weak Test Root CA", AssetKind.CA_CERTIFICATE)
        self.assertEqual(len(roots), 1)                     # one asset for the same SHA-256
        r = roots[0]
        self.assertTrue(r.attributes["trust_anchor"])
        self.assertTrue(r.attributes["self_signed"])
        self.assertTrue(r.attributes["locally_added"])
        self.assertGreaterEqual(len(r.attributes["locations"]), 2)
        self.assertEqual(r.attributes["serial_bits"], r.attributes["serial_bits"])
        kinds = {(u.primitive, u.algorithm, u.key_bits) for u in r.uses}
        self.assertIn((Primitive.PUBLIC_KEY, "rsa", 1024), kinds)
        sig = [u for u in r.uses if u.context == "certificate-signature"][0]
        self.assertEqual(sig.hash_algorithm, "sha1")
        p256 = self.by_name("p256.example.test")[0]
        self.assertFalse(p256.attributes["locally_added"])
        self.assertTrue(p256.attributes["trust_anchor"])

    def test_policy_rule_ids(self):
        self.assertIn("PK-RSA-LT-2048", self.ids)
        self.assertIn("SIG-ANCHOR-WEAK-HASH", self.ids)
        self.assertIn("SIG-HASH-SHA1", self.ids)            # the SHA-1 signed leaf (not an anchor)
        self.assertIn("CERT-EXPIRED", self.ids)             # evaluated at year 2200

    def test_anchor_sha1_is_info_not_high(self):
        anchor_ids = {a.asset_id for a in self.assets if "Weak Test Root CA" in a.name}
        sig = [f for f in self.findings if f.asset_id in anchor_ids and f.rule_id.startswith("SIG-")]
        self.assertTrue(sig)
        for f in sig:
            self.assertEqual(f.rule_id, "SIG-ANCHOR-WEAK-HASH")
            self.assertEqual(f.severity, Severity.INFO)
        leaf = self.by_name("sha1-leaf.example.test")[0]
        self.assertEqual(leaf.kind, AssetKind.CERTIFICATE)
        leaf_f = [f for f in self.findings if f.asset_id == leaf.asset_id and f.rule_id == "SIG-HASH-SHA1"]
        self.assertTrue(leaf_f)
        self.assertGreater(leaf_f[0].severity, Severity.INFO)

    def test_service_certificates(self):
        leaf = self.by_name("sha1-leaf.example.test")[0]
        self.assertEqual(leaf.attributes["mode"], 0o640)
        self.assertIn("serial_bits", leaf.attributes)
        self.assertFalse(leaf.attributes["trust_anchor"])
        ed = self.by_name("ed25519.example.test")[0]
        self.assertTrue(any(u.algorithm == "ed25519" for u in ed.uses))
        server = self.by_name("localhost")
        self.assertTrue(any(a.attributes["is_default_snakeoil"] for a in server))
        self.assertEqual(self.ctx.warnings, [])

    def test_jdk_cacerts(self):
        stores = [a for a in self.assets if a.kind == AssetKind.TRUST_STORE and "cacerts" in a.location]
        self.assertEqual(len(stores), 1)
        self.assertEqual(stores[0].attributes["store_type"], "jks")
        self.assertEqual(stores[0].attributes["count"], 2)
        self.assertEqual(stores[0].attributes["rsa1024"], 1)
        locs = self.by_name("Weak Test Root CA")[0].attributes["locations"]
        self.assertTrue(any("cacerts#weakroot" in l for l in locs))

    def test_jks_keystore_with_key_entry(self):
        ks = [a for a in self.assets if a.kind == AssetKind.JAVA_KEYSTORE and a.location.endswith("keystore.jks")]
        self.assertEqual(len(ks), 1)
        self.assertEqual(ks[0].attributes["format"], "jks")
        self.assertEqual(ks[0].attributes["key_entries"], 1)
        self.assertIn("JavaSoft", ks[0].attributes["key_protectors"][0])

    def test_pkcs12_weak_pbe_detected(self):
        p12 = {os.path.basename(a.location): a for a in self.assets if a.kind == AssetKind.JAVA_KEYSTORE
               and a.attributes.get("format") == "pkcs12"}
        self.assertEqual(set(p12), {"legacy.p12", "rc2.p12", "modern.p12"})
        legacy = p12["legacy.p12"]
        self.assertTrue(legacy.attributes["encrypted"])
        self.assertIn("1.2.840.113549.1.12.1.3", legacy.attributes["pbe_oids"])
        self.assertIn("1.2.840.113549.1.12.1.6", p12["rc2.p12"].attributes["pbe_oids"])
        self.assertEqual(p12["modern.p12"].uses, [])
        by_asset = {}
        for f in self.findings:
            by_asset.setdefault(f.asset_id, set()).add(f.rule_id)
        self.assertIn("CIPHER-3DES", by_asset[legacy.asset_id])
        self.assertIn("MAC-SHA1", by_asset[legacy.asset_id])
        self.assertIn("CIPHER-RC2", by_asset[p12["rc2.p12"].asset_id])
        self.assertNotIn("CIPHER-3DES", by_asset.get(p12["modern.p12"].asset_id, set()))

    def test_extra_paths(self):
        extra = make_root()
        self.addCleanup(rmtree, extra)
        put(extra, "/anywhere/x.crt", read(cert_path("p256_leaf.pem")))
        put(extra, "/anywhere/blob", read(cert_path("ed25519_cert.pem")))      # no extension: found by magic
        ctx = ScanContext(root=self.root, extra_paths=[os.path.join(extra, "anywhere")])
        out = CertsLocalCollector().collect(ctx)
        locs = [l for a in out for l in a.attributes.get("locations", [])]
        self.assertTrue(any(l.endswith("anywhere/x.crt") for l in locs))
        self.assertTrue(any(l.endswith("anywhere/blob") for l in locs))

    def test_empty_root_is_quiet(self):
        empty = make_root()
        self.addCleanup(rmtree, empty)
        ctx = ScanContext(root=empty)
        self.assertEqual(CertsLocalCollector().collect(ctx), [])
        self.assertEqual(ctx.warnings, [])


class HelperTests(unittest.TestCase):
    def test_parse_nss_list(self):
        text = """
Certificate Nickname                                         Trust Attributes
                                                             SSL,S/MIME,JAR/XPI

Corp Root CA                                                 CT,C,C
my server cert                                               u,u,u
Some Peer                                                    P,,
"""
        self.assertEqual(parse_nss_list(text), [("Corp Root CA", "CT,C,C"), ("my server cert", "u,u,u"), ("Some Peer", "P,,")])

    def test_trust_store_summary(self):
        certs = _certs("ca1024_sha1_root.pem", "p256_leaf.pem", "ed25519_cert.pem")
        s = trust_store_summary(certs, now=FUTURE)
        self.assertEqual(s["count"], 3)
        self.assertEqual(s["expired"], 3)
        self.assertEqual(s["rsa1024"], 1)
        self.assertEqual(s["sha1_roots"], 1)

    def test_jks_roundtrip_and_jceks(self):
        der = pem_to_der(read(cert_path("p256_leaf.pem")))
        data = jks_builder.build([("trusted", "a", der), ("key", "b", [der, der])])
        st = jks.parse_jks(data)
        self.assertEqual((st.format, st.version, len(st.entries)), ("jks", 2, 2))
        self.assertEqual(st.entries[1].certs, [der, der])
        self.assertEqual(st.entries[1].key_protector_oid, "1.3.6.1.4.1.42.2.17.1.1")
        jc = jks.parse_jks(jks_builder.build([("trusted", "a", der), ("secret", "s")], magic=jks_builder.JCEKS))
        self.assertEqual(jc.format, "jceks")
        self.assertEqual(len(jc.entries), 1)
        self.assertTrue(jc.notes)
        # truncated input never raises beyond ValueError and keeps a note
        part = jks.parse_jks(data[:60])
        self.assertTrue(part.notes)
        self.assertEqual(jks.sniff(data), "jks")
        self.assertIsNone(jks.sniff(b"hello world"))


if __name__ == "__main__":
    unittest.main()
