import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('dispositions', Path(__file__).with_name('check_source_dispositions.py'))
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)


class SourceDispositionControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        source = self.root / 'proof/Example.lean'
        source.parent.mkdir()
        source.write_text('theorem example : True := True.intro\n')
        inputs = {}
        for name in ('tools/lean/proof-gate.sh', 'tools/lean/AuditAxioms.lean', 'tools/lean/trusted-native.txt'):
            f = self.root / name
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text('native verifier fixture\n')
            inputs[name] = hashlib.sha256(f.read_bytes()).hexdigest()
        self.record = dict(schema='cryptanalysis.lean-source-dispositions/v1', toolchain=d.TOOLCHAIN,
                           source_commit='1' * 40, verifier_inputs=inputs, groups=[dict(role='core-proof',
                           sha256=hashlib.sha256(source.read_bytes()).hexdigest(), paths=['proof/Example.lean'], theorems=['example'])])

    def test_exact_sources_and_verifier_inputs_are_bound(self):
        self.assertEqual(d.validate(self.root, self.record), {'proof/Example.lean'})

    def test_changed_source_cannot_keep_its_disposition(self):
        (self.root / 'proof/Example.lean').write_text('axiom example : False\n')
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            d.validate(self.root, self.record)

    def test_missing_theorem_identity_is_rejected(self):
        self.record['groups'][0]['theorems'] = []
        with self.assertRaisesRegex(ValueError, 'theorem identities'):
            d.validate(self.root, self.record)

    def test_proof_cannot_be_reclassified_as_an_archive(self):
        for role in ('archived-no-theorems', 'archived-build-failure', 'archived-verifier-input'):
            with self.subTest(role=role):
                r = copy.deepcopy(self.record)
                r['groups'][0].update(role=role, diagnostic='original failure')
                with self.assertRaisesRegex(ValueError, 'outside an evidence'):
                    d.validate(self.root, r)

    def test_duplicate_paths_and_escape_paths_are_rejected(self):
        for paths in (['proof/Example.lean'] * 2, ['../Example.lean'], ['/Example.lean']):
            with self.subTest(paths=paths):
                r = copy.deepcopy(self.record)
                r['groups'][0]['paths'] = paths
                with self.assertRaisesRegex(ValueError, 'invalid or duplicate'):
                    d.validate(self.root, r)

    def test_unrecognized_verifier_archive_is_not_exempt(self):
        self.record['groups'][0].update(role='archived-verifier-input', paths=['unrelated/evidence/Example.lean'])
        with self.assertRaisesRegex(ValueError, 'missing or escapes|unrecognized'):
            d.validate(self.root, self.record)

    def test_changed_or_omitted_native_verifier_binding_is_rejected(self):
        (self.root / 'tools/lean/AuditAxioms.lean').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'verifier input changed'):
            d.validate(self.root, self.record)
        self.record['verifier_inputs'].pop('tools/lean/AuditAxioms.lean')
        with self.assertRaisesRegex(ValueError, 'incomplete native verifier'):
            d.validate(self.root, self.record)

    def test_unpinned_revision_and_unknown_role_fail_closed(self):
        self.record['source_commit'] = 'main'
        with self.assertRaisesRegex(ValueError, 'immutable'):
            d.validate(self.root, self.record)
        self.record['source_commit'] = '1' * 40
        self.record['groups'][0]['role'] = 'skip'
        with self.assertRaisesRegex(ValueError, 'unknown source disposition'):
            d.validate(self.root, self.record)


if __name__ == '__main__':
    unittest.main()
