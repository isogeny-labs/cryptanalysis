"""Metadata/source-publication checkpoint; no compiled source or verifier change."""
from pathlib import Path
from datetime import datetime,timezone
import subprocess,json,hashlib,shutil,lzma
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-reference';base='ea833df7e109682104ec8b1cce387011fd68eb31'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
d=s/'evidence/g3-norm-ci-metadata-governance-01';d.mkdir();shutil.copyfile(__file__,d/'original-command.py')
scope=[str(s.relative_to(r)),'.github/workflows/pcc-gate.yml','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
 v=subprocess.run(cmd,cwd=r,capture_output=True);data=v.stdout+v.stderr
 if len(data)>60000:z=lzma.compress(data,format=lzma.FORMAT_XZ);assert lzma.decompress(z)==data;(d/(name+'.txt.xz')).write_bytes(z)
 else:(d/(name+'.txt')).write_bytes(data)
 (d/(name+'.exit')).write_text(str(v.returncode)+'\n');print(name,v.returncode,flush=True);assert v.returncode==0,data.decode(errors='replace')[:1800]
run('portablehashes',['sha256sum','--check',str((s/'g3-norm-reference-01.sha256').relative_to(r))])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github/workflows/chained-transfer-reference.yml',str((s/'g3-norm-checker').relative_to(r)),str((s/'check-g3-norm.sh').relative_to(r)),str((s/'g3-norm-reference-01.sha256').relative_to(r))],cwd=r)
after=(r/'.github/workflows/pcc-gate.yml').read_text();assert after==subprocess.check_output(['git','show',base+':.github/workflows/pcc-gate.yml'],cwd=r,text=True)
subjects=[]
for p in paths():
 if p.startswith(b'pcc/claims/'):
  for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
   if proof.get('kind')=='attestation':
    x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'],x['path'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('actionlint',['/workspace/scratch/actionlint-bin/actionlint','.github/workflows/pcc-gate.yml','.github/workflows/chained-transfer-reference.yml']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
 ps=paths();f=Path('/workspace/scratch/ct56-norm-ci-metadata.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
 for p in subjects:
  if subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected:continue
  path=r/p;manifest=path.parent/'.artifacts.json';m=json.loads(manifest.read_text());entry=m['files'][path.name];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'] and path.stat().st_size==entry['bytes'];assert str(manifest.relative_to(r)).encode() in selected;assert after.count(' '+p)==2,p
 return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(d/'custody.json').write_text(json.dumps(dict(base=base,ownledger_prose_whitespace_wiring_actionlint_benchrec_artifact=0,all437focusedinputs_unchanged=True,no_Rust_Lean_verifier_or_trust_change=True,ONLYPCCworkflowdelta='NONE vs metadataea;prior451/532 exactdataread unchanged',all_new_subjecthashes_andstaging_or_genuine_managedpaths_covered=True,native_full='7b231c COMPLETE',rawactual='48e581/82e079/1dd28b/5327f4',own7CI='168c99 all7SUCCESS exact069/36nativeJSON/24canonicalbindings;settled',report='61f7a2 ONE34768page ALLinspected;earlierreportsimmutable',rootglobal='access/signing/ledger/conflictgaps remain'),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','NormCI metadata governance ownea833ledger/prose/workingcachedwhitespace/wiring/actionlint/benchrec/artifact0/all437focusedinputs unchanged/newsubjecthash/stagingorGENUINEmanageddata coverage. NO new PCCworkflowdelta;prior451bc2 exactb992dataread unchanged;nativeRust/Lean/verifier/trust/whole7workflow unchanged. Completefull7b231c/ALL6+2nativearchivesactuallypublished/primary69520subjectgenuine/ONE34768inspectedCIPDFpage plus earlierfullreport. Firstwiring1/untrackedmanifest andoriginalPCCnot_covered retained. Own7CI168c99 ALLSEVENSUCCESS/36nativeJSON/24canonicalbindings/wholepartial+completearchives genuinelypublishedcfbe78/f5c83d;settled;mainledger/signing/conflict/rootfixture andcostadmission gaps notpromoted.']
for p in sorted(d.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct56-norm-ci-metadata-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: checkpoint seven-job canonical norm CI and complete raw custody'],cwd=r,check=True)
print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
