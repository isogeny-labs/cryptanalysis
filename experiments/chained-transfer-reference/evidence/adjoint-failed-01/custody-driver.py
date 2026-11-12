from pathlib import Path
from datetime import datetime, timezone
import subprocess, hashlib, shutil, json, sys

c=Path('/workspace/cryptanalysis');r=Path('/workspace/crypto')
s=Path('experiments/chained-transfer-reference/src');e=c/'experiments/chained-transfer-reference/evidence'
base='b2972eb51fd794e1a6061c41fd5f3828890c08e3'
def previous(name):
    return subprocess.run(['git','show',base+':'+str(s/(name+'.rs'))],cwd=c,capture_output=True,text=True,check=True).stdout
def current(name):return (c/s/(name+'.rs')).read_text()
def body(text,name):
    start=text.index('fn '+name+'(');op=text.index('{',start);depth=0
    for i in range(op,len(text)):
        if text[i]=='{':depth+=1
        elif text[i]=='}':
            depth-=1
            if depth==0:return text[op:i+1]
    raise AssertionError(name)
old=previous('seven_chain');new=current('seven_chain')
assert body(old,'dual')==body(new,'dual_reference')
for name in ['forward','forward_reference','quarter_phi','quarter_phi_points','naive']:
    assert body(old,name)==body(new,name),name
marker='#[test]\nfn seven_chain_prime109_source_recovery_and_direct_coordinates()'
assert old[old.index(marker):]==new[new.index(marker):]
assert body(new,'dual').strip()=='{\n        self.adjoint.evaluate(d)\n    }'
assert current('prime_field_psi').replace('pub(super) fn key(', 'fn key(')==previous('prime_field_psi')
assert current('quartic_norm')==(r/'research/chained_jacobian_transfers_20261110/evidence/t1-direct-norm-source-18.rs').read_text()
for name in ['fixed','pull','old_pull','key','all_four_direct_quartic_pullbacks_match_existing_r_p']:
    assert body(current('quartic_pullback'),name)==body(previous('quartic_pullback'),name),name
for name in ['balanced','quartic_cover','quartic_lagrange','quartic_pullback_points']:
    assert current(name)==previous(name),name
prototype=(r/'research/chained_jacobian_transfers_20261110/evidence/prime-adjoint-24/ct30_prime_dual.rs').read_text()
adj=current('prime_field_adjoint')
for name in ['new','evaluate']:assert body(adj,name)==body(prototype,name),name
assert 'old.dual_reference(d)' in adj and 'old.dual(d)' not in adj
receipt=e/'adjoint-source-guards-01.txt';assert not receipt.exists()
receipt.write_text('PASS exact b297 old dual body preserved as dual_reference;all old chain forward/forward_reference/quarter/naive bodies and test suffix unchanged.\nPASS actual dual selects standalone adjoint;full new comparison explicitly calls old dual_reference.\nPASS accepted T1norm18 source byte-identical;adjoint24 constructor/evaluator bodies byte-identical after path/visibility adaptations.\nPASS old pullback constructor/evaluator/tests unchanged;point enumeration reused by wrapper,not loaded twice.\nPASS Balanced,quartic cover/Lagrange/point sources unchanged;primeforward key visibility only.\n')
names=['balanced','seven_chain','quartic_cover','quartic_lagrange','quartic_norm','quartic_pullback','quartic_pullback_points','prime_field_psi','prime_field_adjoint']
manifest=[];subjects=[receipt]
for name in names:
    p=c/s/(name+'.rs');q=e/('adjoint-'+name+'-source-01.rs');assert not q.exists();shutil.copyfile(p,q)
    manifest.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(c)))
    if name in ['seven_chain','quartic_norm','prime_field_adjoint']:subjects.append(q)
m=e/'adjoint-source-01.sha256';m.write_text('\n'.join(manifest)+'\n');subjects.append(m)
cl=e/'adjoint-clippy-01.txt';shutil.copyfile('/workspace/scratch/ct31-adjoint-clippy-01.txt',cl);subjects.append(cl)
statement='Unsigned actual adjoint integration01 strictClippy/exact source guards pass:SevenChain.dual selects standalone PrimeFieldAdjoint;exact old dual remains dual_reference and full comparison explicitly calls it. All old forward/reference/quarter/naive bodies and old test suffix unchanged. T1norm18 source and adjoint24 constructor/evaluator arithmetic byte-identical;only model data/path/visibility/helper delegation added. Balanced/cover/Lagrange/point sources unchanged. Nine source snapshots/hashmanifest frozen;full changed25native/92reference+five/one oldignored pending. Parent1506/b29790-suite fixed;no timing claim.'
def claim(repo,text,paths):
    args=[sys.executable,'tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',text]
    for p in paths:args+=['--proof','attestation:'+str(p.relative_to(repo))]
    return subprocess.run(args,cwd=repo,capture_output=True,text=True,check=True).stdout.strip()
cc=claim(c,statement,subjects)
re=r/'research/chained_jacobian_transfers_20261110/evidence';rs=[]
for p in subjects:
    q=re/('consumer-'+p.name);assert not q.exists();shutil.copyfile(p,q);rs.append(q)
rc=claim(r,statement,rs);now=datetime.now(timezone.utc).isoformat()
entry=f'''\n## {now} — actual adjoint source01 frozen for complete guard02 (Codex)

### What was done (commands, files, features)
- Actual strictClippy/exact source custody passes;consumer{cc},root{rc}. Existing dual now selects standalone adjoint,exact oldbody is dual_reference and new full comparison calls that explicit reference. Old chain forward/quarter/naive/test suffix unchanged. Accepted T1norm18 source and adjoint24 constructor/evaluator arithmetic byte-identical;helper delegates to one existing point enumerator. All9source snapshots/manifest frozen. [pcc:unverified]

### Decisions made (and why)
- Run one full changed check.sh02 on stable source01,expected25native/92reference unit+five integrations/one historical ignored. Raw/workspace/scratch/ct31-adjoint-complete-02.txt. Do not edit actual9sources until completion/afterhash;no narrower case filtering. Parent1506/b297 stays fixed with full90 accepted and ownCI next~09:00.
- Existing primary/global526f9f/4934b4/78176c/native18/dcbb58 review applies;KB unavailable,no novelty or timing claim.

### Open threads (unfinished, pick up next time)
- Actual adjoint full02/finalnewreport/readychild1506. Root20/138written/26modules/compression/geometry checkpoint;root971 ownCI next08:39. T2 secondhop/compressed integration follows after this actual child checkpoint.

### Errors (what went wrong, how it was handled)
- No actual adjoint stage01 static/source failure. Original live90 sources changed only on the new child after b297 was committed/published;its frozen snapshots/reports/proofs remain intact.
'''
for repo in [c,r]:
    with (repo/'docs/session-logs/2026-11-12.md').open('a') as f:f.write(entry)
print(json.dumps(dict(consumer_claim=cc,root_claim=rc,at=now)))
