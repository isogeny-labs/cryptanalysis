"""IPsec / VPN collector against a fixture root (strongSwan, libreswan, swanctl, racoon, OpenVPN, WireGuard, PPTP, L2TP)."""

import os
import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.ipsec import (IpsecCollector, openvpn_cipher, parse_ipsec_conf, parse_proposals,
                                         parse_racoon)
from cryptoscan.policy import evaluate

ROOT = os.path.join(os.path.dirname(__file__), "fixtures", "ipsec", "root")


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


class IpsecTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.assets = IpsecCollector().collect(ScanContext(root=ROOT, hostname="h", options={"openvpn_version": "2.4.12"}))

    def named(self, name):
        found = [a for a in self.assets if a.name == name]
        self.assertEqual(len(found), 1, f"{name}: {[a.name for a in self.assets]}")
        return found[0]

    def test_ipsec_conf_aggressive_3des_md5_modp1024(self):
        a = self.named("ipsec conn legacy-aggr")
        self.assertTrue({"PROTO-IKEV1-AGGR", "CIPHER-3DES", "MAC-MD5", "PK-DH-LT-2048"} <= ids([a]))
        self.assertNotIn("PROTO-IKEV1", ids([a]))                    # aggressive replaces plain ikev1
        self.assertEqual(a.attributes["authby"], "secret")           # inherited from %default
        self.assertTrue(a.attributes["psk"])
        ctxs = {u.context for u in a.uses}
        self.assertEqual(ctxs, {"ike-version", "ike-proposal", "esp-proposal"})

    def test_ipsec_conf_modern_conn_is_clean_but_rsa_sha1(self):
        a = self.named("ipsec conn modern")
        r = ids([a])
        self.assertFalse({"PROTO-IKEV1", "CIPHER-3DES", "MAC-MD5", "PK-DH-LT-2048"} & r)
        self.assertIn("SIG-HASH-SHA1", r)                            # authby=rsa-sha1
        dh = [u for u in a.uses if u.algorithm == "ecdh"]
        self.assertTrue(all(u.curve == "p-384" and u.key_bits == 384 for u in dh))
        gcm = [u for u in a.uses if u.algorithm == "aes"][0]
        self.assertEqual((gcm.key_bits, gcm.mode, gcm.extra["icv_bits"]), (256, "gcm", 128))

    def test_l2tp_psk_conn_and_xl2tpd(self):
        a = self.named("ipsec conn l2tp-psk")
        self.assertIn("PROTO-L2TP-PSK", ids([a]))
        x = self.named("L2TP/IPsec (xl2tpd)")
        self.assertIn("PROTO-L2TP-PSK", ids([x]))

    def test_libreswan_included_conf(self):
        a = self.named("ipsec conn lswan-v1")
        self.assertEqual(a.location, "/etc/ipsec.d/libreswan.conf")
        r = ids([a])
        self.assertIn("PROTO-IKEV1", r)
        self.assertIn("CIPHER-NULL", r)                              # esp=aes_gcm256-null
        aes = [u for u in a.uses if u.algorithm == "aes" and u.context == "esp-proposal"][0]
        self.assertEqual((aes.key_bits, aes.mode), (256, "gcm"))

    def test_swanctl(self):
        a = self.named("swanctl connection site-a")
        r = ids([a])
        self.assertTrue({"PROTO-IKEV1", "PK-DH-LT-2048", "CIPHER-3DES", "MAC-SHA1"} <= r)
        self.assertTrue(a.attributes["psk"])
        b = self.named("swanctl connection site-b")
        self.assertFalse(ids([b]) & {"PROTO-IKEV1", "CIPHER-3DES", "MAC-SHA1", "PK-DH-LT-2048"})
        self.assertNotIn("not-a-real-secret", repr([vars(x) for x in self.assets]))

    def test_racoon(self):
        a = self.named("racoon remote anonymous")
        self.assertTrue({"PROTO-IKEV1-AGGR", "CIPHER-3DES", "MAC-MD5", "PK-DH-LT-2048"} <= ids([a]))
        s = self.named("racoon sainfo anonymous")
        self.assertTrue({"CIPHER-3DES", "MAC-MD5", "PK-DH-LT-2048"} <= ids([s]))

    def test_openvpn_server(self):
        a = self.named("OpenVPN config server.conf")
        r = ids([a])
        self.assertTrue({"CIPHER-64BIT-BLOCK", "MAC-SHA1"} <= r)
        self.assertIn("PROTO-TLS10", r)
        self.assertIn("PK-DH-LT-2048", r)                            # dh1024.pem measured from the file
        self.assertEqual(a.attributes["dh_bits"], 1024)
        self.assertEqual(a.attributes["role"], "server")
        self.assertTrue(a.attributes["tls_auth"])
        self.assertEqual(a.attributes["compression"], ["comp-lzo"])
        self.assertIn("KX-RSA", r)                                   # tls-cipher AES256-SHA (static RSA)
        suites = [u.raw for u in a.uses if u.context == "tls-cipher-suite"]
        self.assertEqual(suites, ["AES256-SHA", "ECDHE-RSA-AES128-GCM-SHA256"])

    def test_openvpn_default_bf_cbc_only_before_2_5(self):
        ctx = ScanContext(root=ROOT, hostname="h", options={"openvpn_version": "2.4.12"})
        col = IpsecCollector()
        # a config with no cipher directive
        a = col._openvpn_file(ctx, os.path.join(ROOT, "etc/openvpn/client.ovpn"), (2, 4))[0]
        self.assertEqual([u.algorithm for u in a.uses if u.primitive.value == "cipher"], ["aes", "aes"])   # data-ciphers set -> no default
        tmp = os.path.join(ROOT, "etc/openvpn/server/server.conf")
        with open(tmp) as fh:
            text = fh.read().replace("cipher BF-CBC\n", "")
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "nocipher.conf")
            with open(p, "w") as fh:
                fh.write(text)
            old = col._openvpn_file(ctx, p, (2, 4))[0]
            new = col._openvpn_file(ctx, p, (2, 5))[0]
            unknown = col._openvpn_file(ctx, p, None)[0]
        bf = [u for u in old.uses if u.algorithm == "blowfish"]
        self.assertEqual(len(bf), 1)
        self.assertEqual(bf[0].extra["source"], "default")
        self.assertIn("CIPHER-64BIT-BLOCK", ids([old]))
        self.assertFalse([u for u in new.uses if u.algorithm == "blowfish"])
        self.assertIn("default_cipher", unknown.attributes)

    def test_openvpn_inline_ca(self):
        c = self.named("OpenVPN config client.ovpn")
        self.assertEqual(c.attributes["role"], "client")
        self.assertTrue(c.attributes["tls_crypt"])
        self.assertTrue({"MAC-SHA1"} - ids([c]) == {"MAC-SHA1"})      # SHA512 auth, GCM data ciphers
        certs = [a for a in self.assets if a.kind.value == "ca_certificate"]
        self.assertEqual(len(certs), 1)
        r = ids(certs)
        self.assertIn("PK-RSA-LT-2048", r)
        self.assertTrue(certs[0].attributes["trust_anchor"])
        self.assertEqual(certs[0].location, "/etc/openvpn/client.ovpn#<ca>")

    def test_wireguard(self):
        a = self.named("WireGuard wg0")
        self.assertEqual(a.attributes["peer_count"], 2)
        self.assertEqual(a.attributes["preshared_key_per_peer"], [True, False])
        self.assertTrue(a.attributes["preshared_key_present"])
        kx = [u for u in a.uses if u.context == "wireguard" and u.primitive.value == "key_exchange"][0]
        self.assertEqual((kx.algorithm, kx.curve, kx.key_bits), ("ecdh", "curve25519", 256))
        blob = repr(vars(a)) + repr([vars(u) for u in a.uses])
        for k in ("AAAAAAAA", "BBBBBBBB", "CCCCCCCC", "DDDDDDDD"):
            self.assertNotIn(k, blob)

    def test_pptp(self):
        a = self.named("PPTP server")
        self.assertIn("PROTO-PPTP", ids([a]))
        self.assertEqual(a.attributes["ppp_options"], ["refuse-pap", "require-mppe-128", "require-mschap-v2"])


class ParserTest(unittest.TestCase):
    def test_proposals(self):
        uses, bad = parse_proposals("aes128-sha1-modp1024,3des-md5-modp768!", "ike-proposal")
        self.assertEqual([(u.primitive.value, u.algorithm, u.key_bits) for u in uses],
                         [("cipher", "aes", 128), ("mac", "hmac", None), ("key_exchange", "dh", 1024),
                          ("cipher", "3des", 168), ("mac", "hmac", None), ("key_exchange", "dh", 768)])
        self.assertEqual(bad, [])
        uses, bad = parse_proposals("aes256gcm16-prfsha256-ecp256bp-curve25519-frobnicate", "x")
        self.assertEqual(bad, ["frobnicate"])
        self.assertEqual([u.curve for u in uses if u.algorithm == "ecdh"], ["brainpoolp256r1", "curve25519"])
        self.assertTrue([u for u in uses if u.extra.get("prf")])

    def test_ipsec_conf_parser(self):
        secs, inc = parse_ipsec_conf("conn a\n  keyexchange=ikev1 # c\n  ike = aes-sha1\nconn b\n  also=a\ninclude x/*.conf\n")
        self.assertEqual([(k, n) for k, n, _ in secs], [("conn", "a"), ("conn", "b")])
        self.assertEqual(secs[0][2], {"keyexchange": "ikev1", "ike": "aes-sha1"})
        self.assertEqual(inc, ["x/*.conf"])

    def test_racoon_parser(self):
        blocks = parse_racoon("remote 1.2.3.4 { exchange_mode main; proposal { dh_group 2; } }  # c\n")
        self.assertEqual(blocks[0][0], ["remote", "1.2.3.4"])

    def test_openvpn_cipher_names(self):
        self.assertEqual(openvpn_cipher("DES-EDE3-CBC", "c").algorithm, "3des")
        self.assertEqual(openvpn_cipher("AES-256-GCM", "c").mode, "gcm")
        self.assertEqual(openvpn_cipher("none", "c").algorithm, "null")
        self.assertEqual(openvpn_cipher("BF-CBC", "c").algorithm, "blowfish")


if __name__ == "__main__":
    unittest.main()
