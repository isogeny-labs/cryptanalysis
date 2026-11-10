"""OpenPGP packet parser and collector (no gpg needed: packets are built in code)."""

import base64
import hashlib
import os
import struct
import tempfile
import unittest

from cryptoscan.collectors import pgp
from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.pgp import PgpCollector, crc24, dearmor, parse_colons, parse_keyring
from cryptoscan.policy import evaluate


def mpi(value_bytes: bytes) -> bytes:
    bits = (len(value_bytes) - 1) * 8 + value_bytes[0].bit_length()
    return struct.pack(">H", bits) + value_bytes


def rsa_pub_body(bits=1024, created=1500000000):
    n = b"\xc5" + bytes((i * 7 + 3) & 0xFF for i in range(bits // 8 - 1))
    n = n[:-1] + bytes([n[-1] | 1])
    return b"\x04" + struct.pack(">I", created) + b"\x01" + mpi(n) + mpi(b"\x01\x00\x01")


def new_packet(tag: int, body: bytes) -> bytes:
    n = len(body)
    if n < 192:
        hdr = bytes([n])
    elif n < 8384:
        n2 = n - 192
        hdr = bytes([(n2 >> 8) + 192, n2 & 0xFF])
    else:
        hdr = b"\xff" + struct.pack(">I", n)
    return bytes([0xC0 | tag]) + hdr + body


def old_packet(tag: int, body: bytes) -> bytes:
    n = len(body)
    if n < 256:
        return bytes([0x80 | (tag << 2) | 0]) + bytes([n]) + body
    return bytes([0x80 | (tag << 2) | 1]) + struct.pack(">H", n) + body


def subpacket(t: int, data: bytes) -> bytes:
    return bytes([len(data) + 1, t]) + data


def sig_body(hashalgo: int, sigtype=0x13, issuer_keyid: bytes = None, key_expires=None, flags=0x03, created=1500000100):
    hashed = subpacket(2, struct.pack(">I", created)) + subpacket(27, bytes([flags]))
    if key_expires is not None:
        hashed += subpacket(9, struct.pack(">I", key_expires))
    unhashed = subpacket(16, issuer_keyid) if issuer_keyid else b""
    return (b"\x04" + bytes([sigtype, 1, hashalgo]) + struct.pack(">H", len(hashed)) + hashed +
            struct.pack(">H", len(unhashed)) + unhashed + b"\xab\xcd" + mpi(b"\x80" * 128))


def fingerprint_v4(body: bytes) -> str:
    return hashlib.sha1(b"\x99" + struct.pack(">H", len(body)) + body).hexdigest().upper()


def armor(data: bytes, kind="PUBLIC KEY BLOCK") -> bytes:
    b64 = base64.b64encode(data).decode()
    lines = [b64[i:i + 64] for i in range(0, len(b64), 64)]
    crc = base64.b64encode(struct.pack(">I", crc24(data))[1:]).decode()
    return (f"-----BEGIN PGP {kind}-----\nVersion: test\nComment: fixture\n\n" + "\n".join(lines) + f"\n={crc}\n-----END PGP {kind}-----\n").encode()


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


class PgpParserTest(unittest.TestCase):
    def setUp(self):
        self.body = rsa_pub_body(1024)
        self.fp = fingerprint_v4(self.body)
        self.keyid = bytes.fromhex(self.fp[-16:])
        self.stream = (new_packet(6, self.body) + new_packet(13, b"Test Key <test@example.org>") +
                       new_packet(2, sig_body(2, issuer_keyid=self.keyid, key_expires=86400 * 30)))

    def collect_stream(self, data, name="test.gpg"):
        with tempfile.TemporaryDirectory() as root:
            d = os.path.join(root, "usr/share/keyrings")
            os.makedirs(d)
            with open(os.path.join(d, name), "wb") as fh:
                fh.write(data)
            return PgpCollector().collect(ScanContext(root=root, hostname="h"))

    def test_rsa1024_sha1_selfsig_rules(self):
        assets = self.collect_stream(self.stream)
        self.assertEqual(len(assets), 1)
        a = assets[0]
        self.assertEqual(a.kind.value, "pgp_key")
        self.assertEqual(a.attributes["fingerprint"], self.fp)
        self.assertEqual(a.attributes["user_ids"], ["Test Key <test@example.org>"])
        self.assertEqual(a.location, "/usr/share/keyrings/test.gpg")
        r = ids([a])
        self.assertTrue({"PK-RSA-LT-2048", "HASH-SHA1"} <= r)
        prim = [u for u in a.uses if u.context == "pgp-primary"][0]
        self.assertEqual((prim.algorithm, prim.key_bits), ("rsa", 1024))
        self.assertEqual(prim.extra["capabilities"], "CS")
        self.assertEqual(a.attributes["expires"], "2017-08-13")       # created 2017-07-14 + 30 days
        self.assertTrue(a.attributes["expired"])
        h = [u for u in a.uses if u.context == "pgp-selfsig"]
        self.assertEqual([(u.primitive.value, u.algorithm) for u in h], [("hash", "sha1")])

    def test_armored_variant_and_old_packet_headers(self):
        old = (old_packet(6, self.body) + old_packet(13, b"Old Style") + old_packet(2, sig_body(2, issuer_keyid=self.keyid)))
        for data in (armor(self.stream), armor(old)):
            a = self.collect_stream(data, "x.asc")[0]
            self.assertTrue({"PK-RSA-LT-2048", "HASH-SHA1"} <= ids([a]))
            self.assertEqual(a.attributes["fingerprint"], self.fp)
        self.assertEqual(dearmor(armor(self.stream)), self.stream)

    def test_third_party_signature_ignored(self):
        stranger = bytes.fromhex("0102030405060708")
        stream = (new_packet(6, self.body) + new_packet(13, b"uid") +
                  new_packet(2, sig_body(8, issuer_keyid=self.keyid)) +
                  new_packet(2, sig_body(2, issuer_keyid=stranger)))      # certification by someone else (SHA-1)
        a = self.collect_stream(stream)[0]
        self.assertNotIn("HASH-SHA1", ids([a]))
        self.assertEqual([u.algorithm for u in a.uses if u.context == "pgp-selfsig"], ["sha256"])

    def test_md5_selfsig_is_broken(self):
        a = self.collect_stream(new_packet(6, self.body) + new_packet(13, b"u") + new_packet(2, sig_body(1)))[0]
        self.assertIn("HASH-BROKEN", ids([a]))

    def test_subkeys_ecc_and_revocation(self):
        # v4 EdDSA(legacy) primary, ECDH cv25519 subkey with binding, key revocation
        ed_oid = bytes.fromhex("2b06010401da470f01")
        cv_oid = bytes.fromhex("2b060104019755010501")
        point = b"\x40" + b"\x11" * 32
        prim = b"\x04" + struct.pack(">I", 1600000000) + b"\x16" + bytes([len(ed_oid)]) + ed_oid + mpi(point)
        sub = (b"\x04" + struct.pack(">I", 1600000000) + b"\x12" + bytes([len(cv_oid)]) + cv_oid + mpi(point) +
               b"\x03\x01\x08\x07")
        keyid = bytes.fromhex(fingerprint_v4(prim)[-16:])
        stream = (new_packet(6, prim) + new_packet(13, b"ecc") + new_packet(2, sig_body(8, issuer_keyid=keyid)) +
                  new_packet(14, sub) + new_packet(2, sig_body(8, sigtype=0x18, issuer_keyid=keyid, flags=0x0C)) +
                  new_packet(2, sig_body(8, sigtype=0x20, issuer_keyid=keyid)))
        a = self.collect_stream(stream)[0]
        p = [u for u in a.uses if u.context == "pgp-primary"][0]
        s = [u for u in a.uses if u.context == "pgp-subkey"][0]
        self.assertEqual((p.algorithm, p.curve, p.key_bits), ("ed25519", "curve25519", 256))
        self.assertEqual((s.algorithm, s.curve, s.key_bits), ("ecdh", "curve25519", 256))
        self.assertEqual(s.extra["capabilities"], "E")
        self.assertTrue(p.extra["revoked"])
        self.assertFalse(s.extra["revoked"])
        self.assertTrue(a.attributes["revoked"])
        self.assertEqual(ids([a], "legacy") - {"PQC-TRANSITION"}, set())

    def test_nist_and_brainpool_curves_dsa_elgamal(self):
        oid = bytes.fromhex("2a8648ce3d030107")
        point = b"\x04" + b"\x22" * 64
        ecdsa = b"\x04" + struct.pack(">I", 1) + b"\x13" + bytes([len(oid)]) + oid + mpi(point)
        bp = bytes.fromhex("2b2403030208010107")
        ecdh_bp = b"\x04" + struct.pack(">I", 1) + b"\x12" + bytes([len(bp)]) + bp + mpi(point) + b"\x03\x01\x08\x07"
        p1024 = b"\xff" * 128
        dsa = b"\x04" + struct.pack(">I", 1) + b"\x11" + mpi(p1024) + mpi(b"\xaa" * 20) + mpi(b"\x02") + mpi(b"\x55" * 128)
        elg = b"\x04" + struct.pack(">I", 1) + b"\x10" + mpi(p1024) + mpi(b"\x05") + mpi(b"\x66" * 128)
        keys = parse_keyring(new_packet(6, ecdsa) + new_packet(6, ecdh_bp) + new_packet(6, dsa) + new_packet(6, elg))
        got = [(k.primary.algorithm, k.primary.key_bits, k.primary.curve) for k in keys]
        self.assertEqual(got, [("ecdsa", 256, "p-256"), ("ecdh", 256, "brainpoolp256r1"), ("dsa", 1024, None),
                               ("elgamal", 1024, None)])

    def test_v4_dsa1024_rule(self):
        p1024 = b"\xff" * 128
        dsa = b"\x04" + struct.pack(">I", 1) + b"\x11" + mpi(p1024) + mpi(b"\xaa" * 20) + mpi(b"\x02") + mpi(b"\x55" * 128)
        a = self.collect_stream(new_packet(6, dsa))[0]
        self.assertIn("PK-DSA", ids([a]))

    def test_v6_ed25519_and_x25519(self):
        raw = b"\x07" * 32
        def v6(algo):
            return b"\x06" + struct.pack(">I", 1700000000) + bytes([algo]) + struct.pack(">I", 32) + raw
        keys = parse_keyring(new_packet(6, v6(27)) + new_packet(14, v6(25)))
        k = keys[0]
        self.assertEqual((k.primary.version, k.primary.algorithm, k.primary.curve), (6, "ed25519", "curve25519"))
        self.assertEqual((k.subkeys[0].algorithm, k.subkeys[0].curve), ("ecdh", "curve25519"))
        self.assertEqual(len(k.primary.fingerprint), 64)
        expected = hashlib.sha256(b"\x9b" + struct.pack(">I", len(v6(27))) + v6(27)).hexdigest().upper()
        self.assertEqual(k.primary.fingerprint, expected)

    def test_v3_rsa_key(self):
        n = b"\x80" + b"\x11" * 63
        body = b"\x03" + struct.pack(">I", 1000000) + struct.pack(">H", 0) + b"\x01" + mpi(n) + mpi(b"\x03")
        keys = parse_keyring(old_packet(6, body))
        self.assertEqual((keys[0].primary.algorithm, keys[0].primary.key_bits, keys[0].primary.version), ("rsa", 512, 3))
        self.assertEqual(keys[0].primary.keyid, n[-8:].hex().upper())

    def test_garbage_and_truncation_do_not_raise(self):
        self.assertEqual(parse_keyring(b""), [])
        self.assertEqual(parse_keyring(b"\x00\x01\x02"), [])
        self.assertEqual(len(parse_keyring(new_packet(6, self.body)[:-5])), 0)

    def test_multi_key_keyring_and_secret_key_packet(self):
        sec = self.body + b"\x00" + b"S" * 40        # tag 5: public part followed by secret data
        keys = parse_keyring(new_packet(6, self.body) + new_packet(5, sec))
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0].primary.fingerprint, keys[1].primary.fingerprint)
        self.assertTrue(keys[1].primary.secret)
        a = self.collect_stream(new_packet(5, sec))[0]
        self.assertNotIn("SSSS", repr([vars(u) for u in a.uses]) + repr(a.attributes))

    def test_kbx_keyblocks(self):
        blob_key = new_packet(6, self.body) + new_packet(13, b"kbx")
        hdr = struct.pack(">IBB", 32, 1, 1) + b"\x00\x00" + b"KBXf" + b"\x00" * 20
        off = 20
        blob = struct.pack(">IBBH", off + len(blob_key), 2, 1, 0) + struct.pack(">II", off, len(blob_key)) + b"\x00" * 4 + blob_key
        keys = pgp.parse_key_file(hdr + blob)
        self.assertEqual(len(keys), 1)
        self.assertEqual(keys[0].primary.fingerprint, self.fp)


class ColonTest(unittest.TestCase):
    SAMPLE = (
        "tru::1:1700000000:0:3:1:5\n"
        "pub:u:1024:1:AAAAAAAAAAAAAAAA:1500000000:1600000000::u:::scESC::::::23::0:\n"
        "fpr:::::::::0123456789ABCDEF0123456789ABCDEF01234567:\n"
        "uid:u::::1500000000::DEADBEEF::Alice \\x3a Test <a@example.org>::::::::::0:\n"
        "sub:e:256:18:BBBBBBBBBBBBBBBB:1500000000::::::e:::::nistp256:::\n"
        "fpr:::::::::89ABCDEF0123456789ABCDEF0123456789ABCDEF:\n"
        "pub:r:256:22:CCCCCCCCCCCCCCCC:1500000000::::::scESC:::::ed25519:::\n"
        "fpr:::::::::FEDCBA9876543210FEDCBA9876543210FEDCBA98:\n"
        "sub:u:255:18:DDDDDDDDDDDDDDDD:1500000000::::::e:::::cv25519::\n"
        "fpr:::::::::1111111111111111111111111111111111111111:\n")

    def test_parse(self):
        keys = parse_colons(self.SAMPLE)
        self.assertEqual(len(keys), 2)
        k0, k1 = keys
        self.assertEqual((k0.primary.algorithm, k0.primary.key_bits, k0.primary.expires, k0.primary.caps), ("rsa", 1024, 1600000000, "SC"))
        self.assertTrue(k0.primary.fingerprint.startswith("0123456789"))
        self.assertEqual(k0.uids, ["Alice : Test <a@example.org>"])
        self.assertEqual((k0.subkeys[0].algorithm, k0.subkeys[0].curve, k0.subkeys[0].key_bits), ("ecdh", "p-256", 256))
        self.assertTrue(k0.subkeys[0].caps == "E")
        self.assertEqual((k1.primary.algorithm, k1.primary.curve, k1.primary.revoked), ("ed25519", "curve25519", True))
        self.assertEqual((k1.subkeys[0].algorithm, k1.subkeys[0].curve, k1.subkeys[0].key_bits), ("ecdh", "curve25519", 256))

    def test_asset_from_colons(self):
        keys = parse_colons(self.SAMPLE)
        with tempfile.TemporaryDirectory() as root:
            a = PgpCollector()._key_asset(ScanContext(root=root, hostname="h"), keys[0], "/home/u/.gnupg", "gnupg-home", {})
        self.assertIn("PK-RSA-LT-2048", ids([a]))
        self.assertEqual(a.attributes["expired"], True)


if __name__ == "__main__":
    unittest.main()
