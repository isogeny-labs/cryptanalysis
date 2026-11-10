"""web_servers collector against a temporary root populated from tests/fixtures/web.

Suite-expansion assertions branch on whether the `openssl` binary is installed:
with it, `ALL:!aNULL` expands to concrete suites (static-RSA, CBC ...); without
it the keyword heuristic stands in.  Everything else is independent of openssl.
"""

import json
import os
import shutil
import tempfile
import unittest
import dataclasses

from cryptoscan import ciphers
from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.web_servers import (WebServersCollector, parse_postfix_main, parse_postfix_protocols,
                                               tomcat_protocols, _yaml_flatten, _toml_flatten)
from cryptoscan.policy import evaluate
from cryptoscan.util import which

FIX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
WEB = os.path.join(FIX, "web")

LAYOUT = {
    "nginx.conf": "/etc/nginx/nginx.conf",
    "nginx_site_legacy": "/etc/nginx/sites-enabled/legacy",
    "nginx_site_modern.conf": "/etc/nginx/conf.d/modern.conf",
    "apache2.conf": "/etc/apache2/apache2.conf",
    "apache_ssl_mod.conf": "/etc/apache2/mods-enabled/ssl.conf",
    "apache_vhost.conf": "/etc/apache2/sites-enabled/shop-ssl.conf",
    "haproxy.cfg": "/etc/haproxy/haproxy.cfg",
    "postfix_main.cf": "/etc/postfix/main.cf",
    "tomcat_server.xml": "/etc/tomcat9/server.xml",
    "kubelet_config.yaml": "/var/lib/kubelet/config.yaml",
    "kube-apiserver.yaml": "/etc/kubernetes/manifests/kube-apiserver.yaml",
    "dovecot.conf": "/etc/dovecot/dovecot.conf",
    "dovecot_10-ssl.conf": "/etc/dovecot/conf.d/10-ssl.conf",
    "exim4.conf": "/etc/exim4/exim4.conf",
    "lighttpd.conf": "/etc/lighttpd/lighttpd.conf",
    "lighttpd_ssl.conf": "/etc/lighttpd/conf.d/ssl.conf",
    "traefik_dynamic.toml": "/etc/traefik/dynamic/tls.toml",
    "envoy.yaml": "/etc/envoy/envoy.yaml",
    "spring_application.properties": "/opt/shop/config/application.properties",
}


def _put(root, rel, src):
    dst = os.path.join(root, rel.lstrip("/"))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def ids(assets, profile="nist"):
    return {f.rule_id for f in evaluate(assets, profile)}


class WebServersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = tempfile.mkdtemp(prefix="cryptoscan-web-")
        for name, rel in LAYOUT.items():
            _put(cls.root, rel, os.path.join(WEB, name))
        _put(cls.root, "/etc/ssl/certs/server.pem", os.path.join(FIX, "certs", "server_sha256.pem"))
        key = _put(cls.root, "/etc/ssl/private/server.key", os.path.join(FIX, "certs", "server.key"))
        os.chmod(key, 0o600)
        _put(cls.root, "/etc/ssl/dhparam1024.pem", os.path.join(FIX, "keys", "dhparam1024.pem"))
        # HAProxy: certificate + key in one PEM
        with open(os.path.join(FIX, "certs", "server_sha256.pem"), "rb") as a, open(os.path.join(FIX, "certs", "server.key"), "rb") as b:
            combined = a.read() + b"\n" + b.read()
        p = os.path.join(cls.root, "etc/haproxy/certs/site.pem")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(combined)
        os.chmod(p, 0o640)
        cls.ctx = ScanContext(root=cls.root, hostname="web1", active_probes=False)
        cls.assets = WebServersCollector().collect(cls.ctx)
        cls.endpoints = [a for a in cls.assets if a.kind.value == "tls_endpoint"]

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.root, ignore_errors=True)

    def ep(self, software, contains=""):
        found = [a for a in self.endpoints if a.attributes["software"] == software and contains in a.name]
        self.assertTrue(found, f"{software}/{contains}: {[a.name for a in self.endpoints]}")
        return found[0]

    # ---- nginx -------------------------------------------------------------
    def test_nginx_legacy_site(self):
        a = self.ep("nginx", "legacy.example.com")
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "PROTO-TLS11", "CFG-DHPARAM-DEFAULT"} <= r, r)
        self.assertEqual(a.attributes["server_names"], ["legacy.example.com", "www.legacy.example.com"])
        self.assertEqual(a.attributes["config_file"], "/etc/nginx/sites-enabled/legacy")
        self.assertNotIn("tls1.3", a.attributes)
        self.assertTrue(a.attributes["prefer_server_ciphers"])           # inherited from http {}
        suites = [u for u in a.uses if u.context == "tls-cipher-suite"]
        self.assertTrue(suites)
        self.assertTrue(all(u.negotiated is False for u in suites))
        if which("openssl"):
            self.assertTrue(a.attributes["ciphers_expanded"])
            self.assertTrue({"KX-RSA", "TLS-CBC"} <= r, r)
        else:
            self.assertIn("heuristic", a.attributes["cipher_string_flags"]["ssl_ciphers"])
            self.assertTrue({"CIPHER-RC4", "CIPHER-3DES"} <= r, r)       # ALL heuristic stands in

    def test_nginx_port80_server_is_not_an_endpoint(self):
        self.assertFalse([a for a in self.endpoints if a.attributes["software"] == "nginx" and a.attributes["listen"] == ["80"]])

    def test_nginx_modern_site(self):
        a = self.ep("nginx", "modern.example.com")
        r = ids([a])
        self.assertTrue(a.attributes.get("tls1.3"))
        self.assertFalse({"PROTO-TLS10", "PROTO-TLS11", "PROTO-TLS12", "CFG-DHPARAM-DEFAULT", "KX-RSA"} & r, r)
        curves = {u.curve for u in a.uses if u.context == "tls-group"}
        self.assertEqual(curves, {"curve25519", "p-384"})
        self.assertTrue(a.attributes["http2"])
        self.assertTrue(a.attributes["ocsp_stapling"])
        self.assertIn("TLS_AES_256_GCM_SHA384", {u.raw for u in a.uses})

    def test_nginx_stream_defaults_unknown_version(self):
        a = self.ep("nginx", "server _")
        self.assertEqual(a.attributes["context"], "stream")
        self.assertTrue(a.attributes["defaults_assumed"])
        protos = [u for u in a.uses if u.context == "tls-protocol"]
        self.assertEqual({u.algorithm for u in protos}, {"tls1.0", "tls1.1", "tls1.2"})
        self.assertTrue(all(u.extra["source"] == "default-unknown-version" for u in protos))
        self.assertTrue(any(u.extra.get("source") == "default" for u in a.uses if u.context == "tls-cipher-suite"))

    def test_nginx_default_by_version(self):
        ctx = ScanContext(root=self.root, hostname="web1", options={"nginx_version": "1.25.3", "web_servers_only": "nginx"})
        a = [x for x in WebServersCollector().collect(ctx) if "server _" in x.name][0]
        self.assertEqual({u.algorithm for u in a.uses if u.context == "tls-protocol"}, {"tls1.2", "tls1.3"})
        self.assertTrue(a.attributes["tls1.3"])

    # ---- certificates / keys ------------------------------------------------
    def test_certificate_and_key_assets_shared(self):
        certs = [a for a in self.assets if a.kind.value in ("certificate", "ca_certificate")]
        keys = [a for a in self.assets if a.kind.value == "private_key"]
        self.assertTrue(certs and keys)
        c = [x for x in certs if "/etc/ssl/certs/server.pem" in x.attributes["locations"]][0]
        self.assertGreater(len(c.attributes["used_by"]), 3)
        self.assertIn("public-key", {u.context for u in c.uses})
        self.assertIn("certificate-signature", {u.context for u in c.uses})
        self.assertIn("serial_bits", c.attributes)
        k = [x for x in keys if x.location == "/etc/ssl/private/server.key"][0]
        self.assertEqual(k.attributes["mode"], 0o600)
        self.assertFalse(k.attributes["encrypted"])
        self.assertEqual(k.uses[0].algorithm, "rsa")
        hk = [x for x in keys if x.location == "/etc/haproxy/certs/site.pem"]
        self.assertEqual(len(hk), 1)
        self.assertIn("KEY-PERMS", ids(hk))

    # ---- Apache ---------------------------------------------------------------
    def test_apache_vhost(self):
        a = self.ep("apache", "shop.example.com")
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "PROTO-TLS11", "CIPHER-RC4", "PK-DH-LT-2048"} <= r, r)
        self.assertNotIn("PROTO-SSLV3", r)                       # <IfModule !mod_ssl.c> is skipped
        self.assertNotIn("CIPHER-NULL", r)                       # <Directory> scoped directive ignored
        self.assertTrue(a.attributes["tls1.3"])
        self.assertTrue(a.attributes["honor_cipher_order"])      # server-config default inherited
        self.assertEqual(a.attributes["dh_bits"], 1024)
        self.assertEqual(len([x for x in self.endpoints if x.attributes["software"] == "apache"]), 1)

    def test_apache_protocol_expression(self):
        self.assertEqual(ciphers.resolve_protocol_expr("all -SSLv3"), ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"])
        self.assertEqual(ciphers.resolve_protocol_expr("-all +TLSv1.2 +TLSv1.3"), ["TLSv1.2", "TLSv1.3"])
        self.assertEqual(ciphers.resolve_protocol_expr("TLSv1.2"), ["TLSv1.2"])

    # ---- HAProxy --------------------------------------------------------------
    def test_haproxy(self):
        a = self.ep("haproxy", "bind :443")
        r = ids([a])
        self.assertTrue({"PK-DH-LT-2048", "PROTO-TLS10"} <= r, r)
        self.assertNotIn("PROTO-SSLV3", r)
        self.assertEqual(a.attributes["dh_bits"], 1024)
        b = self.ep("haproxy", "bind :8443")
        self.assertFalse({"PROTO-TLS10", "PROTO-TLS11"} & ids([b]))
        srv = self.ep("haproxy", "server app1")
        self.assertEqual(srv.attributes["role"], "client")
        self.assertEqual({u.algorithm for u in srv.uses if u.context == "tls-protocol"}, {"tls1.2", "tls1.3"})

    # ---- Postfix --------------------------------------------------------------
    def test_postfix(self):
        a = self.ep("postfix", "smtpd")
        r = ids([a])
        self.assertIn("PROTO-TLS10", r)
        self.assertNotIn("PROTO-SSLV3", r)
        self.assertNotIn("CIPHER-RC4", r)                        # excluded
        self.assertNotIn("KX-ANON", r)                           # aNULL excluded
        self.assertEqual(a.attributes["cipher_grades"], {"smtpd_tls_ciphers": "medium", "smtpd_tls_mandatory_ciphers": "high"})
        c = self.ep("postfix", "smtp client")
        self.assertEqual({u.algorithm for u in c.uses if u.context == "tls-protocol"}, {"tls1.2", "tls1.3"})

    def test_postfix_protocol_syntax(self):
        self.assertEqual(parse_postfix_protocols("!SSLv2, !SSLv3"), ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"])
        self.assertEqual(parse_postfix_protocols(">=TLSv1.2"), ["TLSv1.2", "TLSv1.3"])
        self.assertEqual(parse_postfix_protocols("TLSv1.2 TLSv1.3"), ["TLSv1.2", "TLSv1.3"])
        self.assertEqual(parse_postfix_protocols("!SSLv2 !SSLv3 !TLSv1 !TLSv1.1"), ["TLSv1.2", "TLSv1.3"])
        cf = parse_postfix_main("a = /x\nb = $a/y\n  z\n# c = 1\n")
        self.assertEqual(cf["b"], "/x/y z")

    # ---- Tomcat ---------------------------------------------------------------
    def test_tomcat(self):
        a = self.ep("tomcat", "8443")
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "CIPHER-3DES", "KX-RSA"} <= r, r)
        self.assertNotIn("PROTO-TLS11", r)
        self.assertEqual(a.attributes["keystores"], ["conf/keystore.jks"])
        self.assertNotIn("PLACEHOLDER-PASS", json.dumps(dataclasses.asdict(a), default=str))
        self.assertEqual(len([x for x in self.endpoints if x.attributes["software"] == "tomcat"]), 1)
        self.assertEqual(tomcat_protocols("TLSv1.2+TLSv1.3"), ["TLSv1.2", "TLSv1.3"])
        self.assertEqual(tomcat_protocols("all"), ["TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"])
        self.assertEqual(tomcat_protocols("TLSv1,TLSv1.1"), ["TLSv1", "TLSv1.1"])
        self.assertEqual(tomcat_protocols("all -TLSv1 -TLSv1.1"), ["TLSv1.2", "TLSv1.3"])

    # ---- Kubernetes -----------------------------------------------------------
    def test_kubelet_and_apiserver(self):
        a = self.ep("kubelet")
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "CIPHER-3DES"} <= r, r)
        k = self.ep("kubernetes", "kube-apiserver")
        self.assertFalse({"PROTO-TLS10", "PROTO-TLS11"} & ids([k]))
        self.assertEqual(len([u for u in k.uses if u.context == "tls-cipher-suite"]), 2)

    # ---- the rest -------------------------------------------------------------
    def test_dovecot(self):
        a = self.ep("dovecot")
        r = ids([a])
        self.assertTrue({"PROTO-TLS11", "PK-DH-LT-2048"} <= r, r)
        self.assertNotIn("PROTO-TLS10", r)
        self.assertEqual(a.attributes["ssl"], "required")

    def test_exim(self):
        a = self.ep("exim")
        r = ids([a])
        self.assertIn("PROTO-TLS11", r)
        self.assertNotIn("PROTO-TLS10", r)
        self.assertIn("CIPHER-3DES", r)                          # explicit DES-CBC3-SHA

    def test_lighttpd(self):
        a = self.ep("lighttpd")
        r = ids([a])
        self.assertIn("PROTO-SSLV3", r)                          # ssl.use-sslv3 = enable
        self.assertNotIn("PROTO-TLS10", r)
        self.assertEqual({u.curve for u in a.uses if u.context == "tls-group"}, {"curve25519", "p-384"})

    def test_traefik(self):
        legacy = self.ep("traefik", "legacy")
        self.assertTrue({"PROTO-TLS10", "KX-RSA"} <= ids([legacy]))
        default = self.ep("traefik", "tls.options.default")
        self.assertFalse({"PROTO-TLS10", "PROTO-TLS11"} & ids([default]))

    def test_envoy(self):
        a = self.ep("envoy")
        r = ids([a])
        self.assertTrue({"PROTO-TLS10", "CIPHER-3DES", "TLS-CBC"} <= r, r)
        self.assertIn("ECDHE-RSA-CHACHA20-POLY1305", {u.raw for u in a.uses})

    def test_spring(self):
        a = self.ep("spring-boot")
        self.assertTrue({"PROTO-TLS11", "KX-RSA"} <= ids([a]))
        self.assertNotIn("PLACEHOLDER-PASS", json.dumps(dataclasses.asdict(a), default=str))

    def test_yaml_and_toml_flatteners(self):
        flat = _yaml_flatten("a:\n  b: 1\n  c:\n  - x\n  - y\nd: [p, q]\ne:\n- name: n1\n  v: 2\n")
        self.assertIn((("a", "b"), "1"), flat)
        self.assertIn((("a", "c"), "x"), flat)
        self.assertIn((("d",), "q"), flat)
        self.assertIn((("e", "v"), "2"), flat)
        t = _toml_flatten('[x.y]\nk = "v"\narr = [\n "a",\n "b"\n]\n')
        self.assertEqual(t, [(("x", "y", "k"), "v"), (("x", "y", "arr"), "a"), (("x", "y", "arr"), "b")])

    def test_every_asset_is_json_serialisable_and_nothing_raises(self):
        self.assertEqual(self.ctx.warnings, [])
        for a in self.assets:
            json.dumps(dataclasses.asdict(a), default=str)
        self.assertEqual({a.collector for a in self.assets}, {"web_servers"})

    def test_empty_root(self):
        root = tempfile.mkdtemp(prefix="cryptoscan-web-empty-")
        try:
            self.assertEqual(WebServersCollector().collect(ScanContext(root=root)), [])
        finally:
            shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
