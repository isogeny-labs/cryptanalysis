#!/usr/bin/env python3
"""J3 gate probes. Mocked compiler/auditor output is not native Lean evidence."""
import contextlib
import fnmatch
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

BASE = Path('/var/tmp/cryptanalysis-known-label-review-20261028')
OUT = Path(__file__).resolve().parent
os.environ['TMPDIR'] = str(OUT / 'tmp')
tempfile.tempdir = str(OUT / 'tmp')
spec = importlib.util.spec_from_file_location('gate_probe', BASE / 'tools/lean/current-corpus-gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
PROJECT = gate.HECKE_CI.relative_to(BASE)
NAMES = sorted(gate.KNOWN_LABEL_THEOREMS)
PRINTED = ''.join(f"'{name}' depends on axioms: [propext, Quot.sound]\n" for name in NAMES)
AUDITED = ''.join(f'ok    {name}  [propext, Quot.sound]\n' for name in NAMES)
AUDITED += 'audited 4 theorems; 0 failing, 0 trusted\n'
results = []


def probe(name, *, setup=None, mutate_stage=None, mutate_file=None,
          printed=PRINTED, audited=AUDITED, wrong_path=False, audit_exit=0):
    with tempfile.TemporaryDirectory(prefix='probe-', dir=OUT / 'tmp') as temporary:
        root = Path(temporary)
        project = root / PROJECT
        project.mkdir(parents=True)
        for file in gate.KNOWN_LABEL_PROJECT_INPUTS:
            shutil.copyfile(BASE / PROJECT / file, project / file)
        source = root / gate.KNOWN_LABEL_SOURCE
        source.parent.mkdir(parents=True)
        shutil.copyfile(BASE / gate.KNOWN_LABEL_SOURCE, source)
        if setup:
            setup(source, project)
        calls = []
        native_modules = []

        def subprocess_stub(args, **kwargs):
            stage = 'build' if args[:3] == ['lake', 'env', 'lean'] else 'audit'
            calls.append(stage)
            if stage == mutate_stage:
                changed = source if mutate_file == 'source' else project / mutate_file
                changed.write_bytes(changed.read_bytes() + b'\n')
            if stage == 'build':
                output = Path(args[args.index('-o') + 1])
                native_modules.append({
                    'path': str(output.relative_to(OUT)),
                    'private_output_outside_fixture_root': not output.is_relative_to(root),
                    'source_argument_is_original': args[-1] == str(source),
                })
                return subprocess.CompletedProcess(args, 0, printed, '')
            native_modules[-1]['audited_module'] = args[-1]
            native_modules[-1]['private_search_prefix'] = kwargs['env']['LEAN_PATH'].split(os.pathsep)[0]
            return subprocess.CompletedProcess(args, audit_exit, audited, 'audit failed' if audit_exit else '')

        with patch.object(gate, 'ROOT', root), patch.object(gate, 'HECKE_CI', project), \
                contextlib.redirect_stdout(io.StringIO()):
            try:
                if wrong_path:
                    with patch.object(gate, 'reviewed_quartic_sources', return_value={}), \
                            patch.object(gate, 'run', return_value=SimpleNamespace(stdout='dependencies\n')):
                        value = gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE.replace('Algebra.lean', 'Other.lean')})
                else:
                    with patch.object(gate.subprocess, 'run', side_effect=subprocess_stub):
                        value = gate.check_known_label_algebra('dependencies')
                result = {'case': name, 'decision': 'accepted', 'returned': value}
            except ValueError as exc:
                result = {'case': name, 'decision': 'refused', 'error': str(exc)}
        result['native_calls_mocked'] = calls
        result['source_hash_matches'] = gate.digest(source) == gate.KNOWN_LABEL_SHA256
        result['project_hashes_match'] = {
            file: gate.digest(project / file) == expected
            for file, expected in gate.KNOWN_LABEL_PROJECT_INPUTS.items()
        }
        if name == 'baseline':
            result['module_command_observations'] = native_modules
        results.append(result)


probe('baseline')
probe('wrong_path', wrong_path=True)
probe('changed_source_hash', setup=lambda source, project: source.write_bytes(source.read_bytes() + b'\n'))
probe('wrong_printed_namespace', printed=PRINTED.replace('KnownLabelLeads.', 'Other.'))
probe('wrong_audited_namespace', audited=AUDITED.replace('KnownLabelLeads.', 'Other.'))
probe('empty_audit', audited='')
probe('zero_audit', audited='audited 0 theorems; 0 failing, 0 trusted\n')
probe('nonstandard_printed_axiom', printed=PRINTED.replace('Quot.sound', 'sorryAx'))
probe('native_auditor_nonzero', audit_exit=1)
probe('source_mutated_during_audit', mutate_stage='audit', mutate_file='source')
for file in gate.KNOWN_LABEL_PROJECT_INPUTS:
    probe('prechanged_' + file, setup=lambda source, project, file=file:
          (project / file).write_bytes((project / file).read_bytes() + b'\n'))
    for stage in ('build', 'audit'):
        probe(file + '_mutated_during_' + stage, mutate_stage=stage, mutate_file=file)

# The parser relies on the native auditor's exit code/summary integrity.
# This contradictory stdout cannot be produced by the declared auditor on success.
probe('contradictory_stdout_from_untrusted_auditor', audited='FAIL  forged  non-standard axioms: [sorryAx]\n' + AUDITED)

try:
    gate.run([sys.executable, '-c', 'import sys; sys.exit(7)'], cwd=OUT)
    results.append({'case': 'actual_nonzero_subprocess', 'decision': 'accepted'})
except ValueError as exc:
    results.append({'case': 'actual_nonzero_subprocess', 'decision': 'refused', 'error': str(exc)})

workflow = (BASE / '.github/workflows/lean-proof-gate.yml').read_text()
routes = {}
for event, end in [('pull_request', 'push'), ('push', 'workflow_dispatch')]:
    block = workflow.split('  ' + event + ':', 1)[1].split('  ' + end + ':', 1)[0]
    patterns = re.findall(r"^      - '([^']+)'$", block, re.MULTILINE)
    routes[event] = {
        name: [pattern for pattern in patterns if fnmatch.fnmatchcase(str(PROJECT / name), pattern)]
        for name in gate.KNOWN_LABEL_PROJECT_INPUTS
    }
payload = {
    'schema': 'known-label-j3-diagnostic/v1',
    'native_lean_run': False,
    'all_native_build_and_audit_outputs_mocked': True,
    'cases': results,
    'workflow_event_pattern_matches': routes,
    'known_label_alone_satisfies_hecke_detector': gate.KNOWN_LABEL_SOURCE.startswith('experiments/hecke-') and '/formal/' in gate.KNOWN_LABEL_SOURCE,
}
(OUT / 'diagnostic-output.json').write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n')
print(json.dumps(payload, indent=2, sort_keys=True))
