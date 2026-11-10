"""SNMP BER codec round trips and the netdev collector's opt-in SNMP probe against a local fake agent."""

import dataclasses
import json
import socket
import threading
import unittest

from cryptoscan import snmp
from cryptoscan.collectors.base import ScanContext, Target
from cryptoscan.collectors.netdev import NetdevCollector
from cryptoscan.policy import evaluate

COMMUNITY = "s3cr3t-c0mmunity"


class FakeAgent:
    """UDP SNMPv2c agent on 127.0.0.1 answering GET sysDescr for one community."""

    def __init__(self, communities=(COMMUNITY,), versions=(snmp.VERSION_V2C,)):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.communities = communities
        self.versions = versions
        self.received = []
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self.thread.join(2)
        self.sock.close()

    def _run(self):
        while not self._stop.is_set():
            try:
                data, addr = self.sock.recvfrom(65535)
            except OSError:
                continue
            self.received.append(data)
            try:
                resp = snmp.build_response(data, "FakeOS Software, Version 1.2.3 " + "x" * 300,
                                           version_ok=self.versions, communities=self.communities)
            except snmp.SnmpError:
                resp = None
            if resp:
                self.sock.sendto(resp, addr)


class BerTest(unittest.TestCase):
    def test_integer_and_oid_round_trip(self):
        for v in (0, 1, 127, 128, 255, 256, 65535, 2 ** 31 - 1, -1, -128, -129):
            tlv, _ = snmp.decode_tlv(snmp.enc_int(v))
            self.assertEqual(snmp.decode_int(tlv.value), v)
        for oid in (snmp.SYS_DESCR, "1.3.6.1.4.1.9.9.999999.1", "2.999.3"):
            tlv, _ = snmp.decode_tlv(snmp.enc_oid(oid))
            self.assertEqual(snmp.decode_oid(tlv.value), oid)
        long = snmp.enc_octets(b"a" * 300)
        tlv, end = snmp.decode_tlv(long)
        self.assertEqual(len(tlv.value), 300)
        self.assertEqual(end, len(long))

    def test_get_request_and_response(self):
        req = snmp.build_get_request(snmp.VERSION_V2C, "public", request_id=4242)
        m = snmp.parse_message(req)
        self.assertEqual((m.version, m.community, m.pdu_type, m.request_id), (1, b"public", snmp.PDU_GET, 4242))
        self.assertEqual(m.varbinds[0][0], snmp.SYS_DESCR)
        resp = snmp.build_response(req, "Router OS 15.2")
        r = snmp.parse_message(resp)
        self.assertEqual(r.pdu_type, snmp.PDU_RESPONSE)
        self.assertEqual(r.request_id, 4242)
        self.assertEqual(r.value_text(snmp.SYS_DESCR), "Router OS 15.2")
        self.assertIsNone(snmp.build_response(snmp.build_get_request(0, "public"), "x"))      # v1 not accepted
        self.assertIsNone(snmp.build_response(req, "x", communities=("other",)))

    def test_v3_discovery(self):
        m = snmp.parse_message(snmp.build_v3_discovery(msg_id=7))
        self.assertEqual(m.version, 3)
        self.assertEqual(m.msg_id, 7)
        self.assertEqual(m.flags, 4)
        self.assertEqual(m.engine_id, b"")

    def test_malformed(self):
        for bad in (b"", b"\x30", b"\x30\x05\x02\x01", b"\x04\x02ab", b"\x30\x03\x02\x01\x07"):
            with self.assertRaises(snmp.SnmpError):
                snmp.parse_message(bad)


class SnmpProbeTest(unittest.TestCase):
    def _ctx(self, port, snmp_probe):
        return ScanContext(targets=[Target("127.0.0.1", port, "snmp")], snmp_probe=snmp_probe, active_probes=True,
                           options={"snmp_communities": ["public", COMMUNITY], "snmp_timeout": 0.5})

    def test_probe_records_snmpv2c_without_community(self):
        with FakeAgent() as agent:
            assets = NetdevCollector().collect(self._ctx(agent.port, True))
        self.assertEqual(len(assets), 1)
        a = assets[0]
        v2 = [u for u in a.uses if u.algorithm == "snmpv2c"]
        self.assertEqual(len(v2), 1)
        self.assertTrue(v2[0].negotiated)
        self.assertNotIn("snmpv1", {u.algorithm for u in a.uses})
        self.assertIn("PROTO-SNMPV2C", {f.rule_id for f in evaluate(assets, "nist")})
        self.assertTrue(a.attributes["sysDescr"].startswith("FakeOS Software"))
        self.assertLessEqual(len(a.attributes["sysDescr"]), 200)
        self.assertFalse(a.attributes["snmpv3"])
        d = json.dumps(dataclasses.asdict(a), default=str)
        self.assertNotIn(COMMUNITY, d)
        self.assertNotIn("public", d)
        # the agent saw v1 and v2c GETs per community (until one answered) and one v3 discovery
        versions = [snmp.parse_message(p).version for p in agent.received]
        self.assertIn(snmp.VERSION_V1, versions)
        self.assertIn(snmp.VERSION_V2C, versions)
        self.assertIn(snmp.VERSION_V3, versions)

    def test_no_packets_without_consent(self):
        with FakeAgent() as agent:
            assets = NetdevCollector().collect(self._ctx(agent.port, False))
        self.assertEqual(agent.received, [])
        self.assertEqual(assets, [])

    def test_no_probe_when_active_probes_off(self):
        with FakeAgent() as agent:
            ctx = self._ctx(agent.port, True)
            ctx.active_probes = False
            ok, _ = NetdevCollector().applicable(ctx)
            assets = NetdevCollector().collect(ctx)
        self.assertFalse(ok)
        self.assertEqual(agent.received, [])
        self.assertEqual(assets, [])


class TelnetHttpProbeTest(unittest.TestCase):
    def test_telnet_iac_and_http(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.bind(("127.0.0.1", 0))
        srv.listen(4)
        port = srv.getsockname()[1]
        http = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        http.bind(("127.0.0.1", 0))
        http.listen(4)
        hport = http.getsockname()[1]

        def serve_telnet():
            c, _ = srv.accept()
            c.sendall(b"\xff\xfd\x18\xff\xfd\x20login: ")
            c.close()

        def serve_http():
            c, _ = http.accept()
            c.recv(1024)
            c.sendall(b"HTTP/1.0 200 OK\r\nServer: DeviceWeb/1.0\r\n\r\n<html>")
            c.close()

        threads = [threading.Thread(target=serve_telnet, daemon=True), threading.Thread(target=serve_http, daemon=True)]
        for t in threads:
            t.start()
        from cryptoscan.collectors.netdev import probe_http, probe_telnet
        try:
            self.assertTrue(probe_telnet("127.0.0.1", port, 2))
            r = probe_http("127.0.0.1", hport, 2)
            self.assertEqual(r["server"], "DeviceWeb/1.0")
            self.assertTrue(r["status"].startswith("HTTP/1.0 200"))
        finally:
            for t in threads:
                t.join(2)
            srv.close()
            http.close()


if __name__ == "__main__":
    unittest.main()
