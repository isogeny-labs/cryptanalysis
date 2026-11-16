"""Owned prospective protocol checkpoint; original repository gates only."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib,shutil
r=Path('/workspace/cryptanalysis');s=r/'experiments/chained-transfer-public-target';base='1e4f1292d473a9c01821d946c0ec846b17f8ae1a'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip()==base
report='pcc/claims/PCC-20261113-ad4849.json'
g=s/'evidence/protocol-governance-02';g.mkdir();shutil.copyfile(__file__,g/'original-command.py')
scope=[str(s.relative_to(r)),'problems/chained-transfer-public-target-destination-bridge.md','problems/README.md','pcc/claims','pcc/ledger.jsonl','docs/session-logs/2026-11-13.md','.resume/RESUME.md']
def paths():return sorted((set(subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z','--',*scope],cwd=r).split(b'\0'))|set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0')))-{b''})
def run(name,cmd):
    v=subprocess.run(cmd,cwd=r,capture_output=True);(g/(name+'.txt')).write_bytes(v.stdout+v.stderr);(g/(name+'.exit')).write_text(str(v.returncode)+'\n');print(name,v.returncode,flush=True);assert v.returncode==0,(v.stdout+v.stderr).decode()[:1800]
run('parent437',['sha256sum','--check','experiments/chained-transfer-reference/g3-norm-reference-01.sha256'])
assert not subprocess.check_output(['git','diff','--name-only',base,'--','tools','suite','.github','experiments/chained-transfer-reference'],cwd=r)
assert not any(p.endswith((b'.rs',b'.lean')) for p in paths())
subjects=[]
for p in paths():
    if p.startswith(b'pcc/claims/'):
        for proof in json.loads((r/p.decode()).read_text()).get('proofs',[]):
            if proof.get('kind')=='attestation':
                x=proof['subject'];assert hashlib.sha256((r/x['path']).read_bytes()).hexdigest()==x['sha256'];subjects.append(x['path'])
run('ledger',['python3','tools/pcc/pcc.py','ledger','verify','--base',base]);run('prose',['python3','tools/pcc/pcc.py','lint-prose',*[p.decode() for p in paths() if p.endswith(b'.md') and not p.endswith(b'/PROTOCOL-01.md')]]);run('whitespace',['git','diff','--check','--',*scope]);run('wiring',['python3','tools/artifacts/wire_workflows.py','--check']);run('benchrec',['python3','tools/benchrec.py','gate'])
def stage():
    ps=paths();f=Path('/workspace/scratch/ct57-protocol-02.paths0');f.write_bytes(b'\0'.join(p for p in ps if p!=b'.resume/RESUME.md')+b'\0');subprocess.run(['git','add','--sparse','--pathspec-from-file='+str(f),'--pathspec-file-nul'],cwd=r,check=True);subprocess.run(['git','add','--sparse','-u','--','.resume/RESUME.md'],cwd=r,check=True);selected=set(subprocess.check_output(['git','diff','--cached','--name-only','-z'],cwd=r).split(b'\0'))-{b''};assert selected==set(ps)
    for p in subjects:assert subprocess.run(['git','cat-file','-e',base+':'+p],cwd=r,capture_output=True).returncode==0 or p.encode() in selected,p
    return selected
stage();run('cached-whitespace',['git','diff','--cached','--check']);tree=subprocess.check_output(['git','write-tree'],cwd=r,text=True).strip();run('artifact',['python3','tools/artifacts/artifacts.py','check',base,tree])
(g/'custody.json').write_text(json.dumps(dict(base=base,all437_parent_inputs_unchanged=True,whole_old7workflow_and_producer_workflow_unchanged=True,no_new_Rust_Lean_native_case=True,own_ledger_required_claim_prose_whitespace_wiring_benchrec_artifact=0,extra_frozen_protocol_future_lint="original1 retained andclarified;not achievedclaim",all_new_attestation_hashes_and_subject_staging_covered=True,protocol='7e016c prospective, publish BEFORE newcases/code',report=report,benchmark_admission=False),indent=2)+'\n')
cmd=['python3','tools/pcc/pcc.py','claim','new','--kind','statement','--claim-type','data','--statement','Publictarget pre-codeprotocol governance:own1e4ledger/requiredclaimprose/workingcachedwhitespace/wiring/benchrec/artifact0;all437parentnativeinputs/whole7workflow unchanged/no newRustLean orcasegeneration. Allnewsubjecthash/stagingcoverage;prospective7e016c andONE35418inspectedproposalPDF. Readychild/normalpublication requiredBEFOREimplementation. Extra future-instruction protocol lint1 retained/clarified;frozen7e016c unchanged/no achievedclaim. No benchmark admission/verifier/trust/policy edits.']
for p in sorted(g.iterdir()):cmd+=['--proof','attestation:'+str(p.relative_to(r))]
cl=subprocess.check_output(cmd,cwd=r,text=True).strip();Path('/workspace/scratch/ct57-protocol-governance.claim').write_text(cl+'\n');selected=stage();subprocess.run(['git','diff','--cached','--check'],cwd=r,check=True);subprocess.run(['git','commit','--quiet','-m','research: freeze public-target N4 continuation before implementation'],cwd=r,check=True);print(cl,subprocess.check_output(['git','log','-1','--format=%H %T %P'],cwd=r,text=True).strip(),len(selected),flush=True)
