import socket
import ssl
import threading
import unittest

from cryptoscan import x509
from cryptoscan.collectors import tls_remote as tr
from cryptoscan.collectors.base import ScanContext, Target
from cryptoscan.collectors._certassets import hostname_matches
from cryptoscan.model import AssetKind, Primitive
from cryptoscan.policy import evaluate

try:
    from fixtures_util import cert_path, read
except ImportError:                     # pragma: no cover
    from .fixtures_util import cert_path, read


def server_context(cert: str, key: str, version=ssl.TLSVersion.TLSv1_2, ciphers="ECDHE-RSA-AES128-SHA") -> ssl.SSLContext:
    c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    c.set_ciphers(ciphers + ":@SECLEVEL=0")
    c.load_cert_chain(cert_path(cert), cert_path(key))
    c.minimum_version = version
    c.maximum_version = version
    return c


class FakeServer:
    """Threaded loopback server.  `greet(conn)` runs before the TLS handshake (STARTTLS dialogue)."""

    def __init__(self, tls: ssl.SSLContext, pre=None):
        self.tls = tls
        self.pre = pre
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(32)
        self.port = self.sock.getsockname()[1]
        self.stop = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stop:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        try:
            conn.settimeout(5)
            if self.pre and not self.pre(conn):
                return
            t = self.tls.wrap_socket(conn, server_side=True)
            try:
                t.recv(1)
            except OSError:
                pass
            t.close()
        except (OSError, ssl.SSLError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def close(self):
        self.stop = True
        self.sock.close()


def _line(conn):
    buf = b""
    while not buf.endswith(b"\n"):
        c = conn.recv(1)
        if not c:
            break
        buf += c
    return buf


def smtp_pre(offer_starttls=True):
    def pre(conn):
        conn.sendall(b"220 fake.example ESMTP\r\n")
        _line(conn)                                                   # EHLO
        if offer_starttls:
            conn.sendall(b"250-fake.example\r\n250-STARTTLS\r\n250 8BITMIME\r\n")
        else:
            conn.sendall(b"250-fake.example\r\n250 8BITMIME\r\n")
            return False
        if not _line(conn).upper().startswith(b"STARTTLS"):
            return False
        conn.sendall(b"220 2.0.0 Ready to start TLS\r\n")
        return True
    return pre


def postgres_pre(conn):
    if conn.recv(8) != bytes.fromhex("0000000804d2162f"):
        return False
    conn.sendall(b"S")
    return True


def run_collector(targets, **opts):
    ctx = ScanContext(targets=targets, timeout=4.0, options=dict(opts))
    return ctx, tr.TlsRemoteCollector().collect(ctx)


class TlsRemoteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = FakeServer(server_context("server_sha256.pem", "server.key"))
        cls.ctx, cls.assets = run_collector([Target("127.0.0.1", cls.server.port, "tls")], tls_target_deadline=60)
        cls.findings = evaluate(cls.assets, "nist")
        cls.ep = [a for a in cls.assets if a.kind == AssetKind.TLS_ENDPOINT][0]

    @classmethod
    def tearDownClass(cls):
        cls.server.close()

    def test_protocols(self):
        protos = {u.algorithm for u in self.ep.uses if u.primitive == Primitive.PROTOCOL}
        self.assertEqual(protos, {"tls1.2"})                 # only what negotiated; "disabled" is never recorded
        self.assertFalse(self.ep.attributes["tls1.3"])
        self.assertTrue(all(u.negotiated for u in self.ep.uses if u.primitive == Primitive.PROTOCOL))

    def test_cipher_suite_enumeration(self):
        suites = [u for u in self.ep.uses if u.context == "tls-cipher-suite"]
        self.assertEqual([u.raw for u in suites], ["ECDHE-RSA-AES128-SHA"])
        self.assertEqual(suites[0].mode, "cbc")
        self.assertEqual(suites[0].extra["protocol"], "tls1.2")

    def test_certificate_asset(self):
        certs = [a for a in self.assets if a.kind == AssetKind.CERTIFICATE]
        self.assertEqual(len(certs), 1)
        leaf = certs[0]
        self.assertEqual(leaf.name, "localhost (leaf)")
        self.assertEqual(leaf.location, f"127.0.0.1:{self.server.port}")
        self.assertEqual(leaf.host, "127.0.0.1")
        self.assertEqual(leaf.attributes["chain_position"], 0)
        self.assertTrue(leaf.attributes["hostname_match"])          # SAN IP:127.0.0.1
        self.assertIn("serial_bits", leaf.attributes)
        ctxs = {u.context for u in leaf.uses}
        self.assertEqual(ctxs, {"public-key", "certificate-signature"})
        self.assertEqual(self.ep.attributes["chain_length"], 1)

    def test_policy(self):
        ids = {f.rule_id for f in self.findings}
        self.assertIn("TLS-CBC", ids)
        self.assertIn("PROTO-TLS12", ids)
        self.assertNotIn("PROTO-TLS10", ids)

    def test_endpoint_attributes(self):
        a = self.ep.attributes
        self.assertEqual(a["port"], self.server.port)
        self.assertIsNone(a["starttls"])
        self.assertIn("alpn", a)
        self.assertIn("compression", a)
        self.assertIn("protocols", a)
        self.assertEqual(a["protocols"], ["tls1.2"])
        self.assertTrue(a.get("group_probe") or a.get("sslv3_probe"))     # either probed or noted as unavailable
        self.assertEqual(self.ctx.warnings, [])


class TlsRemoteSha1AndTls13Tests(unittest.TestCase):
    def test_sha1_certificate_and_tls13(self):
        c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        c.set_ciphers("DEFAULT:@SECLEVEL=0")
        c.load_cert_chain(cert_path("server_sha1.pem"), cert_path("server_sha1.key"))
        server = FakeServer(c)
        self.addCleanup(server.close)
        _, assets = run_collector([Target("127.0.0.1", server.port, "https")], tls_max_handshakes=60)
        ep = [a for a in assets if a.kind == AssetKind.TLS_ENDPOINT][0]
        self.assertTrue(ep.attributes["tls1.3"])
        self.assertIn("tls1.3", ep.attributes["protocols"])
        ids = {f.rule_id for f in evaluate(assets, "nist")}
        # The fixture is self-signed with CA:TRUE (openssl req -x509 default), so the policy treats its own
        # signature as a trust-anchor signature (informational); a CA-signed SHA-1 leaf would be SIG-HASH-SHA1.
        self.assertTrue({"SIG-HASH-SHA1", "SIG-ANCHOR-WEAK-HASH"} & ids, ids)
        self.assertNotIn("PROTO-TLS12", ids)                # TLS 1.3 available: the 1.2 rule stays quiet
        self.assertTrue(any(u.context == "tls-cipher-suite" and u.extra.get("protocol") == "tls1.3" for u in ep.uses))


class StarttlsTests(unittest.TestCase):
    def test_smtp_starttls(self):
        server = FakeServer(server_context("server_sha256.pem", "server.key"), pre=smtp_pre())
        self.addCleanup(server.close)
        _, assets = run_collector([Target("127.0.0.1", server.port, "smtp")], tls_max_handshakes=30)
        ep = [a for a in assets if a.kind == AssetKind.TLS_ENDPOINT][0]
        self.assertEqual(ep.attributes["starttls"], "smtp")
        self.assertEqual(ep.attributes["protocols"], ["tls1.2"])
        self.assertTrue(any(a.kind == AssetKind.CERTIFICATE and a.name == "localhost (leaf)" for a in assets))
        self.assertEqual(ep.errors, [])

    def test_smtp_without_starttls_is_reported_not_raised(self):
        server = FakeServer(server_context("server_sha256.pem", "server.key"), pre=smtp_pre(offer_starttls=False))
        self.addCleanup(server.close)
        _, assets = run_collector([Target("127.0.0.1", server.port, "smtp")])
        ep = assets[0]
        self.assertEqual(len(assets), 1)
        self.assertIn("starttls_error", ep.attributes)
        self.assertTrue(ep.errors)
        self.assertFalse([u for u in ep.uses if u.primitive == Primitive.PROTOCOL])

    def test_postgres_sslrequest(self):
        server = FakeServer(server_context("server_sha256.pem", "server.key"), pre=postgres_pre)
        self.addCleanup(server.close)
        _, assets = run_collector([Target("127.0.0.1", server.port, "postgres")], tls_max_handshakes=30)
        ep = assets[0]
        self.assertEqual(ep.attributes["starttls"], "postgres")
        self.assertEqual(ep.attributes["protocols"], ["tls1.2"])

    def test_closed_port(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        ctx, assets = run_collector([Target("127.0.0.1", port, "tls")])
        self.assertEqual(len(assets), 1)
        self.assertTrue(assets[0].errors)


class PureFunctionTests(unittest.TestCase):
    def test_resolve_mode(self):
        self.assertEqual(tr.resolve_mode(Target("h", None, "auto")), (443, None))
        self.assertEqual(tr.resolve_mode(Target("h", 587, "auto")), (587, "smtp"))
        self.assertEqual(tr.resolve_mode(Target("h", 993, "auto")), (993, None))
        self.assertEqual(tr.resolve_mode(Target("h", 5432, "auto")), (5432, "postgres"))
        self.assertEqual(tr.resolve_mode(Target("h", None, "smtp")), (25, "smtp"))
        self.assertEqual(tr.resolve_mode(Target("h", 465, "smtp")), (465, None))     # implicit TLS port
        self.assertEqual(tr.resolve_mode(Target("h", None, "ldaps")), (636, None))
        self.assertEqual(tr.resolve_mode(Target("h", 4000, "auto")), (4000, None))

    def test_applicable(self):
        col = tr.TlsRemoteCollector()
        self.assertTrue(col.needs_network)
        self.assertFalse(col.applicable(ScanContext(targets=[Target("h", 22, "ssh")]))[0])
        self.assertFalse(col.applicable(ScanContext(targets=[]))[0])
        self.assertTrue(col.applicable(ScanContext(targets=[Target("h", None, "auto")]))[0])
        self.assertFalse(col.applicable(ScanContext(targets=[Target("h", None, "tls")], active_probes=False))[0])

    def test_ldap_starttls_bytes(self):
        from cryptoscan import asn1
        node = asn1.decode(tr.LDAP_STARTTLS_REQUEST)
        self.assertEqual(node.children[0].as_int(), 1)
        self.assertEqual(node.children[1].tag, 23)                           # ExtendedRequest
        self.assertEqual(node.children[1].children[0].value, b"1.3.6.1.4.1.1466.20037")
        ok = bytes.fromhex("300c02010178070a010004000400")                   # ExtendedResponse, success
        busy = bytes.fromhex("300c02010178070a010404000400")
        self.assertEqual(tr.ldap_starttls_result(ok), 0)
        self.assertEqual(tr.ldap_starttls_result(busy), 4)
        self.assertIsNone(tr.ldap_starttls_result(b"\x00\x01"))

    def test_group_parsing(self):
        u = tr.group_use_from("Server Temp Key: ECDH, prime256v1, 256 bits\n", False)
        self.assertEqual((u.algorithm, u.curve), ("ecdh", "p-256"))
        u = tr.group_use_from("Server Temp Key: X25519, 253 bits\n", True)
        self.assertEqual(u.curve, "curve25519")
        u = tr.group_use_from("Server Temp Key: DH, 1024 bits\n", False)       # Logjam
        self.assertEqual((u.primitive, u.algorithm, u.key_bits), (Primitive.KEY_EXCHANGE, "dh", 1024))
        u = tr.group_use_from("Negotiated TLS1.3 group: X25519MLKEM768\n", True)
        self.assertEqual(u.algorithm, "hybrid-pq")
        u = tr.group_use_from("Server Temp Key: DH, 2048 bits\n", True)
        self.assertEqual((u.algorithm, u.key_bits), ("dh", 2048))
        self.assertIsNone(tr.group_use_from("nothing here", False))

    def test_logjam_dh1024_policy(self):
        from cryptoscan.model import Asset
        a = Asset(AssetKind.TLS_ENDPOINT, "x", "h:443", "tls_remote")
        a.add(tr.group_use_from("Server Temp Key: DH, 1024 bits\n", False))
        self.assertIn("PK-DH-LT-2048", {f.rule_id for f in evaluate([a], "nist")})

    def test_sig_uses(self):
        u = tr._sig_uses("Peer signature type: RSA-PSS\nPeer signing digest: SHA256\n")[0]
        self.assertEqual((u.algorithm, u.hash_algorithm), ("rsa-pss", "sha256"))
        u = tr._sig_uses("Peer signing digest: SHA1\nPeer signature type: RSA\n")[0]
        self.assertEqual((u.algorithm, u.hash_algorithm), ("rsa", "sha1"))

    def test_hostname_matching(self):
        c = x509.load_certificates(read(cert_path("server_sha256.pem")))[0]
        self.assertTrue(hostname_matches(c, "localhost"))
        self.assertTrue(hostname_matches(c, "127.0.0.1"))
        self.assertFalse(hostname_matches(c, "example.com"))
        c.sans = ["DNS:*.example.com"]
        self.assertTrue(hostname_matches(c, "www.example.com"))
        self.assertFalse(hostname_matches(c, "a.b.example.com"))
        self.assertFalse(hostname_matches(c, "example.com"))


if __name__ == "__main__":
    unittest.main()
