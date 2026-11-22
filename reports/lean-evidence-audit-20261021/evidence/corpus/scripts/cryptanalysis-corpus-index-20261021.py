import hashlib,json,re,subprocess
from pathlib import Path
root=Path('/home/ec2-user/cryptanalysis-proof-audit-20261021')
allf=set(subprocess.check_output(['git','ls-files','--','*.lean'],cwd=root,text=True).splitlines())
groups={}
def add(path,group,evidence):
 if path in groups:raise AssertionError(f'duplicate coverage: {path}: {groups[path]} vs {group}')
 groups[path]={'source':path,'sha256':hashlib.sha256((root/path).read_bytes()).hexdigest(),'method':group,'evidence':evidence}
for check in subprocess.check_output(['git','ls-files','--','experiments/**/check.py'],cwd=root,text=True).splitlines():
 receipt=root/Path(check).parent/'lean-build.txt'
 if not receipt.exists():continue
 for path in re.findall(r'^sha256 (.*\.lean): [0-9a-f]{64}$',receipt.read_text(),re.M):
  if path not in groups:add(path,'pinned experiment check.py',check)
for label in ('mixed640','core','dependent'):
 file=Path(f'/var/tmp/cryptanalysis-{label}-replay-20261021/summary.json')
 rows=json.loads(file.read_text())
 assert all(r['status']=='PASS' and not r['bad_axioms'] and r['expected_prints']==r['actual_prints'] for r in rows)
 for r in rows:
  add(r['source'],f'{label} Lean build and axiom printout',f'{label}/summary.json')
  assert groups[r['source']]['sha256']==r['sha256']
for path,log in [
 ('experiments/prime-j0-gauge-tree-20261012/GaugeTree.lean','extra/GaugeTree.log'),
 ('experiments/prime-j0-hex-orbit-materialized-20261013/OrbitCompression.lean','extra/OrbitCompression.log'),
 ('experiments/orbit-quotient-summation/lean/OrbitPairIndex.lean','orbit-build.log and orbit-audit.log'),
 ('experiments/orbit-quotient-summation/lean/AxiomAudit.lean','orbit-audit.log'),
 ('research/binary_genus2_cover_20261014/lean/BinaryGenusTwo.lean','binary-build.log')]:
 add(path,'pinned direct or Lake build',log)
assert set(groups)==allf,(len(groups),len(allf),sorted(allf-set(groups)),sorted(set(groups)-allf))
counts={}
for r in groups.values():counts[r['method']]=counts.get(r['method'],0)+1
payload={'schema':'cryptanalysis.lean_corpus_replay.v1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'tracked_lean_files':len(allf),'compiled_lean_files':len(groups),'uncompiled_lean_files':0,'coverage_by_method':counts,'proof_scope':'Lean source compilation and source-directed axiom printouts; semantic claim mapping and implementation refinement remain open','files':sorted(groups.values(),key=lambda r:r['source'])}
Path('/var/tmp/cryptanalysis-corpus-index-20261021.json').write_text(json.dumps(payload,indent=2)+'\n')
print(len(groups),counts)
