"""Preserve rejected verifier invocation; correct caller toolchain, not verifier."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,subprocess,sys,os
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct75-norm-inverse-proof-01');e=s/'evidence/norm-arithmetic-inverse-proof-01';dst=s/'norm-arithmetic-audit/lean';shutil.copyfile(__file__,e/'finish-command.py')
shutil.copyfile(raw/'conjugate_product-binding.json',e/'first-canonical435-binding-failure.json');shutil.copyfile(raw/'first-canonical-lean-toolchain435',e/'first-canonical-lean-toolchain435')
for name in ['consumer435-canonical-diagnosis','consumer434-canonical-correction']:
 shutil.copytree(raw/name,e/name)
 for suffix in ['.exit','.txt']:shutil.copyfile(raw/(name+suffix),e/(name+suffix))
(e/'caller-correction.json').write_text(json.dumps({'failed_first_binding_actual_exit':1,'cause':'Consumer original auditor is pinned to4.34.1 and uses Lean.ofReduceBool/Lean.trustCompiler/String.trim absent under4.35.0. Module itself builds under both versions, root original435 gate passes. First canonical pin435 was wrong for the consumer auditor.','correction':'Canonical module pin4.34.1; caller uses original434 toolchain. No gate/audit/source theorem mutation. Both gate baselines retained.','scope':'caller/version mismatch, not a rejected mathematical theorem'},indent=2)+'\n')
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
claims=[];env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH'])
for short in ['conjugate_product','scaled_conjugate_inverse','inverse_pair_norm']:
 name='NormArithmetic.'+short;_,statement=m.lean_find_declaration([dst/'QuadraticInverse.lean'],name)
 if short=='conjugate_product':claim='pcc/claims/PCC-20261114-36febb.json'
 else:
  proof={'path':(dst/'QuadraticInverse.lean').relative_to(r).as_posix(),'theorem':name,'decl_sha256':hashlib.sha256(statement.encode()).hexdigest()}
  cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope','Universal commutative-ring inverse formula conditional on explicit genuine norm inverse. Actual field, encoding, nonzero norm, base inversion, counters, program and global geometry remain separate native/written obligations. Original consumer434 and root435 gates audit3theorems0trusted; no new aggregate uniqueness or performance claim.','--proof','lean:'+json.dumps(proof)];claim=subprocess.check_output(cmd,cwd=r,text=True).strip()
 claims.append({'name':name,'claim':claim,'statement':statement})
 q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True);(raw/(short+'-binding02.json')).write_bytes(q.stdout);(raw/(short+'-binding02.stderr.txt')).write_bytes(q.stderr);(raw/(short+'-binding02.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0,(q.stdout+q.stderr)[:2000];assert json.loads(q.stdout)['verdict']=='pass'
 for suffix in ['.json','.exit']:shutil.copyfile(raw/(short+'-binding02'+suffix),e/(short+'-binding02'+suffix))
 print(claim,name,'local pass',flush=True)
(e/'bindings.json').write_text(json.dumps(claims,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Inverse-pair proof canonical caller first failed original consumer audit1 under wrong435 pin (36febb); exact failedverdict/full auditor diagnostics retained. Consumer auditor needs434 (ofReduceBool/trustCompiler/trim APIs), root auditor435. Canonical pin corrected434 with unchanged module/theorem headers and original gates; BOTH3declaration gates0trusted and allTHREE exact original PCC local statement bindings now pass. Multiplicative norm reused, no duplicate novelty/aggregate count. All local results remain unsigned; actual finite field/encoding/nonzero/program/geometry gaps remain.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
