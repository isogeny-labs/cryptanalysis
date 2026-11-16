"""Bind declarations through the unchanged original PCC implementation."""
from pathlib import Path
import hashlib,importlib.util,json,os,subprocess,sys
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';d=s/'evidence/norm-sampling-bindings-01';d.mkdir()
spec=importlib.util.spec_from_file_location('original_pcc',r/'tools/pcc/pcc.py');pcc=importlib.util.module_from_spec(spec);sys.modules[spec.name]=pcc;spec.loader.exec_module(pcc)
env=dict(os.environ,PATH='/home/agent/.elan/bin:/home/agent/.cargo/bin:'+os.environ['PATH'],ELAN_TOOLCHAIN='leanprover/lean4:v4.34.1');claims=[];verdicts=[]
path=Path('experiments/chained-transfer-public-target/norm-assisted-ic/lean/NormAssistedSampling.lean')
for name in ['norm_half_roundtrip','prepared_sample_exact','omitted_half_rejected']:
 theorem='NormAssistedSampling223.'+name;found=pcc.lean_find_declaration([path],theorem);assert found;where,statement=found
 proof=dict(path=str(where),theorem=theorem,decl_sha256=hashlib.sha256(statement.encode()).hexdigest())
 cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','theorem','--claim-type','interpretive','--statement',statement,'--scope','Faithful conditional norm-assisted sampling for native9bc5e6:scalar equivariance/PhiNorm=[2]/ell2773073-torsion and genuine scalar action laws derive Phi(inv2NormG)=G using2*1386537=ell+1;actual prepared Phi(u)=G plus scalar equivariance derives exactallr samples;genuine groupcancellation/nonzeroG excludesomittedinverse2. Both unchanged original4.35/4.34.1 gatesPASS3/zero trusted;no customaxioms/holes/nativeevaluation. ActualPicard/ellsubtypes/groupactions/geometricPhiNorm/scalar-equivalence remainexplicitwritten-nativebridges;no completecost/formalgeometry/signedexecution claim.','--proof','lean:'+json.dumps(proof)]
 cl=subprocess.check_output(cmd,cwd=r,env=env,text=True).strip();claims.append(dict(theorem=theorem,claim_path=cl,statement=statement,proof=proof));(d/'claims-partial.json').write_text(json.dumps(claims,indent=2)+'\n')
 v=subprocess.run(['python3','tools/pcc/pcc.py','verify',cl,'--json'],cwd=r,env=env,capture_output=True);(d/(name+'-verdict.json')).write_bytes(v.stdout+v.stderr);(d/(name+'-verdict.exit')).write_text(str(v.returncode)+'\n');assert v.returncode==0,(name,v.stdout,v.stderr)
 parsed=json.loads(v.stdout);assert parsed['verdict']=='pass'and not parsed['reasons'];verdicts.append(parsed);print(name,cl,'localpass/unsigned',flush=True)
(d/'claims.json').write_text(json.dumps(claims,indent=2)+'\n');(d/'local-verdicts.json').write_text(json.dumps(verdicts,indent=2)+'\n');Path('/workspace/scratch/ct71-sampler-bound-claims.json').write_text(json.dumps(claims,indent=2)+'\n')
