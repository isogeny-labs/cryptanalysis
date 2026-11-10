"""Keytab parser and kerberos collector keytab handling (offline, hand-built keytabs)."""

import os
import struct
import tempfile
import unittest

from cryptoscan import keytab
from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.kerberos import KerberosCollector
from cryptoscan.policy import evaluate

KEY_SENTINEL = b"\xde\xad\xbe\xef\xca\xfe\xba\xbe" * 4


def _cs(s: str, endian: str = ">") -> bytes:
    b = s.encode()
    return struct.pack(endian + "H", len(b)) + b


def build_entry(princ, realm, etype, kvno, ts=1700000000, name_type=1, key=KEY_SENTINEL, vno32=True,
                v1=False, endian=">"):
    comps = princ.split("/")
    body = struct.pack(endian + "H", len(comps) + (1 if v1 else 0)) + _cs(realm, endian)
    for c in comps:
        body += _cs(c, endian)
    if not v1:
        body += struct.pack(endian + "I", name_type)
    body += struct.pack(endian + "I", ts) + struct.pack("B", kvno & 0xFF)
    body += struct.pack(endian + "HH", etype, len(key)) + key
    if vno32:
        body += struct.pack(endian + "I", kvno)
    return struct.pack(endian + "i", len(body)) + body


def build_keytab(extra_deleted=True):
    data = struct.pack(">H", 0x0502)
    data += build_entry("host/server.example.com", "EXAMPLE.COM", 23, 3)       # rc4-hmac
    if extra_deleted:
        dead = build_entry("host/dead.example.com", "EXAMPLE.COM", 1, 1)
        data += struct.pack(">i", -(len(dead) - 4)) + dead[4:]                   # deleted slot
    data += build_entry("host/server.example.com", "EXAMPLE.COM", 18, 3)       # aes256
    data += build_entry("nfs/server.example.com", "EXAMPLE.COM", 1, 2, vno32=False)   # des-cbc-crc
    return data


class KeytabParserTest(unittest.TestCase):
    def test_v2_entries_and_deleted_slot(self):
        res = keytab.parse_keytab_ex(build_keytab())
        self.assertEqual(res.version, 0x0502)
        self.assertEqual(res.deleted_slots, 1)
        self.assertFalse(res.truncated)
        got = [(e.principal, e.enctype, e.kvno, e.timestamp, e.key_length) for e in res.entries]
        self.assertEqual(got, [("host/server.example.com@EXAMPLE.COM", 23, 3, 1700000000, 32),
                               ("host/server.example.com@EXAMPLE.COM", 18, 3, 1700000000, 32),
                               ("nfs/server.example.com@EXAMPLE.COM", 1, 2, 1700000000, 32)])

    def test_entries_have_no_key_bytes(self):
        for e in keytab.parse_keytab(build_keytab()):
            self.assertNotIn(KEY_SENTINEL.hex(), repr(e))
            self.assertFalse(any(isinstance(v, (bytes, bytearray)) for v in vars(e).values()))

    def test_v1_native_endian(self):
        import sys
        endian = "<" if sys.byteorder == "little" else ">"
        data = struct.pack("BB", 5, 1) + build_entry("host/a.example.com", "EXAMPLE.COM", 17, 7, v1=True, endian=endian)
        res = keytab.parse_keytab_ex(data)
        self.assertEqual(res.version, 0x0501)
        self.assertEqual([(e.principal, e.enctype, e.kvno, e.name_type) for e in res.entries],
                         [("host/a.example.com@EXAMPLE.COM", 17, 7, None)])

    def test_bad_magic_and_truncation(self):
        with self.assertRaises(keytab.KeytabError):
            keytab.parse_keytab(b"\x00\x00\x00")
        res = keytab.parse_keytab_ex(build_keytab()[:-10])
        self.assertTrue(res.truncated)
        self.assertEqual(len(res.entries), 2)


class KeytabCollectorTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        os.makedirs(os.path.join(self.root, "etc"))
        self.kt = os.path.join(self.root, "etc", "krb5.keytab")
        with open(self.kt, "wb") as fh:
            fh.write(build_keytab())
        os.chmod(self.kt, 0o600)

    def tearDown(self):
        self.tmp.cleanup()

    def test_asset_and_rules(self):
        ctx = ScanContext(root=self.root, hostname="h")
        assets = [a for a in KerberosCollector().collect(ctx) if a.kind.value == "kerberos_keytab"]
        self.assertEqual(len(assets), 1)
        a = assets[0]
        self.assertEqual(a.location, "/etc/krb5.keytab")
        self.assertEqual(a.attributes["entry_count"], 3)
        self.assertEqual(a.attributes["principals"], ["host/server.example.com@EXAMPLE.COM", "nfs/server.example.com@EXAMPLE.COM"])
        self.assertEqual(a.attributes["kvnos"], [2, 3])
        self.assertEqual(a.attributes["mode"], 0o600)
        ids = {f.rule_id for f in evaluate(assets, "nist")}
        self.assertEqual(ids, {"KRB-RC4", "KRB-DES"})
        self.assertEqual({u.context for u in a.uses}, {"keytab-key"})

    def test_no_key_material_in_serialised_asset(self):
        import json
        from cryptoscan.model import _to_jsonable
        import dataclasses
        ctx = ScanContext(root=self.root, hostname="h")
        a = [x for x in KerberosCollector().collect(ctx) if x.kind.value == "kerberos_keytab"][0]
        blob = json.dumps(_to_jsonable(dataclasses.asdict(a)))
        self.assertNotIn(KEY_SENTINEL.hex(), blob)
        self.assertNotIn("deadbeef", blob.lower())

    def test_not_a_keytab_records_error(self):
        os.makedirs(os.path.join(self.root, "etc", "security", "keytabs"))
        with open(os.path.join(self.root, "etc", "security", "keytabs", "junk"), "wb") as fh:
            fh.write(b"hello world")
        ctx = ScanContext(root=self.root, hostname="h")
        junk = [a for a in KerberosCollector().collect(ctx) if a.location.endswith("keytabs/junk")]
        self.assertEqual(len(junk), 1)
        self.assertTrue(junk[0].errors)


if __name__ == "__main__":
    unittest.main()
