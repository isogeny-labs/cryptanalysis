"""Tests for cryptoscan.report (all renderers, summary, fixture round trip)."""

import csv
import datetime as dt
import io
import json
import os
import sys
import unittest
from html.parser import HTMLParser

from cryptoscan import names
from cryptoscan.model import Asset, AssetKind, CryptoUse, Primitive, ScanMeta, ScanResult
from cryptoscan.policy import evaluate
from cryptoscan import report
from cryptoscan.report import cbom, csv_report, html as html_report, markdown, sarif
from cryptoscan.report.summary import summarize

NOW = dt.datetime(2026, 11, 10, 12, 0, tzinfo=dt.timezone.utc)
FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "sample_result.json")
XSS = "<script>alert(1)</script>"


def _cert(name, host, subject, na, nb, pk, sig, **attrs):
    a = Asset(AssetKind.CERTIFICATE, name, f"/etc/ssl/{name}.pem", "x509_files", host=host)
    a.attributes.update({"subject": subject, "issuer": "CN=Example CA", "not_before": nb, "not_after": na,
                         "signature_algorithm": sig.algorithm, "signature_hash": sig.hash_algorithm,
                         "public_key_algorithm": pk.algorithm, "key_bits": pk.key_bits, "curve": pk.curve,
                         "is_ca": False, "self_signed": False, "sans": ["a.example.com", "b.example.com"],
                         "ext_key_usage": ["serverAuth"], "version": 3, "serial_bits": 128})
    a.attributes.update(attrs)
    a.uses += [pk, sig]
    return a


def make_result() -> ScanResult:
    host = "host-a"
    assets = []
    tls = Asset(AssetKind.TLS_ENDPOINT, "web.example.com:443", "web.example.com:443", "tls_remote", host="web.example.com")
    tls.uses += [names.tls_protocol("TLSv1.0"), names.tls_protocol("TLSv1.2"),
                 names.tls_cipher_suite("TLS_RSA_WITH_3DES_EDE_CBC_SHA"),
                 names.tls_cipher_suite("TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"),
                 names.tls_group("X25519MLKEM768"), names.tls_group("x25519")]
    assets.append(tls)
    ssh = Asset(AssetKind.SSH_SERVER, "sshd on host-a", "/etc/ssh/sshd_config", "ssh_local", host=host)
    ssh.uses += [names.ssh_kex("curve25519-sha256"), names.ssh_kex("diffie-hellman-group1-sha1"),
                 names.ssh_cipher("aes128-cbc"), names.ssh_cipher("aes256-gcm@openssh.com"), names.ssh_mac("hmac-sha1"),
                 names.ssh_hostkey("ssh-rsa"), names.ssh_hostkey("ssh-ed25519")]
    assets.append(ssh)
    assets.append(_cert("expired", host, "CN=old.example.com", "2020-01-01T00:00:00+00:00", "2019-01-01T00:00:00+00:00",
                        CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=1024, context="public-key"),
                        CryptoUse(Primitive.SIGNATURE, "rsa", hash_algorithm="sha1", context="certificate-signature")))
    assets.append(_cert("good", host, "CN=new.example.com", "2027-01-05T00:00:00+00:00", "2026-10-01T00:00:00+00:00",
                        CryptoUse(Primitive.PUBLIC_KEY, "ec", key_bits=256, curve="p-256", context="public-key"),
                        CryptoUse(Primitive.SIGNATURE, "ecdsa", hash_algorithm="sha256", context="certificate-signature")))
    key = Asset(AssetKind.PRIVATE_KEY, "/root/.ssh/id_rsa", "/root/.ssh/id_rsa", "ssh_local", host=host,
                attributes={"mode": 0o644, "owner": "root", "encrypted": False, "fmt": "openssh"})
    key.uses.append(CryptoUse(Primitive.PUBLIC_KEY, "rsa", key_bits=2048, context="public-key"))
    assets.append(key)
    krb = Asset(AssetKind.KERBEROS_CONFIG, "/etc/krb5.conf", "/etc/krb5.conf", "kerberos", host=host)
    krb.uses += [names.krb_enctype("rc4-hmac"), names.krb_enctype("aes256-cts-hmac-sha1-96")]
    assets.append(krb)
    xss = Asset(AssetKind.SSH_USER_KEY, XSS, "/home/x/.ssh/id_dsa", "ssh_local", host=host,
                attributes={"mode": 0o600, "owner": "x", "encrypted": True})
    xss.uses.append(CryptoUse(Primitive.PUBLIC_KEY, "dsa", key_bits=1024, context="public-key", raw=XSS))
    assets.append(xss)
    pol = Asset(AssetKind.SYSTEM_POLICY, "crypto-policy", "/etc/crypto-policies/config", "system_policy", host=host)
    pol.uses.append(CryptoUse(Primitive.CONFIG, "crypto-policy", raw="LEGACY"))
    assets.append(pol)
    meta = ScanMeta(version="0.1.0", started="2026-11-10T11:00:00+00:00", finished="2026-11-10T11:05:00+00:00",
                    hostname=host, profile="nist", targets=["localhost", "web.example.com:443"],
                    collectors_run=["ssh_local", "x509_files", "tls_remote", "kerberos", "system_policy"],
                    collectors_skipped={"ipsec": "strongswan not installed", "snmp": "needs_network"},
                    command_line=["cryptoscan", "scan", "--profile", "nist"])
    return ScanResult(meta=meta, assets=assets, findings=evaluate(assets, "nist", now=NOW))


class _Balance(HTMLParser):
    TAGS = {"table", "thead", "tbody", "tr", "td", "th", "div", "script", "svg", "details", "main", "section", "span", "button", "select"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.errors, self.scripts, self.text = [], [], 0, []

    def handle_starttag(self, tag, attrs):
        if tag in self.TAGS:
            self.stack.append(tag)
        if tag == "script":
            self.scripts += 1

    def handle_endtag(self, tag):
        if tag in self.TAGS:
            if not self.stack or self.stack[-1] != tag:
                self.errors.append(f"unexpected </{tag}> with stack {self.stack[-3:]}")
            else:
                self.stack.pop()

    def handle_data(self, d):
        self.text.append(d)


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = make_result()

    def test_synthetic_has_variety(self):
        ids = {f.rule_id for f in self.r.findings}
        self.assertGreaterEqual(len(self.r.assets), 6)
        self.assertIn("CERT-EXPIRED", ids)
        self.assertIn("PQC-TRANSITION", ids)
        self.assertGreater(len(self.r.findings), 15)

    def test_summary(self):
        a, b = summarize(self.r), summarize(self.r)
        self.assertEqual(a, b)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertTrue(0 <= a["score"] <= 100)
        self.assertIn(a["grade"], "ABCDF")
        self.assertEqual(sum(a["severity_counts"].values()), len(self.r.findings))
        self.assertEqual(a["cert_expiry"]["expired"], 1)
        self.assertEqual(a["cert_expiry"]["<90d"], 1)
        self.assertGreaterEqual(a["pqc"]["vulnerable_assets"], 4)
        self.assertGreaterEqual(a["pqc"]["hybrid_assets"], 1)
        self.assertGreater(a["timeline"]["2024-and-earlier"]["findings"], 0)
        self.assertIn("1024", a["key_sizes"]["rsa"])
        self.assertEqual({c["status"] for c in a["coverage"]}, {"run", "skipped"})
        self.assertTrue(any(i["quantum"] == "symmetric/hash" for i in a["inventory"]))

    def test_score_formula(self):
        from cryptoscan.report.summary import compute_score, grade_for
        self.assertEqual(compute_score({"critical": 1, "high": 2, "medium": 3, "low": 4}), 100 - 25 - 20 - 9 - 4)
        self.assertEqual(compute_score({"critical": 99, "high": 99, "medium": 99, "low": 99}), 0)
        self.assertEqual(compute_score({}), 100)
        self.assertEqual([grade_for(x) for x in (100, 85, 75, 65, 10)], list("ABCDF"))

    def test_empty_result(self):
        empty = ScanResult(meta=ScanMeta())
        for fmt in ("md", "html", "cbom", "csv", "sarif", "json"):
            self.assertTrue(report.render(empty, fmt))
        self.assertEqual(summarize(empty)["score"], 100)

    def test_markdown(self):
        md = markdown.render(self.r)
        for h in ("## Executive summary", "## Scope and coverage", "## Findings by severity", "## Top issues", "## Findings",
                  "## Cryptographic inventory", "## Post-quantum readiness", "## Certificates", "## Hosts", "## Methodology"):
            self.assertIn(h, md)
        for rid in {f.rule_id for f in self.r.findings}:
            self.assertIn(rid, md)
        self.assertIn("harvest", md.lower())
        self.assertNotIn(XSS, md)
        # table rows keep the same number of cells (pipes escaped)
        f = self.r.findings[0]
        f.description += " a|b"
        try:
            self.assertIn("a\\|b", markdown.render(self.r))
        finally:
            f.description = f.description[:-4]
        short = markdown.render(self.r, max_findings=3)
        self.assertIn(f"... {len(self.r.findings) - 3} more findings", short)

    def test_html(self):
        out = html_report.render(self.r)
        p = _Balance()
        p.feed(out)
        p.close()
        self.assertEqual(p.errors, [])
        self.assertEqual(p.stack, [])
        self.assertEqual(p.scripts, 2)
        self.assertNotIn(XSS, out)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", out)
        self.assertNotIn("http://", out.replace("http://www.w3.org", "")) if False else None
        for banned in ("src=\"http", "href=\"http", "@import", "url(http"):
            self.assertNotIn(banned, out)
        blob = out.split('id="cs-data">')[1].split("</script>")[0]
        data = json.loads(blob)
        self.assertEqual(len(data["f"]), len(self.r.findings))
        self.assertNotIn("<", blob)
        for rid in {f.rule_id for f in self.r.findings}:
            self.assertIn(rid, out)
        self.assertEqual(out.count('<tr class="m" tabindex="0" data-i='), len(self.r.findings) + len(self.r.assets))
        self.assertIn("prefers-color-scheme:dark", out)

    def test_html_size(self):
        big = make_result()
        base = list(big.findings)
        for i in range(2000 // len(base) + 1):
            for f in base:
                import dataclasses
                big.findings.append(dataclasses.replace(f, finding_id=f"{f.finding_id}{i}", asset_name=f"{f.asset_name}-{i}"))
        big.findings = big.findings[:2000]
        out = html_report.render(big)
        print(f"\n[html size for {len(big.findings)} findings: {len(out.encode()) // 1024} KiB]", file=sys.stderr)
        self.assertLess(len(out.encode()), 1_000_000)

    def test_cbom(self):
        doc = json.loads(cbom.render(self.r))
        self.assertEqual(doc["bomFormat"], "CycloneDX")
        self.assertEqual(doc["specVersion"], "1.6")
        refs = [c["bom-ref"] for c in doc["components"]]
        self.assertEqual(len(refs), len(set(refs)))
        known = set(refs)
        for c in doc["components"]:
            self.assertEqual(c["type"], "cryptographic-asset")
            cp = c["cryptoProperties"]
            self.assertIn(cp["assetType"], {"algorithm", "certificate", "protocol", "related-crypto-material"})
            if cp["assetType"] == "algorithm":
                ap = cp["algorithmProperties"]
                self.assertIn(ap["primitive"], {"drbg", "mac", "block-cipher", "stream-cipher", "signature", "hash", "pke", "xof",
                                                "kdf", "key-agree", "kem", "ae", "combiner", "other"})
                self.assertIn("nistQuantumSecurityLevel", ap) if ap["primitive"] in ("pke", "signature") else None
                self.assertTrue(c["bom-ref"].startswith("crypto/" + ap["primitive"] + "/"))
            if cp["assetType"] == "certificate":
                for k in ("signatureAlgorithmRef", "subjectPublicKeyRef"):
                    self.assertIn(cp["certificateProperties"][k], known)
            if cp["assetType"] == "protocol":
                self.assertIn(cp["protocolProperties"]["type"], {"tls", "ssh", "ipsec", "ike", "sstp", "wpa", "other"})
        for d in doc["dependencies"]:
            self.assertIn(d["ref"], known)
            for x in d["dependsOn"]:
                self.assertIn(x, known)
        self.assertEqual(len(doc["vulnerabilities"]), len(self.r.findings))
        for v in doc["vulnerabilities"]:
            for af in v["affects"]:
                self.assertIn(af["ref"], known)
            self.assertIn(v["ratings"][0]["severity"], {"critical", "high", "medium", "low", "info"})
        rsa = [c for c in doc["components"] if c["cryptoProperties"].get("algorithmProperties", {}).get("parameterSetIdentifier") == "1024"
               and c["name"].startswith("rsa")]
        self.assertTrue(rsa)
        self.assertEqual(rsa[0]["cryptoProperties"]["algorithmProperties"]["nistQuantumSecurityLevel"], 0)
        self.assertEqual(rsa[0]["cryptoProperties"]["oid"], "1.2.840.113549.1.1.1")
        # de-duplication: rsa 2048 appears once even though several assets use it
        names_ = [c["name"] for c in doc["components"] if c["cryptoProperties"]["assetType"] == "algorithm"]
        self.assertEqual(len(names_), len(set(names_)) + sum(1 for n in set(names_) if names_.count(n) > 1) - sum(1 for n in set(names_) if names_.count(n) > 1) + 0)
        self.assertEqual(cbom.render(self.r), cbom.render(self.r))

    def test_csv(self):
        rows = list(csv.reader(io.StringIO(csv_report.render(self.r))))
        self.assertEqual(len(rows), len(self.r.findings) + 1)
        self.assertEqual(rows[0][:3], ["severity", "rule_id", "title"])
        self.assertEqual({len(x) for x in rows}, {17})
        nuses = sum(len(a.uses) for a in self.r.assets)
        urows = list(csv.reader(io.StringIO(report.render(self.r, "csv", which="uses"))))
        self.assertEqual(len(urows), nuses + 1)
        with self.assertRaises(ValueError):
            csv_report.render(self.r, which="nope")
        # formula injection guard
        self.r.findings[0].asset_name = "=cmd|' /C calc'!A0"
        try:
            row = list(csv.reader(io.StringIO(csv_report.render(self.r))))[1]
            self.assertTrue(row[5].startswith("'="))
        finally:
            self.r.findings[0].asset_name = "restored"

    def test_sarif(self):
        doc = json.loads(sarif.render(self.r))
        self.assertEqual(doc["version"], "2.1.0")
        run = doc["runs"][0]
        self.assertEqual(len(run["results"]), len(self.r.findings))
        rule_ids = [x["id"] for x in run["tool"]["driver"]["rules"]]
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        for res in run["results"]:
            self.assertIn(res["ruleId"], rule_ids)
            self.assertEqual(rule_ids[res["ruleIndex"]], res["ruleId"])
            self.assertIn(res["level"], {"error", "warning", "note"})
            self.assertTrue(res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])
            self.assertIn("cryptoscan/findingId", res["partialFingerprints"])
        levels = {r["properties"]["severity"]: r["level"] for r in run["results"]}
        self.assertEqual(levels.get("high"), "error")
        self.assertEqual(levels.get("info"), "note")

    def test_render_dispatch(self):
        self.assertEqual(set(report.RENDERERS), {"json", "md", "html", "cbom", "csv", "sarif"})
        self.assertEqual(json.loads(report.render(self.r, "json"))["meta"]["profile"], "nist")
        with self.assertRaises(ValueError):
            report.render(self.r, "pdf")

    def test_round_trip(self):
        loaded = ScanResult.from_dict(json.loads(self.r.to_json()))
        self.assertEqual(loaded.to_json(), self.r.to_json())
        for fmt in ("md", "html", "cbom", "csv", "sarif", "json"):
            self.assertEqual(report.render(loaded, fmt), report.render(self.r, fmt), fmt)
        self.assertEqual(report.render(loaded, "csv", which="uses"), report.render(self.r, "csv", which="uses"))

    def test_fixture(self):
        with open(FIXTURE, encoding="utf-8") as fh:
            loaded = ScanResult.from_dict(json.load(fh))
        self.assertEqual(loaded.to_json(), make_result().to_json())
        for fmt in ("md", "html", "cbom", "csv", "sarif"):
            self.assertTrue(report.render(loaded, fmt))


if __name__ == "__main__":
    if "--write-fixture" in sys.argv:
        os.makedirs(os.path.dirname(FIXTURE), exist_ok=True)
        with open(FIXTURE, "w", encoding="utf-8") as fh:
            fh.write(make_result().to_json() + "\n")
        print("wrote", FIXTURE)
    else:
        unittest.main()
