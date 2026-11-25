"""Original Lean/PCC statement binding and source custody only."""
from pathlib import Path
import hashlib,importlib.util,json,shutil,subprocess,sys,os
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';e=s/'evidence/nondual13-nonsquare-proof-01';e.mkdir()
for label in ['01','02']:
 shutil.copytree('/workspace/scratch/ct77-nonsquare-proof-'+label,e/('attempt'+label))
shutil.copyfile(__file__,e/'original-record-command.py')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Observed12/24 nonsquare finite-residue proof: originalconsumer434/root435 gates attempt01 reject1 due default maximumrecursiondepth before proof acceptance; fullsource/logs retained.02 keeps exactsame theorem and decide proof with bounded maxRecDepth8192, same120spergate; bothoriginalgatesPASS1theorem0trusted. Uses kernel decision, no native_decide/oracle/customaxioms. Scopeonly allcanonicalNat residuesmod223, no finitefield/towerlaw/ppav/program theorem or aggregate novelty count. Unsigned localproofcustody.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
path=s/'nondual13-next-preflight/lean/NonsquareResidues.lean';name='NonsquareResidues.base_square_nonroots';_,statement=m.lean_find_declaration([path],name)
proof=dict(path=path.relative_to(r).as_posix(),theorem=name,decl_sha256=hashlib.sha256(statement.encode()).hexdigest())
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope','For each canonical residue x:Fin223, its Nat square modulo223 is neither12 nor24. Explicit finite residue arithmetic only; primality/field encoding/odd-degree tower law/polarized Jacobian geometry and program correspondence are separate. Both unmodified434/435 gates pass1theorem0trusted. Failed01 default-recursion attempt preserved. No novel aggregate claim.','--proof','lean:'+json.dumps(proof)]
claim=subprocess.check_output(cmd,cwd=r,text=True).strip();env=dict(os.environ,PATH='/home/agent/.elan/toolchains/leanprover--lean4---v4.34.1/bin:'+os.environ['PATH'])
q=subprocess.run(['python3','tools/pcc/pcc.py','verify',claim,'--json'],cwd=r,env=env,capture_output=True);(e/'binding.json').write_bytes(q.stdout);(e/'binding.stderr.txt').write_bytes(q.stderr);(e/'binding.exit').write_text(str(q.returncode)+'\n');assert q.returncode==0 and json.loads(q.stdout)['verdict']=='pass';print(claim,'exact local binding pass;unsigned',flush=True)
(e/'binding-scope.json').write_text(json.dumps(dict(claim=claim,theorem=name,statement=statement,scope='both original standalone gates pass and original local exactbinding passes; no signed verdict/field or extension theorem'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Bothoriginal434/435gates accept same finite223residue nonroot theorem for12/24 with zero trusted; original exactPCC localbinding passes. Faileddefault-recursion01 andbounded02/wholelogs retained. No field/towerlaw/geometry or signedexecution promotion.']
for p in sorted(e.rglob('*')):
 if p.is_file():cmd+=['--proof','attestation:'+p.relative_to(r).as_posix()]
print(subprocess.check_output(cmd,cwd=r,text=True).strip(),flush=True)
