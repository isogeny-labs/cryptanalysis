"""Project reviewed CI files, merge literal source guards, and record custody."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, subprocess

repo = Path('/workspace/cryptanalysis')
study = repo / 'experiments/chained-transfer-public-target'
ci = study / 'ci_original_relation'
draft = Path('/workspace/scratch/ct111-whole-diagnostic-CI-draft-01')
evidence = study / 'evidence/whole-diagnostic-CI-source-01'
evidence.mkdir()
shutil.copyfile(__file__, evidence / 'original-projection-command.py')
for name in ['check-01.sh', 'validate_receipts_01.py', 'accept_completed_01.py', 'phase-plan-01.txt', 'kernel-declarations-01.txt', 'kernel-statement-bindings-01.txt']:
    assert not (ci / name).exists()
    shutil.copyfile(draft / name, ci / name)
driver = ci / 'check-01.sh'
text = driver.read_text().replace('# Draft for literal projection after the separately pinned comparator control run.', '# Whole diagnostic replay after the separately pinned complete comparator03 controls.')
driver.write_text(text)
workflow = repo / '.github/workflows/chained-transfer-original-relation.yml'
assert not workflow.exists()
shutil.copyfile(draft / 'workflow-01.yml', workflow)

# Preserve every original guard and add exact new files. No generated result
# or mutable problem/log/Resume is frozen into this scientific input manifest.
guards = {}
def merge_manifest(path):
    for line in path.read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert len(digest) == 64
        assert name not in guards or guards[name] == digest, name
        guards[name] = digest
for path in [study / 'ci_original_fixed_ic/reference-01.sha256', ci / 'frozen-comparator-inputs-03.sha256']:
    merge_manifest(path)
for package in ['original-relation-kernel-01', 'original-relation-rank-01', 'original-relation-character-01']:
    for path in sorted((study / package).rglob('*')):
        if path.is_file():
            name = path.relative_to(repo).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            assert name not in guards or guards[name] == digest, name
            guards[name] = digest
for path in [driver, ci / 'validate_receipts_01.py', ci / 'accept_completed_01.py', ci / 'phase-plan-01.txt', ci / 'kernel-declarations-01.txt', ci / 'kernel-statement-bindings-01.txt', ci / 'frozen-comparator-inputs-03.sha256', workflow, repo / 'scripts/checkpoint.sh', repo / '.gitignore', repo / 'docs/chained-transfer-checkpoint-transport/PROTOCOL_01.md']:
    guards[path.relative_to(repo).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
for filename in (ci / 'kernel-statement-bindings-01.txt').read_text().splitlines():
    path = repo / 'pcc/claims' / (filename + '.json')
    guards[path.relative_to(repo).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
manifest = ci / 'reference-01.sha256'
assert not manifest.exists()
manifest.write_text(''.join(digest + '  ' + name + '\n' for name, digest in sorted(guards.items())))
for name, digest in guards.items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest, name
checks = [
    ('shell-syntax', ['bash', '-n', str(driver)]),
    ('workflow-actionlint', ['/workspace/scratch/actionlint-bin/actionlint', str(workflow)]),
    ('operational-Python-syntax', ['python3', '-m', 'py_compile', str(ci / 'validate_receipts_01.py'), str(ci / 'accept_completed_01.py')]),
    ('entire-input-reference', ['sha256sum', '--check', str(manifest)]),
    ('original-comparator-source-guards', ['sha256sum', '--check', str(ci / 'frozen-comparator-inputs-03.sha256')]),
    ('original-workflow-wiring', ['python3', 'tools/artifacts/wire_workflows.py', '--check']),
]
for name, command in checks:
    result = subprocess.run(command, cwd=repo, capture_output=True)
    (evidence / (name + '.txt')).write_bytes(result.stdout + result.stderr)
    (evidence / (name + '.exit')).write_text(str(result.returncode) + '\n')
    print(name, result.returncode, flush=True)
    assert result.returncode == 0
custody = dict(consumer_parent=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(), entire_guard_count=len(guards), existing_guards_preserved=True, fixed_historical_comparator_result='PCC-20261115-241ee2', prior_public_contract='PCC-20261115-9aad0c', phase_count=len((ci / 'phase-plan-01.txt').read_text().splitlines()), exact_checkpoint_tool_revision='3de8c174cf65e6b34bf8579d97b817b8f5dc2ded', exact_checkpoint_tool_sha256='3c4192168bbc390bf94be46c765914a419a4eff8c30e3f52f5b94ea432738056', original_science_and_workflows_unchanged=True, no_fresh_diagnostic_execution=True, scope='unsigned source/static-check custody; no mathematical or execution standing')
(evidence / 'custody.json').write_text(json.dumps(custody, indent=2) + '\n')
cmd = ['python3', 'tools/pcc/pcc.py', 'claim', 'new', '--kind', 'statement', '--claim-type', 'data', '--statement', f'Full original relation diagnostic CI source projection under already published9aad0c after historical comparator03 result241ee2: new driver/static{custody["phase_count"]}phase plan/inputreference covering{len(guards)}entire original-and-new files, operational prefix validator plus completed-run final-exit acceptor, and single new workflow. Reuses unchanged complete inherited IC/sampler driver/all102phases, full passive100/60/660, rank360/entirecertificates, character60/allwitnesses, original math negative controls, complete historical comparison/eightnegatives/elapsed-only and both original27declaration/ninebinding Lean gates. Before any math, credential-scoped immutable original checkpoint tool at3de8 performs genuine exact-source gate and complete remote pack/Resume/meta readbacks, with separate later credential-free native steps. Full source/actual executable/prepared engine/raw/positive/negative/proof/partial outputs retained. Shell/actionlint/operationalPython syntax/fullinputreference/oldcomparatorguards/originalwiring0. Fresh native diagnosticCI UNEXECUTED; no result/claim criterion changed and no signed/calibrated/global/numericalLean promotion.']
for path in [driver, ci / 'validate_receipts_01.py', ci / 'accept_completed_01.py', ci / 'phase-plan-01.txt', ci / 'kernel-declarations-01.txt', ci / 'kernel-statement-bindings-01.txt', manifest, workflow, *sorted(evidence.iterdir())]:
    cmd += ['--proof', 'attestation:' + path.relative_to(repo).as_posix()]
claim = subprocess.check_output(cmd, cwd=repo, text=True).strip()
Path('/workspace/scratch/ct118-full-diagnostic-CI-source.claim').write_text(claim + '\n')
entry = f'''# Full fresh diagnostic CI source integrated; execution pending publication

## What was done
{claim}: new whole diagnostic driver/static99-phase plan/operational validators/single workflow and complete{len(guards)}-file guard reference, preserving every inherited guard. Shell/actionlint/operational Python syntax/whole source reference/old comparator guards/workflow wiring0. Exact original pre-native checkpoint transport/readbacks are before any math; entire inherited102-phase IC/sampler, native/rank/character controls, strict historical comparison, both27-declaration gates/ninebindings and full partial-output retention remain required. Fresh CI is unexecuted. [pcc:unverified]

## Decisions made
Publish this exact source with unchanged original algorithms, tools, checkpoint script, artifact policy and old workflows. Then execute the new workflow at its exact head and inspect complete outputs, including failures. The completed-run acceptor requires the entire ordered plan, all process/tee exits, original.exit0 and final guards; the internal validator explicitly leaves its own/final exits to the caller. [pcc:unverified]

## Open threads
Source governance/publication and actual fresh diagnosticCI; full scientificNEW28 including draft/build/failed/control/runtime/proof/CI archives; reviewed prospective unassisted completion and all existing math/cost/reference/admission/merge gates. [pcc:unverified]

## Errors
No new execution outcome. Historical memory134 and false rank-count1 remain frozen and resolved only for historical comparator03 by241ee2. Conductor/KB runtime unavailability and primary reviewed fallback remain recorded; no novelty claim. [pcc:unverified]
'''
with (repo / 'docs/session-logs/2026-11-15.md').open('a') as output:
    output.write('\n' + datetime.now(timezone.utc).isoformat() + '\n\n' + entry + '\n---\n')
resume = repo / '.resume/RESUME.md'
resume.write_text(entry + '\n---\n\n' + resume.read_text())
print(claim, len(guards), flush=True)
