"""Install literal old solver and existing I/O-only build/custody helpers; no math."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';p=s/'original-fixed-model-ic-01';old=s/'original-full-evaluator-01'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()=='7550409db980a583bad7ce46e9fd0c29db5cce29'
assert json.loads((r/'pcc/claims/PCC-20261115-3da7fe.json').read_text())['producer']['commit']=='41e35d8c701484a6ca5406ecbf7bb83278be6073'
source=s/'new-target-ic/derived/class_solver.rs';dest=p/'derived/class_solver.rs';dest.parent.mkdir();shutil.copyfile(source,dest);assert source.read_bytes()==dest.read_bytes()
(p/'.gitattributes').write_text('derived/class_solver.rs -whitespace\n')
refs={}
for name in ['ci_fixed_chain/reference-03.sha256','ci_induced_transfer/reference-01.sha256']:
 for line in(s/name).read_text().splitlines():
  h,n=line.split('  ',1);assert hashlib.file_digest((r/n).open('rb'),'sha256').hexdigest()==h
  assert n not in refs or refs[n]==h;refs[n]=h
for f in [s/'ORIGINAL_FIXED_MODEL_IC_PROTOCOL_01.md',s/'reports/original-fixed-model-IC-proposal-01/report.pdf',s/'evidence/original-fixed-model-IC-prospective-01/literal-input-pins.json']:
 refs[f.relative_to(r).as_posix()]=hashlib.file_digest(f.open('rb'),'sha256').hexdigest()
(p/'frozen-prior-inputs-01.sha256').write_text(''.join(h+'  '+n+'\n'for n,h in sorted(refs.items())))
for name in ['inherit_prepared.py','capture_binary.py','capture_engine.py','runtime_custody.py']:shutil.copyfile(old/name,p/name)
t=(old/'build-only-01.sh').read_text().replace('chained_n4_original_full_evaluator','chained_n4_original_fixed_model_ic').replace('audit-original-full-chain','audit-original-fixed-model-ic');(p/'build-only-01.sh').write_text(t)
(p/'literal-source-provenance.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),protocol='PCC-20261115-3da7fe',protocol_published_before_Rust='7550409db980a583bad7ce46e9fd0c29db5cce29',source=str(source),source_sha256=hashlib.file_digest(source.open('rb'),'sha256').hexdigest(),literal_destination=str(dest),whole_solver_byte_equal=True,solver_edits=[],context_changes='new geometry-side selector binds existing original-geometry NormNew/case/mask/P0/order; only surrounding type/admission context adapted',frozen_prior_paths=len(refs),all_old1440_and_proof73_paths_preserved=True,helpers='literal existing full evaluator I/O/custody helpers; only compile target/bin names changed in the new build driver',scope='source implementation custody only; no native outcome or performance inference'),indent=2)+'\n')
shutil.copyfile(__file__,p/'materialize-support.py')
print('literal existing solver unchanged; prior source guards',len(refs),flush=True)
