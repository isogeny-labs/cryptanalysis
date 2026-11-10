"""Kerberos collector: krb5.conf, kdc.conf, Samba, AD export, klist parsing."""

import os
import shutil
import tempfile
import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.kerberos import (KerberosCollector, decode_ad_enctypes, enctype_uses, parse_klist)
from cryptoscan.policy import evaluate

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "kerberos")


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


class KerberosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, name, dest):
        d = os.path.join(self.root, dest.lstrip("/"))
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy(os.path.join(FIX, name), d)

    def collect(self, **opts):
        return KerberosCollector().collect(ScanContext(root=self.root, hostname="h", options=opts))

    def test_krb5_conf_with_include_and_nested_realms(self):
        self.put("krb5.conf", "/etc/krb5.conf")
        self.put("krb5.conf.d/extra.conf", "/etc/krb5.conf.d/extra.conf")
        assets = [a for a in self.collect() if a.attributes.get("role") == "client"]
        locs = sorted(a.location for a in assets)
        self.assertEqual(locs, ["/etc/krb5.conf", "/etc/krb5.conf.d/extra.conf"])   # includedir + glob deduped
        main = [a for a in assets if a.location == "/etc/krb5.conf"][0]
        self.assertEqual(main.attributes["realms"], ["EXAMPLE.COM", "OTHER.ORG"])
        self.assertEqual(main.attributes["pkinit_anchors"], ["EXAMPLE.COM: FILE:/etc/pki/example-ca.pem"])
        self.assertTrue(main.attributes["capaths"])
        neg = [u for u in main.uses if u.raw == "-des3"]
        self.assertEqual(len(neg), 1)
        self.assertTrue(neg[0].extra["negated"])
        self.assertEqual(neg[0].context, "default_tgs_enctypes")
        # only the main file is graded here: weak crypto + RC4, but the negated des3 is ignored
        self.assertEqual(ids([main]), {"KRB-ALLOW-WEAK", "KRB-RC4"})
        self.assertNotIn("KRB-3DES", ids([main]))
        # the include file permits des3 explicitly
        inc = [a for a in assets if a.location.endswith("extra.conf")][0]
        self.assertIn("KRB-3DES", ids([inc]))

    def test_library_defaults_when_no_list(self):
        os.makedirs(os.path.join(self.root, "etc"))
        with open(os.path.join(self.root, "etc", "krb5.conf"), "w") as fh:
            fh.write("[libdefaults]\n default_realm = X\n")
        a = [x for x in self.collect(krb5_version="1.19.2") if x.location == "/etc/krb5.conf"][0]
        self.assertTrue(all(u.extra.get("source") == "default" for u in a.uses))
        self.assertTrue({"KRB-RC4", "KRB-3DES"} <= ids([a]))
        a = [x for x in self.collect(krb5_version="1.21.1") if x.location == "/etc/krb5.conf"][0]
        self.assertFalse({"KRB-RC4", "KRB-3DES"} & ids([a]))
        self.assertTrue(a.uses)
        a = [x for x in self.collect() if x.location == "/etc/krb5.conf"][0]      # offline: version unknown
        self.assertEqual(a.uses, [])
        self.assertIn("unknown", a.attributes["library_defaults"])

    def test_kdc_conf(self):
        self.put("kdc.conf", "/var/kerberos/krb5kdc/kdc.conf")
        a = [x for x in self.collect() if x.attributes.get("role") == "kdc"][0]
        ctxs = {(u.context, u.raw) for u in a.uses}
        self.assertIn(("supported_enctypes", "des3-hmac-sha1"), ctxs)
        self.assertIn(("master_key_type", "aes256-cts"), ctxs)
        self.assertEqual(a.attributes["default_principal_flags"], {"EXAMPLE.COM": "+preauth"})
        self.assertEqual(ids([a]), {"KRB-3DES"})

    def test_samba(self):
        self.put("smb.conf", "/etc/samba/smb.conf")
        a = [x for x in self.collect() if x.attributes.get("role") == "samba"][0]
        self.assertEqual(ids([a]), {"PROTO-NTLMV1", "PROTO-SMBV1"})
        self.assertEqual(a.attributes["smb_encrypt"], "desired")
        self.assertEqual(a.attributes["kerberos_encryption_types"], "strong")

    def test_ad_csv_export(self):
        path = os.path.join(FIX, "ad_export.csv")
        accts = {a.attributes["account"]: a for a in self.collect(ad_enctype_export=path)
                 if a.attributes.get("role") == "ad-account"}
        self.assertEqual(set(accts), {"alice", "bob", "svc-old", "svc-none", "svc-aes"})
        self.assertEqual(ids([accts["alice"]]), {"KRB-RC4"})         # 28 = RC4|AES128|AES256
        self.assertEqual(ids([accts["bob"]]), {"KRB-RC4"})
        self.assertEqual(ids([accts["svc-old"]]), {"KRB-DES"})       # 3 = DES only
        self.assertEqual(ids([accts["svc-aes"]]), set())             # 24 = AES only
        none = accts["svc-none"]
        self.assertTrue(none.attributes["default_applied"])
        self.assertTrue(none.uses[0].extra["assumed"])
        self.assertEqual({u.context for u in alice_uses(accts)}, {"msDS-SupportedEncryptionTypes"})

    def test_ad_json_export(self):
        p = os.path.join(self.root, "ad.json")
        with open(p, "w") as fh:
            fh.write('[{"samAccountName": "x", "msDS-SupportedEncryptionTypes": 4}, {"SamAccountName": "y", "msDS-SupportedEncryptionTypes": "0x18"}]')
        accts = {a.attributes["account"]: a for a in self.collect(ad_enctype_export=p) if a.attributes.get("role") == "ad-account"}
        self.assertEqual(ids([accts["x"]]), {"KRB-RC4"})
        self.assertEqual(ids([accts["y"]]), set())


def alice_uses(accts):
    return accts["alice"].uses


class HelpersTest(unittest.TestCase):
    def test_enctype_uses_strips_nothing_and_flags_negation(self):
        us = enctype_uses("aes256-cts +rc4 -des3, !des", "permitted_enctypes")
        self.assertEqual([u.extra["negated"] for u in us], [False, False, True, True])

    def test_decode_bitmask(self):
        ets, defaulted, other = decode_ad_enctypes(0x1C)
        self.assertEqual([e for e, _ in ets], [23, 17, 18])
        self.assertFalse(defaulted)
        self.assertEqual(decode_ad_enctypes(0)[1], True)
        self.assertEqual(decode_ad_enctypes(None)[0][0][0], 23)

    def test_parse_klist(self):
        text = (
            "Ticket cache: FILE:/tmp/krb5cc_1000\n"
            "Default principal: alice@EXAMPLE.COM\n\n"
            "Valid starting       Expires              Service principal\n"
            "11/10/2026 10:00:00  11/10/2026 20:00:00  krbtgt/EXAMPLE.COM@EXAMPLE.COM\n"
            "\tEtype (skey, tkt): aes256-cts-hmac-sha1-96, aes256-cts-hmac-sha1-96 \n"
            "11/10/2026 10:01:00  11/10/2026 20:00:00  host/srv.example.com@EXAMPLE.COM\n"
            "\tEtype (skey, tkt): DEPRECATED:arcfour-hmac, DEPRECATED:arcfour-hmac \n")
        caches = parse_klist(text)
        self.assertEqual(len(caches), 1)
        c = caches[0]
        self.assertEqual(c["principal"], "alice@EXAMPLE.COM")
        self.assertEqual([(t["service"], t["skey"], t["tkt"]) for t in c["tickets"]],
                         [("krbtgt/EXAMPLE.COM@EXAMPLE.COM", "aes256-cts-hmac-sha1-96", "aes256-cts-hmac-sha1-96"),
                          ("host/srv.example.com@EXAMPLE.COM", "arcfour-hmac", "arcfour-hmac")])


if __name__ == "__main__":
    unittest.main()
