"""netdev collector against the sample device configurations in tests/fixtures/netdev."""

import dataclasses
import json
import os
import shutil
import tempfile
import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.netdev import NetdevCollector, detect_platform, parse_config
from cryptoscan.confparse import brace_paths, junos_paths, parse_forti, parse_indent_tree, tokenize
from cryptoscan.policy import evaluate

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "netdev")

# placeholder secret values used in the fixtures: none may ever appear in an asset
SECRETS = ["0822455D0A16", "$1$abcd$xxxxxxxxxxxxxxxxxxxxxx", "$1$efgh$", "PLACEHOLDER", "8Ry2YjIyt7RRXU24", "2KFQnbNIdI",
           "$9$", "%^%#", "ENC SH2", "$6$abcd"]


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


def load(name):
    ctx = ScanContext(netdev_configs=[os.path.join(FIX, name)], active_probes=False, hostname="scanner")
    assets = NetdevCollector().collect(ctx)
    assert len(assets) == 1, [a.name for a in assets]
    return assets[0]


def dumped(asset):
    return json.dumps(dataclasses.asdict(asset), default=str)


class NetdevTest(unittest.TestCase):
    def assertNoSecrets(self, asset):
        d = dumped(asset)
        for s in SECRETS:
            self.assertNotIn(s, d, f"secret-like value {s!r} leaked into {asset.name}")

    def test_platform_detection(self):
        expect = {"cisco_ios_legacy.cfg": "ios", "cisco_ios_hardened.cfg": "iosxe", "junos_brace.conf": "junos",
                  "junos_set.conf": "junos", "asa.cfg": "asa", "fortigate.conf": "fortios", "arista.cfg": "eos",
                  "mikrotik.rsc": "mikrotik", "huawei.cfg": "huawei", "panos.set": "panos", "f5.conf": "f5",
                  "nxos.cfg": "nxos", "unknown_vendor.txt": "generic"}
        for name, plat in expect.items():
            with open(os.path.join(FIX, name), encoding="utf-8") as fh:
                self.assertEqual(detect_platform(fh.read()), plat, name)
        self.assertEqual(detect_platform("!! IOS XR Configuration 7.3.2\nhostname xr1\nssh server v2\n"), "iosxr")
        self.assertEqual(detect_platform('; J9727A Configuration Editor; Created on release #WB.16.10\nhostname "sw1"\n'), "procurve")

    def test_cisco_ios_legacy(self):
        a = load("cisco_ios_legacy.cfg")
        r = ids([a])
        need = {"PROTO-TELNET", "PROTO-SNMPV2C", "CFG-PASSWORD-HASH", "PROTO-IKEV1", "CIPHER-3DES", "CIPHER-DES",
                "PK-DH-LT-2048", "PROTO-HTTP-MGMT", "SSH-PROTOCOL-1", "PK-RSA-LT-2048"}
        self.assertTrue(need <= r, need - r)
        self.assertTrue({"MAC-MD5", "HASH-BROKEN"} & r)
        self.assertEqual(a.host, "branch-rtr-01")
        self.assertEqual(a.kind.value, "network_device")
        self.assertEqual(a.attributes["platform"], "ios")
        self.assertEqual(a.attributes["os_version"], "12.4")
        self.assertEqual(a.attributes["hostname"], "branch-rtr-01")
        self.assertTrue(a.attributes["config_file"].endswith("cisco_ios_legacy.cfg"))
        kinds = {u.raw for u in a.uses if u.algorithm == "password-hash"}
        self.assertTrue({"type7", "type5", "type0"} <= kinds)
        self.assertNoSecrets(a)
        # the banner text (telnet / ssh version 1 / des) must not produce uses
        self.assertFalse([u for u in a.uses if u.raw and "Authorized" in u.raw])

    def test_cisco_ios_hardened(self):
        a = load("cisco_ios_hardened.cfg")
        r = ids([a])
        bad = {"PROTO-TELNET", "PROTO-SNMPV2C", "CFG-PASSWORD-HASH", "PROTO-IKEV1", "CIPHER-3DES", "CIPHER-DES",
               "PK-DH-LT-2048", "PROTO-HTTP-MGMT", "SSH-PROTOCOL-1", "PK-RSA-LT-2048", "MAC-MD5", "HASH-BROKEN",
               "PROTO-SNMPV1", "KX-SHA1", "PROTO-TLS10", "PROTO-TLS11", "PROTO-IKEV1-AGGR"}
        self.assertFalse(bad & r, bad & r)
        self.assertEqual(a.attributes["platform"], "iosxe")
        self.assertNoSecrets(a)

    def test_junos_brace_and_set(self):
        for name in ("junos_brace.conf", "junos_set.conf"):
            a = load(name)
            r = ids([a])
            self.assertTrue({"CIPHER-3DES", "PK-DH-LT-2048", "SNMP-AUTH-MD5", "SNMP-PRIV-DES", "PROTO-IKEV1"} <= r, (name, r))
            self.assertNoSecrets(a)
        brace = load("junos_brace.conf")
        r = ids([brace])
        self.assertTrue({"PROTO-TELNET", "PROTO-HTTP-MGMT", "PROTO-IKEV1-AGGR", "MAC-MD5", "CIPHER-DES", "CFG-PASSWORD-HASH"} <= r, r)
        self.assertEqual(brace.host, "edge-srx-01")
        self.assertEqual(load("junos_set.conf").host, "edge-mx-02")

    def test_asa(self):
        a = load("asa.cfg")
        r = ids([a])
        self.assertIn("PROTO-TLS10", r)
        self.assertTrue({"PK-DH-LT-2048", "KX-SHA1"} & r)
        self.assertIn("PROTO-TELNET", r)
        self.assertEqual(a.attributes["os_version"], "9.8(4)")
        self.assertNoSecrets(a)

    def test_fortigate(self):
        a = load("fortigate.conf")
        r = ids([a])
        self.assertTrue({"PROTO-IKEV1-AGGR", "PROTO-TELNET", "PROTO-HTTP-MGMT", "PROTO-TLS10", "CIPHER-3DES", "CIPHER-DES",
                         "PK-DH-LT-2048", "PROTO-SNMPV2C"} <= r, r)
        self.assertNotIn("PROTO-SNMPV1", r)                      # v1 explicitly disabled
        self.assertFalse(a.errors)
        self.assertFalse(a.attributes["strong_crypto"])
        self.assertEqual(a.host, "fgt-branch-07")
        self.assertNoSecrets(a)

    def test_arista(self):
        a = load("arista.cfg")
        r = ids([a])
        self.assertTrue({"PROTO-HTTP-MGMT", "PROTO-TELNET", "PROTO-SNMPV2C", "SNMP-AUTH-MD5", "SNMP-PRIV-DES", "CIPHER-3DES",
                         "MAC-MD5", "PK-DH-LT-2048", "PROTO-TLS10"} <= r, r)
        self.assertEqual(a.attributes["os_version"], "4.22.1F")
        self.assertNoSecrets(a)

    def test_mikrotik(self):
        a = load("mikrotik.rsc")
        r = ids([a])
        self.assertTrue({"PROTO-TELNET", "PROTO-HTTP-MGMT", "PROTO-IKEV1-AGGR", "CIPHER-DES", "CIPHER-3DES", "PK-DH-LT-2048",
                         "PK-DH-BROKEN", "SNMP-AUTH-MD5", "SNMP-PRIV-DES", "PROTO-SNMPV2C"} <= r, r)
        self.assertNotIn("PROTO-FTP", r)                         # ftp disabled=yes
        self.assertEqual(a.host, "mt-branch-03")
        self.assertNoSecrets(a)

    def test_huawei(self):
        a = load("huawei.cfg")
        r = ids([a])
        self.assertTrue({"PROTO-TELNET", "PROTO-HTTP-MGMT", "SSH-PROTOCOL-1", "PROTO-SNMPV2C", "SNMP-AUTH-MD5",
                         "SNMP-PRIV-DES", "CIPHER-DES", "CIPHER-3DES", "PK-DH-LT-2048", "PROTO-IKEV1"} <= r, r)
        self.assertEqual(a.host, "hw-agg-01")
        self.assertNoSecrets(a)

    def test_panos(self):
        a = load("panos.set")
        r = ids([a])
        self.assertTrue({"PROTO-TELNET", "PROTO-HTTP-MGMT", "PROTO-SNMPV2C", "PROTO-TLS10", "CIPHER-3DES", "CIPHER-DES",
                         "PROTO-IKEV1-AGGR", "PK-DH-LT-2048", "CFG-PASSWORD-HASH", "HASH-BROKEN"} <= r, r)
        self.assertEqual(a.host, "pa-edge-01")
        self.assertNoSecrets(a)

    def test_f5(self):
        a = load("f5.conf")
        r = ids([a])
        self.assertTrue({"CIPHER-RC4", "CIPHER-3DES", "PROTO-TLS10", "PROTO-SNMPV2C", "SNMP-AUTH-MD5", "SNMP-PRIV-DES",
                         "MAC-MD5"} <= r, r)
        prof = [u for u in a.uses if u.context == "client-ssl /Common/legacy-clientssl" and u.primitive.value == "protocol"]
        self.assertNotIn("sslv3", {u.algorithm for u in prof})   # options no-sslv3
        self.assertEqual(a.attributes["os_version"], "13.1.3")
        self.assertNoSecrets(a)

    def test_nxos(self):
        a = load("nxos.cfg")
        r = ids([a])
        self.assertTrue({"PROTO-TELNET", "PROTO-HTTP-MGMT", "PROTO-TFTP", "PK-RSA-LT-2048", "SNMP-AUTH-MD5", "SNMP-PRIV-DES",
                         "PROTO-SNMPV2C", "CIPHER-3DES", "CFG-PASSWORD-HASH"} <= r, r)
        self.assertEqual(a.host, "nx-spine-01")
        self.assertNoSecrets(a)

    def test_generic_heuristic(self):
        a = load("unknown_vendor.txt")
        r = ids([a])
        self.assertTrue({"PROTO-TELNET", "SSH-PROTOCOL-1", "PROTO-SNMPV2C", "CIPHER-3DES", "HASH-BROKEN", "PK-DH-LT-2048",
                         "PROTO-TLS10"} <= r, r)
        self.assertNotIn("PROTO-FTP", r)
        self.assertTrue(a.attributes["heuristic"])
        self.assertEqual(a.attributes["platform"], "generic")
        self.assertEqual(a.host, "unknown_vendor")
        self.assertTrue(all(u.extra.get("heuristic") for u in a.uses))
        self.assertNoSecrets(a)

    def test_directory_input_and_extra_paths(self):
        tmp = tempfile.mkdtemp(prefix="cryptoscan-netdev-")
        try:
            sub = os.path.join(tmp, "site-a")
            os.makedirs(sub)
            shutil.copy(os.path.join(FIX, "cisco_ios_legacy.cfg"), tmp)
            shutil.copy(os.path.join(FIX, "junos_set.conf"), sub)
            with open(os.path.join(tmp, "blob.bin"), "wb") as fh:
                fh.write(b"\x00\x01telnet\x00")
            other = tempfile.mkdtemp(prefix="cryptoscan-extra-")
            shutil.copy(os.path.join(FIX, "huawei.cfg"), other)
            with open(os.path.join(other, "notes.txt"), "w") as fh:
                fh.write("telnet is bad, des too\n")
            ctx = ScanContext(netdev_configs=[tmp], extra_paths=[other], active_probes=False)
            assets = NetdevCollector().collect(ctx)
            self.assertEqual(sorted(a.attributes["platform"] for a in assets), ["huawei", "ios", "junos"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            shutil.rmtree(other, ignore_errors=True)

    def test_not_applicable_without_inputs(self):
        ok, why = NetdevCollector().applicable(ScanContext(active_probes=False))
        self.assertFalse(ok)
        self.assertTrue(why)

    def test_parser_failure_is_recorded_not_raised(self):
        ctx = ScanContext()
        a = parse_config("config system global\n set admin-telnet enable\nend\n", "/x/fw.conf", ctx, platform="fortios")
        self.assertEqual(a.host, "fw")
        self.assertIn("PROTO-TELNET", ids([a]))

    def test_confparse_helpers(self):
        self.assertEqual(tokenize('set a "b c" \'d\' e'), ["set", "a", "b c", "d", "e"])
        tree = parse_indent_tree("a\n b\n  c\n d\ne\n")
        self.assertEqual([n.text for n in tree], ["a", "e"])
        self.assertEqual([c.text for c in tree[0].children], ["b", "d"])
        self.assertIn(("x", "y", "z"), brace_paths("x { y z; }"))
        self.assertIn(("x", "l", "p"), brace_paths("x { l [ p q ]; }"))
        self.assertEqual(junos_paths("set a b\nset c d\ndelete a\n"), [("c", "d")])
        secs = parse_forti("config system global\n    set hostname \"x\"\nend\n")
        self.assertEqual(secs[0].first("hostname"), "x")


if __name__ == "__main__":
    unittest.main()
