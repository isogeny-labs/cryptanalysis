"""Proof custody and original PCC statement binding only; no research arithmetic."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,subprocess,sys,os
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';raw=Path('/workspace/scratch/ct75-norm-inverse-proof-01');dst=s/'norm-arithmetic-audit/lean';dst.mkdir();shutil.copyfile(raw/'QuadraticInverse.lean',dst/'QuadraticInverse.lean');(dst/'lean-toolchain').write_text('leanprover/lean4:v4.35.0\n')
e=s/'evidence/norm-arithmetic-inverse-proof-01';e.mkdir()
for n in ['lean434.exit','lean434.txt','lean435.exit','lean435.txt','root-original-gate.exit','root-original-gate.txt','consumer-original-gate.exit','consumer-original-gate.txt']:
 assert not n.endswith('.exit') or (raw/n).read_text().strip()=='0';shutil.copyfile(raw/n,e/n)
for n in ['root-original-gate','consumer-original-gate']:shutil.copytree(raw/n,e/n)
shutil.copyfile(__file__,e/'record-command.py')
context={'scope':'Universal commutative-ring cleared quadratic inverse-pair formula conditional on a norm inverse, not actual finite-field/integer-encoding/counter implementation or global Jacobian formalization.','source_formula':'quadratic-picard-engine/src/lib.rs Fq::invu; original nonzero norm and base_invu are separate native obligations','reused_existing_norm_product':'crypto:research/chained_jacobian_transfers_20261110/lean/IsogenyCycles.lean IsogenyCycles.quadratic_norm_multiplicative; existing Int QuadraticNormIdentity.norm_multiplicative; not duplicated','native_bridge':'e70b64 all49728 nonzero actual inverses vs unchanged FpR body; shared lower Zp/fpm dependencies disclosed','do_not_infer':'No inverse existence proof, nonzero norm theorem, finite field construction, integer bounds, counter correctness, program equivalence, global variety construction or cost advantage.','aggregate_binding_count':'Not changed here; these three local headers are listed explicitly and helper conjugate_product is not a new research finding.'}
(e/'context.json').write_text(json.dumps(context,indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','New quadratic inverse-pair module builds under4.34.1 and4.35.0; BOTH unchanged original proof gates audit3 declarations0failing0trusted with only propext/Classical.choice/Quot.sound. Norm-product identity reused, not duplicated or promoted as new. Universal ring inverse formula is conditional on genuine inverse of norm; actual finite-field/encoding/nonzero/program/counter/global geometry remain explicit native/written gaps. Module-specific statement bindings follow; unsigned local evidence only.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
claims=[]
for short in ['conjugate_product','scaled_conjugate_inverse','inverse_pair_norm']:
 name='NormArithmetic.'+short;_,statement=m.lean_find_declaration([dst/'QuadraticInverse.lean'],name)
 proof={'path':(dst/'QuadraticInverse.lean').relative_to(r).as_posix(),'theorem':name,'decl_sha256':hashlib.sha256(statement.encode()).hexdigest()}
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope',context['scope']+' '+context['do_not_infer'],'--proof','lean:'+json.dumps(proof)]
 claim=subprocess.check_output(cmd,cwd=r,text=True).strip();claims.append({'name':name,'claim':claim,'statement':statement});print(claim,name,flush=True)
 env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.35.0/bin:'+os.environ['PATH']);q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True);(raw/(short+'-binding.json')).write_bytes(q.stdout);(raw/(short+'-binding.stderr.txt')).write_bytes(q.stderr);(raw/(short+'-binding.exit')).write_text(str(q.returncode)+'\n');assert q.returncode==0,(q.stdout+q.stderr)[:2000]
 verdict=json.loads(q.stdout);assert verdict['status']=='pass',verdict
 shutil.copyfile(raw/(short+'-binding.json'),e/(short+'-binding.json'));shutil.copyfile(raw/(short+'-binding.exit'),e/(short+'-binding.exit'))
(e/'bindings.json').write_text(json.dumps(claims,indent=2)+'\n')
print('three original local statement bindings pass, unsigned',flush=True)
