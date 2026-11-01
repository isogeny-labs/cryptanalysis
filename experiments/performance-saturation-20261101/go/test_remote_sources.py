#!/usr/bin/env python3
"""Hermetic regressions for source identity in shallow remote checkouts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
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
