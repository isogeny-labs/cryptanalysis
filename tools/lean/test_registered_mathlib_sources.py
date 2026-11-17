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

    def test_namespace_resolution_keeps_original_query_and_exact_native_name(self):
        rows = gate.registered_mathlib_sources()
        row = next(row for path, row in rows.items() if path.endswith('/RankOneCoordinate.lean'))
        self.assertEqual(row['requested'], ['no_rank_gap_at_centered_slope'])
        self.assertEqual(row['native_names'], ['XedniRankOneCoordinate.no_rank_gap_at_centered_slope'])

    def test_compiled_checks_receive_fully_qualified_names(self):
        rows = gate.registered_mathlib_sources()
        with mock.patch.object(gate, 'check_known_label_project_inputs'), \
             mock.patch.object(gate, 'run', return_value=mock.Mock(stdout='cache')), \
             mock.patch.object(gate, 'check_pinned_mathlib_source', return_value='checked') as check:
            gate.check_registered_mathlib_sources(set(rows))
        actual = {call.args[0]: call.kwargs['exact_names'] for call in check.call_args_list}
        for path, row in rows.items():
            if row['role'] == 'mathlib-proof':
                self.assertEqual(actual[path], frozenset(row['native_names']))

    def test_missing_duplicate_and_unrelated_native_names_are_rejected(self):
        row = next(row for row in self.record['sources'].values() if row['role'] == 'mathlib-proof')
        for names in [[], ['unrelated'] * len(row['requested']), [row['requested'][0]] * len(row['requested'])]:
            row['native_names'] = names
            self.write_manifest()
            with self.assertRaisesRegex(ValueError, 'native theorem identities'):
                gate.registered_mathlib_sources()

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
