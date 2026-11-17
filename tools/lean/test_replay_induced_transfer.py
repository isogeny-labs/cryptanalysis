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


if __name__ == "__main__":
    unittest.main()
