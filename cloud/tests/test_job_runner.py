"""Run cloud/job_runner.sh locally, the way Modal and the pods run it."""
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import tree  # noqa: E402
from test_tree import make_repo  # noqa: E402

RUNNER = HERE / "job_runner.sh"


def run_job(tmp, command, outs=(), changed=False, *, closed=False, path=None):
    repo = Path(tmp, "repo")
    repo.mkdir()
    data, _ = tree.pack(make_repo(repo))
    src = Path(tmp, "src.tar.gz")
    src.write_bytes(data)
    job_dir, workdir = Path(tmp, "job"), Path(tmp, "work")
    env = {**os.environ, "JOB_ID": "t1", "JOB_DIR": str(job_dir), "JOB_WORKDIR": str(workdir),
           "JOB_SRC": str(src), "JOB_CMD": command, "JOB_OUTS": "\n".join(outs),
           "JOB_CHANGED": "1" if changed else "0", "SHARD_INDEX": "2", "SHARD_COUNT": "4"}
    if closed:
        env["JOB_ENVIRONMENT_CLOSED"] = "1"
    if path is not None:
        env["PATH"] = path
    proc = subprocess.run(
        ["/usr/bin/bash" if closed else "bash", str(RUNNER)],
        env=env, capture_output=True, text=True,
    )
    return proc, job_dir


def outputs(job_dir):
    path = job_dir / "out.tar.gz"
    if not path.exists():
        return {}
    with tarfile.open(path) as tar:
        return {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}


class JobRunnerTest(unittest.TestCase):
    def test_closed_mode_uses_absolute_isolated_shell_and_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            shims = Path(tmp, "shims")
            shims.mkdir()
            for name in ("bash", "python3"):
                path = shims / name
                path.write_text("#!/bin/sh\nexit 91\n")
                path.chmod(0o755)
            proc, job_dir = run_job(
                tmp, 'test -z "${JOB_ENVIRONMENT_CLOSED:-}" && echo closed',
                closed=True, path=f"{shims}:/usr/bin:/bin",
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("closed", proc.stdout)
            self.assertEqual(
                json.loads((job_dir / "status.json").read_text())["returncode"], 0,
            )

    def test_exit_status_log_and_status_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, job_dir = run_job(tmp, 'echo "shard $SHARD_INDEX of $SHARD_COUNT"; exit 3')
            self.assertEqual(proc.returncode, 3)
            self.assertIn("shard 2 of 4", proc.stdout)
            self.assertIn("shard 2 of 4", (job_dir / "log.txt").read_text())
            status = json.loads((job_dir / "status.json").read_text())
            self.assertEqual((status["returncode"], status["shard"], status["shards"]), (3, 2, 4))
            self.assertGreaterEqual(status["cpus"], 1)

    def test_named_outputs_come_back_and_missing_ones_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, job_dir = run_job(
                tmp, "mkdir -p results && echo 1 > results/a.csv && echo 2 > results/b.csv",
                outs=["results", "absent.txt"])
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(outputs(job_dir), {"results/a.csv": b"1\n", "results/b.csv": b"2\n"})
            self.assertIn("output absent.txt was not produced", proc.stdout)

    def test_changed_returns_new_and_modified_files_but_not_build_trees(self):
        with tempfile.TemporaryDirectory() as tmp:
            command = ("echo new > fresh.txt && echo edited >> README && "
                       "mkdir -p build && echo obj > build/x.o")
            proc, job_dir = run_job(tmp, command, changed=True)
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(set(outputs(job_dir)), {"fresh.txt", "README"})

    def test_the_command_runs_in_the_unpacked_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, _ = run_job(tmp, "cat src/a.c notes.txt")
            self.assertIn("int a = 1;", proc.stdout)
            self.assertIn("untracked", proc.stdout)


if __name__ == "__main__":
    unittest.main()
