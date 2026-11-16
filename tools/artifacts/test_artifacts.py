"""End-to-end tests for tools/artifacts against a file:// remote in a scratch repository.

    python3 -m unittest tools/artifacts/test_artifacts.py
"""

import base64
from unittest import mock
import shlex
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "artifacts.py"
sys.path.insert(0, str(TOOL.parent))
import artifacts  # noqa: E402
import wire_workflows  # noqa: E402


def sh(cwd, *argv, check=True, env=None):
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, check=check, env=env)


class RoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name).resolve()
        self.repo, self.remote, self.cache = base / "repo", base / "remote", base / "cache"
        self.repo.mkdir()
        self.env = {**os.environ, "ARTIFACTS_REMOTE": f"file://{self.remote}", "ARTIFACTS_CACHE": str(self.cache),
                    "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                    "GIT_COMMITTER_EMAIL": "t@t"}
        sh(self.repo, "git", "init", "-q", "-b", "main")
        runs = self.repo / "research" / "r1" / "runs"
        runs.mkdir(parents=True)
        self.big = os.urandom(300_000)
        (runs / "a.jsonl").write_bytes(self.big)
        (runs / "weird [1]*.log").write_bytes(os.urandom(70_000))
        (runs / "small.jsonl").write_bytes(b"{}\n")        # under data_min_bytes: stays
        (self.repo / "research" / "r1" / "README.md").write_text("x" * 2_000_000)  # code ext: stays
        (self.repo / "research" / "r1" / "blob.unknown").write_bytes(os.urandom(1_100_000))  # > max_bytes
        self.git("add", "-A")
        self.git("commit", "-qm", "seed")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, *a):
        return sh(self.repo, "git", *a, env=self.env).stdout

    def art(self, *a, check=True, cwd=None):
        return sh(cwd or self.repo, sys.executable, str(TOOL), *a, check=check, env=self.env)

    def test_push_commit_clone_pull_verify(self):
        plan = self.art("plan").stdout
        self.assertIn("research/r1/runs/a.jsonl", plan)
        self.assertIn("research/r1/blob.unknown", plan)
        self.assertNotIn("small.jsonl", plan)
        self.assertNotIn("README.md", plan)

        self.art("push", "research")
        self.git("commit", "-qm", "move data to the store")
        tracked = self.git("ls-files").split("\n")
        self.assertNotIn("research/r1/runs/a.jsonl", tracked)
        self.assertIn("research/r1/runs/.artifacts.json", tracked)
        self.assertIn("research/r1/runs/small.jsonl", tracked)
        self.assertEqual(self.git("status", "--porcelain"), "")  # hydrated files are ignored

        digest = hashlib.sha256(self.big).hexdigest()
        self.assertTrue((self.remote / "sha256" / digest[:2] / digest).exists())
        m = json.loads((self.repo / "research/r1/runs/.artifacts.json").read_text())
        self.assertEqual(m["files"]["a.jsonl"], {"sha256": digest, "bytes": len(self.big)})

        # A fresh clone has pointers only; pull a subtree, then everything.
        clone = Path(self.tmp.name) / "clone"
        sh(self.tmp.name, "git", "clone", "-q", str(self.repo), str(clone))
        self.assertFalse((clone / "research/r1/runs/a.jsonl").exists())
        self.art("pull", "research/r1/runs/a.jsonl", cwd=clone)
        self.assertEqual((clone / "research/r1/runs/a.jsonl").read_bytes(), self.big)
        self.assertFalse((clone / "research/r1/blob.unknown").exists())
        self.art("pull", cwd=clone)
        self.assertTrue((clone / "research/r1/runs/weird [1]*.log").exists())
        self.assertEqual(self.art("verify", "--remote", cwd=clone).returncode, 0)
        self.assertEqual(sh(clone, "git", "status", "--porcelain").stdout, "")

        # CI can read a tracked manifest from the index while its directory is
        # absent from a sparse working tree. Pull must create that directory.
        sparse = Path(self.tmp.name) / "sparse-clone"
        sh(self.tmp.name, "git", "clone", "-q", str(self.repo), str(sparse))
        sh(sparse, "git", "sparse-checkout", "set", "--no-cone", "/*", "!/research/")
        self.assertFalse((sparse / "research").exists())
        self.art("pull", "research/r1/runs/a.jsonl", cwd=sparse)
        self.assertEqual((sparse / "research/r1/runs/a.jsonl").read_bytes(), self.big)

        # Editing a hydrated file in place is caught, and never corrupts the cache.
        (clone / "research/r1/runs/a.jsonl").write_bytes(b"tampered")
        self.assertEqual(self.art("verify", cwd=clone, check=False).returncode, 1)
        self.art("pull", cwd=clone)
        self.assertEqual((clone / "research/r1/runs/a.jsonl").read_bytes(), self.big)

    def test_corrupt_remote_object_is_refused(self):
        self.art("push", "research/r1/runs/a.jsonl")
        digest = hashlib.sha256(self.big).hexdigest()
        obj = self.remote / "sha256" / digest[:2] / digest
        obj.write_bytes(b"x" * len(self.big))
        os.remove(self.repo / "research/r1/runs/a.jsonl")
        for p in (self.cache / "sha256").rglob("*"):
            if p.is_file():
                p.chmod(0o644)
                p.unlink()
        r = self.art("pull", check=False)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("refused", r.stderr)
        self.assertFalse((self.repo / "research/r1/runs/a.jsonl").exists())

    def test_same_size_corrupt_cache_is_refetched_or_refused(self):
        self.art("push", "research/r1/runs/a.jsonl")
        digest = hashlib.sha256(self.big).hexdigest()
        cached = self.cache / "sha256" / digest[:2] / digest
        dest = self.repo / "research/r1/runs/a.jsonl"
        cached.chmod(0o644)
        cached.write_bytes(b"x" * len(self.big))
        dest.unlink()

        self.art("pull", "research/r1/runs/a.jsonl")
        self.assertEqual(dest.read_bytes(), self.big)
        self.assertEqual(cached.read_bytes(), self.big)

        cached.chmod(0o644)
        cached.write_bytes(b"x" * len(self.big))
        (self.remote / "sha256" / digest[:2] / digest).write_bytes(b"y" * len(self.big))
        dest.unlink()
        result = self.art("pull", "research/r1/runs/a.jsonl", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refused", result.stderr)
        self.assertFalse(dest.exists())

    def test_push_merges_existing_manifest_and_gitignore(self):
        (self.repo / "research/r1/runs/.gitignore").write_text("/tmp/\n")
        self.art("push", "research/r1/runs/a.jsonl")
        self.art("push", "research/r1/runs")
        gi = (self.repo / "research/r1/runs/.gitignore").read_text()
        self.assertTrue(gi.startswith("/tmp/\n"))
        self.assertEqual(gi.count(artifacts.BEGIN), 1)
        self.assertIn("/weird \\[1\\]\\*.log", gi)
        m = json.loads((self.repo / "research/r1/runs/.artifacts.json").read_text())
        self.assertEqual(sorted(m["files"]), ["a.jsonl", "weird [1]*.log"])

    def test_push_from_sparse_checkout_reads_blobs(self):
        (self.repo / "research/r1/runs/.gitignore").write_text("/keep-me/\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "gitignore")
        self.git("sparse-checkout", "set", "--no-cone", "/*", "!/research/")
        self.assertFalse((self.repo / "research").exists())
        self.art("push", "research")
        self.git("commit", "-qm", "move from sparse")
        self.git("sparse-checkout", "disable")
        gi = (self.repo / "research/r1/runs/.gitignore").read_text()
        self.assertTrue(gi.startswith("/keep-me/\n"))
        self.assertNotIn("research/r1/runs/a.jsonl", self.git("ls-files"))
        self.art("pull")
        self.assertEqual((self.repo / "research/r1/runs/a.jsonl").read_bytes(), self.big)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_pull_recreates_parent_outside_sparse_checkout(self):
        self.art("push", "research/r1/runs/a.jsonl")
        self.git("commit", "-qm", "move data to the store")
        target = self.repo / "research/r1/runs/a.jsonl"
        target.unlink()
        self.git("sparse-checkout", "set", "--no-cone", "/*", "!/research/")
        self.assertFalse((self.repo / "research").exists())

        result = self.art("pull", "research/r1/runs/a.jsonl", check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(target.read_bytes(), self.big)
        self.assertFalse((target.parent / ".artifacts.json").exists())

    def test_pull_into_absent_sparse_directory_preserves_bytes_and_clean_tree(self):
        self.art("push", "research/r1/runs/a.jsonl")
        self.git("commit", "-qm", "archive fixture")
        (self.repo / "research/r1/runs/a.jsonl").unlink()
        self.git("sparse-checkout", "set", "--no-cone", "/*", "!/research/")
        self.assertFalse((self.repo / "research").exists())
        self.art("pull", "research/r1/runs/a.jsonl")
        self.assertEqual((self.repo / "research/r1/runs/a.jsonl").read_bytes(), self.big)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_check_gate(self):
        base = self.git("rev-parse", "HEAD").strip()
        (self.repo / "new.jsonl").write_bytes(os.urandom(100_000))
        (self.repo / "tool.py").write_text("x = 1\n" * 300_000)
        self.git("add", "-A")
        self.git("commit", "-qm", "add data")
        r = self.art("check", base, check=False)
        self.assertEqual(r.returncode, 1)
        self.assertIn("new.jsonl", r.stdout)
        self.assertNotIn("tool.py", r.stdout)

        base = self.git("rev-parse", "HEAD").strip()
        self.art("push", "new.jsonl")
        self.git("commit", "-qm", "move it")
        self.assertEqual(self.art("check", base).returncode, 0)

    def test_pull_creates_missing_parent_in_blobless_sparse_clone(self):
        self.art("push", "research/r1/runs/a.jsonl")
        self.git("commit", "-qm", "move data into store")
        self.git("config", "uploadpack.allowFilter", "true")

        clone = Path(self.tmp.name) / "pull-blobless"
        sh(self.tmp.name, "git", "clone", "-q", "--filter=blob:none", "--sparse",
           self.repo.as_uri(), str(clone), env=self.env)
        dest = clone / "research/r1/runs/a.jsonl"
        self.assertFalse(dest.parent.exists())

        self.art("pull", "research/r1/runs/a.jsonl", cwd=clone)
        self.assertEqual(dest.read_bytes(), self.big)
        self.assertEqual(sh(clone, "git", "status", "--porcelain").stdout, "")

    def test_check_gate_in_blobless_sparse_clone(self):
        runs = self.repo / "research" / "r1" / "runs"
        (runs / "new.jsonl").write_bytes(os.urandom(100_000))
        self.git("add", "-A")
        self.git("commit", "-qm", "add data in an omitted directory")
        self.git("config", "uploadpack.allowFilter", "true")

        clone = Path(self.tmp.name) / "blobless"
        sh(self.tmp.name, "git", "clone", "-q", "--filter=blob:none", "--sparse",
           self.repo.as_uri(), str(clone), env=self.env)
        sh(clone, "git", "config", "core.abbrev", "7")
        self.assertFalse((clone / "research").exists())

        result = self.art("check", "HEAD^", "HEAD", check=False, cwd=clone)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("research/r1/runs/new.jsonl", result.stdout)
        self.assertNotIn("not a valid object name", result.stderr)
    def test_check_fetches_missing_blob_in_partial_clone(self):
        base = self.git("rev-parse", "HEAD").strip()
        outside = self.repo / "outside"
        outside.mkdir()
        (outside / "new.jsonl").write_bytes(os.urandom(90_000))
        self.git("add", "outside/new.jsonl")
        self.git("commit", "-qm", "add data outside checkout")
        blob = self.git("rev-parse", "HEAD:outside/new.jsonl").strip()
        self.git("config", "uploadpack.allowFilter", "true")
        clone = Path(self.tmp.name) / "partial"
        sh(self.tmp.name, "git", "clone", "--filter=blob:none", "--no-checkout",
           self.repo.as_uri(), str(clone), env=self.env)
        missing = sh(clone, "git", "rev-list", "--objects", "--all", "--missing=print",
                     env=self.env).stdout.splitlines()
        self.assertIn("?" + blob, missing)

        result = self.art("check", base, cwd=clone, check=False)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("outside/new.jsonl", result.stdout)
        self.assertIn("data file(s) belong in the store", result.stderr)

    def install_content_filter(self):
        # Public reversible fixture exercises Git's filter contract, not AES.
        script = Path(self.tmp.name) / "content_filter.py"
        script.write_text("import sys\nraw=sys.stdin.buffer.read()\n"
                          "if sys.argv[1]=='clean': out=b'FILTERED:'+raw.hex().encode()\n"
                          "else: out=bytes.fromhex(raw[9:].decode()) if raw.startswith(b'FILTERED:') else raw\n"
                          "sys.stdout.buffer.write(out)\n")
        command = shlex.quote(sys.executable) + " " + shlex.quote(str(script))
        self.git("config", "filter.fixture.clean", command + " clean")
        self.git("config", "filter.fixture.smudge", command + " smudge")
        self.git("config", "filter.fixture.required", "true")
        (self.repo / '.gitattributes').write_text('research/** filter=fixture\n')
        self.git('add', '.gitattributes')
        self.git('add', '--renormalize', 'research')
        self.git('commit', '-qm', 'public filter fixture')

    def test_sparse_offload_uses_filtered_plaintext_size_and_preserves_ignore(self):
        (self.repo / 'research/r1/runs/.gitignore').write_text('/keep-me/\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'ignore fixture')
        self.install_content_filter()
        self.git('sparse-checkout', 'set', '--no-cone', '/*', '!/research/')
        self.art('push', 'research/r1/runs/a.jsonl')
        digest = hashlib.sha256(self.big).hexdigest()
        self.assertEqual((self.remote/'sha256'/digest[:2]/digest).read_bytes(), self.big)
        manifest=json.loads((self.repo/'research/r1/runs/.artifacts.json').read_text())
        self.assertEqual(manifest['files']['a.jsonl'], {'sha256':digest,'bytes':len(self.big)})
        self.assertTrue((self.repo/'research/r1/runs/.gitignore').read_text().startswith('/keep-me/\n'))

    def test_required_filter_failure_cannot_upload_raw_staged_bytes(self):
        self.install_content_filter()
        self.git('sparse-checkout', 'set', '--no-cone', '/*', '!/research/')
        self.git('config', 'filter.fixture.smudge', 'false')
        result=self.art('push', 'research/r1/runs/a.jsonl', check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo/'research/r1/runs/.artifacts.json').exists())
        self.assertFalse(list(self.remote.rglob('*')) if self.remote.exists() else [])
        self.assertFalse(list((self.cache/'tmp').glob('*')))

    def test_staged_metadata_filter_failure_is_not_absence(self):
        (self.repo / 'research/r1/runs/.gitignore').write_text('/keep-me/\n')
        self.git('add', '-A')
        self.git('commit', '-qm', 'ignore fixture')
        self.install_content_filter()
        self.git('sparse-checkout', 'set', '--no-cone', '/*', '!/research/')
        self.git('config', 'filter.fixture.smudge', 'false')
        with mock.patch.object(artifacts, 'repo_root', return_value=self.repo):
            with self.assertRaises(subprocess.CalledProcessError):
                artifacts.read_text_or_index(self.repo/'research/r1/runs/.gitignore')

    def test_pull_preserves_case_and_unicode_aliases_of_tracked_paths(self):
        self.art("push", "research/r1/runs/a.jsonl")
        directory = self.repo / "research/r1/runs"
        successor = b"current tracked successor\n"
        for source_name, alias in (("a.jsonl", "A.JSONL"), ("caf\u00e9.jsonl", "cafe\u0301.JSONL")):
            with self.subTest(alias=alias):
                source = directory / source_name
                source.write_bytes(successor)
                self.git("add", "-f", f"research/r1/runs/{source_name}")
                manifest = {"schema": artifacts.MANIFEST_SCHEMA, "files": {
                    alias: {"sha256": hashlib.sha256(self.big).hexdigest(), "bytes": len(self.big)}}}
                (directory / ".artifacts.json").write_text(json.dumps(manifest))
                self.git("add", "research/r1/runs/.artifacts.json")
                self.art("pull", "research")
                self.assertEqual(source.read_bytes(), successor)
                # Source ownership remains authoritative while sparse/omitted.
                source.unlink()
                self.art("pull", "research")
                self.assertFalse(source.exists())
                self.assertFalse((directory / alias).exists())

    def test_manifest_cannot_replace_linked_worktree_control_files(self):
        self.art("push", "research/r1/runs/a.jsonl")
        self.git("commit", "-qm", "store fixture")
        linked = Path(self.tmp.name) / "linked"
        self.git("worktree", "add", "-b", "linked-control", str(linked), "HEAD")
        original = (linked / ".git").read_bytes()
        for name in (".git", ".GIT", ".git ", ".git.", ".git::$DATA",
                     ".artifacts.json", ".gitignore", ".gitattributes"):
            with self.subTest(name=name):
                manifest = {"schema": artifacts.MANIFEST_SCHEMA, "files": {
                    name: {"sha256": hashlib.sha256(self.big).hexdigest(), "bytes": len(self.big)}}}
                (linked / ".artifacts.json").write_text(json.dumps(manifest))
                sh(linked, "git", "add", ".artifacts.json", env=self.env)
                result = self.art("pull", cwd=linked, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid manifest entry", result.stderr)
                self.assertEqual((linked / ".git").read_bytes(), original)

    def test_pull_preserves_tracked_successor_and_unstaged_edits(self):
        self.art("push", "research")
        path = self.repo / "research/r1/runs/a.jsonl"
        successor = b"current authoritative tracked successor\n"
        path.write_bytes(successor)
        self.git("add", "-f", "research/r1/runs/a.jsonl")
        # Siblings still hydrate, while the staged successor stays authoritative.
        sibling = self.repo / "research/r1/blob.unknown"
        sibling.unlink()
        self.art("pull", "research")
        self.assertEqual(path.read_bytes(), successor)
        self.assertTrue(sibling.is_file())
        edited = successor + b"local edit\n"
        path.write_bytes(edited)
        result = self.art("pull", "research/r1/runs/a.jsonl")
        self.assertEqual(path.read_bytes(), edited)
        self.assertIn("preserved 1 tracked files", result.stderr)
        # An omitted tracked path is also authoritative, not a hydration target.
        path.unlink()
        self.art("pull", "research/r1/runs/a.jsonl")
        self.assertFalse(path.exists())

    def test_manifest_paths_cannot_escape_their_directory(self):
        self.art("push", "research/r1/runs/a.jsonl")
        target = Path(self.tmp.name) / "escaped.jsonl"
        for name in ("../escaped.jsonl", "nested/file.jsonl", "..\\escaped.jsonl", "", ".", ".."):
            with self.subTest(name=name):
                manifest = {"schema": artifacts.MANIFEST_SCHEMA, "files": {
                    name: {"sha256": hashlib.sha256(self.big).hexdigest(), "bytes": len(self.big)}}}
                (self.repo / ".artifacts.json").write_text(json.dumps(manifest))
                self.git("add", ".artifacts.json")
                result = self.art("pull", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid manifest entry", result.stderr)
                self.assertFalse(target.exists())

    def test_manifest_metadata_is_validated_before_any_pull(self):
        for entry in ({"sha256": "0" * 64, "bytes": True},
                      {"sha256": "0" * 64, "bytes": -1},
                      {"sha256": "BAD", "bytes": 1}, None):
            with self.subTest(entry=entry):
                (self.repo / ".artifacts.json").write_text(json.dumps(
                    {"schema": artifacts.MANIFEST_SCHEMA, "files": {"data.jsonl": entry}}))
                self.git("add", ".artifacts.json")
                result = self.art("pull", check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("invalid manifest entry", result.stderr)

    def test_manifest_directory_symlink_cannot_redirect_hydration(self):
        self.art("push", "research/r1/runs/a.jsonl")
        directory = self.repo / "research/r1/runs"
        outside = Path(self.tmp.name) / "outside"
        directory.rename(outside)
        directory.symlink_to(outside, target_is_directory=True)
        target = outside / "a.jsonl"
        target.unlink()
        result = self.art("pull", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the repository", result.stderr)
        self.assertFalse(target.exists())

    def test_push_refuses_unmerged_index_without_changing_stages(self):
        path = "research/r1/runs/a.jsonl"
        oids = []
        for payload in (self.big, self.big + b"ours\n", self.big + b"theirs\n"):
            result = subprocess.run(["git", "hash-object", "-w", "--stdin"], cwd=self.repo,
                                    input=payload, capture_output=True, check=True, env=self.env)
            oids.append(result.stdout.decode().strip())
        self.assertEqual(len(set(oids)), 3)
        self.git("update-index", "--force-remove", path)
        rows = "".join(f"100644 {oid} {stage}\t{path}\n" for stage, oid in enumerate(oids, 1))
        subprocess.run(["git", "update-index", "--index-info"], cwd=self.repo,
                       input=rows, text=True, check=True, env=self.env)
        original_index = self.git("ls-files", "--stage")
        for arguments in (("push", path), ("push", "research"), ("push", "--dry-run", path)):
            with self.subTest(arguments=arguments):
                result = self.art(*arguments, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("unresolved Git index conflicts", result.stderr)
                self.assertEqual(self.git("ls-files", "--stage"), original_index)
                self.assertEqual((self.repo / path).read_bytes(), self.big)
                self.assertFalse(self.remote.exists())
                self.assertFalse((self.repo / "research/r1/runs/.artifacts.json").exists())





class Policy(unittest.TestCase):
    P = artifacts.DEFAULT_POLICY

    def test_rules(self):
        f = artifacts.belongs_in_store
        self.assertTrue(f("a/b.jsonl", 70_000, self.P))
        self.assertFalse(f("a/b.jsonl", 60_000, self.P))
        self.assertTrue(f("a/b.json", 2 << 20, self.P))
        self.assertFalse(f("a/b.json", 500_000, self.P))
        self.assertFalse(f("src/big.rs", 5 << 20, self.P))
        self.assertTrue(f("x/fb.tar.part-0001", 100_000, self.P))
        self.assertFalse(f("x/.artifacts.json", 5 << 20, self.P))
        self.assertFalse(f("docs/browser/data.json", 30 << 20, {**self.P, "keep": ["docs/browser/data.json"]}))


class S3Argv(unittest.TestCase):
    def setUp(self):
        cfg = artifacts.Config(root=Path("."), remote="s3://bucket/store", endpoint=None, read_url=None,
                               cache=Path("/c"), aws="aws")
        self.r = artifacts.Remote(cfg)
        self.d = hashlib.sha256(b"x").hexdigest()

    def test_layout_matches_crypto_store(self):
        self.assertEqual(self.r.key(self.d), f"store/sha256/{self.d[:2]}/{self.d}")

    def test_put_is_write_once_and_checksummed(self):
        a = self.r.put_args(self.d, Path("f"))
        self.assertEqual(a[a.index("--if-none-match") + 1], "*")
        self.assertEqual(a[a.index("--checksum-sha256") + 1], base64.b64encode(bytes.fromhex(self.d)).decode())
        self.assertEqual(a[a.index("--bucket") + 1], "bucket")

    def test_rejects_non_digest(self):
        with self.assertRaises(SystemExit):
            artifacts.object_key("../../etc/passwd")


class WorkflowPaths(unittest.TestCase):
    def test_unrelated_sibling_does_not_pull_whole_archive(self):
        moved = {"ecc2k130/research/runs/result.jsonl"}
        dirs = {"ecc2k130", "ecc2k130/research", "ecc2k130/research/runs"}
        text = "path: ecc2k130/build/cuda\nrun: ecc2k130/scripts/fetch_cuda.sh"
        self.assertEqual(wire_workflows.needed(text, moved, dirs), [])

    def test_named_file_and_directory_are_pulled(self):
        moved = {"research/runs/result.jsonl"}
        dirs = {"research", "research/runs"}
        self.assertEqual(wire_workflows.needed("run: cat research/runs/result.jsonl", moved, dirs),
                         ["research/runs/result.jsonl"])
        self.assertEqual(wire_workflows.needed("run: cat research/runs/*", moved, dirs),
                         ["research/runs"])



class WorkflowBootstrap(unittest.TestCase):
    def test_sparse_clone_can_load_tool_and_remote_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sh(root, "git", "init", "-q", "-b", "main")
            for name, content in {".github/scripts/scope.py": "", "tools/artifacts/artifacts.py": TOOL.read_text(), ".artifacts/config.json": '{"remote":"file:///test-store"}'}.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
            sh(root, "git", "add", ".")
            sh(root, "git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
            block = ["      - uses: actions/checkout@v4", "        with:", "          sparse-checkout: .github/scripts"]
            wired = wire_workflows.add_sparse_pattern(block, "      ")
            patterns = [line.strip() for line in wired[3:]]
            sh(root, "git", "sparse-checkout", "set", "--cone", *patterns)
            self.assertTrue((root / "tools/artifacts/artifacts.py").is_file())
            self.assertEqual(artifacts.Config.load(root).remote, "file:///test-store")

    def test_conditional_full_checkout_is_preserved(self):
        block = ["      - uses: actions/checkout@v4", "        with:", "          sparse-checkout: ${{ needs.changes.outputs.full_checkout != 'true' && env.SPARSE_RULES || '' }}", "          sparse-checkout-cone-mode: false"]
        self.assertEqual(wire_workflows.add_sparse_pattern(block, "      "), block)

    def test_rewiring_refreshes_paths_and_keeps_checkout_condition(self):
        source = "jobs:\n  test:\n    steps:\n      - uses: actions/checkout@v4\n        if: needs.changes.outputs.run == 'true'\n      - run: make check\n"
        once, _ = wire_workflows.wire(source, ["data/new"])
        self.assertEqual(once, wire_workflows.wire(once, ["data/new"])[0])
        stale = once.replace("pull --jobs 16 data/new", "pull data/old")
        self.assertEqual(once, wire_workflows.wire(stale, ["data/new"])[0])
        self.assertEqual(once.count("if: needs.changes.outputs.run == 'true'"), 2)
        self.assertIn("shell: bash", once)
        self.assertIn("working-directory: ${{ github.workspace }}", once)
        self.assertIn('export ARTIFACTS_AWS="$artifacts_cli_aws"', once)

class JobScopedWiring(unittest.TestCase):
    MOVED = {"research/runs/result.jsonl"}
    DIRS = {"research", "research/runs"}
    SOURCE = """# artifacts-scope: job
name: mixed workflow
jobs:
  source:
    steps:
      - uses: actions/checkout@v7
      - run: python3 research/check.py
  replay:
    steps:
      - uses: actions/checkout@v7

      - run: python3 replay.py research/runs/result.jsonl
"""

    def wired(self, source=None):
        return wire_workflows.wire_workflow(source or self.SOURCE, self.MOVED, self.DIRS)[0]

    def test_only_data_consuming_job_gets_a_pull(self):
        result = self.wired()
        source, replay = result.split("  replay:\n")
        self.assertNotIn(wire_workflows.STEP_NAME, source)
        self.assertIn("pull --jobs 16 research/runs/result.jsonl", replay)
        self.assertEqual(result.count(wire_workflows.STEP_NAME), 1)

    def test_new_source_job_data_dependency_requires_a_pull(self):
        changed = self.SOURCE.replace("research/check.py", "research/runs/result.jsonl")
        result = self.wired(changed)
        self.assertNotEqual(result, changed)
        self.assertEqual(result.count(wire_workflows.STEP_NAME), 2)

    def test_global_data_dependency_applies_to_every_job(self):
        source = self.SOURCE.replace("jobs:", "env:\n  INPUT: research/runs\njobs:", 1)
        self.assertEqual(self.wired(source).count(wire_workflows.STEP_NAME), 2)

    def test_stale_bootstrap_does_not_create_its_own_dependency(self):
        stale = wire_workflows.wire(self.SOURCE, ["research/runs"])[0]
        result = self.wired(stale)
        self.assertEqual(result, self.wired())
        self.assertEqual(result, self.wired(result))

    def test_conditional_checkout_keeps_pull_condition(self):
        source = self.SOURCE.replace("  replay:\n    steps:\n      - uses: actions/checkout@v7",
                                     "  replay:\n    steps:\n      - uses: actions/checkout@v7\n        if: needs.scope.outputs.replay == 'true'")
        self.assertEqual(source.count("if: needs.scope.outputs.replay == 'true'"), 1)
        result = self.wired(source)
        self.assertEqual(result.count("if: needs.scope.outputs.replay == 'true'"), 2)

    def test_unmarked_workflows_keep_legacy_wiring(self):
        source = self.SOURCE.replace("# artifacts-scope: job\n", "")
        paths = wire_workflows.needed(source, self.MOVED, self.DIRS)
        self.assertEqual(self.wired(source), wire_workflows.wire(source, paths)[0])
        self.assertEqual(self.wired(source).count(wire_workflows.STEP_NAME), 2)

    def test_unsupported_scope_structure_is_refused(self):
        for source in (self.SOURCE.replace("jobs:", "jobz:", 1),
                       self.SOURCE.replace("  source:", " source:"),
                       self.SOURCE.replace("  replay:", '  "replay":'),
                       self.SOURCE + "env:\n  INPUT: research/runs\n"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                self.wired(source)


if __name__ == "__main__":
    unittest.main()
