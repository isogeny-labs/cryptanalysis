"""Closed native correctness custody; full bulky records retained for NEW19."""
from pathlib import Path
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target'
def record(name,raw,statement):
 e=s/'evidence'/name;e.mkdir();shutil.copyfile(__file__,e/'original-record-command.py')
 index={p.relative_to(raw).as_posix():dict(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(raw.rglob('*')) if p.is_file()};(e/'whole-closed-raw-members.json').write_text(json.dumps(index,indent=2)+'\n')
 for p in sorted(raw.iterdir()):
  if not p.is_file() or p.suffix in ['.bin','.zip']:continue
  b=p.read_bytes();v=lzma.compress(b) if len(b)>60000 else b
  if len(v)<=60000:(e/(p.name+('.xz' if len(b)>60000 else ''))).write_bytes(v)
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement',statement]
 for p in sorted(e.iterdir()):cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
 print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
raw=Path('/workspace/scratch/ct80-current-original-checkpoint-07');assert json.loads((raw/'observation.json').read_text())['original_local_gate']==0
record('exact-source-checkpoint-07',raw,'Exact clean published0db58cf0 original automatic checkpoint43645146574/job132601123070 succeeds: whole249236B artifact14133571649/SHA82f9e7fca45299723097e0f5b2d0d0262c92a3a50845193c375556fde2402d85/all28members, exact source Resume/tool/remote pack-meta/original receipt and local status/gate0/Git unchanged. Precedes corrected native02; unsigned transport only.')
raw=Path('/workspace/scratch/ct80-twisted-pair-native-02')
for label in ['immediate-original-gate','runtime-custody','prior981','native','freeze','whole-compare','final-prior981','orchestrator']:assert(raw/(label+'.exit')).read_text().strip()=='0',label
assert(raw/'omission.exit').read_text().strip()=='101' and not(raw/'must-not-accept-omission.json').exists()
rows=json.loads((raw/'expected-whole-native-01.json').read_text());assert len(rows)==9;d={x['kind']:x['data'] for x in rows};pair=d['N4_TWIST_MATCHED_PAIR'];order=d['N4_TWIST_ORDER_CANDIDATE'];assert order['largest_prime_fixed_before_models']==2771711
summary=dict(order=order,source=pair['source']['unique_matched_row'],target=pair['target']['unique_matched_row'],new_instance=True,original_log_transport=False,complete_Jacobian_evaluator='NOT IMPLEMENTED',standing='unsigned')
record('twisted-pair-native-positive-02',raw,'Corrected fixed-twist native02 at published0db58cf0 after exact original checkpoint/immediategate0 passes ONEunfiltered test0/all981guards and full actual compiler/runtime/source custody. New source order11086844=4*2771711 with original deterministic primality, actual nonzero generators and UNIQUE Hasse multiple4 on BOTH elliptic curves; wrong-order/zero-generator controls reject. Actual Kohel13/independent twisted signed recipes, both complete[13] rational identities/separability/coprimality/SEA11-9,36points each/1024addition each/four2torsion/five NEW public targets pass. Full64coordinate/Frobenius/all4096 addition-original-alternating-form rows/all135 masks fix BOTH transported kernels BEFORE allsix models each. Unique new matches(1,1)D220sqrt79 and(2,0)D217sqrt70 are supported; BOTH old matched quartic arrays and all6-each HLP homogeneity coefficients exact, all12 candidates retained. ALL9 WHOLE ordered records exact/no masks/dedup; actual entire MATCHED_PAIR omission101/nooutput. This is a separate new instance, not original-log transport, a complete rational Jacobian evaluator, signed execution, novelty or computational advantage; field/geometry/program bridges remain explicit. Earlier helper101fe3785 retained.')
e=s/'evidence/twisted-pair-native-positive-summary-02';e.mkdir();(e/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('native02 complete; new model pair supported; summary saved, separate instance only',flush=True)
