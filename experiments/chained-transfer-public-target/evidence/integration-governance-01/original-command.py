"""I/O/governance checkpoint for the independent replay, no crypto arithmetic."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, lzma, shutil, subprocess

r = Path('/workspace/cryptanalysis')
s = r / 'experiments/chained-transfer-public-target'
base = '80b222e8cd53a6ae56e6d97272f7dd735f3483ab'
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=r, text=True).strip() == base
d = s / 'evidence/integration-governance-01'
d.mkdir()
shutil.copyfile(__file__, d / 'original-command.py')
scope = [str(s.relative_to(r)), '.github/workflows/chained-transfer-public-target.yml',
         'pcc/claims', 'pcc/ledger.jsonl', 'docs/session-logs/2026-11-13.md', '.resume/RESUME.md']

def paths():
    return sorted((set(subprocess.check_output(['git', 'ls-files', '--modified', '--others', '--exclude-standard', '-z', '--', *scope], cwd=r).split(b'\0')) |
                   set(subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=r).split(b'\0'))) - {b''})

def run(name, cmd):
    p = subprocess.run(cmd, cwd=r, capture_output=True)
    raw = p.stdout + p.stderr
    if len(raw) > 60000:
        encoded = lzma.compress(raw, format=lzma.FORMAT_XZ)
        assert lzma.decompress(encoded) == raw
        (d / (name + '.txt.xz')).write_bytes(encoded)
    else:
        (d / (name + '.txt')).write_bytes(raw)
    (d / (name + '.exit')).write_text(str(p.returncode) + '\n')
    print(name, p.returncode, flush=True)
    assert p.returncode == 0, raw.decode()[:2000]

ref = s / 'reference-01.sha256'
lines = ref.read_text().splitlines()
assert len(lines) == 433 and sum('../crypto/' in x for x in lines) == 347
(s / 'evidence/integration-plan-01/final-inventory.json').write_text(json.dumps(dict(
    root_inputs=347, consumer_inputs=86, total_portable_inputs=433,
    manifest_bytes=ref.stat().st_size, original_exact_PCC_claims=14,
    positive_native_tee_pairs=29, intentional_negative_native_tee_pairs=14,
    old_whole_seven_job_workflow_unchanged=True,
    unchanged_native_and_formal_source=base, result='not run yet'), indent=2) + '\n')
assert not subprocess.check_output(['git', 'diff', '--name-only', base, '--', 'tools', 'suite',
    '.github/workflows/chained-transfer-reference.yml', '.github/workflows/pcc-gate.yml',
    'experiments/chained-transfer-reference', str((s/'native').relative_to(r)), str((s/'formal').relative_to(r))], cwd=r)
assert (r/'.github/workflows/chained-transfer-reference.yml').read_bytes() == (s/'evidence/primary-01/whole-parent-seven-jobs.yml').read_bytes()
now = datetime.now(timezone.utc).isoformat()
entry = f'''\n## {now} — independent public-target replay source frozen (Codex)\n\nSource80b and producer3d unchanged; integration plan004229 precedes new orchestration. Independent replay pins433inputs(347producer+86consumer),43ordered phase pairs(29positive0/0+14intentional2/0),all3unfiltered native tests/fivepublic targets/both original9+5proof gates/all14exact bindings. Fresh isolated physical Git siblings and outside cache/output required. New PR-sync CI explicitly checks out the head; entire previous seven-job workflow unchanged. No full-replay or own-CI result yet. [pcc:unverified]\n\nNext: publish this integration source, materialize clean siblings, run all four admission controls(expected2/no output), then launch bounded2100s full correctness replay and collect new CI. Preserve every original failure and whole capture. Then versioned rho-answer accessor and actual q223 V2 model/origin/Phi/norm maps; no cost or speed claim. [pcc:unverified]\n'''
for p in [s/'CHECKPOINT.md', r/'.resume/RESUME.md', r/'docs/session-logs/2026-11-13.md']:
    with p.open('a') as f: f.write(entry)
run('shell', ['bash', '-n', str(s/'check.sh')])
run('python-syntax', ['python3', '-m', 'py_compile', str(s/'replay_io.py'), str(s/'freeze_reference.py')])
run('actionlint', ['/workspace/scratch/actionlint-bin/actionlint', '.github/workflows/chained-transfer-public-target.yml'])
run('parent437', ['sha256sum', '--check', 'experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
run('ledger', ['python3', 'tools/pcc/pcc.py', 'ledger', 'verify', '--base', base])
run('prose', ['python3', 'tools/pcc/pcc.py', 'lint-prose', *[p.decode() for p in paths() if p.endswith(b'.md')]])
run('whitespace', ['git', 'diff', '--check', '--', *scope])
run('wiring', ['python3', 'tools/artifacts/wire_workflows.py', '--check'])
run('benchrec', ['python3', 'tools/benchrec.py', 'gate'])

def stage():
    selected = paths()
    f = Path('/workspace/scratch/ct58-integration.paths0')
    f.write_bytes(b'\0'.join(p for p in selected if p != b'.resume/RESUME.md') + b'\0')
    subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'], cwd=r, check=True)
    subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'], cwd=r, check=True)
    actual = set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')) - {b''}
    assert actual == set(selected)
    for p in selected:
        if p.startswith(b'pcc/claims/'):
            for proof in json.loads((r/p.decode()).read_text()).get('proofs', []):
                if proof.get('kind') == 'attestation':
                    x = proof['subject']
                    assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest() == x['sha256']
                    assert x['path'].encode() in actual or subprocess.run(['git','cat-file','-e',base+':'+x['path']],cwd=r,capture_output=True).returncode == 0
    return actual

stage()
run('cached-whitespace', ['git', 'diff', '--cached', '--check'])
tree = subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip()
run('artifact', ['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base, portable_inputs=433,
    old_native_formal_reference_and_verifier_unchanged=True, old_seven_job_workflow_byte_exact=True,
    original_gates='ledger/prose/whitespace/wiring/benchrec/artifact/actionlint all0',
    phase_policy='29native0/tee0+14intentionalnative2/tee0',
    full_replay_and_CI='not run yet', scope='orchestration only;no measured advantage'),indent=2)+'\n')
cmd = ['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data',
    '--statement','P1 independent replay integration source governance:80b native/formal/tools/trust/wholeold7workflow unchanged;433portable inputs347+86;43ordered phase pairs29positive0/0 plus14intentional2/0. Original ledger/prose/whitespace/wiring/benchrec/artifact/actionlint gates0 and newsubject hashes/staging. Four admission controls/full2100s/ownPRsyncCI not yet run. No geometry or speed claim.']
for p in sorted(d.iterdir()): cmd += ['--proof','attestation:'+str(p.relative_to(r))]
claim = subprocess.check_output(cmd,cwd=r,text=True).strip()
selected=stage()
subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True)
subprocess.run(['git','commit','--quiet','-m','ci: add independent public-target N4 replay with exact source and proof pins'],cwd=r,check=True)
print(claim, subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
