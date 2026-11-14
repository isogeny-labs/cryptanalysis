"""Mutate copied JSON only; original native output and engines stay immutable."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,lzma,shutil,subprocess
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';ci=s/'ci_norm_sampling';o=Path('/workspace/scratch/ct71-norm-sampling-JSON-controls-01');o.mkdir()
original=json.loads(lzma.decompress((ci/'expected-native.json.xz').read_bytes()));before=hashlib.sha256((ci/'expected-native.json.xz').read_bytes()).hexdigest();results=[]
for label,expected in [('exact',0),('wall-only',0),('descent-counter',1),('class-witness',1),('call-vector',1),('rejected-tentative-k',1)]:
 rows=json.loads(json.dumps(original));d=o/label;d.mkdir()
 attempts=[x['data']for x in rows if x['kind']=='N4_NORM_SAMPLER_ATTEMPT']
 if label=='wall-only':
  for x in attempts:
   for arm in ['original','candidate']:
    for phase in x[arm]['phases']:phase['wall']+=0.125
    for pair in x[arm]['stats']:
     if pair[0]=='wall_total':pair[1]+=0.25
 elif label=='descent-counter':next(p for x in attempts for p in x['candidate']['phases']if p['phase']=='descent')['mul']+=1
 elif label=='class-witness':next(x for x in rows if x['kind']=='N4_NORM_SAMPLER_SCALARS')['data']['all75'][0]['sampler_class'][1]+=1
 elif label=='call-vector':attempts[0]['explicit_candidate_calls']['completed_transfer']+=1
 elif label=='rejected-tentative-k':next(x for x in attempts if not x['candidate']['ok']and x['candidate']['k_found']is not None)['candidate']['k_found']+=1
 (d/'solver.log').write_text(''.join(x['kind']+' '+json.dumps(x['data'],separators=(',',':'))+'\n'for x in rows))
 cmd=['python3',str(ci/'replay_io.py'),'outputs',str(ci),str(d)];p=subprocess.run(cmd,cwd=r,capture_output=True);(d/'original.log').write_bytes(p.stdout+p.stderr);(d/'original.exit').write_text(str(p.returncode)+'\n');assert p.returncode==expected,(label,p.returncode,p.stdout,p.stderr)
 results.append(dict(label=label,expected=expected,actual=p.returncode));print(label,p.returncode,flush=True)
assert hashlib.sha256((ci/'expected-native.json.xz').read_bytes()).hexdigest()==before
ref=[line.split('  ',1)for line in(ci/'reference-01.sha256').read_text().splitlines()];assert len(ref)==784 and all(hashlib.sha256((r/p).read_bytes()).hexdigest()==h for h,p in ref)
(o/'observation.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),results=results,copied_logs_only=True,original_expected_sha256=before,original_expected_and_all784_inputs_unchanged=True,raw_times_mutated_only_in_copied_positive_control=True,no_new_native_execution_or_verifier_change=True),indent=2)+'\n');shutil.copyfile(__file__,o/'original-command.py')
d=s/'evidence/norm-sampling-JSON-controls-01';d.mkdir();shutil.copyfile(o/'observation.json',d/'observation.json');shutil.copyfile(__file__,d/'original-command.py')
for label,_ in [(x['label'],x['actual'])for x in results]:
 for name in ['original.log','original.exit']:shutil.copyfile(o/label/name,d/(label+'-'+name.replace('.log','.txt')))
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Normsampling strict wholeJSON copied-fixture controls:exact0/wallonly0;descentcounter+1/classwitness+1/explicitcallvector+1/rejectedtentativek+1 ALLreject1. ALL86wholeJSON comparator masksONLYdeclaredATTEMPTwall fields;evenDESCENTcounters mandatoryexact. Originalnative9bc5e6/wholeexpected/all784frozeninputs unchanged/no newnativeexecution/no originalPCCverifierchange. Wholecopiedlogs/exits retained/nextgenuinearchivepending;controlsarenotexecutionverification.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct71-sampling-JSON-controls.claim').write_text(cl+'\n');print(cl,flush=True)
