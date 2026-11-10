"""Tests for sshwire (KEXINIT/banner parsing, probe against fake servers) and ssh_remote."""
import socket
import socketserver
import struct
import threading
import unittest

from cryptoscan import sshwire
from cryptoscan.collectors.base import ScanContext, Target
from cryptoscan.collectors.ssh_remote import SSHRemoteCollector
from cryptoscan.model import AssetKind, Primitive
from cryptoscan.policy import evaluate


def namelist(items):
    raw = ",".join(items).encode()
    return struct.pack(">I", len(raw)) + raw


def kexinit_payload(kex, hostkey, ciphers, macs, comp=("none",), langs=(), follows=False):
    p = bytes([20]) + bytes(range(16))
    for lst in (kex, hostkey, ciphers, ciphers, macs, macs, comp, comp, langs, langs):
        p += namelist(lst)
    return p + (b"\x01" if follows else b"\x00") + b"\x00\x00\x00\x00"


WEAK = dict(
    kex=["diffie-hellman-group1-sha1", "diffie-hellman-group14-sha1", "curve25519-sha256", "ext-info-s",
         "kex-strict-s-v00@openssh.com"],
    hostkey=["ssh-rsa", "ssh-dss", "ssh-ed25519"],
    ciphers=["3des-cbc", "aes128-cbc", "aes128-ctr"],
    macs=["hmac-md5", "hmac-sha1", "hmac-sha2-256"],
)


class FakeHandler(socketserver.BaseRequestHandler):
    def handle(self):
        srv = self.server
        s = self.request
        s.settimeout(5)
        try:
            if srv.mode == "wait_for_client":
                s.recv(256)               # banner only after ours
            if srv.mode == "http":
                s.recv(256)
                s.sendall(b"HTTP/1.1 400 Bad Request\r\nContent-Length: 0\r\n\r\n")
                return
            s.sendall(srv.preamble + srv.banner.encode() + b"\r\n")
            if srv.mode != "wait_for_client":
                s.recv(256)               # our banner (may include our KEXINIT)
            pkt = sshwire.build_packet(kexinit_payload(**WEAK))
            s.sendall(pkt)
            s.settimeout(0.5)
            try:
                s.recv(4096)
            except OSError:
                pass
        except OSError:
            pass


class FakeServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, banner="SSH-2.0-OpenSSH_7.4", mode="normal", preamble=b"", family=socket.AF_INET, addr="127.0.0.1"):
        self.address_family = family
        self.banner, self.mode, self.preamble = banner, mode, preamble
        super().__init__((addr, 0), FakeHandler)
        self.thread = threading.Thread(target=self.serve_forever, daemon=True)
        self.thread.start()

    @property
    def port(self):
        return self.server_address[1]

    def stop(self):
        self.shutdown()
        self.server_close()


class WireParsingTests(unittest.TestCase):
    def test_banner(self):
        self.assertEqual(sshwire.parse_banner("SSH-2.0-OpenSSH_9.6p1 Ubuntu-3ubuntu13\r\n"),
                         ("2.0", "OpenSSH_9.6p1", "Ubuntu-3ubuntu13"))
        self.assertEqual(sshwire.parse_banner("SSH-1.99-Cisco-1.25"), ("1.99", "Cisco-1.25", ""))
        for bad in ("HTTP/1.1 200", "SSH-", "SSH-2.0"):
            with self.assertRaises(ValueError):
                sshwire.parse_banner(bad)

    def test_parse_kexinit_hand_built(self):
        payload = bytes([20]) + b"\xaa" * 16
        lists = ["curve25519-sha256,ext-info-s", "ssh-ed25519", "aes128-ctr", "aes256-ctr",
                 "hmac-sha2-256", "hmac-sha1", "none", "zlib@openssh.com", "", "en"]
        for l in lists:
            b = l.encode()
            payload += struct.pack(">I", len(b)) + b
        payload += b"\x01" + b"\x00" * 4
        pkt_len = 1 + len(payload) + 6
        raw = struct.pack(">IB", pkt_len, 6) + payload + b"\x00" * 6
        got, used = sshwire.parse_packet(raw + b"trailing")
        self.assertEqual(used, len(raw))
        k = sshwire.parse_kexinit(got)
        self.assertEqual(k["kex"], ["curve25519-sha256", "ext-info-s"])
        self.assertEqual(k["ciphers_s2c"], ["aes256-ctr"])
        self.assertEqual(k["macs_s2c"], ["hmac-sha1"])
        self.assertEqual(k["compression_s2c"], ["zlib@openssh.com"])
        self.assertEqual(k["languages_c2s"], [])
        self.assertEqual(k["languages_s2c"], ["en"])
        self.assertTrue(k["first_kex_follows"])
        self.assertEqual(k["cookie"], b"\xaa" * 16)

    def test_incomplete_and_bad_packets(self):
        self.assertIsNone(sshwire.parse_packet(b"\x00\x00"))
        pkt = sshwire.build_packet(sshwire.build_kexinit())
        self.assertIsNone(sshwire.parse_packet(pkt[:-1]))
        with self.assertRaises(sshwire.SSHProbeError):
            sshwire.parse_packet(b"HTTP/1.1 200 OK\r\n")
        with self.assertRaises(sshwire.SSHProbeError):
            sshwire.parse_kexinit(bytes([20]) + b"\x00" * 16 + b"\x00\x00\x00\x09ab")

    def test_build_kexinit_roundtrip(self):
        pkt = sshwire.build_packet(sshwire.build_kexinit(b"c" * 16))
        self.assertEqual(len(pkt) % 8, 0)
        payload, used = sshwire.parse_packet(pkt)
        k = sshwire.parse_kexinit(payload)
        self.assertIn("diffie-hellman-group1-sha1", k["kex"])
        self.assertIn("3des-cbc", k["ciphers_c2s"])
        self.assertEqual(k["cookie"], b"c" * 16)


class ProbeTests(unittest.TestCase):
    def test_probe_weak_server(self):
        srv = FakeServer()
        self.addCleanup(srv.stop)
        r = sshwire.probe("127.0.0.1", srv.port, 3)
        self.assertTrue(r.ok, r.error)
        self.assertEqual((r.protocol_version, r.software), ("2.0", "OpenSSH_7.4"))
        self.assertEqual(r.hostkey, WEAK["hostkey"])
        self.assertEqual(r.ciphers, WEAK["ciphers"])
        self.assertTrue(r.kex_strict and r.ext_info)

    def test_pre_banner_lines(self):
        srv = FakeServer(preamble=b"Welcome to the machine\r\nAuthorized use only\r\n")
        self.addCleanup(srv.stop)
        r = sshwire.probe("127.0.0.1", srv.port, 3)
        self.assertTrue(r.ok, r.error)
        self.assertEqual(r.pre_banner, ["Welcome to the machine", "Authorized use only"])

    def test_banner_only_after_ours(self):
        srv = FakeServer(mode="wait_for_client")
        self.addCleanup(srv.stop)
        r = sshwire.probe("127.0.0.1", srv.port, 4)
        self.assertTrue(r.ok, r.error)

    def test_non_ssh_service(self):
        srv = FakeServer(mode="http")
        self.addCleanup(srv.stop)
        r = sshwire.probe("127.0.0.1", srv.port, 2)
        self.assertFalse(r.ok)
        self.assertIn("not an SSH", r.error or "")

    def test_connection_refused(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        r = sshwire.probe("127.0.0.1", port, 2)
        self.assertFalse(r.ok)
        self.assertEqual(r.error, "connection refused")

    def test_ipv6_literal(self):
        try:
            srv = FakeServer(family=socket.AF_INET6, addr="::1")
        except OSError:
            self.skipTest("IPv6 loopback unavailable")
        self.addCleanup(srv.stop)
        r = sshwire.probe("[::1]", srv.port, 3)
        self.assertTrue(r.ok, r.error)

    def test_ssh1_banner(self):
        srv = FakeServer(banner="SSH-1.99-Legacy_1.0")
        self.addCleanup(srv.stop)
        r = sshwire.probe("127.0.0.1", srv.port, 3)
        self.assertEqual(r.protocol_version, "1.99")


class RemoteCollectorTests(unittest.TestCase):
    def test_applicable(self):
        c = SSHRemoteCollector()
        self.assertFalse(c.applicable(ScanContext(targets=[Target("h", 443, "tls")]))[0])
        self.assertFalse(c.applicable(ScanContext(targets=[Target("h", 2222, "auto")]))[0])
        self.assertTrue(c.applicable(ScanContext(targets=[Target("h", None, "auto")]))[0])
        self.assertTrue(c.applicable(ScanContext(targets=[Target("h", 2222, "ssh")]))[0])
        self.assertFalse(c.applicable(ScanContext(targets=[Target("h", 22, "ssh")], active_probes=False))[0])

    def test_collect_against_fake_server(self):
        s1, s2 = FakeServer(), FakeServer(banner="SSH-1.99-Old")
        self.addCleanup(s1.stop)
        self.addCleanup(s2.stop)
        ctx = ScanContext(targets=[Target("127.0.0.1", s1.port, "ssh"), Target("127.0.0.1", s2.port, "ssh"),
                                   Target("127.0.0.1", 1, "tls")], timeout=3, options={"keyscan": False, "workers": 4})
        assets = SSHRemoteCollector().collect(ctx)
        self.assertEqual(len(assets), 2)
        a = assets[0]
        self.assertEqual(a.kind, AssetKind.SSH_REMOTE)
        self.assertEqual(a.location, f"127.0.0.1:{s1.port}")
        self.assertEqual(a.attributes["software"], "OpenSSH_7.4")
        self.assertIs(a.attributes["kex_strict"], True)
        self.assertIs(a.attributes["ext_info"], True)
        raws = {(u.context, u.raw) for u in a.uses}
        self.assertIn(("kex", "diffie-hellman-group1-sha1"), raws)
        self.assertNotIn(("kex", "ext-info-s"), raws)
        self.assertIn(("hostkey", "ssh-dss"), raws)
        self.assertTrue(all(u.negotiated is False for u in a.uses if u.context in ("kex", "hostkey", "cipher", "mac")))
        self.assertEqual({u.extra["direction"] for u in a.uses if u.context == "cipher"}, {"both"})
        self.assertTrue(any(u.primitive == Primitive.CONFIG and u.algorithm == "ssh-version" and u.raw == "SSH-2.0-OpenSSH_7.4" for u in a.uses))
        ids = {f.rule_id for f in evaluate(assets, "nist")}
        for rid in ("PK-DH-LT-2048", "CIPHER-3DES", "MAC-MD5", "KX-SHA1", "SSH-RSA-SHA1", "SSH-CBC"):
            self.assertIn(rid, ids, rid)
        self.assertNotIn("SSH-TERRAPIN", {f.rule_id for f in evaluate([a], "nist")})
        old = assets[1]
        self.assertTrue(any(u.primitive == Primitive.PROTOCOL and u.algorithm == "ssh1.99" for u in old.uses))
        self.assertIn("SSH-PROTOCOL-1", ids)

    def test_unreachable_target_records_error(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        ctx = ScanContext(targets=[Target("127.0.0.1", port, "ssh")], timeout=2, options={"keyscan": False})
        (a,) = SSHRemoteCollector().collect(ctx)
        self.assertTrue(a.errors and "refused" in a.errors[0])
        self.assertEqual(a.uses, [])


if __name__ == "__main__":
    unittest.main()
