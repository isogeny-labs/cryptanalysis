import copy
import importlib.util
import tempfile
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("replay", Path(__file__).with_name("replay_induced_transfer.py"))
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class SourceGuards(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.roots = [root / p for p in ["current", "producer", "frozen", "frozen-producer"]]
        amendments = {}
        lines = []
        for name in sorted(replay.AMENDMENTS) + ["proof.lean", "../crypto/auditor.lean"]:
            old = ("original:" + name).encode()
            new = ("current:" + name).encode() if name in replay.AMENDMENTS else old
            for (repo, producer), data in [(self.roots[:2], new), (self.roots[2:], old)]:
                path = replay.source_path(repo, producer, name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            lines.append(replay.digest(old) + "  " + name)
            if name in replay.AMENDMENTS:
                amendments[name] = {"historical_sha256": replay.digest(old), "current_sha256": replay.digest(new)}
        reference = ("\n".join(lines) + "\n").encode()
        for repo in [self.roots[0], self.roots[2]]:
            path = repo / replay.REFERENCE
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(reference)
        self.contract = {"schema": "induced-transfer.dual-replay/v1", "historical_consumer": replay.HISTORICAL,
                         "producer": replay.PRODUCER, "historical_reference_sha256": replay.digest(reference), "verifier_amendments": amendments}

    def verify(self, contract=None):
        return replay.verify_files(*self.roots, contract or self.contract)

    def test_both_versions_are_checked(self):
        self.assertEqual(len(self.verify()), 8)
        (self.roots[2] / "tools/pcc/pcc.py").write_bytes(b"changed historical verifier")
        with self.assertRaisesRegex(ValueError, "historical sealed input"):
            self.verify()

    def test_current_verifier_cannot_drift_after_amendment(self):
        (self.roots[0] / "pcc/keyring.json").write_bytes(b"new trust key")
        with self.assertRaisesRegex(ValueError, "current sealed input"):
            self.verify()

    def test_proof_bytes_cannot_be_amended(self):
        contract = copy.deepcopy(self.contract)
        contract["verifier_amendments"]["proof.lean"] = {"historical_sha256": "0" * 64, "current_sha256": "1" * 64}
        with self.assertRaisesRegex(ValueError, "six explicitly amended"):
            self.verify(contract)

    def test_original_reference_cannot_be_rewritten(self):
        (self.roots[0] / replay.REFERENCE).write_text("replacement\n")
        with self.assertRaisesRegex(ValueError, "rewrote the frozen reference"):
            self.verify()

    def test_unamended_proof_and_producer_remain_exact(self):
        (self.roots[1] / "auditor.lean").write_bytes(b"changed producer")
        with self.assertRaisesRegex(ValueError, "current sealed input"):
            self.verify()

    def test_producer_pin_cannot_be_replaced(self):
        contract = copy.deepcopy(self.contract)
        contract["producer"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "original producer pin changed"):
            self.verify(contract)

    def test_no_source_path_escape(self):
        for path in ["/etc/passwd", "../other/file", "../crypto/../../file", "tools/../../file"]:
            with self.subTest(path=path), self.assertRaises(ValueError):
                replay.source_path(self.roots[0], self.roots[1], path)



# These controls isolate process lifecycle; the source guards have their own tests.
import json
import os
import signal
import subprocess
import sys
import time
import uuid


@unittest.skipUnless(hasattr(os, "killpg"), "requires POSIX process groups")
class ReplayInterruption(unittest.TestCase):
    DRIVER = r'''
from pathlib import Path
import importlib.util, json, shlex, signal, sys
from unittest import mock
source, root = Path(sys.argv[1]), Path(sys.argv[2])
final_failure = sys.argv[3] == "yes"
force_timeout = sys.argv[3] == "timeout"
spec = importlib.util.spec_from_file_location("lifecycle_replay", source)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
roots = {name: root / name for name in ("repo", "producer", "frozen", "frozen-producer")}
for p in roots.values(): p.mkdir()
contract = roots["repo"] / "tools/lean/induced-transfer-current-contract.json"
contract.parent.mkdir(parents=True)
contract.write_text(json.dumps({"producer": r.PRODUCER}))
reference = b"sealed lifecycle control\n"
p = roots["frozen"] / r.REFERENCE
p.parent.mkdir(parents=True)
p.write_bytes(reference)
script = roots["frozen"] / r.STUDY / "ci_induced_transfer/check-01.sh"
code = "from pathlib import Path; import os,sys,time; p=Path(sys.argv[1]); t=p.with_suffix('.ready'); t.write_text(str(os.getpid())); t.replace(p)\nwhile True: time.sleep(1)\n"
script.write_text("exec " + shlex.quote(sys.executable) + " -c " + shlex.quote(code) + " " + shlex.quote(str(root / "child.pid")) + "\n")
def head(path):
    if path == roots["frozen"]: return r.HISTORICAL
    if path in (roots["producer"], roots["frozen-producer"]): return r.PRODUCER
    return "c" * 40
calls = 0
def guards(*args):
    global calls
    calls += 1
    if final_failure and calls >= 2: raise ValueError("injected final guard failure")
    return []
before = {s: signal.getsignal(s) for s in (signal.SIGINT, signal.SIGTERM)}
sys.argv = [str(source), "--repo", str(roots["repo"]), "--producer", str(roots["producer"]),
            "--frozen-consumer", str(roots["frozen"]), "--frozen-producer", str(roots["frozen-producer"]),
            "--out", str(root / "out")]
original_wait = r.subprocess.Popen.wait
def limited_wait(self, timeout=None):
    return original_wait(self, timeout=3 if force_timeout and timeout == 1500 else timeout)
with mock.patch.object(r.subprocess.Popen, "wait", new=limited_wait), mock.patch.object(r, "head", side_effect=head), mock.patch.object(r, "verify_files", side_effect=guards), mock.patch.object(r.subprocess, "check_output", return_value=reference):
    code = r.main()
(root / "handlers-restored.json").write_text(json.dumps({str(s): signal.getsignal(s) == h for s, h in before.items()}))
raise SystemExit(code)
'''

    @staticmethod
    def alive(pid):
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        return True

    def trial(self, signum, final_failure=False):
        source = Path(__file__).with_name("replay_induced_transfer.py")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            driver = root / "driver.py"
            driver.write_text(self.DRIVER)
            proc = subprocess.Popen([sys.executable, str(driver), str(source), str(root),
                                     "timeout" if signum is None else "yes" if final_failure else "no"],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    start_new_session=True)
            pid = None
            try:
                deadline = time.monotonic() + 10
                while not (root / "child.pid").exists():
                    if proc.poll() is not None:
                        self.fail("control exited before its child: " + proc.communicate()[1].decode())
                    self.assertLess(time.monotonic(), deadline, "control child did not start")
                    time.sleep(0.01)
                pid = int((root / "child.pid").read_text())
                self.assertEqual(os.getpgid(pid), pid)
                if signum is not None:
                    proc.send_signal(signum)
                stdout, stderr = proc.communicate(timeout=15)
                living = self.alive(pid)
                receipt = json.loads((root / "out/dual-replay.json").read_text())
                restored = json.loads((root / "handlers-restored.json").read_text()) if (root / "handlers-restored.json").exists() else {}
                record = {"signal": int(signum) if signum is not None else None, "parent_exit": proc.returncode,
                          "child_alive_after_interrupt": living, "receipt": receipt,
                          "handlers_restored": restored, "stderr": stderr.decode(),
                          "scope": "disposable lifecycle control with mocked source guards"}
                if os.environ.get("REPLAY_CONTROL_RECEIPTS"):
                    dest = Path(os.environ["REPLAY_CONTROL_RECEIPTS"])
                    dest.mkdir(parents=True, exist_ok=True)
                    (dest / (self.id().rsplit(".", 1)[-1] + "-" + uuid.uuid4().hex + ".json")).write_text(json.dumps(record, indent=2) + "\n")
                return record
            finally:
                if pid is not None and self.alive(pid):
                    try:
                        if os.getpgid(pid) == pid:
                            os.killpg(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if proc.poll() is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.communicate(timeout=5)

    def check_interruption(self, signum):
        record = self.trial(signum)
        self.assertFalse(record["child_alive_after_interrupt"], record)
        self.assertEqual(record["parent_exit"], 128 + signum, record)
        self.assertEqual(record["receipt"]["status"], "interrupted")
        self.assertEqual(record["receipt"]["phases"][0]["status"], "interrupted")
        self.assertTrue(all(record["handlers_restored"].values()))
        self.assertEqual(len(record["handlers_restored"]), 2)

    def test_sigint_stops_phase_child_and_records_interruption(self):
        self.check_interruption(signal.SIGINT)

    def test_sigterm_stops_phase_child_and_records_interruption(self):
        self.check_interruption(signal.SIGTERM)

    def test_phase_timeout_keeps_failure_and_cleans_child(self):
        record = self.trial(None)
        self.assertFalse(record["child_alive_after_interrupt"], record)
        self.assertEqual(record["parent_exit"], 1, record)
        self.assertEqual(record["receipt"]["status"], "fail")
        self.assertEqual(record["receipt"]["phases"][0]["status"], "timeout")

    def test_final_guard_failure_remains_failure_after_interruption(self):
        record = self.trial(signal.SIGINT, final_failure=True)
        self.assertFalse(record["child_alive_after_interrupt"], record)
        self.assertEqual(record["parent_exit"], 1, record)
        self.assertEqual(record["receipt"]["status"], "fail")
        self.assertIn("injected final guard failure", record["receipt"]["final_source_guard_error"])


if __name__ == "__main__":
    unittest.main()
