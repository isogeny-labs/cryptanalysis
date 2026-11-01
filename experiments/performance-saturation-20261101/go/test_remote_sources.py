#!/usr/bin/env python3
"""Hermetic regressions for source identity in shallow remote checkouts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


remote = load("go_remote_ab_sources", "run_remote_ab.py")


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True
    ).strip()


class RemoteSourceIdentityTests(unittest.TestCase):
    def test_combined_mode_is_available_without_prefrozen_binary_hashes(self) -> None:
        options = remote.arguments([
            "--mode", "combined",
            "--out", "unused",
            "--phase", "fixed-peer-key-ab-v8",
            "--protocol-sha256", "0" * 64,
        ])
        self.assertEqual(options.mode, "combined")
        self.assertIsNone(options.baseline_binary_sha256)
        self.assertIsNone(options.candidate_binary_sha256)

    def test_fixed_peer_key_wrapper_binds_exact_source_objects(self) -> None:
        sys.path.insert(0, str(HERE))
        try:
            wrapper = load("go_remote_peer_key_binding", "run_remote_peer_key_ab.py")
        finally:
            sys.path.remove(str(HERE))
        bound = wrapper.runner
        self.assertEqual(
            bound.BASELINE_COMMIT,
            "7c712913b7e912494e87c35e854cfd0129bad89c",
        )
        self.assertEqual(
            bound.CANDIDATE_COMMIT,
            "37b96362a53a7364dd4cc2a18f450a3627ec08d3",
        )
        self.assertEqual(bound.CANDIDATE_PARENT, bound.BASELINE_COMMIT)
        self.assertEqual(
            bound.CANDIDATE_DIFF_SHA256,
            "e29818ed168eaa886dfdc4be3c90777b1026b89246b760fd76d31614f33e8417",
        )
        self.assertEqual(
            bound.COMMON_TEST_BLOB,
            "b487d974638f5fe81a2921fa002b8ce481b956ad",
        )
        self.assertEqual(
            bound.COMMON_TEST_SHA256,
            "4bf65f9fa27f46e04d287e8fc49ce33d00e9fb74e176a25677b04d9f883e35b8",
        )

    def test_reads_recorded_parent_without_parent_object_in_shallow_clone(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            shallow = root / "shallow"
            subprocess.run(["git", "init", "--quiet", str(source)], check=True)
            git(source, "config", "user.name", "Hermetic Test")
            git(source, "config", "user.email", "test@example.invalid")

            tracked = source / "tracked.txt"
            tracked.write_text("parent\n", encoding="utf-8")
            git(source, "add", "tracked.txt")
            git(source, "commit", "--quiet", "-m", "parent")
            parent = git(source, "rev-parse", "HEAD")

            tracked.write_text("child\n", encoding="utf-8")
            git(source, "commit", "--quiet", "-am", "child")
            child = git(source, "rev-parse", "HEAD")
            subprocess.run(
                [
                    "git", "clone", "--quiet", "--depth=1",
                    source.resolve().as_uri(), str(shallow),
                ],
                check=True,
            )

            self.assertTrue((shallow / ".git/shallow").is_file())
            self.assertNotEqual(
                subprocess.run(
                    ["git", "-C", str(shallow), "cat-file", "-e", parent],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                ).returncode,
                0,
            )
            # This was the v4 failure mode: pretty %P respects the shallow
            # boundary and hides the parent even though its id is recorded.
            self.assertEqual(git(shallow, "show", "-s", "--format=%P", child), "")
            self.assertEqual(remote.commit_parents(shallow, child), [parent])
            remote.ensure_commit(shallow, child)


if __name__ == "__main__":
    unittest.main()
