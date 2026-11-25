#!/usr/bin/env python3
"""Read only allowlisted producer inputs; execute bounded mock software controls."""
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
from unittest.mock import patch

ROOT = Path('/home/ec2-user/cryptanalysis-known-label-review-20261029')
OUT = Path(__file__).resolve().parent
HANDOFF = 'reports/known-label-formal-review-20261028/handoff-J3-v3.json'
handoff = json.loads((ROOT / HANDOFF).read_text())
allowed = [HANDOFF] + handoff['allowed_read_paths']
assert len(allowed) == len(set(allowed))
inputs = json.loads((ROOT / 'reports/known-label-formal-review-20261028/inputs-v3.json').read_text())
ledger = []
for name in allowed:
    data = (ROOT / name).read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    expected = inputs['source_sha256'].get(name)
    assert expected is None or expected == actual, name
    ledger.append({'path': str(ROOT / name), 'relative_path': name, 'sha256_before': actual,
                   'bytes': len(data), 'expected_sha256': expected,
                   'manifest_match': actual == expected if expected else None})
(OUT / 'source-ledger-initial.json').write_text(json.dumps(ledger, indent=2) + '\n')

spec = importlib.util.spec_from_file_location('j3_gate', ROOT / 'tools/lean/current-corpus-gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
PROJECT = gate.HECKE_CI.relative_to(ROOT)
NAMES = sorted(gate.KNOWN_LABEL_THEOREMS)
PRINTED = ''.join(f"'{name}' depends on axioms: [propext, Quot.sound]\n" for name in NAMES)
def audit(names=NAMES):
    return ''.join(f'ok    {name}  [propext, Quot.sound]\n' for name in names) + f'audited {len(names)} theorems; 0 failing, 0 trusted\n'
AUDIT = audit()
cases = []

def control(name, expected, *, printed=PRINTED, audited=AUDIT, prechange=None,
            mutate=None, compile_exit=0, audit_exit=0, route='direct', transient=False):
    with tempfile.TemporaryDirectory(prefix=name + '-', dir=OUT / 'tmp') as tmp:
        root = Path(tmp)
        project = root / PROJECT
        project.mkdir(parents=True)
        source = root / gate.KNOWN_LABEL_SOURCE
        source.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / gate.KNOWN_LABEL_SOURCE, source)
        for filename in gate.KNOWN_LABEL_PROJECT_INPUTS:
            shutil.copyfile(ROOT / PROJECT / filename, project / filename)
        manifest = root / 'tools/ci/quartic_certificates.json'
        manifest.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'tools/ci/quartic_certificates.json', manifest)
        if prechange:
            prechange(root, project, source)
        commands = []
        originals = {}
        def runtime(args, **kwargs):
            phase = 'environment' if args[:3] == ['lake', 'env', 'printenv'] else ('audit' if args[:2] == ['lean', '--run'] else 'compile')
            commands.append({'phase': phase, 'args': [str(a) for a in args],
                             'cwd': str(kwargs.get('cwd')),
                             'lean_path': (kwargs.get('env') or {}).get('LEAN_PATH'),
                             'check': kwargs.get('check')})
            if mutate and phase == mutate[0]:
                target = source if mutate[1] == 'source' else project / mutate[1]
                originals[target] = target.read_bytes()
                target.write_bytes(originals[target] + b'\n')
            if transient and phase == 'audit':
                for target, content in originals.items():
                    target.write_bytes(content)
            if phase == 'environment':
                return subprocess.CompletedProcess(args, 0, 'pinned-dependencies\n', '')
            return subprocess.CompletedProcess(args, audit_exit if phase == 'audit' else compile_exit,
                                               audited if phase == 'audit' else printed,
                                               'mock failure' if (audit_exit if phase == 'audit' else compile_exit) else '')
        captured = io.StringIO()
        exception = None
        value = None
        with patch.object(gate, 'ROOT', root), patch.object(gate, 'HECKE_CI', project), \
             patch.object(gate.subprocess, 'run', side_effect=runtime), contextlib.redirect_stdout(captured):
            try:
                if route == 'direct':
                    value = gate.check_known_label_algebra('pinned-dependencies')
                else:
                    value = gate.check_new_hecke({gate.KNOWN_LABEL_SOURCE if route == 'dispatch' else route})
            except (ValueError, FileNotFoundError) as error:
                exception = {'type': type(error).__name__, 'message': str(error)}
        result = 'refused' if exception else 'accepted'
        case = {'case': name, 'expected': expected, 'actual': result, 'pass': result == expected,
                'error': exception, 'returned': value, 'commands': commands,
                'captured_stdout': captured.getvalue()}
        cases.append(case)
        print(json.dumps(case, sort_keys=True))
        return case

def append_file(filename):
    def edit(root, project, source):
        target = source if filename == 'source' else project / filename
        target.write_bytes(target.read_bytes() + b'\n')
    return edit

def remove_file(filename):
    return lambda root, project, source: (source if filename == 'source' else project / filename).unlink()

def symlink_file(filename):
    def edit(root, project, source):
        target = source if filename == 'source' else project / filename
        replacement = root / ('original-' + target.name)
        target.rename(replacement)
        target.symlink_to(replacement)
    return edit

control('baseline_four', 'accepted')
control('three_audited', 'refused', audited=audit(NAMES[:3]))
control('five_audited', 'refused', audited=audit(NAMES + ['Unexpected.extra']))
control('three_rows_summary_four', 'refused', audited=audit(NAMES[:3]).replace('audited 3', 'audited 4'))
control('five_rows_summary_four', 'refused', audited=audit(NAMES + ['Unexpected.extra']).replace('audited 5', 'audited 4'))
control('wrong_compile_namespace', 'refused', printed=PRINTED.replace('KnownLabelLeads.', 'Other.'))
control('wrong_audit_namespace', 'refused', audited=AUDIT.replace('KnownLabelLeads.', 'Other.'))
control('missing_compile_name', 'refused', printed='\n'.join(PRINTED.splitlines()[:-1]) + '\n')
control('duplicate_audit_name', 'refused', audited=AUDIT.replace(NAMES[0], NAMES[1]))
control('empty_audit', 'refused', audited='')
control('zero_audit', 'refused', audited='audited 0 theorems; 0 failing, 0 trusted\n')
control('duplicate_summary', 'refused', audited=AUDIT + 'audited 4 theorems; 0 failing, 0 trusted\n')
control('failed_summary', 'refused', audited=AUDIT.replace('0 failing', '1 failing'))
control('trusted_summary', 'refused', audited=AUDIT.replace('0 trusted', '1 trusted'))
control('custom_compile_axiom', 'refused', printed=PRINTED.replace('Quot.sound', 'ClaimAsAxiom'))
control('compiler_nonzero', 'refused', compile_exit=1)
control('auditor_nonzero', 'refused', audit_exit=1)
control('source_prechanged', 'refused', prechange=append_file('source'))
control('source_missing', 'refused', prechange=remove_file('source'))
control('source_symlink', 'refused', prechange=symlink_file('source'))
control('source_compile_mutation', 'refused', mutate=('compile', 'source'))
control('source_audit_mutation', 'refused', mutate=('audit', 'source'))
for filename in gate.KNOWN_LABEL_PROJECT_INPUTS:
    slug = filename.replace('.', '_')
    control('prechanged_' + slug, 'refused', prechange=append_file(filename))
    control('missing_' + slug, 'refused', prechange=remove_file(filename))
    control('symlink_' + slug, 'refused', prechange=symlink_file(filename))
    for phase in ('compile', 'audit'):
        control('persistent_' + phase + '_' + slug, 'refused', mutate=(phase, filename))
control('exact_dispatch', 'accepted', route='dispatch')
control('wrong_documentation_path', 'refused', route=gate.KNOWN_LABEL_SOURCE.replace('Algebra', 'Other'))
control('unknown_bare_hecke', 'refused', route='experiments/hecke-432-unreviewed/New.lean')
def change_mathlib(root, project, source):
    path = project / 'lake-manifest.json'
    content = json.loads(path.read_text())
    next(p for p in content['packages'] if p['name'] == 'mathlib')['rev'] = '0' * 40
    path.write_text(json.dumps(content))
control('dispatch_changed_mathlib', 'refused', route='dispatch', prechange=change_mathlib)
def change_toolchain(root, project, source):
    (project / 'lean-toolchain').write_text('leanprover/lean4:v0.0.0\n')
control('dispatch_changed_toolchain', 'refused', route='dispatch', prechange=change_toolchain)
# These deliberately inconsistent mocked processes identify trust boundaries.
control('boundary_contradictory_fail_line', 'accepted', audited=AUDIT + 'FAIL  Untrusted.extra  non-standard axioms: [ClaimAsAxiom]\n')
control('boundary_forged_ok_custom_axiom', 'accepted', audited=AUDIT.replace('Quot.sound', 'ClaimAsAxiom'))
control('boundary_transient_source_restored', 'accepted', mutate=('compile', 'source'), transient=True)
control('boundary_transient_project_restored', 'accepted', mutate=('compile', 'lakefile.toml'), transient=True)

workflow = (ROOT / '.github/workflows/lean-proof-gate.yml').read_text()
routing = {}
for event in ('pull_request', 'push'):
    block = re.search(r'^  ' + event + r':\n(.*?)(?=^  [A-Za-z_]+:|^\S|\Z)', workflow, re.M | re.S).group(1)
    patterns = re.findall(r"^      - '([^']+)'$", block, re.M)
    target = str(PROJECT / 'lake-manifest.json')
    routing[event] = {'target': target, 'matching_patterns': [p for p in patterns if fnmatch.fnmatchcase(target, p)]}
    assert routing[event]['matching_patterns'] == ['**/lake-manifest.json']
print('WORKFLOW_ROUTING ' + json.dumps(routing, sort_keys=True))

# Run the real generic subprocess failure adapter with a trivial Python child only.
try:
    gate.run([sys.executable, '-B', '-c', 'raise SystemExit(7)'], cwd=OUT, timeout=10)
    real_child = {'pass': False, 'actual': 'accepted'}
except ValueError as error:
    real_child = {'pass': True, 'actual': 'refused', 'error': str(error), 'child_exit': 7}
print('REAL_CHILD ' + json.dumps(real_child, sort_keys=True))

for row in ledger:
    row['sha256_after'] = hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()
    row['unchanged'] = row['sha256_after'] == row['sha256_before']
assert all(row['unchanged'] for row in ledger)
(OUT / 'source-ledger.json').write_text(json.dumps({'task_id': handoff['task_id'], 'sources': ledger}, indent=2) + '\n')
summary = {'task_id': handoff['task_id'], 'mock_native_evidence': False,
           'native_proof_validity': 'not_verified', 'cases': cases,
           'routing': routing, 'real_child': real_child,
           'counts': {'total': len(cases), 'refused': sum(c['actual'] == 'refused' for c in cases),
                      'accepted': sum(c['actual'] == 'accepted' for c in cases)},
           'all_expectations_met': all(c['pass'] for c in cases) and real_child['pass']}
(OUT / 'control-results.json').write_text(json.dumps(summary, indent=2) + '\n')
print('SUMMARY ' + json.dumps({k: v for k, v in summary.items() if k not in ('cases',)}, sort_keys=True))
assert summary['all_expectations_met']
