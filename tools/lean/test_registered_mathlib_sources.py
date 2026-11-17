import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('corpus', Path(__file__).with_name('current-corpus-gate.py'))
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class RegisteredMathlibControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = Path('tools/lean/registered-mathlib-sources-20261117.json')
        self.record = json.loads((gate.ROOT / self.manifest).read_text())
        paths = {self.manifest}
        for path, row in self.record['sources'].items():
            paths.add(Path(path))
            paths.update(map(Path, row['project_inputs']))
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((gate.ROOT / path).read_bytes())
        patch = mock.patch.object(gate, 'ROOT', self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def write_manifest(self):
        (self.root / self.manifest).write_text(json.dumps(self.record))

    def test_original_sources_projects_and_queries_are_bound(self):
        self.assertEqual(len(gate.registered_mathlib_sources()), 5)

    def test_changed_source_and_build_inputs_fail_closed(self):
        source, row = next(iter(self.record['sources'].items()))
        for name in [source, *row['project_inputs']]:
            with self.subTest(path=name):
                file = self.root / name
                old = file.read_bytes()
                file.write_bytes(old + b'\n-- changed\n')
                with self.assertRaisesRegex(ValueError, 'source changed|project input changed'):
                    gate.registered_mathlib_sources()
                file.write_bytes(old)

    def test_registered_proofs_cannot_be_downgraded_to_verifier_code(self):
        row = next(row for row in self.record['sources'].values() if row['role'] == 'mathlib-proof')
        row['role'] = 'verifier-program'
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'cannot be reclassified'):
            gate.registered_mathlib_sources()

    def test_dependency_pin_changes_are_not_silent(self):
        self.record['mathlib_revision'] = '0' * 40
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'dependency pins'):
            gate.registered_mathlib_sources()

    def test_dropped_project_binding_and_substituted_requests_are_rejected(self):
        source, row = next(iter(self.record['sources'].items()))
        row['project_inputs'].pop(str(Path(source).parent / 'lean-toolchain'))
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'inputs incomplete'):
            gate.registered_mathlib_sources()
        row['project_inputs'][str(Path(source).parent / 'lean-toolchain')] = '0' * 64
        self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'project input changed'):
            gate.registered_mathlib_sources()


if __name__ == '__main__':
    unittest.main()
