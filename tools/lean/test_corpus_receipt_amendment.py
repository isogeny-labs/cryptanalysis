import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("amendment", Path(__file__).with_name("check_corpus_receipt_amendment.py"))
amendment = importlib.util.module_from_spec(spec)
spec.loader.exec_module(amendment)


class ReceiptAmendmentControls(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in (amendment.OLD, amendment.NEW, amendment.BINDING):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((amendment.ROOT / name).read_bytes())

    def mutate(self, name, change):
        path = self.root / name
        data = json.loads(path.read_bytes())
        change(data)
        path.write_text(json.dumps(data))

    def test_exact_source_amendment_is_accepted(self):
        amendment.check(self.root)

    def test_historical_receipt_cannot_be_rewritten(self):
        self.mutate(amendment.OLD, lambda d: d.update(scope="changed history"))
        with self.assertRaisesRegex(ValueError, "historical corpus receipt changed"):
            amendment.check(self.root)

    def test_theorem_evidence_and_counts_cannot_be_rebaselined(self):
        for field in ("glv_theorems", "glv_selector_negative_controls", "glv_axiom_stdout_sha256"):
            with self.subTest(field=field):
                (self.root / amendment.NEW).write_bytes((amendment.ROOT / amendment.NEW).read_bytes())
                self.mutate(amendment.NEW, lambda d: d["fresh_native_evidence"].update({field: "changed"}))
                with self.assertRaisesRegex(ValueError, "more than the three"):
                    amendment.check(self.root)

    def test_current_binding_cannot_drop_original_source(self):
        self.mutate(amendment.BINDING, lambda d: d.update(previous_live_source_commit="0" * 40))
        with self.assertRaisesRegex(ValueError, "lost the historical"):
            amendment.check(self.root)

    def test_current_source_expectation_must_match_binding(self):
        self.mutate(amendment.NEW, lambda d: d["fresh_native_evidence"].update(glv_live_source_sha256="0" * 64))
        with self.assertRaisesRegex(ValueError, "more than the three"):
            amendment.check(self.root)


if __name__ == "__main__":
    unittest.main()
