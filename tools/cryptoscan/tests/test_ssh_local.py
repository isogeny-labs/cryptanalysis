"""Tests for the ssh_local collector against synthetic fixtures (tests/fixtures/ssh)."""
import os
import shutil
import tempfile
import unittest

from cryptoscan.collectors.base import ScanContext
from cryptoscan.collectors.ssh_local import SSHLocalCollector, expand_list, _parse_sshd_T
from cryptoscan.model import AssetKind, Primitive
from cryptoscan.policy import evaluate

FIX = os.path.join(os.path.dirname(__file__), "fixtures", "ssh")


class SSHLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="cs-sshlocal-")
        cls.root = os.path.join(cls.tmp, "root")
        shutil.copytree(os.path.join(FIX, "etc"), os.path.join(cls.root, "etc"))
        cls.home = os.path.join(cls.tmp, "home", "alice")
        shutil.copytree(os.path.join(FIX, "home", "alice"), cls.home)
        modes = {"etc/ssh/ssh_host_rsa_key": 0o644, "etc/ssh/ssh_host_dsa_key": 0o644, "etc/ssh/ssh_host_ecdsa_key": 0o600,
                 "etc/ssh/ssh_host_ed25519_key": 0o600}
        for rel, m in modes.items():
            os.chmod(os.path.join(cls.root, rel), m)
        os.chmod(os.path.join(cls.home, ".ssh", "id_ed25519"), 0o640)
        os.chmod(os.path.join(cls.home, ".ssh", "id_rsa"), 0o600)
        cls.ctx = ScanContext(hostname="fixture", root=cls.root, options={"home_dirs": [cls.home]})
        cls.assets = SSHLocalCollector().collect(cls.ctx)
        cls.findings = evaluate(cls.assets, "nist")
        cls.ids = {f.rule_id for f in cls.findings}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def kind(self, k):
        return [a for a in self.assets if a.kind == k]

    def uses(self, asset, directive):
        return [u for u in asset.uses if u.extra.get("directive") == directive]

    # -- list syntax ----------------------------------------------------
    def test_expand_list(self):
        d = ["a", "b", "c-cert"]
        self.assertEqual(expand_list("x,y", d), (["x", "y"], False))
        self.assertEqual(expand_list("+x", d), (["a", "b", "c-cert", "x"], True))
        self.assertEqual(expand_list("^x", d), (["x", "a", "b", "c-cert"], True))
        self.assertEqual(expand_list("-*cert,b", d), (["a"], True))

    def test_parse_sshd_T(self):
        recs = _parse_sshd_T("port 22\nkexalgorithms a,b\nhostkey /x\npubkeyacceptedkeytypes ssh-rsa\n")
        self.assertEqual([r["kw"] for r in recs], ["port", "kexalgorithms", "hostkey", "pubkeyacceptedalgorithms"])

    # -- server ---------------------------------------------------------
    def test_server_asset_and_relative_syntax(self):
        (srv,) = self.kind(AssetKind.SSH_SERVER)
        self.assertEqual(srv.attributes["config_source"], "files")
        kex = self.uses(srv, "KexAlgorithms")
        names_ = [u.raw for u in kex]
        self.assertIn("diffie-hellman-group14-sha1", names_)
        self.assertIn("curve25519-sha256", names_)          # defaults retained by "+"
        self.assertTrue(all(u.extra.get("relative_to_defaults") for u in kex))
        ciphers = [u.raw for u in self.uses(srv, "Ciphers") if "match" not in u.extra]
        self.assertEqual(ciphers[0], "aes128-cbc")             # "^" prepends
        pk = [u.raw for u in self.uses(srv, "PubkeyAcceptedAlgorithms") if "match" not in u.extra]
        self.assertTrue(pk and not any("cert-v01" in n for n in pk))   # "-" wildcard removal

    def test_include_wins_first_value(self):
        (srv,) = self.kind(AssetKind.SSH_SERVER)
        macs = [u.raw for u in self.uses(srv, "MACs")]
        self.assertEqual(macs, ["hmac-md5", "hmac-sha2-256"])       # conf.d included first, so it wins
        ca = [u.raw for u in self.uses(srv, "CASignatureAlgorithms")]
        self.assertEqual(ca, ["ssh-ed25519", "ssh-rsa"])
        self.assertTrue(all(u.extra["source"] == "config" for u in self.uses(srv, "CASignatureAlgorithms")))

    def test_match_block(self):
        (srv,) = self.kind(AssetKind.SSH_SERVER)
        m = [u for u in srv.uses if u.extra.get("match") == "User backup"]
        self.assertIn("3des-cbc", [u.raw for u in m if u.context == "cipher"])
        self.assertIn("ssh-rsa", [u.raw for u in m if u.context == "pubkey-auth"])
        glob_ciphers = [u for u in self.uses(srv, "Ciphers") if "match" not in u.extra]
        self.assertNotIn("3des-cbc", [u.raw for u in glob_ciphers])

    def test_defaults_when_absent(self):
        (srv,) = self.kind(AssetKind.SSH_SERVER)
        # fixture sets no GSSAPI/Hostbased; HostKeyAlgorithms is explicit; check a default via the client below
        cfg = [u for u in srv.uses if u.primitive == Primitive.CONFIG]
        by = {u.context: u.raw for u in cfg}
        self.assertEqual(by["ssh-protocol"], "2,1")
        self.assertEqual(by["ssh-fingerprint-hash"], "md5")
        self.assertEqual(by["ssh-required-rsa-size"], "1024")
        self.assertEqual(by["weak-moduli"], "2")
        self.assertNotIn("kex_strict", srv.attributes)               # version unknown offline

    def test_client_defaults_and_host_blocks(self):
        (cli,) = self.kind(AssetKind.SSH_CLIENT)
        ciphers = self.uses(cli, "Ciphers")
        dflt = [u for u in ciphers if u.extra.get("source") == "default"]
        self.assertTrue(dflt and all(u.negotiated is None for u in dflt))
        legacy = [u for u in ciphers if u.extra.get("host_block") == "host legacy"]
        self.assertEqual([u.raw for u in legacy], ["3des-cbc"])
        kex = [u for u in self.uses(cli, "KexAlgorithms") if u.extra.get("host_block") == "host legacy"]
        self.assertEqual([u.raw for u in kex], ["diffie-hellman-group1-sha1"])
        macs = [u.raw for u in self.uses(cli, "MACs")]
        self.assertEqual(macs, ["hmac-sha2-512-etm@openssh.com"])    # from ssh_config.d, Host *
        fp = [u for u in cli.uses if u.context == "ssh-fingerprint-hash"]
        self.assertEqual([u.raw for u in fp], ["sha256"])

    # -- keys -----------------------------------------------------------
    def test_host_keys(self):
        hk = {os.path.basename(a.location): a for a in self.kind(AssetKind.SSH_HOST_KEY) if "ssh_host_" in a.location}
        rsa = hk["ssh_host_rsa_key"]
        (u,) = rsa.uses
        self.assertEqual((u.algorithm, u.key_bits, u.context, u.primitive), ("rsa", 1024, "hostkey-material", Primitive.PUBLIC_KEY))
        self.assertEqual(rsa.attributes["mode"], 0o644)
        self.assertIs(rsa.attributes["encrypted"], False)
        self.assertEqual(rsa.attributes["fmt"], "openssh")
        ec = hk["ssh_host_ecdsa_key"].uses[0]
        self.assertEqual((ec.algorithm, ec.key_bits, ec.curve), ("ecdsa", 256, "p-256"))
        self.assertEqual(hk["ssh_host_ed25519_key"].uses[0].algorithm, "ed25519")
        self.assertEqual(hk["ssh_host_dsa_key"].uses[0].algorithm, "dsa")
        self.assertEqual(hk["ssh_host_dsa_key"].uses[0].key_bits, 1024)

    def test_user_keys(self):
        uk = {os.path.basename(a.location): a for a in self.kind(AssetKind.SSH_USER_KEY)}
        self.assertEqual(set(uk), {"id_rsa", "id_ed25519", "id_ecdsa.pub"})
        rsa = uk["id_rsa"]
        self.assertIs(rsa.attributes["encrypted"], True)
        self.assertIn("kdf=bcrypt", rsa.attributes["encryption_note"])
        self.assertEqual(rsa.uses[0].key_bits, 3072)
        self.assertEqual(uk["id_ed25519"].attributes["mode"], 0o640)
        self.assertIs(uk["id_ed25519"].attributes["encrypted"], False)
        self.assertNotIn("mode", uk["id_ecdsa.pub"].attributes)

    def test_authorized_keys_and_known_hosts(self):
        (ak,) = self.kind(AssetKind.SSH_AUTHORIZED_KEY)
        self.assertEqual([u.algorithm for u in ak.uses], ["rsa", "ed25519", "dsa"])
        self.assertEqual(ak.uses[0].key_bits, 1024)
        self.assertEqual(ak.uses[1].extra["options"], 'command="/bin/true",no-pty')
        self.assertEqual([u.extra["line"] for u in ak.uses], [2, 3, 4])
        self.assertTrue(any("unparsable" in e for e in ak.errors))
        kh = {os.path.basename(os.path.dirname(a.location)): a for a in self.kind(AssetKind.SSH_KNOWN_HOST)}
        user_kh = [a for a in self.kind(AssetKind.SSH_KNOWN_HOST) if a.location.endswith(".ssh/known_hosts")][0]
        self.assertEqual(len(user_kh.uses), 3)
        self.assertTrue(user_kh.uses[1].extra["hashed"])
        self.assertTrue(user_kh.uses[1].extra["hostname"].startswith("|1|"))
        self.assertEqual(user_kh.uses[1].curve, "p-384")
        self.assertEqual(user_kh.uses[2].extra["marker"], "@cert-authority")
        sysk = [a for a in self.kind(AssetKind.SSH_KNOWN_HOST) if a.location.endswith("ssh_known_hosts")][0]
        self.assertEqual(sysk.uses[0].extra["hostname"], "fixture.example.org,10.0.0.5")
        self.assertTrue(kh)

    def test_dropbear(self):
        db = [a for a in self.assets if a.attributes.get("software") == "dropbear"]
        self.assertEqual(len(db), 2)
        rsa = [a for a in db if a.attributes["key_type"] == "rsa"][0]
        self.assertEqual(rsa.uses[0].key_bits, 2048)

    # -- policy ---------------------------------------------------------
    def test_policy_rules(self):
        for rid in ("KX-SHA1", "SSH-RSA-SHA1", "SSH-WEAK-MODULI", "KEY-PERMS", "PK-RSA-LT-2048", "CIPHER-3DES",
                    "MAC-MD5", "PK-DSA", "CFG-SSH-FPR-MD5", "SSH-PROTOCOL-1", "KEY-UNENCRYPTED"):
            self.assertIn(rid, self.ids, rid)
        perms = [f for f in self.findings if f.rule_id == "KEY-PERMS"]
        self.assertTrue(any(f.location.endswith("ssh_host_rsa_key") for f in perms))
        self.assertTrue(any(f.location.endswith("id_ed25519") for f in perms))

    def test_missing_ssh_is_quiet(self):
        with tempfile.TemporaryDirectory() as d:
            ctx = ScanContext(root=d, options={"home_dirs": []})
            self.assertEqual(SSHLocalCollector().collect(ctx), [])

    def test_extra_paths(self):
        with tempfile.TemporaryDirectory() as d:
            shutil.copy(os.path.join(FIX, "home", "alice", ".ssh", "id_rsa.pub"), os.path.join(d, "foo.pub"))
            ctx = ScanContext(root=d, options={"home_dirs": []}, extra_paths=[d])
            (a,) = SSHLocalCollector().collect(ctx)
            self.assertEqual(a.kind, AssetKind.SSH_USER_KEY)
            self.assertEqual(a.uses[0].key_bits, 3072)


if __name__ == "__main__":
    unittest.main()
