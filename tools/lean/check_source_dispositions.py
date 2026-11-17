#!/usr/bin/env python3
"""Check explicit current core proofs and frozen diagnostic/code capsules separately."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path('tools/lean/source-dispositions-20261117.json')
TOOLCHAIN = 'leanprover/lean4:v4.34.1'
ARCHIVE_PREFIX = 'experiments/chained-transfer-lp-presentation-01/evidence/whole-development-CI-missing-original-identity-fixture-01/all85-original-members/'


def validate(root: Path, record: dict) -> set[str]:
    if record.get('schema') != 'cryptanalysis.lean-source-dispositions/v1' or record.get('toolchain') != TOOLCHAIN:
        raise ValueError('source disposition schema or toolchain changed')
    if not re.fullmatch('[0-9a-f]{40}', record.get('source_commit', '')):
        raise ValueError('missing immutable source revision')
    for name, expected in record.get('verifier_inputs', {}).items():
        if name not in {'tools/lean/proof-gate.sh', 'tools/lean/AuditAxioms.lean', 'tools/lean/trusted-native.txt'} or hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
            raise ValueError('native verifier input changed')
    if set(record.get('verifier_inputs', {})) != {'tools/lean/proof-gate.sh', 'tools/lean/AuditAxioms.lean', 'tools/lean/trusted-native.txt'}:
        raise ValueError('incomplete native verifier binding')
    paths = set()
    for group in record['groups']:
        if not re.fullmatch('[0-9a-f]{64}', group.get('sha256', '')) or not group.get('paths'):
            raise ValueError('invalid source binding')
        role = group.get('role')
        if role not in {'core-proof', 'archived-build-failure', 'archived-no-theorems', 'archived-verifier-input', 'archived-query-input'}:
            raise ValueError('unknown source disposition')
        if role == 'core-proof' and (not group.get('theorems') or len(group['theorems']) != len(set(group['theorems']))):
            raise ValueError('missing exact theorem identities')
        if role == 'archived-build-failure' and not group.get('diagnostic'):
            raise ValueError('missing original failure diagnostic')
        for path in group['paths']:
            relative = Path(path)
            file = root / relative
            if relative.is_absolute() or '..' in relative.parts or not path.endswith('.lean') or path in paths:
                raise ValueError('invalid or duplicate disposition path')
            if not file.resolve().is_relative_to(root.resolve()) or file.is_symlink() or not file.is_file():
                raise ValueError('disposition source is missing or escapes repository')
            if role.startswith('archived-') and '/evidence/' not in path:
                raise ValueError('archived disposition outside an evidence capsule')
            if role == 'archived-verifier-input' and not path.startswith(ARCHIVE_PREFIX):
                raise ValueError('unrecognized archived verifier capsule')
            if hashlib.sha256(file.read_bytes()).hexdigest() != group['sha256']:
                raise ValueError('disposition source bytes changed')
            if role == 'archived-query-input':
                lines = file.read_text().splitlines()
                names = {name for item in record['groups'] if item['role'] == 'core-proof' for name in item['theorems']}
                imports = {Path(name).stem for item in record['groups'] if item['role'] == 'core-proof' for name in item['paths']}
                if not lines or not any(line.startswith('#print axioms ') for line in lines):
                    raise ValueError('archived query has no bound theorem requests')
                for line in lines:
                    if not line.strip():
                        continue
                    match = re.fullmatch(r'import ([A-Za-z0-9_.]+)', line)
                    if match and match[1] in imports:
                        continue
                    match = re.fullmatch(r'#print axioms ([A-Za-z0-9_.]+)', line)
                    if not match or match[1] not in names:
                        raise ValueError('archived query differs from audited theorem identities')
            paths.add(path)
    return paths


def check(root: Path = ROOT, *, evidence: Path | None = None) -> dict:
    record = json.loads((root / MANIFEST).read_text())
    paths = validate(root, record)
    # Dispositions refer to already retained bytes, not replacement proofs or
    # regenerated failure fixtures. Bind all of them to the original Git tree.
    for group in record['groups']:
        for path in group['paths']:
            original = subprocess.run(['git', 'show', f"{record['source_commit']}:{path}"], cwd=root, capture_output=True, check=True).stdout
            if hashlib.sha256(original).hexdigest() != group['sha256']:
                raise ValueError('original source revision does not bind disposition')
    evidence = evidence or root / '.lean-corpus-evidence' / 'source-dispositions'
    evidence.mkdir(parents=True, exist_ok=True)
    evidence = Path(tempfile.mkdtemp(prefix='attempt-', dir=evidence))
    print(f'retained source-disposition evidence: {evidence}', flush=True)
    env = {**os.environ, 'ELAN_TOOLCHAIN': TOOLCHAIN}
    checked = {'proof_paths': [], 'archived_paths': [], 'unique_proof_modules': 0, 'theorems': 0}
    for group in record['groups']:
        if group['role'] in {'archived-verifier-input', 'archived-query-input'}:
            checked['archived_paths'].extend(group['paths'])
            continue
        sha = group['sha256']
        with tempfile.TemporaryDirectory(prefix='lean-source-disposition-', dir=root) as temp:
            work = Path(temp)
            source = work / f'Source{sha[:16]}.lean'
            source.write_bytes((root / group['paths'][0]).read_bytes())
            log_dir = evidence / sha
            command = ['bash', 'tools/lean/proof-gate.sh', '--out', str(log_dir), str(source.relative_to(root))]
            process = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=120)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    stdout, stderr = process.communicate(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    stdout, stderr = process.communicate()
                (evidence / (sha + '.timeout.stdout')).write_bytes(stdout)
                (evidence / (sha + '.timeout.stderr')).write_bytes(stderr)
                raise ValueError('native source qualification timed out; not admitted')
            result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
            if hashlib.sha256(source.read_bytes()).hexdigest() != sha:
                raise ValueError('staged proof source changed during native qualification')
            (evidence / (sha + '.stdout')).write_bytes(result.stdout)
            (evidence / (sha + '.stderr')).write_bytes(result.stderr)
            statuses = list(log_dir.rglob('status'))
            if len(statuses) != 1:
                raise ValueError('missing unique native proof disposition')
            status = statuses[0].read_text().strip()
            if group['role'] == 'core-proof':
                audit = statuses[0].with_name('audit.log').read_text()
                names = re.findall(r'^ok    (\S+)  \[', audit, re.M)
                expected = group['theorems']
                summaries = re.findall(r'audited ([0-9]+) theorems.*; 0 failing, 0 trusted', audit)
                if result.returncode != 0 or status != 'PASS' or len(summaries) != 1 or int(summaries[0]) != len(expected) or len(names) != len(expected) or set(names) != set(expected):
                    raise ValueError('current native theorem audit differs from exact source disposition')
                checked['proof_paths'].extend(group['paths'])
                checked['unique_proof_modules'] += 1
                checked['theorems'] += len(expected)
            elif group['role'] == 'archived-build-failure':
                build = statuses[0].with_name('build.log').read_text()
                if result.returncode != 1 or status != 'FAIL_build' or group['diagnostic'] not in build:
                    raise ValueError('archived failed attempt no longer has its recorded refusal')
                checked['archived_paths'].extend(group['paths'])
            else:
                audit = statuses[0].with_name('audit.log').read_text()
                if result.returncode != 1 or status != 'FAIL_audit' or 'no theorems' not in audit:
                    raise ValueError('archived startup diagnostic unexpectedly gained theorem standing')
                checked['archived_paths'].extend(group['paths'])
    validate(root, record)
    if set(checked['proof_paths']) | set(checked['archived_paths']) != paths:
        raise ValueError('incomplete source disposition coverage')
    (evidence / 'receipt.json').write_text(json.dumps(checked, indent=2, sort_keys=True) + '\n')
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path)
    args = parser.parse_args()
    result = check(evidence=args.evidence)
    print(json.dumps({key: len(value) if isinstance(value, list) else value for key, value in result.items()}, sort_keys=True))
